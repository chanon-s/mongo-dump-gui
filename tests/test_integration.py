import customtkinter as ctk
import pytest
from core.config import ConfigManager
from core.models import DumpOptions
from core.dumper import build_mongodump_args, mask_uri_secrets
from gui.components.log_viewer import LogViewer

@pytest.fixture(scope="module")
def root_window():
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.withdraw()
    yield root
    try:
        root.destroy()
    except Exception:
        pass

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

def test_log_viewer_toggle(root_window):
    frame = ctk.CTkFrame(root_window)
    log_viewer = LogViewer(frame)
    
    # Initial state is collapsed
    assert not log_viewer.is_log_expanded
    assert log_viewer.btn_toggle_log.cget("text") == "Show Log"
    
    # Toggle to show log
    log_viewer.toggle_log()
    assert log_viewer.is_log_expanded
    assert log_viewer.btn_toggle_log.cget("text") == "Hide Log"
    
    # Append logs
    log_viewer.append_log("Test log entry\n")
    assert "Test log entry" in log_viewer.get_log_text()
    
    # Clear log
    log_viewer.clear_log()
    assert log_viewer.get_log_text().strip() == ""
