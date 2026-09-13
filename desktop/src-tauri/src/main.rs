#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::{
    path::{Path, PathBuf},
    sync::atomic::{AtomicU64, Ordering},
};

use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_dialog::{DialogExt, MessageDialogKind};

static FILE_WINDOW_SEQUENCE: AtomicU64 = AtomicU64::new(1);
static WORKSPACE_WINDOW_SEQUENCE: AtomicU64 = AtomicU64::new(1);
const WORKSPACES_JSON: &str = include_str!("../../workspaces.json");

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
        .unwrap_or("InkDOS file");
    let path_json = serde_json::to_string(&path.to_string_lossy().to_string())
        .map_err(|error| format!("InkDOS could not prepare the file path: {error}"))?;
    let initialization_script = format!("window.__INKDOS_OPEN_PATH__ = {path_json};");

    let window = WebviewWindowBuilder::new(app, &label, WebviewUrl::App(route.into()))
        .title(format!("InkDOS {workspace} — {file_name}"))
        .inner_size(1280.0, 820.0)
        .min_inner_size(900.0, 600.0)
        .resizable(true)
        .initialization_script(initialization_script)
        .build()
        .map_err(|error| format!("InkDOS could not open {file_name}: {error}"))?;

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
            handle_launch_args(app, args);
        }))
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_opener::init())
        .setup(|app| {
            let opened = handle_launch_args(app.handle(), std::env::args());
            if opened > 0 {
                if let Some(main) = app.get_webview_window("main") {
                    let _ = main.hide();
                }
            }
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running InkDOS desktop");
}
