from unittest.mock import patch, MagicMock
from core.detector import detect_mongodump, validate_binary

def test_validate_binary_success():
    with patch("os.path.exists", return_value=True), patch("subprocess.run") as mock_run:
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
    with patch("os.path.exists", return_value=True), patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("Executable not found")
        info = validate_binary("/invalid/path/mongodump")
        assert info.is_valid is False
        assert info.error is not None

def test_detect_mongodump_from_custom_valid():
    with patch("core.detector.validate_binary") as mock_val:
        from core.models import BinaryInfo
        mock_val.return_value = BinaryInfo(path="/custom/mongodump", is_valid=True, version="100.9.4")
        info = detect_mongodump("/custom/mongodump")
        assert info.is_valid is True
        assert info.path == "/custom/mongodump"

def test_detect_mongodump_fallback_to_path():
    with patch("shutil.which") as mock_which, patch("core.detector.validate_binary") as mock_val:
        from core.models import BinaryInfo
        mock_which.return_value = "/usr/bin/mongodump"
        mock_val.return_value = BinaryInfo(path="/usr/bin/mongodump", is_valid=True, version="100.9.4")
        
        info = detect_mongodump("")
        assert info.is_valid is True
        assert info.path == "/usr/bin/mongodump"
