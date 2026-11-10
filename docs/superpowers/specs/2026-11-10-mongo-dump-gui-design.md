# Design Document: Portable Cross-Platform MongoDB Dump GUI

**Date:** 2026-11-10  
**Target Environment:** Windows x86_64 (Primary), macOS, Linux  
**Language/Runtime:** Python 3.10  
**Status:** In Review (Brainstorming Phase)

---

## 1. Intent and Why
MongoDB Database Tools provide the official command-line utility `mongodump` for creating database backups. However, managing complex CLI parameters (URI connection strings, authentication credentials, compression, archive vs. directory outputs, read preferences) can be cumbersome and error-prone when performed manually in terminals.

The goal is to build an intuitive, modern, portable Desktop GUI application that wraps `mongodump`, allows seamless configuration of the binary path across operating systems, remembers settings and presets portably, and provides real-time streaming feedback during backup jobs.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **Portable execution across OSes:** The program runs immediately without an installer across all targets: Windows x86_64 (`.exe`), macOS (`.app` or standalone binary), and Linux (standalone ELF binary), saving its portable configuration locally alongside the executable.
- **Cross-Platform CLI Detection:** Supports finding and selecting `mongodump.exe` (Windows) or `mongodump` (macOS/Linux). Auto-detects if available in system `PATH`.
- **Connection URI First:** Streamlined connection setup via MongoDB Connection URI (with support for username, password, replica sets, TLS/SSL, `mongodb+srv://`, etc.).
- **Common `mongodump` Options Support:**
  - Database (`--db`) and Collection (`--collection`) targeting
  - Output formats: Directory (`--out`) or Single Archive File (`--archive`)
  - Compression (`--gzip`)
  - Parallel collection dumping (`--numParallelCollections`)
  - Replica set read preference (`--readPreference`)
  - Collection exclusions (`--excludeCollection`)
- **Preset Management:** Save, load, update, and delete dump configurations as named presets (e.g. "Staging DB", "Local Docker", "Production Sales") to easily switch between tasks.
- **JSONC Configuration Support:** Supports JSON with comments (`//`, `/* */`, `#`) and trailing commas for portable `config.jsonc` / `config.json` files.
- **Real-Time Log Viewer with Show/Hide Toggle:** Streams `mongodump` stdout/stderr live to the UI without blocking or freezing the application, with start/stop/cancel controls and a **Show/Hide Log** toggle button to expand or collapse the console during/after the dump.
- **Multi-OS Build Support:** Build scripts for Windows, macOS, and Linux, plus a GitHub Actions CI workflow to compile portable binaries for all targets.

### Non-Goals
- **Database Restore GUI (`mongorestore`):** This tool focuses strictly on the dump workflow. (A restore tool can be a separate companion module or future phase).
- **Embedded Database Tools Binaries:** To respect licensing, architecture differences, and version updates, the app points to the user's local `mongodump` binary rather than bundling all platform binaries inside the source repository.
- **Direct Database Driver Access:** The application delegates data dumping entirely to the official `mongodump` CLI tool rather than implementing custom BSON streaming via `pymongo`.

### Anti-Goals
- **Zero Secrets Persistence (Strict Requirement):** Connection strings, URIs, passwords, or credentials must **NEVER** be saved to any file, disk, OS keychain/registry, or persistent storage. They exist exclusively in volatile RAM during runtime.
- **Log Masking:** Passwords and credentials inside URIs must be redacted/masked (e.g., `mongodb://user:***@host...`) before any command string or log line is displayed in the UI.
- **No heavy system installation:** No MSI/installer wizard requiring administrative privileges or Windows registry tampering.
- **No UI freezing:** Long-running dump operations must never lock the GUI thread.
- **No destructive actions without confirmation:** Deleting a preset or canceling an active dump must confirm intent safely.

---

## 3. Constraints
- **Python Version:** 3.10 compatible.
- **Operating System Focus:** Windows x86_64 primary, with full code portability to macOS (x86_64/arm64) and Linux (x86_64).
- **Portability:** Configuration must be written to a local portable path (e.g., `config.jsonc` or `config.json` next to the executable when running as a frozen binary, or next to the script in dev mode).
- **Security & Privacy:** Strictly zero storage of connection URIs or secrets. Presets store only target scopes, output modes, and flags (never connection credentials).

---

## 4. Approaches Considered

### Approach 1: CustomTkinter + Modular Architecture (Selected)
- **UI Framework:** `customtkinter` (modern look, dark/light theme, DPI scaling on Windows, lightweight footprint).
- **Packaging:** PyInstaller single-file portable `.exe`.
- **Pros:** Native-like performance, modern appearance, lightweight bundle (~15-20MB), zero web-engine overhead, simple cross-platform packaging.
- **Cons:** PyInstaller builds native binaries per OS (requires building on each OS or using GitHub Actions CI).

### Approach 2: Standard Tkinter + TTK
- **Pros:** No third-party UI library required.
- **Cons:** Outdated default visual aesthetics, hard to theme smoothly for modern Windows dark/light modes.

### Approach 3: PySide6 (Qt)
- **Pros:** Rich enterprise widget suite.
- **Cons:** Very large binary size (60-100MB+), complex dependency tree for a lightweight utility tool.

---

## 5. Architecture & Component Design

```
mongo-tools/
├── app.py                      # Application entry point
├── core/
│   ├── __init__.py
│   ├── config.py               # Portable config & preset manager (JSON)
│   ├── detector.py             # Binary finder (PATH & validation via --version)
│   ├── dumper.py               # Subprocess runner with async stdout/stderr streaming
│   └── models.py               # Data models (DumpConfig, Preset, BinaryInfo)
├── gui/
│   ├── __init__.py
│   ├── main_window.py          # Main CustomTkinter application window
│   ├── components/
│   │   ├── path_bar.py         # mongodump path selector & validation badge
│   │   ├── preset_bar.py       # Preset dropdown, Save, Save As, Delete
│   │   ├── connection_form.py  # URI input with show/hide password toggle
│   │   ├── options_form.py     # DB, Collection, Output mode, Gzip, ReadPref
│   │   └── log_viewer.py       # Collapsible real-time console log view (Show/Hide Log toggle) & action buttons
├── build/
│   ├── build_windows.bat       # Windows PyInstaller build script
│   ├── build_macos.sh          # macOS PyInstaller build script
│   └── build_linux.sh          # Linux PyInstaller build script
├── .github/
│   └── workflows/
│       └── build.yml           # GitHub Actions automated multi-OS release builder
├── requirements.txt            # Python dependencies (customtkinter, pyinstaller, etc.)
└── README.md                   # User guide & build instructions
```

### 5.1 Configuration & Preset Manager (`core/config.py`)
- Determines the portable base directory:
  - If running as a frozen binary (`getattr(sys, 'frozen', False)`):
    - On macOS inside `.app/Contents/MacOS`: resolves to the parent directory containing the `.app` bundle.
    - On Windows and Linux: uses `os.path.dirname(sys.executable)`.
  - If running from source, uses the project root directory.
- **JSONC (JSON with Comments) Support:**
  - Config reader supports comments (`// ...`, `/* ... */`, `# ...`) and trailing commas so users can manually annotate `config.json` or `config.jsonc`.
  - Automatically loads `config.jsonc` if present, falling back to `config.json`.
- Stores `config.jsonc` / `config.json`:
  ```jsonc
  {
    // Path to MongoDB Database Tools mongodump binary
    "tool_path": "C:\\Tools\\mongodb-database-tools\\bin\\mongodump.exe",
    "last_used_preset": "Default",
    "presets": {
      // Presets store operational parameters ONLY - NEVER connection strings or secrets!
      "Local Dev": {
        "db": "",
        "collection": "",
        "output_mode": "dir",
        "output_path": "./backups",
        "gzip": true,
        "num_parallel_collections": 4,
        "read_preference": "primaryPreferred",
        "exclude_collections": ""
      }
    }
  }
  ```

### 5.2 Tool Detector (`core/detector.py`)
- Searches for `mongodump.exe` (Windows) or `mongodump` (Unix) in:
  1. Configured path from `config.json`
  2. System `PATH` via `shutil.which`
  3. Common default installation paths (e.g., `C:\Program Files\MongoDB\Tools\...\bin`, `/usr/local/bin`, `/opt/homebrew/bin`)
- Validates the executable by running `<path> --version` and extracting the version string.

### 5.3 Dump Execution Engine (`core/dumper.py`)
- Constructs the command array securely:
  `[tool_path, "--uri", uri, ...options]`
- Spawns subprocess using `subprocess.Popen` with `stdout=PIPE`, `stderr=STDOUT` (or merged stream).
- **Log Masking:** Automatically sanitizes passwords/credentials in URI strings before displaying the executed command or log messages to the GUI console.
- Runs log reader on a background worker thread and posts line updates to the UI thread via a thread-safe callback / queue.
- Provides a clean `.cancel()` / `.terminate()` method to abort running jobs gracefully.

### 5.4 Preset Workflow
1. User adjusts fields in the GUI.
2. Clicking **"Save Preset"** updates the operational fields (DB, collection, output, flags) of the selected preset in `config.jsonc`. **Connection URI is strictly excluded and never persisted.**
3. Clicking **"Save As New Preset"** opens a dialog to name a new preset (saving only operational options).
4. Clicking **"Delete Preset"** removes the preset after confirmation.
5. Selecting a preset from the dropdown instantly populates all operational form controls while leaving the in-memory URI untouched.

### 5.5 Collapsible Log Console (Show/Hide Log)
- Below the action buttons (Start / Cancel), there is a **"Show Log" / "Hide Log"** toggle button and a compact status banner (Status: Idle / Dumping... / Finished / Error).
- When collapsed, the window stays compact and clean, showing only progress/status.
- When expanded (Show Log clicked), the scrollable real-time log terminal expands to reveal output from `mongodump` live with auto-scroll and Clear/Copy buttons.
- The toggle state can be switched dynamically at any time without interrupting the active dump process.

---

## 6. What's Left to the Builder
- Precise widget margins, padding, and UI color palettes (dark/light theme tokens).
- Exact regex pattern for masking passwords in logs if desired for security.
- Specific unit and integration test fixtures for config loading/saving and command-line argument construction.
