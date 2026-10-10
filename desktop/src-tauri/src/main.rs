#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    collections::HashMap,
    path::{Path, PathBuf},
    sync::{
        atomic::{AtomicU64, Ordering},
        Mutex, OnceLock,
    },
};

use serde::Serialize;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};
use tauri_plugin_updater::UpdaterExt;

static FILE_WINDOW_SEQUENCE: AtomicU64 = AtomicU64::new(1);
static WORKSPACE_WINDOW_SEQUENCE: AtomicU64 = AtomicU64::new(1);
static OPEN_FILE_TOKEN_SEQUENCE: AtomicU64 = AtomicU64::new(1);
static OPEN_FILE_TOKENS: OnceLock<Mutex<HashMap<String, PathBuf>>> = OnceLock::new();
static OFFICE_WINDOW_SEQUENCE: AtomicU64 = AtomicU64::new(1);
/// Full version (Home engine switch): the ONLYOFFICE editors of InkDOS Office, on their own origin. They open in
/// `office-*` windows: no IPC (not in any capability, refused by require_trusted_window), navigation limited to
/// that origin. WebView2 keeps their offline copy in the app's own data folder, so after the first use they open
/// with no network.
const OFFICE_HOST: &str = "inkdos-tools.github.io";
const OFFICE_EXTENSIONS: &[&str] = &["docx", "doc", "odt", "rtf", "xlsx", "xls", "ods", "csv", "pptx", "ppt", "odp"];
/// A file handed to an office window travels inside its start script; larger files open in the Light version.
const MAX_OFFICE_FILE_BYTES: u64 = 64 * 1024 * 1024;
const OFFICE_OPEN_SCRIPT: &str = include_str!("office_open.js");
const WORKSPACES_JSON: &str = include_str!("../../workspaces.json");

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct UpdateCheckResponse {
    available: bool,
    current_version: String,
    latest_version: String,
    notes: Option<String>,
    pub_date: Option<String>,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct NativeOpenFile {
    name: String,
    bytes: Vec<u8>,
}

fn open_file_tokens() -> &'static Mutex<HashMap<String, PathBuf>> {
    OPEN_FILE_TOKENS.get_or_init(|| Mutex::new(HashMap::new()))
}

fn register_open_file(path: &Path) -> Result<String, String> {
    let sequence = OPEN_FILE_TOKEN_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    let token = format!("inkdos-open-{}-{sequence}", std::process::id());
    let mut files = open_file_tokens()
        .lock()
        .map_err(|_| "InkDOS could not prepare the associated file.".to_string())?;
    files.insert(token.clone(), path.to_path_buf());
    Ok(token)
}

fn discard_open_file(token: &str) {
    if let Ok(mut files) = open_file_tokens().lock() {
        files.remove(token);
    }
}

const MAX_OPEN_FILE_BYTES: u64 = 256 * 1024 * 1024;

/// InkDOS windows only ever show the app's own pages. Any other
/// navigation, e.g. a footer link to GitHub, opens https in the user's browser instead of inside an
/// InkDOS window.
fn is_app_page(url: &tauri::Url) -> bool {
    match url.scheme() {
        "tauri" => url.host_str() == Some("localhost"),
        "http" | "https" => url.host_str() == Some("tauri.localhost"),
        "about" | "blob" | "data" => true,
        _ => false,
    }
}

fn is_office_page(url: &tauri::Url) -> bool {
    url.scheme() == "https" && url.host_str() == Some(OFFICE_HOST)
}

fn navigation_guard<R: tauri::Runtime>() -> tauri::plugin::TauriPlugin<R> {
    tauri::plugin::Builder::new("inkdos-navigation")
        .on_navigation(|webview, url| {
            if is_app_page(url) {
                return true;
            }
            // an office window stays on the office site (any other page opens in the browser)
            if webview.label().starts_with("office-") && is_office_page(url) {
                return true;
            }
            if url.scheme() == "https" || url.scheme() == "mailto" {
                use tauri_plugin_opener::OpenerExt;
                let _ = webview.app_handle().opener().open_url(url.as_str(), None::<&str>);
            }
            false
        })
        .build()
}

/// App commands are for InkDOS's own windows only (office windows get no native access).
fn require_trusted_window<R: tauri::Runtime>(webview: &tauri::Webview<R>) -> Result<(), String> {
    let label = webview.label();
    if label == "main" || label.starts_with("file-") || label.starts_with("workspace-") {
        Ok(())
    } else {
        Err("This window is not allowed to use InkDOS desktop commands.".to_string())
    }
}

#[tauri::command]
fn inkdos_read_open_file(webview: tauri::Webview, token: String) -> Result<NativeOpenFile, String> {
    require_trusted_window(&webview)?;
    let path = {
        let mut files = open_file_tokens()
            .lock()
            .map_err(|_| "InkDOS could not access the associated file token.".to_string())?;
        files
            .remove(&token)
            .ok_or_else(|| "The associated file token is invalid or has already been used.".to_string())?
    };

    if !path.is_file() {
        return Err(format!("File not found: {}", path.display()));
    }
    let name = path
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("InkDOS file")
        .to_string();
    // Larger than any workspace accepts; refuse before reading it into memory and over IPC.
    let size = std::fs::metadata(&path)
        .map_err(|error| format!("InkDOS could not read {name}: {error}"))?
        .len();
    if size > MAX_OPEN_FILE_BYTES {
        return Err(format!("{name} is too large for InkDOS ({} MB; the limit is {} MB).", size / (1024 * 1024), MAX_OPEN_FILE_BYTES / (1024 * 1024)));
    }
    let bytes = std::fs::read(&path)
        .map_err(|error| format!("InkDOS could not read {name}: {error}"))?;
    Ok(NativeOpenFile { name, bytes })
}

#[tauri::command]
async fn inkdos_check_for_updates(
    app: tauri::AppHandle,
    webview: tauri::Webview,
) -> Result<UpdateCheckResponse, String> {
    require_trusted_window(&webview)?;
    let current_version = app.package_info().version.to_string();
    let updater = app
        .updater()
        .map_err(|error| format!("InkDOS updater is not configured: {error}"))?;
    let update = updater
        .check()
        .await
        .map_err(|error| format!("InkDOS could not check for updates: {error}"))?;

    match update {
        Some(update) => Ok(UpdateCheckResponse {
            available: true,
            current_version: update.current_version,
            latest_version: update.version,
            notes: update.body,
            pub_date: update.date.map(|date| date.to_string()),
        }),
        None => Ok(UpdateCheckResponse {
            available: false,
            current_version: current_version.clone(),
            latest_version: current_version,
            notes: None,
            pub_date: None,
        }),
    }
}

#[tauri::command]
async fn inkdos_install_update(
    app: tauri::AppHandle,
    webview: tauri::Webview,
    expected_version: String,
) -> Result<(), String> {
    require_trusted_window(&webview)?;
    if expected_version.trim().is_empty() {
        return Err("InkDOS updater requires an explicitly approved version.".to_string());
    }

    let updater = app
        .updater()
        .map_err(|error| format!("InkDOS updater is not configured: {error}"))?;
    let update = updater
        .check()
        .await
        .map_err(|error| format!("InkDOS could not revalidate the update: {error}"))?
        .ok_or_else(|| "The selected InkDOS update is no longer available. Check again.".to_string())?;

    if update.version != expected_version {
        return Err(format!(
            "InkDOS update changed from {expected_version} to {}. Check again before installing.",
            update.version
        ));
    }

    update
        .download_and_install(|_, _| {}, || {})
        .await
        .map_err(|error| format!("InkDOS could not install update {expected_version}: {error}"))
}

/// The ONLYOFFICE editor language for an InkDOS language code (the editor's own site codes).
fn office_locale(lang: &str) -> Option<&'static str> {
    match lang.split('-').next().unwrap_or("").to_ascii_lowercase().as_str() {
        "pt" => Some("pt"),
        "es" => Some("es"),
        "de" => Some("de"),
        "ja" => Some("ja"),
        "fr" => Some("fr"),
        "ru" => Some("ru"),
        "zh" => Some("zh-CN"),
        _ => None,
    }
}

fn open_office_window(
    app: &tauri::AppHandle,
    path_and_query: &str,
    title: String,
    script: Option<String>,
) -> Result<(), String> {
    let url = tauri::Url::parse(&format!("https://{OFFICE_HOST}{path_and_query}"))
        .map_err(|error| format!("InkDOS could not open the full version: {error}"))?;
    let label = format!("office-{}", OFFICE_WINDOW_SEQUENCE.fetch_add(1, Ordering::Relaxed));
    let mut builder = WebviewWindowBuilder::new(app, &label, WebviewUrl::External(url))
        .title(title)
        .inner_size(1280.0, 820.0)
        .min_inner_size(900.0, 600.0)
        .resizable(true);
    if let Some(script) = script {
        builder = builder.initialization_script(script);
    }
    let window = builder
        .build()
        .map_err(|error| format!("InkDOS could not open the full version: {error}"))?;
    window
        .set_focus()
        .map_err(|error| format!("InkDOS opened the full version but could not focus its window: {error}"))?;
    Ok(())
}

/// Home, Full version: the InkDOS Office start page (Open / New for Word, Excel and PowerPoint) in an office window.
#[tauri::command]
fn inkdos_open_office(app: tauri::AppHandle, webview: tauri::Webview, theme: String, lang: String) -> Result<(), String> {
    require_trusted_window(&webview)?;
    let theme = if theme == "dark" { "dark" } else { "light" };
    let mut query = format!("/?inkdos-theme={theme}");
    if !lang.is_empty() && lang.len() <= 10 && lang.chars().all(|c| c.is_ascii_alphanumeric() || c == '-') {
        query.push_str("&lang=");
        query.push_str(&lang);
    }
    open_office_window(&app, &query, "InkDOS Office".to_string(), None)
}

/// A Word, Excel or PowerPoint file opened from the system, with the Full version chosen: the workspace window that
/// received it hands its token over, the file opens in an office window (the ONLYOFFICE editor's embed mode, driven
/// from inside its own origin) and the workspace window closes. Ok(false) when the file is not for the full version
/// (another format, or too large); the token then stays for the workspace.
#[tauri::command]
fn inkdos_open_office_file(app: tauri::AppHandle, webview: tauri::Webview, token: String, lang: String) -> Result<bool, String> {
    require_trusted_window(&webview)?;
    let path = open_file_tokens()
        .lock()
        .map_err(|_| "InkDOS could not access the associated file token.".to_string())?
        .get(&token)
        .cloned()
        .ok_or_else(|| "The associated file token is invalid or has already been used.".to_string())?;
    let extension = path_extension(&path)?;
    if !OFFICE_EXTENSIONS.contains(&extension.as_str()) {
        return Ok(false);
    }
    let size = std::fs::metadata(&path)
        .map_err(|error| format!("InkDOS could not read {}: {error}", path.display()))?
        .len();
    if size > MAX_OFFICE_FILE_BYTES {
        return Ok(false);
    }
    let name = path.file_name().and_then(|value| value.to_str()).unwrap_or("document").to_string();
    let bytes = std::fs::read(&path).map_err(|error| format!("InkDOS could not read {name}: {error}"))?;
    use base64::Engine;
    let data = base64::engine::general_purpose::STANDARD.encode(bytes);
    let name_json = serde_json::to_string(&name).map_err(|error| error.to_string())?;
    let script = OFFICE_OPEN_SCRIPT
        .replacen("__NAME__", &name_json, 1)
        .replacen("__DATA__", &format!("\"{data}\""), 1);
    let mut query = format!("/editor?embed=1&embedOrigin=https%3A%2F%2F{OFFICE_HOST}");
    if let Some(locale) = office_locale(&lang) {
        query.push_str("&locale=");
        query.push_str(locale);
    }
    // the token stays until the office window exists, so a failure still leaves the file to the workspace
    open_office_window(&app, &query, format!("InkDOS Office — {name}"), Some(script))?;
    discard_open_file(&token);
    // the workspace window only received the file for the office window; it closes
    let _ = webview.window().close();
    Ok(true)
}

fn workspace_manifest() -> Result<serde_json::Map<String, serde_json::Value>, String> {
    let manifest: serde_json::Value = serde_json::from_str(WORKSPACES_JSON)
        .map_err(|error| format!("InkDOS workspace manifest is invalid: {error}"))?;
    manifest
        .as_object()
        .cloned()
        .ok_or_else(|| "InkDOS workspace manifest is invalid.".to_string())
}

fn workspace_for_id(workspace: &str) -> Result<String, String> {
    let workspaces = workspace_manifest()?;
    let entry = workspaces
        .get(workspace)
        .ok_or_else(|| format!("Unsupported InkDOS workspace: {workspace}"))?;
    entry
        .get("route")
        .and_then(|value| value.as_str())
        .map(str::to_string)
        .ok_or_else(|| format!("InkDOS workspace '{workspace}' has no desktop route."))
}

fn path_extension(path: &Path) -> Result<String, String> {
    path.extension()
        .and_then(|value| value.to_str())
        .map(|value| value.to_ascii_lowercase())
        .ok_or_else(|| "Unsupported file format: the selected file has no extension.".to_string())
}

fn workspace_supports_path(workspace: &str, path: &Path) -> Result<String, String> {
    let extension = path_extension(path)?;
    let workspaces = workspace_manifest()?;
    let entry = workspaces
        .get(workspace)
        .ok_or_else(|| format!("Unsupported InkDOS workspace: {workspace}"))?;
    let supports_extension = entry
        .get("extensions")
        .and_then(|value| value.as_array())
        .map(|extensions| {
            extensions.iter().any(|candidate| {
                candidate
                    .as_str()
                    .map(|candidate| candidate.eq_ignore_ascii_case(&extension))
                    .unwrap_or(false)
            })
        })
        .unwrap_or(false);

    if !supports_extension {
        return Err(format!("InkDOS {workspace} does not accept .{extension} files."));
    }

    workspace_for_id(workspace)
}

fn workspace_for_path(path: &Path) -> Result<(String, String), String> {
    let extension = path_extension(path)?;
    let workspaces = workspace_manifest()?;
    for (workspace, entry) in &workspaces {
        let supports_extension = entry
            .get("extensions")
            .and_then(|value| value.as_array())
            .map(|extensions| {
                extensions.iter().any(|candidate| {
                    candidate
                        .as_str()
                        .map(|candidate| candidate.eq_ignore_ascii_case(&extension))
                        .unwrap_or(false)
                })
            })
            .unwrap_or(false);

        if supports_extension {
            return Ok((workspace.clone(), workspace_for_id(workspace)?));
        }
    }

    Err(format!("Unsupported file format: .{extension}"))
}

fn open_workspace_window(app: &tauri::AppHandle, workspace: &str) -> Result<(), String> {
    let route = workspace_for_id(workspace)?;
    let sequence = WORKSPACE_WINDOW_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    let label = format!("workspace-{workspace}-{sequence}");
    let title = format!("InkDOS {workspace}");

    let window = WebviewWindowBuilder::new(app, &label, WebviewUrl::App(route.into()))
        .title(title)
        .inner_size(1280.0, 820.0)
        .min_inner_size(900.0, 600.0)
        .resizable(true)
        .build()
        .map_err(|error| format!("InkDOS could not open the {workspace} workspace: {error}"))?;

    window
        .set_focus()
        .map_err(|error| format!("InkDOS opened {workspace} but could not focus its window: {error}"))?;
    Ok(())
}

fn open_file_window_at_route(
    app: &tauri::AppHandle,
    workspace: &str,
    route: String,
    path: PathBuf,
) -> Result<(), String> {
    let sequence = FILE_WINDOW_SEQUENCE.fetch_add(1, Ordering::Relaxed);
    let label = format!("file-{sequence}");
    let file_name = path
        .file_name()
        .and_then(|value| value.to_str())
        .unwrap_or("InkDOS file")
        .to_string();
    let token = register_open_file(&path)?;
    let token_json = serde_json::to_string(&token)
        .map_err(|error| format!("InkDOS could not prepare the associated file token: {error}"))?;
    let initialization_script = format!("window.__INKDOS_OPEN_TOKEN__ = {token_json};");

    let window = match WebviewWindowBuilder::new(app, &label, WebviewUrl::App(route.into()))
        .title(format!("InkDOS {workspace} — {file_name}"))
        .inner_size(1280.0, 820.0)
        .min_inner_size(900.0, 600.0)
        .resizable(true)
        .initialization_script(initialization_script)
        .build()
    {
        Ok(window) => window,
        Err(error) => {
            discard_open_file(&token);
            return Err(format!("InkDOS could not open {file_name}: {error}"));
        }
    };

    window
        .set_focus()
        .map_err(|error| format!("InkDOS opened {file_name} but could not focus its window: {error}"))?;
    Ok(())
}

fn open_file_window(app: &tauri::AppHandle, path: PathBuf) -> Result<(), String> {
    if !path.is_file() {
        return Err(format!("File not found: {}", path.display()));
    }

    let (workspace, route) = workspace_for_path(&path)?;
    open_file_window_at_route(app, &workspace, route, path)
}

fn open_file_window_for_workspace(
    app: &tauri::AppHandle,
    workspace: &str,
    path: PathBuf,
) -> Result<(), String> {
    if !path.is_file() {
        return Err(format!("File not found: {}", path.display()));
    }

    let route = workspace_supports_path(workspace, &path)?;
    open_file_window_at_route(app, workspace, route, path)
}

fn show_open_error(app: &tauri::AppHandle, message: String) {
    app.dialog()
        .message(message)
        .kind(MessageDialogKind::Error)
        .title("InkDOS — Unsupported file")
        .show(|_| {});
}

fn is_current_executable(path: &Path) -> bool {
    let Ok(executable) = std::env::current_exe() else {
        return false;
    };
    match (path.canonicalize(), executable.canonicalize()) {
        (Ok(path), Ok(executable)) => path == executable,
        _ => path == executable,
    }
}

/// The Home window (`main` in tauri.conf.json, created on demand: `"create": false`). A launch that opens
/// files or a workspace does not start it, so closing those windows ends the app; a launch without
/// either (or a second launch while InkDOS runs) shows Home, created again if it was closed.
fn show_home(app: &tauri::AppHandle) {
    if let Some(home) = app.get_webview_window("main") {
        let _ = home.unminimize();
        let _ = home.show();
        let _ = home.set_focus();
        return;
    }
    let Some(config) = app.config().app.windows.iter().find(|window| window.label == "main") else {
        return;
    };
    match WebviewWindowBuilder::from_config(app, config).and_then(|builder| builder.build()) {
        Ok(home) => {
            let _ = home.set_focus();
        }
        Err(error) => show_open_error(app, format!("InkDOS could not open its Home: {error}")),
    }
}

fn handle_launch_args<I>(app: &tauri::AppHandle, args: I) -> usize
where
    I: IntoIterator<Item = String>,
{
    let args: Vec<String> = args.into_iter().collect();
    let mut opened = 0;
    let mut index = 0;
    let mut active_workspace: Option<String> = None;

    while index < args.len() {
        let raw = &args[index];
        if raw == "--workspace" {
            if let Some(workspace) = args.get(index + 1) {
                active_workspace = Some(workspace.clone());
                match open_workspace_window(app, workspace) {
                    Ok(()) => opened += 1,
                    Err(error) => show_open_error(app, error),
                }
                index += 2;
                continue;
            }
            show_open_error(app, "InkDOS workspace launcher is missing a workspace id.".to_string());
            index += 1;
            continue;
        }

        let path = PathBuf::from(raw);
        if !is_current_executable(&path) && path.is_file() {
            let result = if let Some(workspace) = active_workspace.as_deref() {
                open_file_window_for_workspace(app, workspace, path)
            } else {
                open_file_window(app, path)
            };
            match result {
                Ok(()) => opened += 1,
                Err(error) => show_open_error(app, error),
            }
        }
        index += 1;
    }

    opened
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_single_instance::init(|app, args, _cwd| {
            if handle_launch_args(app, args) == 0 {
                show_home(app);
            }
        }))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .plugin(navigation_guard())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .invoke_handler(tauri::generate_handler![
            inkdos_read_open_file,
            inkdos_check_for_updates,
            inkdos_install_update,
            inkdos_open_office,
            inkdos_open_office_file
        ])
        .setup(|app| {
            // a hidden Home used to stay alive behind a launched file, so the app never exited
            if handle_launch_args(app.handle(), std::env::args()) == 0 {
                show_home(app.handle());
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running InkDOS desktop");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn office_windows_stay_on_the_office_site() {
        assert!(is_office_page(&tauri::Url::parse("https://inkdos-tools.github.io/editor?embed=1").unwrap()));
        assert!(!is_office_page(&tauri::Url::parse("http://inkdos-tools.github.io/").unwrap()));
        assert!(!is_office_page(&tauri::Url::parse("https://vfydr2m9wk-ops.github.io/InkDOS/").unwrap()));
        assert!(!is_office_page(&tauri::Url::parse("https://inkdos-tools.github.io.example.com/").unwrap()));
        // the office site is never an app page: main and workspace windows cannot navigate there
        assert!(!is_app_page(&tauri::Url::parse("https://inkdos-tools.github.io/").unwrap()));
    }

    #[test]
    fn office_locale_follows_the_inkdos_language() {
        assert_eq!(office_locale("pt-BR"), Some("pt"));
        assert_eq!(office_locale("zh-CN"), Some("zh-CN"));
        assert_eq!(office_locale("en"), None);
        assert_eq!(office_locale(""), None);
    }

    #[test]
    fn office_open_script_has_its_placeholders_once() {
        assert_eq!(OFFICE_OPEN_SCRIPT.matches("__NAME__").count(), 1);
        assert_eq!(OFFICE_OPEN_SCRIPT.matches("__DATA__").count(), 1);
        assert!(OFFICE_OPEN_SCRIPT.contains("location.origin !== 'https://inkdos-tools.github.io'"));
    }
}
