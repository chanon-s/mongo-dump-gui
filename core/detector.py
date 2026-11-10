import os
import sys
import shutil
import subprocess
import glob
from pathlib import Path
from typing import Optional, List

from core.models import BinaryInfo


def validate_binary(executable_path: str) -> BinaryInfo:
    """Tests if the given binary is an executable mongodump and returns version info."""
    if not executable_path or not os.path.exists(executable_path):
        return BinaryInfo(
            path=executable_path,
            is_valid=False,
            error="File does not exist"
        )

    try:
        # Avoid creating console window on Windows
        startupinfo = None
        creationflags = 0
        if sys.platform == "win32":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        result = subprocess.run(
            [executable_path, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            startupinfo=startupinfo,
            creationflags=creationflags
        )

        output = result.stdout or result.stderr or ""
        if result.returncode == 0 and "mongodump" in output.lower():
            # Parse first line or version string
            first_line = output.strip().splitlines()[0] if output.strip().splitlines() else output.strip()
            return BinaryInfo(
                path=executable_path,
                is_valid=True,
                version=first_line,
                error=None
            )
        else:
            return BinaryInfo(
                path=executable_path,
                is_valid=False,
                error=f"Unexpected exit code {result.returncode} or output is not mongodump"
            )
    except Exception as e:
        return BinaryInfo(
            path=executable_path,
            is_valid=False,
            error=str(e)
        )


def get_candidate_paths() -> List[str]:
    """Generates a list of candidate filesystem paths to search for mongodump."""
    candidates = []
    binary_name = "mongodump.exe" if sys.platform == "win32" else "mongodump"

    # 1. System PATH
    which_path = shutil.which(binary_name) or shutil.which("mongodump")
    if which_path:
        candidates.append(which_path)

    # 2. OS-specific common installation directories
    if sys.platform == "win32":
        search_patterns = [
            r"C:\Program Files\MongoDB\Tools\*\bin\mongodump.exe",
            r"C:\Program Files\MongoDB\Server\*\bin\mongodump.exe",
            r"C:\mongodb\bin\mongodump.exe",
            r"C:\Tools\mongodb*\bin\mongodump.exe",
        ]
        for pat in search_patterns:
            candidates.extend(glob.glob(pat))
    elif sys.platform == "darwin":
        candidates.extend([
            "/opt/homebrew/bin/mongodump",
            "/usr/local/bin/mongodump",
            "/opt/homebrew/opt/mongodb-database-tools/bin/mongodump",
            "/usr/local/opt/mongodb-database-tools/bin/mongodump",
        ])
    else:  # Linux / Unix
        candidates.extend([
            "/usr/bin/mongodump",
            "/usr/local/bin/mongodump",
            "/opt/mongodb-database-tools/bin/mongodump",
        ])

    return candidates


def detect_mongodump(custom_path: Optional[str] = None) -> BinaryInfo:
    """Finds and validates the mongodump binary, prioritizing custom_path."""
    if custom_path and custom_path.strip():
        validated = validate_binary(custom_path.strip())
        if validated.is_valid:
            return validated
        # If custom path is provided but invalid, return with its error so user sees it
        return validated

    # Check candidates
    for cand in get_candidate_paths():
        validated = validate_binary(cand)
        if validated.is_valid:
            return validated

    binary_name = "mongodump.exe" if sys.platform == "win32" else "mongodump"
    return BinaryInfo(
        path="",
        is_valid=False,
        error=f"Could not locate '{binary_name}'. Please select its path manually."
    )
