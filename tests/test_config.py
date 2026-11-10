from pathlib import Path
import json
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
        num_parallel_collections=4,
        read_preference="primaryPreferred",
        exclude_collections="cache"
    )
    cm.save_preset("Production", options)
    
    # Read raw config file from disk to ensure zero secrets
    config_file = tmp_path / "config.jsonc"
    assert config_file.exists()
    raw_content = config_file.read_text(encoding="utf-8")
    assert "password" not in raw_content.lower()
    assert "uri" not in raw_content.lower()
    assert "mongodb://" not in raw_content.lower()
    
    # Reload preset
    loaded = cm.get_preset("Production")
    assert loaded is not None
    assert loaded.db == "sales"
    assert loaded.collection == "orders"
    assert loaded.output_mode == "archive"
    assert loaded.output_path == "./sales.dump"
    assert loaded.gzip is True
    assert loaded.num_parallel_collections == 4
    assert loaded.read_preference == "primaryPreferred"
    assert loaded.exclude_collections == "cache"

def test_preset_deletion(tmp_path):
    cm = ConfigManager(base_dir=tmp_path)
    options = DumpOptions(db="testdb")
    cm.save_preset("TempPreset", options)
    assert "TempPreset" in cm.list_presets()
    
    deleted = cm.delete_preset("TempPreset")
    assert deleted is True
    assert "TempPreset" not in cm.list_presets()
    assert cm.get_preset("TempPreset") is None
