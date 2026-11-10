import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from core.config import ConfigManager
from core.detector import detect_mongodump, validate_binary
from core.dumper import MongoDumper
from core.models import DumpOptions, BinaryInfo
from gui.components.path_bar import PathBar
from gui.components.preset_bar import PresetBar
from gui.components.connection_form import ConnectionForm
from gui.components.options_form import OptionsForm
from gui.components.log_viewer import LogViewer


class MongoDumpApp(ctk.CTk):
    """Main Application Window for Portable MongoDB Dump GUI."""

    def __init__(self, config_manager: ConfigManager = None):
        super().__init__()

        self.title("MongoDB Dump GUI (Portable)")
        self.geometry("820x680")
        self.minsize(720, 520)

        # Set default appearance
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.config_manager = config_manager or ConfigManager()
        self.dumper = MongoDumper()
        self.binary_info = BinaryInfo(path="", is_valid=False)

        self._build_ui()
        self._initialize_data()

        # Handle window closing when dump process may be running
        self.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)

        # Header / Branding
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=15, pady=(12, 4))

        self.lbl_app_title = ctk.CTkLabel(
            self.header_frame,
            text="🍃 MongoDB Dump GUI",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.lbl_app_title.pack(side="left")

        self.lbl_version_badge = ctk.CTkLabel(
            self.header_frame,
            text="Portable • Zero-Secrets",
            font=ctk.CTkFont(size=11),
            text_color="#95a5a6"
        )
        self.lbl_version_badge.pack(side="left", padx=10, pady=(4, 0))

        # Main scrollable or stacked container
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True, padx=15, pady=5)

        # 1. Path Bar
        self.path_bar = PathBar(
            self.container,
            on_path_changed=self._on_path_changed
        )
        self.path_bar.pack(fill="x", pady=4)

        # 2. Preset Bar
        self.preset_bar = PresetBar(
            self.container,
            on_preset_selected=self._on_preset_selected,
            on_save_preset=self._on_save_preset,
            on_save_as_preset=self._on_save_as_preset,
            on_delete_preset=self._on_delete_preset
        )
        self.preset_bar.pack(fill="x", pady=4)

        # 3. Connection URI Form
        self.conn_form = ConnectionForm(self.container)
        self.conn_form.pack(fill="x", pady=4)

        # 4. Dump Options Form
        self.options_form = OptionsForm(self.container)
        self.options_form.pack(fill="x", pady=4)

        # 5. Collapsible Log Viewer & Controls
        self.log_viewer = LogViewer(
            self.container,
            on_start_clicked=self._on_start_dump,
            on_cancel_clicked=self._on_cancel_dump
        )
        self.log_viewer.pack(fill="both", expand=True, pady=4)

    def _initialize_data(self) -> None:
        """Initializes application state from portable config and detects tools."""
        # 1. Detect or load mongodump path
        saved_tool_path = self.config_manager.get_tool_path()
        self.binary_info = detect_mongodump(saved_tool_path)
        if self.binary_info.path:
            self.path_bar.set_path(self.binary_info.path)
            self._update_binary_status(self.binary_info)
        else:
            self.path_bar.set_status(False, "mongodump not found. Please click Browse.")

        # 2. Load presets into dropdown
        presets = self.config_manager.list_presets()
        last_used = self.config_manager.get_last_used_preset()
        self.preset_bar.set_presets(presets, current=last_used)

        # 3. Load active preset options into form
        active_opts = self.config_manager.get_preset(last_used)
        if active_opts:
            self.options_form.set_options(active_opts)

    def _update_binary_status(self, info: BinaryInfo) -> None:
        if info.is_valid:
            self.path_bar.set_status(True, info.version or "Valid binary")
        else:
            self.path_bar.set_status(False, info.error or "Invalid binary")

    def _on_path_changed(self, new_path: str) -> None:
        if not new_path.strip():
            self.binary_info = BinaryInfo(path="", is_valid=False, error="Path is empty")
            self._update_binary_status(self.binary_info)
            return

        self.binary_info = validate_binary(new_path)
        self._update_binary_status(self.binary_info)
        if self.binary_info.is_valid:
            self.config_manager.set_tool_path(new_path)

    def _on_preset_selected(self, preset_name: str) -> None:
        opts = self.config_manager.get_preset(preset_name)
        if opts:
            self.options_form.set_options(opts)
            self.config_manager.set_last_used_preset(preset_name)

    def _on_save_preset(self, preset_name: str) -> None:
        opts = self.options_form.get_options()
        self.config_manager.save_preset(preset_name, opts)
        messagebox.showinfo("Preset Saved", f"Preset '{preset_name}' updated successfully.")

    def _on_save_as_preset(self, new_name: str) -> None:
        opts = self.options_form.get_options()
        self.config_manager.save_preset(new_name, opts)
        presets = self.config_manager.list_presets()
        self.preset_bar.set_presets(presets, current=new_name)
        messagebox.showinfo("Preset Saved", f"New preset '{new_name}' created successfully.")

    def _on_delete_preset(self, preset_name: str) -> None:
        if self.config_manager.delete_preset(preset_name):
            presets = self.config_manager.list_presets()
            last_used = self.config_manager.get_last_used_preset()
            self.preset_bar.set_presets(presets, current=last_used)
            active_opts = self.config_manager.get_preset(last_used)
            if active_opts:
                self.options_form.set_options(active_opts)

    def _on_start_dump(self) -> None:
        # Validate binary
        current_path = self.path_bar.get_path()
        if current_path != self.binary_info.path or not self.binary_info.is_valid:
            self.binary_info = validate_binary(current_path)
            self._update_binary_status(self.binary_info)
            if not self.binary_info.is_valid:
                messagebox.showerror(
                    "Invalid Tool Path",
                    f"Please specify a valid mongodump executable before running.\n\nError: {self.binary_info.error}"
                )
                return
            self.config_manager.set_tool_path(current_path)

        # Validate URI
        uri = self.conn_form.get_uri()
        if not uri:
            messagebox.showerror("Missing URI", "Please provide a MongoDB Connection URI.")
            return

        # Automatically reveal log if it was hidden so user can see progress
        if not self.log_viewer.is_log_expanded:
            self.log_viewer.toggle_log()

        options = self.options_form.get_options()
        self.log_viewer.set_running_state(True, "Status: Dumping...")

        def on_log(line: str):
            self.after(0, self.log_viewer.append_log, line)

        def on_finished(returncode: int):
            self.after(0, self._on_dump_finished, returncode)

        try:
            self.dumper.start(
                tool_path=self.binary_info.path,
                uri=uri,
                options=options,
                on_log=on_log,
                on_finished=on_finished
            )
        except Exception as e:
            self.log_viewer.set_running_state(False, "Status: Error")
            messagebox.showerror("Execution Error", str(e))

    def _on_cancel_dump(self) -> None:
        if not self.dumper.is_running:
            return
        confirm = messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel the current dump?")
        if confirm:
            self.log_viewer.append_log("\n>>> Cancelling dump process...\n")
            self.dumper.cancel()

    def _on_dump_finished(self, returncode: int) -> None:
        if self.dumper.is_cancelled:
            self.log_viewer.set_running_state(False, "Status: Cancelled")
        elif returncode == 0:
            self.log_viewer.set_running_state(False, "Status: Completed Successfully")
            messagebox.showinfo("Dump Complete", "MongoDB dump completed successfully!")
        else:
            self.log_viewer.set_running_state(False, f"Status: Failed (Code {returncode})")

    def _on_window_close(self) -> None:
        """Gracefully handle window close when a background dump is in progress."""
        if self.dumper.is_running:
            if messagebox.askyesno("Exit Application", "A dump is currently running. Cancel dump and exit?"):
                self.dumper.cancel()
                self.destroy()
        else:
            self.destroy()
