import os
import sys
import re
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from core.models import DumpOptions


class ConfigManager:
    """Manages portable application configuration and presets in JSONC format.
    
    STRICT SECURITY INVARIANT:
    No connection strings, URIs, passwords, or credentials are ever stored in
    configuration files. Presets store non-sensitive operational parameters only.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir if base_dir is not None else self.get_base_dir()
        self.config_jsonc_path = self.base_dir / "config.jsonc"
        self.config_json_path = self.base_dir / "config.json"

    @staticmethod
    def get_base_dir() -> Path:
        """Determines the portable application root directory."""
        if getattr(sys, "frozen", False):
            exe_dir = Path(sys.executable).resolve().parent
            # On macOS, if inside an .app bundle (e.g. MyApp.app/Contents/MacOS),
            # move up to the folder containing the .app bundle for true portability.
            if "Contents/MacOS" in str(exe_dir):
                return exe_dir.parents[2]
            return exe_dir
        # Development mode: find directory containing this script or project root
        return Path(__file__).resolve().parent.parent

    @staticmethod
    def strip_jsonc_comments(content: str) -> str:
        """Strips C-style (//, /* */) and shell-style (#) comments and trailing commas

        from JSONC strings while strictly preserving string literals.
        """
        # Tokenizer regex: matches string literals OR comments
        pattern = re.compile(
            r'("(?:\\.|[^"\\])*")|'          # Group 1: Double-quoted string
            r'(\/\*[\s\S]*?\*\/)|'           # Group 2: Multi-line C comment
            r'(\/\/[^\r\n]*)|'               # Group 3: Single-line C comment
            r'(#[^\r\n]*)'                   # Group 4: Shell/Python style comment
        )

        def replace_token(match: re.Match) -> str:
            # If it's a quoted string literal, preserve it verbatim
            if match.group(1) is not None:
                return match.group(1)
            # Otherwise it's a comment, strip it
            return ""

        cleaned = pattern.sub(replace_token, content)

        # Remove trailing commas before closing braces/brackets: , \s* [}\]]
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
        return cleaned

    def get_active_config_path(self) -> Path:
        """Returns the config file path, preferring config.jsonc if exists."""
        if self.config_jsonc_path.exists():
            return self.config_jsonc_path
        if self.config_json_path.exists():
            return self.config_json_path
        return self.config_jsonc_path

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration from JSONC/JSON, returning defaults if file doesn't exist."""
        path = self.get_active_config_path()
        if not path.exists():
            return self._default_config()

        try:
            raw_text = path.read_text(encoding="utf-8")
            cleaned = self.strip_jsonc_comments(raw_text)
            data = json.loads(cleaned)
            if not isinstance(data, dict):
                return self._default_config()
            return data
        except Exception:
            # Fallback to safe defaults if malformed
            return self._default_config()

    def save_config(self, data: Dict[str, Any]) -> None:
        """Saves configuration data to config.jsonc.
        
        Strictly sanitizes data to ensure no secret fields are written.
        """
        path = self.get_active_config_path()
        sanitized = self._sanitize_config(data)

        # Format output as formatted JSON with helpful header comment
        formatted_json = json.dumps(sanitized, indent=2, ensure_ascii=False)
        content = (
            "// MongoDB Dump GUI Portable Configuration (JSONC supported)\n"
            "// Note: Connection strings and credentials are NEVER saved here.\n"
            f"{formatted_json}\n"
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def get_tool_path(self) -> str:
        config = self.load_config()
        return config.get("tool_path", "")

    def set_tool_path(self, tool_path: str) -> None:
        config = self.load_config()
        config["tool_path"] = tool_path
        self.save_config(config)

    def get_last_used_preset(self) -> str:
        config = self.load_config()
        return config.get("last_used_preset", "Default")

    def set_last_used_preset(self, preset_name: str) -> None:
        config = self.load_config()
        config["last_used_preset"] = preset_name
        self.save_config(config)

    def list_presets(self) -> List[str]:
        config = self.load_config()
        presets = config.get("presets", {})
        return list(presets.keys())

    def get_preset(self, name: str) -> Optional[DumpOptions]:
        config = self.load_config()
        presets = config.get("presets", {})
        if name in presets:
            return DumpOptions.from_dict(presets[name])
        return None

    def save_preset(self, name: str, options: DumpOptions) -> None:
        config = self.load_config()
        if "presets" not in config:
            config["presets"] = {}
        # Ensure only operational DumpOptions fields are saved
        config["presets"][name] = options.to_dict()
        config["last_used_preset"] = name
        self.save_config(config)

    def delete_preset(self, name: str) -> bool:
        config = self.load_config()
        presets = config.get("presets", {})
        if name in presets:
            del presets[name]
            config["presets"] = presets
            if config.get("last_used_preset") == name:
                config["last_used_preset"] = list(presets.keys())[0] if presets else "Default"
            self.save_config(config)
            return True
        return False

    def _default_config(self) -> Dict[str, Any]:
        return {
            "tool_path": "",
            "last_used_preset": "Default",
            "presets": {
                "Default": DumpOptions().to_dict()
            }
        }

    def _sanitize_config(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures that no secret keys (uri, password, credentials) ever enter the config."""
        forbidden_keys = {"uri", "password", "secret", "credentials", "auth"}
        clean = {}
        for k, v in data.items():
            if k.lower() in forbidden_keys:
                continue
            if isinstance(v, dict):
                clean[k] = self._sanitize_config(v)
            else:
                clean[k] = v
        return clean
