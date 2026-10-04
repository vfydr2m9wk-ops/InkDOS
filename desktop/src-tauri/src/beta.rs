//! Beta tools channel: web-edition beta tools delivered to the desktop without a desktop release.
//!
//! A bundle is a tar.gz published as the `inkdos-beta-tools.tar.gz` asset of a `beta-tools-<N>`
//! GitHub prerelease. It holds `manifest.json`, `manifest.json.sig` (minisign, beta-channel key,
//! separate from the updater key) and `files/<path>`. Installation requires a valid signature from
//! the pinned public key, a version newer than the installed one, a host at least `minDesktop`,
//! and every file matching the SHA-256 the signed manifest lists (no extra or missing files).
//!
//! Installed bundles are served only through the `inkdos-beta` scheme, into `beta-*` windows that
//! no capability names and that the app commands refuse: beta code gets no native access.

use std::{
    borrow::Cow,
    collections::BTreeMap,
    fs,
    io::Read,
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
    time::Duration,
};

use base64::Engine;
use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};
use tauri::{http, Manager, Runtime, WebviewUrl, WebviewWindowBuilder};

pub const SCHEME: &str = "inkdos-beta";
pub const WINDOW_PREFIX: &str = "beta-";
const PUBLIC_KEY: &str = include_str!("../beta-channel.pub");
const PUBLIC_KEY_PLACEHOLDER: &str = "INKDOS_BETA_PUBLIC_KEY_REQUIRED";
const RELEASES_API: &str = "https://api.github.com/repos/vfydr2m9wk-ops/InkDOS/releases?per_page=30";
const DOWNLOAD_PREFIX: &str = "https://github.com/vfydr2m9wk-ops/InkDOS/releases/download/beta-tools-";
const TAG_PREFIX: &str = "beta-tools-";
const ASSET_NAME: &str = "inkdos-beta-tools.tar.gz";
const MAX_DOWNLOAD_BYTES: usize = 64 * 1024 * 1024;
const MAX_UNPACKED_BYTES: u64 = 96 * 1024 * 1024;
const MAX_MANIFEST_BYTES: u64 = 1024 * 1024;
const CSP: &str = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'; frame-ancestors 'none'";

static BETA_WINDOW_SEQUENCE: AtomicU64 = AtomicU64::new(1);

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BetaTool {
    id: String,
    title: String,
    entry: String,
}

#[derive(Debug, Deserialize)]
#[serde(rename_all = "camelCase", deny_unknown_fields)]
struct Manifest {
    schema: u32,
    channel: String,
    version: u64,
    commit: String,
    min_desktop: String,
    tools: Vec<BetaTool>,
    files: BTreeMap<String, String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BetaStatus {
    configured: bool,
    installed_version: Option<u64>,
    tools: Vec<BetaTool>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BetaUpdate {
    updated: bool,
    version: Option<u64>,
}

#[derive(Deserialize)]
struct Release {
    tag_name: String,
    prerelease: bool,
    draft: bool,
    assets: Vec<Asset>,
}

#[derive(Deserialize)]
struct Asset {
    name: String,
    browser_download_url: String,
}

fn configured() -> bool {
    let key = PUBLIC_KEY.trim();
    !key.is_empty() && key != PUBLIC_KEY_PLACEHOLDER
}

fn decode_base64_text(value: &str, what: &str) -> Result<String, String> {
    let bytes = base64::engine::general_purpose::STANDARD
        .decode(value.trim())
        .map_err(|_| format!("Beta tools {what} is not valid base64."))?;
    String::from_utf8(bytes).map_err(|_| format!("Beta tools {what} is not valid text."))
}

fn verify_signature(data: &[u8], signature_file: &[u8]) -> Result<(), String> {
    if !configured() {
        return Err("Beta tools are not configured in this InkDOS build.".to_string());
    }
    verify_signature_with(PUBLIC_KEY, data, signature_file)
}

fn verify_signature_with(public_key: &str, data: &[u8], signature_file: &[u8]) -> Result<(), String> {
    let public_key = minisign_verify::PublicKey::decode(&decode_base64_text(public_key, "public key")?)
        .map_err(|_| "Beta tools public key is invalid.".to_string())?;
    let signature_text = std::str::from_utf8(signature_file)
        .map_err(|_| "Beta tools signature is not valid text.".to_string())?;
    let signature = minisign_verify::Signature::decode(&decode_base64_text(signature_text, "signature")?)
        .map_err(|_| "Beta tools signature is invalid.".to_string())?;
    public_key
        .verify(data, &signature, true)
        .map_err(|_| "Beta tools signature does not match: the package was not published by InkDOS.".to_string())
}

/// A relative path made of plain segments only (letters, digits, `.`, `_`, `-`), never `.`/`..`.
fn safe_relative_path(path: &str) -> Option<PathBuf> {
    if path.is_empty() || path.len() > 240 {
        return None;
    }
    let mut out = PathBuf::new();
    for segment in path.split('/') {
        if segment.is_empty()
            || segment == "."
            || segment == ".."
            || !segment
                .bytes()
                .all(|b| b.is_ascii_alphanumeric() || b == b'.' || b == b'_' || b == b'-')
        {
            return None;
        }
        out.push(segment);
    }
    Some(out)
}

fn version_tuple(value: &str) -> Option<(u64, u64, u64)> {
    let mut parts = value.split('.').map(|part| part.parse::<u64>().ok());
    let tuple = (parts.next()??, parts.next()??, parts.next()??);
    parts.next().is_none().then_some(tuple)
}

fn host_version<R: Runtime>(app: &tauri::AppHandle<R>) -> (u64, u64, u64) {
    let version = &app.package_info().version;
    (version.major, version.minor, version.patch)
}

fn parse_manifest(host: (u64, u64, u64), bytes: &[u8]) -> Result<Manifest, String> {
    let manifest: Manifest =
        serde_json::from_slice(bytes).map_err(|error| format!("Beta tools manifest is invalid: {error}"))?;
    if manifest.schema != 1 || manifest.channel != "beta-tools" || manifest.version == 0 {
        return Err("Beta tools manifest is not for this channel.".to_string());
    }
    if manifest.commit.len() != 40 || !manifest.commit.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("Beta tools manifest has an invalid commit.".to_string());
    }
    let required = version_tuple(&manifest.min_desktop)
        .ok_or_else(|| "Beta tools manifest has an invalid minimum version.".to_string())?;
    if host < required {
        return Err(format!(
            "These beta tools need InkDOS {} or newer. Update InkDOS first.",
            manifest.min_desktop
        ));
    }
    if manifest.files.is_empty()
        || manifest.files.iter().any(|(path, hash)| {
            safe_relative_path(path).is_none() || hash.len() != 64 || !hash.bytes().all(|b| b.is_ascii_hexdigit())
        })
    {
        return Err("Beta tools manifest lists an invalid file.".to_string());
    }
    if manifest.tools.is_empty()
        || manifest.tools.iter().any(|tool| {
            tool.id.is_empty()
                || !tool.id.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
                || tool.title.is_empty()
                || tool.title.len() > 80
                || !manifest.files.contains_key(&tool.entry)
        })
    {
        return Err("Beta tools manifest lists an invalid tool.".to_string());
    }
    Ok(manifest)
}

fn root_dir<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<PathBuf, String> {
    app.path()
        .app_local_data_dir()
        .map(|dir| dir.join("beta-tools"))
        .map_err(|error| format!("InkDOS could not locate its data folder: {error}"))
}

fn installed_version(root: &Path) -> Option<u64> {
    let version = fs::read_to_string(root.join("current")).ok()?.trim().parse::<u64>().ok()?;
    root.join(format!("v{version}")).join("manifest.json").is_file().then_some(version)
}

fn installed_manifest<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<Option<(PathBuf, Manifest)>, String> {
    let root = root_dir(app)?;
    let Some(version) = installed_version(&root) else {
        return Ok(None);
    };
    let dir = root.join(format!("v{version}"));
    let bytes = fs::read(dir.join("manifest.json")).map_err(|error| format!("Beta tools are damaged: {error}"))?;
    let signature = fs::read(dir.join("manifest.json.sig")).map_err(|error| format!("Beta tools are damaged: {error}"))?;
    verify_signature(&bytes, &signature)?;
    Ok(Some((dir, parse_manifest(host_version(app), &bytes)?)))
}

fn read_limited<T: Read>(reader: &mut T, limit: u64) -> Result<Vec<u8>, String> {
    let mut data = Vec::new();
    reader
        .take(limit + 1)
        .read_to_end(&mut data)
        .map_err(|error| format!("Beta tools package could not be read: {error}"))?;
    if data.len() as u64 > limit {
        return Err("Beta tools package entry is too large.".to_string());
    }
    Ok(data)
}

/// Verify a downloaded package and install it under `root` as `v<version>`; returns the version.
fn install_package(
    root: &Path,
    host: (u64, u64, u64),
    verify: impl Fn(&[u8], &[u8]) -> Result<(), String>,
    package: &[u8],
    expected_version: u64,
) -> Result<u64, String> {
    let mut archive = tar::Archive::new(flate2::read::GzDecoder::new(package));
    let mut entries = archive
        .entries()
        .map_err(|error| format!("Beta tools package is invalid: {error}"))?;

    let mut next_entry = |expected: &str, limit: u64| -> Result<Vec<u8>, String> {
        let mut entry = entries
            .next()
            .ok_or_else(|| "Beta tools package is incomplete.".to_string())?
            .map_err(|error| format!("Beta tools package is invalid: {error}"))?;
        let name = entry.path().map_err(|_| "Beta tools package is invalid.".to_string())?.to_string_lossy().into_owned();
        if name != expected || !entry.header().entry_type().is_file() {
            return Err("Beta tools package is out of order.".to_string());
        }
        read_limited(&mut entry, limit)
    };
    let manifest_bytes = next_entry("manifest.json", MAX_MANIFEST_BYTES)?;
    let signature = next_entry("manifest.json.sig", 4096)?;
    drop(next_entry);
    verify(&manifest_bytes, &signature)?;
    let manifest = parse_manifest(host, &manifest_bytes)?;
    if manifest.version != expected_version {
        return Err("Beta tools package version does not match its release.".to_string());
    }
    if installed_version(root).is_some_and(|installed| installed >= manifest.version) {
        return Err("Beta tools package is not newer than the installed one.".to_string());
    }

    let staging = root.join(format!("staging-{}", manifest.version));
    let _ = fs::remove_dir_all(&staging);
    fs::create_dir_all(&staging).map_err(|error| format!("InkDOS could not prepare beta tools: {error}"))?;
    let result = (|| -> Result<(), String> {
        let mut remaining: BTreeMap<&str, &str> =
            manifest.files.iter().map(|(path, hash)| (path.as_str(), hash.as_str())).collect();
        let mut unpacked = 0u64;
        for entry in entries {
            let mut entry = entry.map_err(|error| format!("Beta tools package is invalid: {error}"))?;
            if !entry.header().entry_type().is_file() {
                return Err("Beta tools package contains a non-file entry.".to_string());
            }
            let name = entry.path().map_err(|_| "Beta tools package is invalid.".to_string())?.to_string_lossy().into_owned();
            let relative = name
                .strip_prefix("files/")
                .ok_or_else(|| "Beta tools package contains an unexpected entry.".to_string())?
                .to_string();
            let expected_hash = remaining
                .remove(relative.as_str())
                .ok_or_else(|| "Beta tools package contains a file its manifest does not list.".to_string())?;
            let data = read_limited(&mut entry, MAX_UNPACKED_BYTES - unpacked)?;
            unpacked += data.len() as u64;
            let actual = Sha256::digest(&data);
            let actual: String = actual.iter().map(|byte| format!("{byte:02x}")).collect();
            if !actual.eq_ignore_ascii_case(expected_hash) {
                return Err(format!("Beta tools file does not match its signed hash: {relative}"));
            }
            let target = staging.join(safe_relative_path(&relative).ok_or_else(|| "Beta tools path is invalid.".to_string())?);
            if let Some(parent) = target.parent() {
                fs::create_dir_all(parent).map_err(|error| format!("InkDOS could not write beta tools: {error}"))?;
            }
            fs::write(&target, &data).map_err(|error| format!("InkDOS could not write beta tools: {error}"))?;
        }
        if !remaining.is_empty() {
            return Err("Beta tools package is missing files its manifest lists.".to_string());
        }
        fs::write(staging.join("manifest.json"), &manifest_bytes)
            .and_then(|_| fs::write(staging.join("manifest.json.sig"), &signature))
            .map_err(|error| format!("InkDOS could not write beta tools: {error}"))
    })();
    if let Err(error) = result {
        let _ = fs::remove_dir_all(&staging);
        return Err(error);
    }

    let final_dir = root.join(format!("v{}", manifest.version));
    let _ = fs::remove_dir_all(&final_dir);
    fs::rename(&staging, &final_dir).map_err(|error| format!("InkDOS could not install beta tools: {error}"))?;
    let pointer = root.join("current.tmp");
    fs::write(&pointer, manifest.version.to_string())
        .and_then(|_| fs::rename(&pointer, root.join("current")))
        .map_err(|error| format!("InkDOS could not activate beta tools: {error}"))?;
    if let Ok(children) = fs::read_dir(&root) {
        for child in children.flatten() {
            let name = child.file_name().to_string_lossy().into_owned();
            if child.path().is_dir() && name != format!("v{}", manifest.version) {
                let _ = fs::remove_dir_all(child.path());
            }
        }
    }
    Ok(manifest.version)
}

fn latest_release(releases: Vec<Release>) -> Option<(u64, String)> {
    releases
        .into_iter()
        .filter(|release| release.prerelease && !release.draft)
        .filter_map(|release| {
            let version = release.tag_name.strip_prefix(TAG_PREFIX)?.parse::<u64>().ok()?;
            let url = release
                .assets
                .into_iter()
                .find(|asset| asset.name == ASSET_NAME)?
                .browser_download_url;
            url.starts_with(&format!("{DOWNLOAD_PREFIX}{version}/")).then_some((version, url))
        })
        .max_by_key(|(version, _)| *version)
}

pub async fn update<R: Runtime>(app: &tauri::AppHandle<R>) -> Result<BetaUpdate, String> {
    if !configured() {
        return Err("Beta tools are not configured in this InkDOS build.".to_string());
    }
    if rustls::crypto::CryptoProvider::get_default().is_none() {
        let _ = rustls::crypto::ring::default_provider().install_default();
    }
    let client = reqwest::Client::builder()
        .user_agent(format!("InkDOS-desktop/{}", app.package_info().version))
        .timeout(Duration::from_secs(60))
        .https_only(true)
        .build()
        .map_err(|error| format!("InkDOS could not prepare the beta tools download: {error}"))?;
    let releases: Vec<Release> = client
        .get(RELEASES_API)
        .header("Accept", "application/vnd.github+json")
        .send()
        .await
        .and_then(|response| response.error_for_status())
        .map_err(|error| format!("InkDOS could not check for beta tools: {error}"))?
        .json()
        .await
        .map_err(|error| format!("InkDOS could not read the beta tools list: {error}"))?;
    let installed = installed_version(&root_dir(app)?);
    let Some((version, url)) = latest_release(releases) else {
        return Ok(BetaUpdate { updated: false, version: installed });
    };
    if installed.is_some_and(|installed| installed >= version) {
        return Ok(BetaUpdate { updated: false, version: installed });
    }
    let response = client
        .get(&url)
        .send()
        .await
        .and_then(|response| response.error_for_status())
        .map_err(|error| format!("InkDOS could not download beta tools: {error}"))?;
    if response.content_length().is_some_and(|length| length > MAX_DOWNLOAD_BYTES as u64) {
        return Err("Beta tools package is too large.".to_string());
    }
    let package = response
        .bytes()
        .await
        .map_err(|error| format!("InkDOS could not download beta tools: {error}"))?;
    if package.len() > MAX_DOWNLOAD_BYTES {
        return Err("Beta tools package is too large.".to_string());
    }
    let root = root_dir(app)?;
    let host = host_version(app);
    let version = tauri::async_runtime::spawn_blocking(move || install_package(&root, host, verify_signature, &package, version))
        .await
        .map_err(|error| format!("InkDOS could not install beta tools: {error}"))??;
    Ok(BetaUpdate { updated: true, version: Some(version) })
}

pub fn status<R: Runtime>(app: &tauri::AppHandle<R>) -> BetaStatus {
    let installed = if configured() { installed_manifest(app).ok().flatten() } else { None };
    BetaStatus {
        configured: configured(),
        installed_version: installed.as_ref().map(|(_, manifest)| manifest.version),
        tools: installed.map(|(_, manifest)| manifest.tools).unwrap_or_default(),
    }
}

fn scheme_base() -> String {
    if cfg!(windows) || cfg!(target_os = "android") {
        format!("http://{SCHEME}.localhost/")
    } else {
        format!("{SCHEME}://localhost/")
    }
}

pub fn open<R: Runtime>(app: &tauri::AppHandle<R>, tool_id: &str) -> Result<(), String> {
    let (_, manifest) = installed_manifest(app)?
        .ok_or_else(|| "Beta tools are not installed yet. Connect to the internet and try again.".to_string())?;
    let tool = manifest
        .tools
        .iter()
        .find(|tool| tool.id == tool_id)
        .ok_or_else(|| format!("Beta tool not found: {tool_id}"))?;
    let base = scheme_base();
    let url = tauri::Url::parse(&format!("{base}{}", tool.entry))
        .map_err(|error| format!("Beta tool address is invalid: {error}"))?;
    let label = format!("{WINDOW_PREFIX}{}-{}", tool.id, BETA_WINDOW_SEQUENCE.fetch_add(1, Ordering::Relaxed));
    let opener_app = app.clone();
    let window = WebviewWindowBuilder::new(app, &label, WebviewUrl::CustomProtocol(url))
        .title(format!("InkDOS — {}", tool.title))
        .inner_size(1180.0, 820.0)
        .min_inner_size(720.0, 520.0)
        .resizable(true)
        .on_navigation(move |url| {
            if url.as_str().starts_with(&base) {
                return true;
            }
            // External links (e.g. the official ITI validator) open in the user's browser, never here.
            if url.scheme() == "https" {
                use tauri_plugin_opener::OpenerExt;
                let _ = opener_app.opener().open_url(url.as_str(), None::<&str>);
            }
            false
        })
        .build()
        .map_err(|error| format!("InkDOS could not open {}: {error}", tool.title))?;
    let _ = window.set_focus();
    Ok(())
}

fn content_type(path: &str) -> &'static str {
    match path.rsplit('.').next().unwrap_or("").to_ascii_lowercase().as_str() {
        "html" => "text/html; charset=utf-8",
        "js" | "mjs" => "text/javascript; charset=utf-8",
        "css" => "text/css; charset=utf-8",
        "json" => "application/json",
        "svg" => "image/svg+xml",
        "png" => "image/png",
        "wasm" => "application/wasm",
        "txt" | "md" => "text/plain; charset=utf-8",
        _ => "application/octet-stream",
    }
}

fn respond(status: u16, content_type: &str, body: Vec<u8>) -> http::Response<Cow<'static, [u8]>> {
    http::Response::builder()
        .status(status)
        .header("Content-Type", content_type)
        .header("Content-Security-Policy", CSP)
        .header("X-Content-Type-Options", "nosniff")
        .header("Cache-Control", "no-store")
        .body(Cow::Owned(body))
        .unwrap_or_else(|_| http::Response::new(Cow::Borrowed(&[][..])))
}

/// `inkdos-beta` scheme: serves files of the installed, signature-checked bundle to beta windows only.
pub fn serve<R: Runtime>(app: &tauri::AppHandle<R>, webview_label: &str, request: &http::Request<Vec<u8>>) -> http::Response<Cow<'static, [u8]>> {
    if !webview_label.starts_with(WINDOW_PREFIX) || request.method() != http::Method::GET {
        return respond(403, "text/plain", b"Forbidden".to_vec());
    }
    let path = request.uri().path().trim_start_matches('/');
    let Ok(Some((dir, manifest))) = installed_manifest(app) else {
        return respond(404, "text/plain", b"Beta tools are not installed".to_vec());
    };
    let (Some(relative), true) = (safe_relative_path(path), manifest.files.contains_key(path)) else {
        return respond(404, "text/plain", b"Not found".to_vec());
    };
    match fs::read(dir.join(relative)) {
        Ok(body) => respond(200, content_type(path), body),
        Err(_) => respond(404, "text/plain", b"Not found".to_vec()),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rejects_unsafe_paths() {
        for path in ["", "../x", "a/../b", "/abs", "a//b", "a/./b", "a\\b", "a/b c", "C:/x"] {
            assert!(safe_relative_path(path).is_none(), "{path}");
        }
        assert_eq!(safe_relative_path("labs/pdf/index.html"), Some(PathBuf::from("labs/pdf/index.html")));
    }

    #[test]
    fn parses_versions() {
        assert_eq!(version_tuple("2.7.7"), Some((2, 7, 7)));
        assert_eq!(version_tuple("2.7"), None);
        assert_eq!(version_tuple("2.7.7.1"), None);
        assert_eq!(version_tuple("2.x.7"), None);
    }

    #[test]
    fn picks_newest_signed_channel_release() {
        let release = |tag: &str, prerelease: bool, url: &str| Release {
            tag_name: tag.to_string(),
            prerelease,
            draft: false,
            assets: vec![Asset { name: ASSET_NAME.to_string(), browser_download_url: url.to_string() }],
        };
        let ok = |n: u64| format!("{DOWNLOAD_PREFIX}{n}/{ASSET_NAME}");
        let releases = vec![
            release("beta-tools-3", true, &ok(3)),
            release("beta-tools-9", false, &ok(9)),
            release("beta-tools-7", true, "https://evil.example/beta-tools-7/x"),
            release("beta-tools-5", true, &ok(5)),
            release("v2.7.6", false, "https://github.com/vfydr2m9wk-ops/InkDOS/releases/download/v2.7.6/x"),
        ];
        assert_eq!(latest_release(releases), Some((5, ok(5))));
    }

    use base64::engine::general_purpose::STANDARD as B64;
    use ring::signature::{Ed25519KeyPair, KeyPair};

    struct TestKey {
        pair: Ed25519KeyPair,
        public_key_file: String,
    }

    fn test_key(seed: u8) -> TestKey {
        let pair = Ed25519KeyPair::from_seed_unchecked(&[seed; 32]).unwrap();
        let mut raw = b"Ed".to_vec();
        raw.extend_from_slice(&[seed; 8]);
        raw.extend_from_slice(pair.public_key().as_ref());
        let text = format!("untrusted comment: test key\n{}\n", B64.encode(raw));
        TestKey { pair, public_key_file: B64.encode(text) }
    }

    /// A legacy (non-prehashed) minisign signature, base64-wrapped like `tauri signer sign` output.
    fn sign(key: &TestKey, seed: u8, data: &[u8]) -> Vec<u8> {
        let signature = key.pair.sign(data);
        let mut raw = b"Ed".to_vec();
        raw.extend_from_slice(&[seed; 8]);
        raw.extend_from_slice(signature.as_ref());
        let trusted = "timestamp:0\tfile:manifest.json";
        let mut global = signature.as_ref().to_vec();
        global.extend_from_slice(trusted.as_bytes());
        let text = format!(
            "untrusted comment: test\n{}\ntrusted comment: {trusted}\n{}\n",
            B64.encode(raw),
            B64.encode(key.pair.sign(&global).as_ref())
        );
        B64.encode(text).into_bytes()
    }

    fn hex_sha256(data: &[u8]) -> String {
        Sha256::digest(data).iter().map(|b| format!("{b:02x}")).collect()
    }

    fn manifest(version: u64, files: &[(&str, &[u8])]) -> Vec<u8> {
        let files: BTreeMap<String, String> = files.iter().map(|(p, d)| (p.to_string(), hex_sha256(d))).collect();
        serde_json::to_vec(&serde_json::json!({
            "schema": 1, "channel": "beta-tools", "version": version,
            "commit": "0123456789abcdef0123456789abcdef01234567", "minDesktop": "2.7.7",
            "tools": [{"id": "pdf", "title": "PDF tools (beta)", "entry": "labs/pdf/index.html"}],
            "files": files
        }))
        .unwrap()
    }

    fn package(manifest: &[u8], signature: &[u8], files: &[(&str, &[u8])]) -> Vec<u8> {
        let mut builder = tar::Builder::new(flate2::write::GzEncoder::new(Vec::new(), flate2::Compression::fast()));
        let mut add = |name: &str, data: &[u8]| {
            let mut header = tar::Header::new_ustar();
            header.set_size(data.len() as u64);
            header.set_mode(0o644);
            header.set_cksum();
            builder.append_data(&mut header, name, data).unwrap();
        };
        add("manifest.json", manifest);
        add("manifest.json.sig", signature);
        for (path, data) in files {
            add(&format!("files/{path}"), data);
        }
        builder.into_inner().unwrap().finish().unwrap()
    }

    const FILES: &[(&str, &[u8])] = &[("labs/pdf/index.html", b"<!doctype html>"), ("labs/pdf/lab.js", b"1")];

    fn install(root: &Path, key: &TestKey, package: &[u8], version: u64) -> Result<u64, String> {
        let public_key = key.public_key_file.clone();
        install_package(root, (2, 7, 7), move |data, sig| verify_signature_with(&public_key, data, sig), package, version)
    }

    #[test]
    fn installs_a_signed_package_and_refuses_tampering() {
        let dir = tempfile::tempdir().unwrap();
        let root = dir.path().join("beta-tools");
        let key = test_key(7);
        let m1 = manifest(1, FILES);
        assert_eq!(install(&root, &key, &package(&m1, &sign(&key, 7, &m1), FILES), 1), Ok(1));
        assert_eq!(installed_version(&root), Some(1));
        assert_eq!(fs::read(root.join("v1/labs/pdf/lab.js")).unwrap(), b"1");

        let m2 = manifest(2, FILES);
        let good_sig = sign(&key, 7, &m2);
        // a file that does not match its signed hash
        let tampered: &[(&str, &[u8])] = &[("labs/pdf/index.html", b"<!doctype html>"), ("labs/pdf/lab.js", b"2")];
        assert!(install(&root, &key, &package(&m2, &good_sig, tampered), 2).is_err());
        // an extra file the manifest does not list
        let extra: &[(&str, &[u8])] = &[FILES[0], FILES[1], ("labs/pdf/evil.js", b"x")];
        assert!(install(&root, &key, &package(&m2, &good_sig, extra), 2).is_err());
        // a missing file
        assert!(install(&root, &key, &package(&m2, &good_sig, &FILES[..1]), 2).is_err());
        // another key
        let other = test_key(9);
        assert!(install(&root, &key, &package(&m2, &sign(&other, 9, &m2), FILES), 2).is_err());
        // a release tag that does not match the signed version
        assert!(install(&root, &key, &package(&m2, &good_sig, FILES), 3).is_err());
        // the failed attempts left the installed version untouched
        assert_eq!(installed_version(&root), Some(1));

        assert_eq!(install(&root, &key, &package(&m2, &good_sig, FILES), 2), Ok(2));
        assert_eq!(installed_version(&root), Some(2));
        assert!(!root.join("v1").exists());
        // no rollback to an older signed package
        assert!(install(&root, &key, &package(&m1, &sign(&key, 7, &m1), FILES), 1).is_err());
    }

    #[test]
    fn refuses_a_package_for_a_newer_host() {
        let dir = tempfile::tempdir().unwrap();
        let key = test_key(7);
        let m = String::from_utf8(manifest(1, FILES)).unwrap().replace("2.7.7", "9.0.0").into_bytes();
        let public_key = key.public_key_file.clone();
        let result = install_package(
            &dir.path().join("beta-tools"),
            (2, 7, 7),
            move |data, sig| verify_signature_with(&public_key, data, sig),
            &package(&m, &sign(&key, 7, &m), FILES),
            1,
        );
        assert!(result.unwrap_err().contains("9.0.0"));
    }

    /// End-to-end check of a real bundle signed by `cargo tauri signer sign`:
    /// INKDOS_BETA_E2E_PUBKEY=<public key> INKDOS_BETA_E2E_PACKAGE=<tar.gz> INKDOS_BETA_E2E_VERSION=<n>
    /// cargo test -- --ignored beta_e2e
    #[test]
    #[ignore]
    fn beta_e2e_installs_a_cli_signed_bundle() {
        let public_key = std::env::var("INKDOS_BETA_E2E_PUBKEY").unwrap();
        let package = fs::read(std::env::var("INKDOS_BETA_E2E_PACKAGE").unwrap()).unwrap();
        let version: u64 = std::env::var("INKDOS_BETA_E2E_VERSION").unwrap().parse().unwrap();
        let dir = tempfile::tempdir().unwrap();
        let root = dir.path().join("beta-tools");
        let installed = install_package(&root, (2, 7, 7), |d, s| verify_signature_with(&public_key, d, s), &package, version);
        assert_eq!(installed, Ok(version));
        assert!(root.join(format!("v{version}/labs/pdf/index.html")).is_file());
    }

    #[test]
    fn signature_check_refuses_when_unconfigured_or_wrong() {
        if !configured() {
            assert!(verify_signature(b"data", b"").is_err());
        } else {
            assert!(verify_signature(b"data", b"bm90IGEgc2lnbmF0dXJl").is_err());
        }
    }
}
