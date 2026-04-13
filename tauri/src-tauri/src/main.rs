#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::io::Write;
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tauri::State;

struct AppState {
    llama_child: Mutex<Option<Child>>,
}

#[derive(serde::Deserialize)]
struct LaunchOptions {
    model_path: String,
    threads: Option<u32>,
    context_length: Option<u32>,
    gpu_layers: Option<u32>,
}

#[derive(serde::Serialize)]
struct ProcessStatus {
    running: bool,
}

#[tauri::command]
fn start_model(opts: LaunchOptions, state: State<AppState>) -> Result<String, String> {
    let mut guard = state.llama_child.lock().map_err(|_| "mutex poisoned")?;
    if guard.is_some() {
        return Err("Model already running".into());
    }

    let threads = opts.threads.unwrap_or(8).to_string();
    let context = opts.context_length.unwrap_or(4096).to_string();
    let gpu_layers = opts.gpu_layers.unwrap_or(0).to_string();

    let child = Command::new("llama-cli")
        .arg("-m")
        .arg(opts.model_path)
        .arg("-t")
        .arg(threads)
        .arg("-c")
        .arg(context)
        .arg("-ngl")
        .arg(gpu_layers)
        .arg("--interactive")
        .stdin(Stdio::piped())
        .stdout(Stdio::null())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| e.to_string())?;

    *guard = Some(child);
    Ok("started".into())
}

#[tauri::command]
fn stop_model(state: State<AppState>) -> Result<String, String> {
    let mut guard = state.llama_child.lock().map_err(|_| "mutex poisoned")?;
    if let Some(child) = guard.as_mut() {
        child.kill().map_err(|e| e.to_string())?;
    }
    *guard = None;
    Ok("stopped".into())
}

#[tauri::command]
fn model_status(state: State<AppState>) -> Result<ProcessStatus, String> {
    let guard = state.llama_child.lock().map_err(|_| "mutex poisoned")?;
    Ok(ProcessStatus {
        running: guard.is_some(),
    })
}

#[tauri::command]
fn send_prompt(prompt: String, state: State<AppState>) -> Result<String, String> {
    let mut guard = state.llama_child.lock().map_err(|_| "mutex poisoned")?;
    let child = guard.as_mut().ok_or("Model is not running")?;
    let stdin = child.stdin.as_mut().ok_or("Model stdin unavailable")?;
    stdin
        .write_all(format!("{}\n", prompt).as_bytes())
        .map_err(|e| e.to_string())?;
    Ok("prompt_sent".into())
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            llama_child: Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![start_model, stop_model, model_status, send_prompt])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
