// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Carson McRae
//! Purpose: The TTSNative desktop app: one window that shows the existing web UI from the bundled local
//!   server, started and stopped with the app.
//! Scope: Single instance (a second launch focuses the window or hands it a one-shot reading ticket),
//!   the window (its size and position
//!   remembered, the start-up screen while the server starts), navigation rules (only the start-up
//!   screen and the local server load inside the window; other links open in the default browser),
//!   the commands the web UI may call, and a clean server shutdown on exit. A Microsoft Store build (the
//!   `store` feature) leaves out the updater plugin and tells the web UI that the Store updates it.
//! Does NOT belong: Running the server (backend.rs), updates (updates.rs), file locations (paths.rs) or
//!   deleting the user's data (erase.rs).

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod backend;
mod erase;
mod paths;
mod prefs;
mod updates;

use serde::Serialize;
use std::sync::Mutex;
use tauri::webview::NewWindowResponse;
use tauri::{AppHandle, Manager, RunEvent, Url, WebviewUrl, WebviewWindowBuilder};
use tauri_plugin_opener::OpenerExt;

use crate::backend::{Backend, Status};
use crate::paths::Paths;

/// A request received while the server starts waits for its first navigation. No ticket is logged.
#[derive(Default)]
struct AgentNavigation {
    ready: bool,
    pending: Option<String>,
}

impl AgentNavigation {
    fn receive(&mut self, ticket: String) -> Option<String> {
        if self.ready {
            Some(ticket)
        } else {
            self.pending = Some(ticket);
            None
        }
    }

    fn started(&mut self) -> Option<String> {
        self.ready = true;
        self.pending.take()
    }
}

fn valid_agent_ticket(ticket: &str) -> bool {
    ticket.len() == 64 && ticket.bytes().all(|value| value.is_ascii_digit() || (b'a'..=b'f').contains(&value))
}

fn agent_ticket(args: impl Iterator<Item = String>) -> Option<String> {
    let mut ticket = None;
    for argument in args {
        if let Some(value) = argument.strip_prefix("--agent-read=") {
            if ticket.is_some() || !valid_agent_ticket(value) {
                return None;
            }
            ticket = Some(value.to_string());
        }
    }
    ticket
}

/// The only external argument is an opaque capability: it cannot name a URL, file or executable.
fn agent_target(origin: &str, ticket: &str) -> Option<Url> {
    let mut target = Url::parse(origin).ok()?;
    if !valid_agent_ticket(ticket)
        || target.scheme() != "http"
        || target.host_str() != Some("127.0.0.1")
        || target.origin().ascii_serialization() != origin
    {
        return None;
    }
    target.set_path("/agent-read");
    target.set_fragment(Some(ticket));
    Some(target)
}

fn receive_agent_read(app: &AppHandle, args: impl Iterator<Item = String>) {
    focus_main(app);
    let Some(ticket) = agent_ticket(args) else { return };
    let navigation = app.state::<Mutex<AgentNavigation>>();
    if let Ok(mut navigation) = navigation.lock() {
        if let Some(ticket) = navigation.receive(ticket) {
            if let Some(origin) = app.state::<AppState>().backend.origin() {
                if let (Some(window), Some(target)) = (app.get_webview_window("main"), agent_target(&origin, &ticket)) {
                    let _ = window.navigate(target);
                }
            }
        }
    };
}

pub struct AppState {
    pub paths: Paths,
    pub backend: Backend,
    pub prefs: prefs::Store,
}

#[derive(Serialize)]
#[serde(rename_all = "camelCase")]
struct DesktopInfo {
    version: String,
    channel: &'static str,
    /// Who updates this copy: `app` (its own updater, from GitHub Releases) or `store` (the Microsoft Store).
    updates: &'static str,
    data_dir: String,
    log_dir: String,
    auto_check: bool,
    last_checked_at: Option<u64>,
}

#[tauri::command]
fn desktop_info(app: AppHandle) -> DesktopInfo {
    let state = app.state::<AppState>();
    let version = &app.package_info().version;
    let saved = state.prefs.get();
    DesktopInfo {
        version: version.to_string(),
        channel: if version.pre.is_empty() && version.build.is_empty() {
            "stable"
        } else {
            "development"
        },
        updates: if cfg!(feature = "store") { "store" } else { "app" },
        data_dir: state.paths.data().display().to_string(),
        log_dir: state.paths.logs().display().to_string(),
        auto_check: saved.auto_check,
        last_checked_at: saved.last_check,
    }
}

#[tauri::command]
fn backend_status(app: AppHandle) -> Status {
    app.state::<AppState>().backend.status()
}

#[tauri::command]
fn backend_retry(app: AppHandle) {
    launch(app);
}

#[tauri::command]
fn open_folder(app: AppHandle, which: String) -> Result<(), String> {
    let state = app.state::<AppState>();
    let folder = match which.as_str() {
        "data" => state.paths.data(),
        "logs" => state.paths.logs(),
        // The licences of everything the installer ships, opened in the system's text editor.
        "notices" => state.paths.runtime.join("THIRD-PARTY-NOTICES.txt"),
        _ => return Err("Unknown folder.".into()),
    };
    app.opener()
        .open_path(folder.display().to_string(), None::<&str>)
        .map_err(|error| error.to_string())
}

#[tauri::command]
fn app_quit(app: AppHandle) {
    app.exit(0);
}

/// Starts the server in the background and shows the app once it answers.
pub fn launch(app: AppHandle) {
    if let Ok(mut navigation) = app.state::<Mutex<AgentNavigation>>().lock() {
        navigation.ready = false;
    }
    std::thread::spawn(move || {
        let state = app.state::<AppState>();
        if let Status::Ready { url, origin } = state.backend.start(&state.paths) {
            let main_thread = app.clone();
            // A background navigate is queued, but the single-instance callback navigates inline.
            // Select readiness and navigate on the same UI thread so a queued home cannot replace
            // a newer ticket navigation. Until this task runs, incoming tickets remain pending.
            let _ = app.run_on_main_thread(move || {
                let navigation = main_thread.state::<Mutex<AgentNavigation>>();
                let target = {
                    let Ok(mut navigation) = navigation.lock() else { return };
                    navigation.started().and_then(|ticket| agent_target(&origin, &ticket))
                        .or_else(|| url.parse::<Url>().ok())
                };
                if let (Some(window), Some(target)) = (main_thread.get_webview_window("main"), target) {
                    let _ = window.navigate(target);
                }
            });
        }
    });
}

fn is_start_screen(url: &Url) -> bool {
    url.scheme() == "tauri" || url.host_str() == Some("tauri.localhost")
}

/// Only the start-up screen and the local server load in the window; anything else opens outside it.
fn allow_navigation(app: &AppHandle, url: &Url) -> bool {
    let origin = url.origin().ascii_serialization();
    if is_start_screen(url)
        || app
            .state::<AppState>()
            .backend
            .origin()
            .is_some_and(|own| own == origin)
    {
        return true;
    }
    open_outside(app, url);
    false
}

fn open_outside(app: &AppHandle, url: &Url) {
    if matches!(url.scheme(), "https" | "http" | "mailto") {
        let _ = app.opener().open_url(url.as_str(), None::<&str>);
    }
}

fn focus_main(app: &AppHandle) {
    if let Some(window) = app.get_webview_window("main") {
        let _ = window.unminimize();
        let _ = window.show();
        let _ = window.set_focus();
    }
}

/// WebView2's switches: wry's own (no "mini menu", no SmartScreen prompt, autoplay), plus the debugging
/// switch that only a build with the `test-hooks` feature can add (see `debug_switch`).
#[cfg(windows)]
fn browser_args(args: impl Iterator<Item = String>) -> String {
    let mut switches = String::from(
        "--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection --autoplay-policy=no-user-gesture-required",
    );
    if let Some(switch) = debug_switch(args) {
        switches.push(' ');
        switches.push_str(&switch);
    }
    switches
}

/// Test builds only (the automated installer tests drive the window): Chromium's
/// `--remote-debugging-port=N` on the command line opens that port on 127.0.0.1. The switch text exists
/// only in this build, which is how build.mjs and the release workflow prove a release has no hooks.
#[cfg(all(windows, feature = "test-hooks"))]
fn debug_switch(mut args: impl Iterator<Item = String>) -> Option<String> {
    let port = args.find_map(|arg| {
        arg.strip_prefix("--remote-debugging-port=")
            .and_then(|value| value.parse::<u16>().ok())
    })?;
    Some(format!("--remote-debugging-port={port}"))
}

/// Release builds never enable WebView debugging through command-line arguments.
#[cfg(all(windows, not(feature = "test-hooks")))]
fn debug_switch(_args: impl Iterator<Item = String>) -> Option<String> {
    None
}

fn create_window(app: &AppHandle) -> tauri::Result<()> {
    let navigation = app.clone();
    let popups = app.clone();
    let builder = WebviewWindowBuilder::new(app, "main", WebviewUrl::App("index.html".into()));
    #[cfg(windows)]
    let builder = builder.additional_browser_args(&browser_args(std::env::args()));
    builder
        .title("TTSNative")
        .inner_size(1280.0, 860.0)
        .min_inner_size(420.0, 560.0)
        .center()
        // The web UI handles dropped documents and recordings itself.
        .disable_drag_drop_handler()
        .initialization_script("window.__TTSNATIVE_DESKTOP__ = true;")
        .on_navigation(move |url| allow_navigation(&navigation, url))
        .on_new_window(move |url, _features| {
            open_outside(&popups, &url);
            NewWindowResponse::Deny
        })
        .build()?;
    Ok(())
}

fn main() {
    // WebView2 would also take browser switches from this variable in the process environment; the app
    // never wants that route (a test build takes the switch on its command line instead), so it is
    // dropped before any window exists. The matching registry policy stays an administrator's decision.
    std::env::remove_var("WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS");
    let builder = tauri::Builder::default()
        .manage(Mutex::new(AgentNavigation { ready: false, pending: agent_ticket(std::env::args()) }))
        // Registered first, so a second launch only focuses the running window.
        .plugin(tauri_plugin_single_instance::init(|app, args, _cwd| receive_agent_read(app, args.into_iter())))
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .plugin(tauri_plugin_opener::init());
    // The Store build has no updater at all: the Store replaces the package.
    #[cfg(not(feature = "store"))]
    let builder = builder.plugin(tauri_plugin_updater::Builder::new().build());
    let app = builder
        .setup(|app| {
            let paths = Paths::resolve(app.handle())?;
            paths.ensure()?;
            let prefs = prefs::Store::load(paths.prefs());
            let version = app.package_info().version.to_string();
            app.manage(AppState {
                paths,
                backend: Backend::new(version),
                prefs,
            });
            create_window(app.handle())?;
            launch(app.handle().clone());
            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            app_quit,
            backend_retry,
            backend_status,
            desktop_info,
            erase::delete_user_data,
            open_folder,
            updates::update_check,
            updates::update_install,
            updates::update_set_auto,
            updates::update_snooze,
        ])
        .build(tauri::generate_context!())
        .expect("TTSNative could not start its window");
    app.run(|app, event| {
        if let RunEvent::Exit = event {
            app.state::<AppState>().backend.stop();
        }
    });
}

#[cfg(all(test, windows))]
mod tests {
    use super::{agent_target, agent_ticket, browser_args, AgentNavigation};

    fn started_with(args: &[&str]) -> impl Iterator<Item = String> {
        args.iter()
            .map(|arg| (*arg).to_string())
            .collect::<Vec<_>>()
            .into_iter()
    }

    #[test]
    fn keeps_wrys_own_switches() {
        let switches = browser_args(started_with(&["TTSNative.exe"]));
        assert!(switches.starts_with("--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection"));
        assert!(switches.ends_with("--autoplay-policy=no-user-gesture-required"));
    }

    #[test]
    fn agent_read_accepts_only_one_opaque_ticket() {
        let ticket = "a1".repeat(32);
        assert_eq!(agent_ticket(started_with(&["TTSNative.exe", &format!("--agent-read={ticket}")])), Some(ticket.clone()));
        for value in ["", "a", "https://example.com", "../private", &"G".repeat(64), &"a".repeat(65)] {
            assert_eq!(agent_ticket(started_with(&[&format!("--agent-read={value}")])), None);
        }
        assert_eq!(agent_ticket(started_with(&[&format!("--agent-read={ticket}"), &format!("--agent-read={ticket}")])), None);
        assert_eq!(agent_ticket(started_with(&["TTSNative.exe", "--other"])), None);
    }

    #[test]
    fn agent_read_stays_on_the_owned_loopback_origin() {
        let ticket = "b".repeat(64);
        assert_eq!(agent_target("http://127.0.0.1:8770", &ticket).unwrap().as_str(), format!("http://127.0.0.1:8770/agent-read#{ticket}"));
        for origin in ["invalid", "https://127.0.0.1:8770", "http://localhost:8770", "http://example.com", "http://127.0.0.1:8770/other", "http://user@127.0.0.1:8770"] {
            assert!(agent_target(origin, &ticket).is_none());
        }
        assert!(agent_target("http://127.0.0.1:8770", "javascript:bad").is_none());
    }

    #[test]
    fn agent_read_rejects_argument_injection_and_non_ascii_values() {
        let ticket = "a".repeat(64);
        for value in [
            format!("{ticket};calc.exe"),
            format!("{ticket}\n--remote-debugging-port=9222"),
            format!("{ticket}/../private"),
            "Ａ".repeat(64),
            "١".repeat(64),
            "a".repeat(63) + "\0",
        ] {
            assert!(agent_ticket(started_with(&[&format!("--agent-read={value}")])).is_none());
        }
        assert!(agent_ticket(started_with(&["--agent-read", &ticket])).is_none());
        assert!(agent_ticket(started_with(&["--agent-read=invalid", &format!("--agent-read={ticket}")])).is_none());
        for origin in ["http://127.0.0.1:8770?url=https://example.com", "http://127.0.0.1:8770#other", "http://127.0.0.1:8770@evil.example", "file:///C:/private"] {
            assert!(agent_target(origin, &ticket).is_none());
        }
    }

    #[test]
    fn cold_and_warm_requests_do_not_race_the_initial_navigation() {
        let mut navigation = AgentNavigation::default();
        assert_eq!(navigation.receive("cold".into()), None);
        assert_eq!(navigation.receive("newer-during-startup".into()), None);
        assert_eq!(navigation.started(), Some("newer-during-startup".into()));
        assert_eq!(navigation.pending, None);
        assert_eq!(navigation.receive("warm".into()), Some("warm".into()));
        navigation.ready = false; // Backend retries queue requests until the new origin is ready.
        assert_eq!(navigation.receive("during-retry".into()), None);
        assert_eq!(navigation.started(), Some("during-retry".into()));
        assert_eq!(navigation.started(), None);
    }

    #[cfg(feature = "test-hooks")]
    #[test]
    fn a_test_build_opens_the_port_it_is_given() {
        let switches = browser_args(started_with(&["TTSNative.exe", "--remote-debugging-port=9222"]));
        assert!(switches.ends_with(" --remote-debugging-port=9222"));
    }

    #[cfg(feature = "test-hooks")]
    #[test]
    fn a_test_build_ignores_a_port_that_is_not_a_number() {
        let switches = browser_args(started_with(&["TTSNative.exe", "--remote-debugging-port=nine"]));
        assert!(!switches.contains("debugging"));
    }

    #[cfg(not(feature = "test-hooks"))]
    #[test]
    fn a_release_build_ignores_the_switch() {
        let switches = browser_args(started_with(&["TTSNative.exe", "--remote-debugging-port=9222"]));
        assert!(!switches.contains("debugging"));
    }
}
