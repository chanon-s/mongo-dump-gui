# Portable Cross-Platform MongoDB Dump GUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a portable, cross-platform Desktop GUI application (Python 3.10 + CustomTkinter) that executes `mongodump` from MongoDB Database Tools with live streaming logs, collapsible log viewer, preset management, and JSONC configuration, strictly enforcing zero persistence of credentials and connection strings.

**Architecture:** Modular architecture with clean separation of core logic and GUI components. `core/` manages portable path resolution, JSONC parsing with comment support, zero-secret preset storage, cross-platform binary auto-detection and validation, and asynchronous subprocess execution with URI secret masking. `gui/` builds a responsive CustomTkinter interface with collapsible log console. `build/` and `.github/` provide multi-OS portable packaging for Windows, macOS, and Linux.

**Tech Stack:** Python 3.10, CustomTkinter, PyInstaller, Pytest.

**Spec:** [`docs/superpowers/specs/2026-11-10-mongo-dump-gui-design.md`](file:///Users/chanon/Development/mongo-tools/docs/superpowers/specs/2026-11-10-mongo-dump-gui-design.md)

## Global Constraints

- **Python Version:** 3.10 compatible.
- **Primary Target OS:** Windows x86_64, with portable support for macOS and Linux.
- **Portability:** Config file (`config.jsonc` / `config.json`) saved in the portable application folder (next to the executable or parent directory of macOS `.app`).
- **Zero Secrets Persistence (Strict Requirement):** Connection strings, URIs, passwords, or credentials must NEVER be written to files, disk, OS keychain/registry, or persistent storage. They exist exclusively in memory (RAM).
- **Log Masking:** Passwords/credentials inside URIs must be redacted/masked (e.g., `mongodb://user:***@host...`) before displaying command or log lines in the UI console.
- **JSONC Support:** Config reader must tolerate C-style (`//`, `/* */`), shell-style (`#`) comments, and trailing commas.

## Review Focus

1. **Secret Leakage in Presets:** A user enters a URI with a password and clicks "Save Preset" -> Verify that `config.jsonc` does NOT contain the URI or password under any circumstances.
2. **Secret Leakage in Logs:** `mongodump` prints commands or connection info with a password -> Verify that the regex log masker replaces credentials with `***` before sending to the UI.
3. **Missing or Invalid `mongodump` Binary:** User selects an invalid executable or file path -> App shows a clear validation error badge without crashing.
4. **Active Dump Cancellation:** User clicks "Cancel Dump" mid-process -> Process is terminated cleanly without lingering zombie processes or UI lockup.
5. **Corrupted or Hand-Edited JSONC:** User manually adds comments or trailing commas to `config.jsonc` -> Parser reads correctly; if JSON is malformed, fallback to safe defaults without crashing.

---

### Task 1: Core Models & JSONC Config Manager with Zero-Secrets Policy

**Files:**
- Create: `core/__init__.py`
- Create: `core/models.py`
- Create: `core/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces:
  - `DumpOptions`: Dataclass containing `db`, `collection`, `output_mode` ("dir"|"archive"), `output_path`, `gzip`, `num_parallel_collections`, `read_preference`, `exclude_collections`. (Does NOT store URI!).
  - `BinaryInfo`: Dataclass containing `path`, `is_valid`, `version`, `error`.
  - `ConfigManager`:
    - `get_base_dir() -> Path`
    - `load_config() -> dict`
    - `save_config(data: dict) -> None`
    - `strip_jsonc_comments(content: str) -> str`
    - `save_preset(name: str, options: DumpOptions) -> None`
    - `delete_preset(name: str) -> bool`
    - `get_preset(name: str) -> Optional[DumpOptions]`
    - `list_presets() -> list[str]`

- [ ] **Step 1: Write failing tests for JSONC parsing and Zero-Secrets Config Manager**

```python
# tests/test_config.py
from pathlib import Path
import pytest
from core.models import DumpOptions
from core.config import ConfigManager

def test_jsonc_comment_stripping():
    cm = ConfigManager(base_dir=Path("/tmp"))
    jsonc_text = """
    {
        // Single-line C comment
        /* Multi-line
           comment */
        # Python style comment
        "tool_path": "mongodump.exe",
        "last_used_preset": "Default", // inline comment
    }
    """
    cleaned = cm.strip_jsonc_comments(jsonc_text)
    import json
    data = json.loads(cleaned)
    assert data["tool_path"] == "mongodump.exe"
    assert data["last_used_preset"] == "Default"

def test_zero_secrets_enforcement(tmp_path):
    cm = ConfigManager(base_dir=tmp_path)
    options = DumpOptions(
        db="sales",
        collection="orders",
        output_mode="archive",
        output_path="./sales.dump",
        gzip=True,
    )
    cm.save_preset("Production", options)
    
    # Read raw config file from disk to ensure zero secrets
    raw_content = (tmp_path / "config.jsonc").read_text()
    assert "password" not in raw_content.lower()
    assert "uri" not in raw_content.lower()
    assert "mongodb://" not in raw_content.lower()
    
    # Reload preset
    loaded = cm.get_preset("Production")
    assert loaded is not None
    assert loaded.db == "sales"
    assert loaded.collection == "orders"
    assert loaded.output_mode == "archive"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core'`

- [ ] **Step 3: Implement `core/models.py` and `core/config.py`**

- `core/models.py`: Implement dataclasses `DumpOptions`, `Preset`, `BinaryInfo`.
- `core/config.py`: Implement `ConfigManager` with portable directory resolution (`sys.frozen` check), regex-based comment stripper preserving strings, and preset CRUD that strictly excludes any URI or credentials.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/ tests/test_config.py
git commit -m "feat(core): implement core models and JSONC config manager with zero-secrets policy"
```

---

### Task 2: Binary Detection & Validation

**Files:**
- Create: `core/detector.py`
- Test: `tests/test_detector.py`

**Interfaces:**
- Consumes: `core.models.BinaryInfo`
- Produces:
  - `detect_mongodump(custom_path: Optional[str] = None) -> BinaryInfo`
  - `validate_binary(executable_path: str) -> BinaryInfo`

- [ ] **Step 1: Write failing tests for binary detection and validation**

```python
# tests/test_detector.py
from unittest.mock import patch, MagicMock
import subprocess
from core.detector import detect_mongodump, validate_binary

def test_validate_binary_success():
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="mongodump version: 100.9.4\ngit version: 12345\nGo version: go1.20",
            stderr=""
        )
        info = validate_binary("/mock/bin/mongodump")
        assert info.is_valid is True
        assert "100.9.4" in info.version
        assert info.error is None

def test_validate_binary_failure():
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("Executable not found")
        info = validate_binary("/invalid/path/mongodump")
        assert info.is_valid is False
        assert info.error is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_detector.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core.detector'`

- [ ] **Step 3: Implement `core/detector.py`**

- Use `shutil.which` to locate `mongodump` / `mongodump.exe` in system PATH.
- Check common OS install paths (e.g. `C:\Program Files\MongoDB\Tools\...\bin\mongodump.exe`, `/usr/local/bin/mongodump`, `/opt/homebrew/bin/mongodump`).
- Implement `validate_binary(path)` which executes `[path, "--version"]` with a timeout of 5 seconds, parsing version output.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_detector.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/detector.py tests/test_detector.py
git commit -m "feat(core): implement cross-platform mongodump detector and validator"
```

---

### Task 3: Dump Execution Engine & Log Streamer with Secret Masking

**Files:**
- Create: `core/dumper.py`
- Test: `tests/test_dumper.py`

**Interfaces:**
- Consumes: `core.models.DumpOptions`
- Produces:
  - `mask_uri_secrets(text: str) -> str`
  - `build_mongodump_args(tool_path: str, uri: str, options: DumpOptions) -> list[str]`
  - `MongoDumper`:
    - `is_running: bool`
    - `start(tool_path: str, uri: str, options: DumpOptions, on_log: Callable[[str], None], on_finished: Callable[[int], None]) -> None`
    - `cancel() -> None`

- [ ] **Step 1: Write failing tests for command construction, secret masking, and cancellation**

```python
# tests/test_dumper.py
from core.models import DumpOptions
from core.dumper import mask_uri_secrets, build_mongodump_args, MongoDumper

def test_mask_uri_secrets():
    raw_cmd = "mongodump --uri=mongodb://admin:SuperSecretPass123!@localhost:27017/sales?authSource=admin --gzip"
    masked = mask_uri_secrets(raw_cmd)
    assert "SuperSecretPass123!" not in masked
    assert "mongodb://admin:***@localhost:27017/sales?authSource=admin" in masked

def test_build_mongodump_args_archive():
    opts = DumpOptions(
        db="mydb",
        collection="mycol",
        output_mode="archive",
        output_path="backup.archive",
        gzip=True,
        num_parallel_collections=2,
        read_preference="secondaryPreferred"
    )
    args = build_mongodump_args("/usr/bin/mongodump", "mongodb://localhost:27017", opts)
    assert args[0] == "/usr/bin/mongodump"
    assert "--uri=mongodb://localhost:27017" in args
    assert "--db=mydb" in args
    assert "--collection=mycol" in args
    assert "--archive=backup.archive" in args
    assert "--gzip" in args
    assert "--numParallelCollections=2" in args
    assert "--readPreference=secondaryPreferred" in args
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_dumper.py -v`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core.dumper'`

- [ ] **Step 3: Implement `core/dumper.py`**

- Implement `mask_uri_secrets(text: str) -> str` using regex matching standard `mongodb://` and `mongodb+srv://` URIs with username and password.
- Implement `build_mongodump_args(...)`.
- Implement `MongoDumper` thread runner using `subprocess.Popen(..., stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)`.
- Stream lines to `on_log(masked_line)`.
- Implement `cancel()` to send SIGTERM/SIGKILL (or `taskkill` on Windows) and set flag.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_dumper.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add core/dumper.py tests/test_dumper.py
git commit -m "feat(core): implement dump runner with streaming logs and credential masking"
```

---

### Task 4: GUI Form Components (Path, Preset, Connection, Options)

**Files:**
- Create: `gui/__init__.py`
- Create: `gui/components/__init__.py`
- Create: `gui/components/path_bar.py`
- Create: `gui/components/preset_bar.py`
- Create: `gui/components/connection_form.py`
- Create: `gui/components/options_form.py`
- Test: `tests/test_gui_components.py`

**Interfaces:**
- Consumes: `core.models.DumpOptions`, `core.config.ConfigManager`, `core.detector`
- Produces:
  - `PathBar`: Component with entry, browse button, and validation status label.
  - `PresetBar`: Component with dropdown, "Save", "Save As", "Delete" buttons, triggering callbacks.
  - `ConnectionForm`: Component with URI input, show/hide password toggle button.
  - `OptionsForm`: Component with DB, Collection, Exclude, Directory/Archive toggle, path browse, Gzip checkbox, Parallel jobs spinbox, ReadPreference dropdown.
  - `get_dump_options() -> DumpOptions`
  - `set_dump_options(options: DumpOptions) -> None`

- [ ] **Step 1: Write tests for form state conversion**

```python
# tests/test_gui_components.py
from core.models import DumpOptions

def test_options_form_data_mapping():
    opts = DumpOptions(
        db="mydb",
        collection="users",
        output_mode="dir",
        output_path="./dump",
        gzip=True,
        num_parallel_collections=4,
        read_preference="primary",
        exclude_collections="logs,cache"
    )
    assert opts.db == "mydb"
    assert opts.output_mode == "dir"
    assert opts.gzip is True
```

- [ ] **Step 2: Implement CustomTkinter components**

- Implement `PathBar` in `gui/components/path_bar.py`.
- Implement `PresetBar` in `gui/components/preset_bar.py` with custom modal dialog for "Save As".
- Implement `ConnectionForm` in `gui/components/connection_form.py` with password masking `show="*"` toggle.
- Implement `OptionsForm` in `gui/components/options_form.py` with `get_dump_options()` and `set_dump_options()`.

- [ ] **Step 3: Run component tests**

Run: `pytest tests/test_gui_components.py -v`  
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add gui/ tests/test_gui_components.py
git commit -m "feat(gui): create modular form components for path, presets, connection, and options"
```

---

### Task 5: Collapsible Log Viewer & Main Window Assembly

**Files:**
- Create: `gui/components/log_viewer.py`
- Create: `gui/main_window.py`
- Create: `app.py`
- Test: `tests/test_integration.py`

**Interfaces:**
- Consumes: All `core` and `gui/components` modules
- Produces:
  - `LogViewer`: Collapsible frame with Start/Cancel buttons, Status badge, "Show Log" / "Hide Log" toggle button, scrollable CTkTextbox, Clear and Copy buttons.
  - `MongoDumpApp(customtkinter.CTk)`: Assembled desktop window with thread-safe UI updates.

- [ ] **Step 1: Write integration tests**

```python
# tests/test_integration.py
from core.config import ConfigManager
from core.models import DumpOptions
from core.dumper import build_mongodump_args, mask_uri_secrets

def test_full_dump_pipeline(tmp_path):
    cm = ConfigManager(base_dir=tmp_path)
    opts = DumpOptions(
        db="testdb",
        collection="",
        output_mode="archive",
        output_path=str(tmp_path / "test.dump"),
        gzip=True
    )
    cm.save_preset("MyBackup", opts)
    loaded = cm.get_preset("MyBackup")
    assert loaded is not None
    
    cmd = build_mongodump_args("/bin/mongodump", "mongodb://user:pass@127.0.0.1:27017", loaded)
    masked = mask_uri_secrets(" ".join(cmd))
    assert "pass" not in masked
    assert "user:***@" in masked
```

- [ ] **Step 2: Run test to verify it fails if anything is missing**

Run: `pytest tests/test_integration.py -v`  
Expected: PASS

- [ ] **Step 3: Implement `gui/components/log_viewer.py`, `gui/main_window.py`, and `app.py`**

- `log_viewer.py`:
  - Top action row: Start Dump button, Cancel Dump button, Status text ("Ready", "Running...", "Completed", "Cancelled", "Error"), "Show Log" / "Hide Log" toggle button.
  - Collapsible container: `CTkTextbox` containing live streaming logs, with "Clear" and "Copy to Clipboard" buttons. Toggle button calls `.pack()` / `.pack_forget()` to smoothly expand or hide the log container.
- `main_window.py`:
  - Combines `PathBar`, `PresetBar`, `ConnectionForm`, `OptionsForm`, and `LogViewer`.
  - Wire actions: on preset change, fill options. On start dump: validate path and URI (check URI is non-empty), construct options, invoke `MongoDumper.start()`.
  - Handle thread synchronization via `window.after(0, ...)`.
- `app.py`:
  - Entry point initializing CustomTkinter theme (System/Dark), creating `MongoDumpApp`, and starting `mainloop()`.

- [ ] **Step 4: Run all tests**

Run: `pytest -v`  
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add gui/components/log_viewer.py gui/main_window.py app.py tests/test_integration.py
git commit -m "feat(gui): implement collapsible log viewer, main window assembly, and app entry point"
```

---

### Task 6: Multi-OS Build Scripts, GitHub Actions CI & Documentation

**Files:**
- Create: `requirements.txt`
- Create: `build/build_windows.bat`
- Create: `build/build_macos.sh`
- Create: `build/build_linux.sh`
- Create: `.github/workflows/build.yml`
- Create: `README.md`

**Interfaces:**
- Produces:
  - Portable single-file Windows executable `MongoDumpGUI.exe` via PyInstaller.
  - Portable standalone binary for macOS and Linux.
  - Automated CI workflow building assets on push/release.
  - Comprehensive documentation explaining portable usage, JSONC config, preset usage, and build steps.

- [ ] **Step 1: Create `requirements.txt`**

Specify `customtkinter`, `pyinstaller`, `pytest`.

- [ ] **Step 2: Implement build scripts**

- `build/build_windows.bat`:
  `pyinstaller --noconfirm --onedir --windowed --name "MongoDumpGUI" --add-data ".../customtkinter;customtkinter/" app.py` (or `--onefile` portable).
- `build/build_macos.sh`:
  PyInstaller script targeting macOS standalone app/binary.
- `build/build_linux.sh`:
  PyInstaller script targeting Linux standalone binary.

- [ ] **Step 3: Implement `.github/workflows/build.yml`**

Matrix workflow (`windows-latest`, `macos-latest`, `ubuntu-latest`) running PyInstaller and uploading release artifacts.

- [ ] **Step 4: Create `README.md`**

Provide user guide:
- Features overview
- How to run in development mode
- How to build portable executables
- Zero-secrets security model explanation
- JSONC configuration and presets documentation

- [ ] **Step 5: Run full test suite and verify file structure**

Run: `pytest -v`  
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add requirements.txt build/ .github/ README.md
git commit -m "feat(build): add multi-OS packaging scripts, GitHub Actions workflow, and documentation"
```
