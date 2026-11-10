import sys
import re
import shlex
import subprocess
import threading
from typing import Callable, List, Optional

from core.models import DumpOptions


def mask_uri_secrets(text: str) -> str:
    """Masks username:password credentials inside MongoDB URIs in strings and logs."""
    # Matches: mongodb://username:password@... or mongodb+srv://username:password@...
    pattern = re.compile(r'(mongodb(?:\+srv)?:\/\/[^:\s\/]+):([^@\s\/]+)@', re.IGNORECASE)
    return pattern.sub(r'\1:***@', text)


def build_mongodump_args(tool_path: str, uri: str, options: DumpOptions) -> List[str]:
    """Constructs the command-line argument list for mongodump."""
    clean_uri = uri.strip().strip("'\"")
    args = [tool_path, f"--uri={clean_uri}"]

    if options.db and options.db.strip():
        args.append(f"--db={options.db.strip()}")

    if options.collection and options.collection.strip():
        args.append(f"--collection={options.collection.strip()}")

    if options.exclude_collections and options.exclude_collections.strip():
        for col in options.exclude_collections.split(","):
            col_clean = col.strip()
            if col_clean:
                args.append(f"--excludeCollection={col_clean}")

    if options.output_mode == "archive":
        args.append(f"--archive={options.output_path.strip()}")
    else:
        args.append(f"--out={options.output_path.strip()}")

    if options.gzip:
        args.append("--gzip")

    if options.num_parallel_collections > 0:
        args.append(f"--numParallelCollections={options.num_parallel_collections}")

    if options.read_preference and options.read_preference.strip():
        args.append(f"--readPreference={options.read_preference.strip()}")

    return args


class MongoDumper:
    """Manages the background execution of mongodump subprocess with streaming logs."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._thread: Optional[threading.Thread] = None
        self._is_running: bool = False
        self._cancelled: bool = False
        self._lock = threading.Lock()

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    def start(
        self,
        tool_path: str,
        uri: str,
        options: DumpOptions,
        on_log: Callable[[str], None],
        on_finished: Callable[[int], None]
    ) -> None:
        """Starts the mongodump process in a dedicated background worker thread."""
        with self._lock:
            if self._is_running:
                raise RuntimeError("A dump operation is already in progress.")
            self._is_running = True
            self._cancelled = False

        args = build_mongodump_args(tool_path, uri, options)
        masked_cmd = " ".join([mask_uri_secrets(arg) for arg in args])

        def worker():
            returncode = -1
            try:
                on_log(f"> Executing: {masked_cmd}\n")

                creationflags = 0
                if sys.platform == "win32":
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

                self._process = subprocess.Popen(
                    args,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,  # Merge stderr into stdout stream
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    creationflags=creationflags
                )

                if self._process.stdout:
                    for line in iter(self._process.stdout.readline, ""):
                        if not line:
                            break
                        # Always sanitize line before emitting to callback
                        on_log(mask_uri_secrets(line))

                self._process.wait()
                returncode = self._process.returncode

            except Exception as e:
                on_log(f"\n[Error executing mongodump]: {mask_uri_secrets(str(e))}\n")
                returncode = -1
            finally:
                with self._lock:
                    self._is_running = False
                    self._process = None

                if self._cancelled:
                    on_log("\n[Dump cancelled by user]\n")
                elif returncode == 0:
                    on_log("\n[Dump completed successfully]\n")
                else:
                    on_log(f"\n[Dump process exited with code {returncode}]\n")

                on_finished(returncode)

        self._thread = threading.Thread(target=worker, daemon=True)
        self._thread.start()

    def cancel(self) -> None:
        """Cancels the running dump operation."""
        with self._lock:
            if not self._is_running or not self._process:
                return
            self._cancelled = True

        try:
            if sys.platform == "win32":
                # On Windows kill child tree without flashing console window
                flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(self._process.pid)], creationflags=flags)
            else:
                self._process.terminate()
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass

    def wait(self, timeout: Optional[float] = None) -> None:
        """Waits for the worker thread to finish (mainly used for testing)."""
        if self._thread:
            self._thread.join(timeout=timeout)
