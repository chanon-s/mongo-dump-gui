import sys
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from typing import Callable, Optional


class PathBar(ctk.CTkFrame):
    """Top bar for configuring and displaying the mongodump CLI binary path and its status."""

    def __init__(
        self,
        master,
        on_path_changed: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_path_changed = on_path_changed

        self.columnconfigure(1, weight=1)

        # Label
        self.lbl_title = ctk.CTkLabel(
            self,
            text="mongodump Path:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, padx=(10, 5), pady=(10, 5), sticky="w")

        # Entry
        self.entry_path = ctk.CTkEntry(self, placeholder_text="Select or enter path to mongodump binary...")
        self.entry_path.grid(row=0, column=1, padx=5, pady=(10, 5), sticky="ew")
        self.entry_path.bind("<FocusOut>", self._on_entry_changed)
        self.entry_path.bind("<Return>", self._on_entry_changed)

        # Browse Button
        self.btn_browse = ctk.CTkButton(
            self,
            text="Browse...",
            width=90,
            command=self._on_browse
        )
        self.btn_browse.grid(row=0, column=2, padx=(5, 10), pady=(10, 5), sticky="e")

        # Status Badge
        self.lbl_status = ctk.CTkLabel(
            self,
            text="Checking binary...",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.lbl_status.grid(row=1, column=0, columnspan=3, padx=10, pady=(0, 8), sticky="w")

    def get_path(self) -> str:
        return self.entry_path.get().strip()

    def set_path(self, path: str) -> None:
        self.entry_path.delete(0, tk.END)
        self.entry_path.insert(0, path)

    def set_status(self, is_valid: bool, message: str) -> None:
        if is_valid:
            self.lbl_status.configure(
                text=f"✓ Ready: {message}",
                text_color="#2ecc71"  # Modern green
            )
        else:
            self.lbl_status.configure(
                text=f"✗ {message}",
                text_color="#e74c3c"  # Modern red
            )

    def _on_browse(self) -> None:
        filetypes = []
        if sys.platform == "win32":
            filetypes = [("Executable files", "*.exe"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*")]

        chosen = filedialog.askopenfilename(
            title="Select mongodump binary",
            filetypes=filetypes
        )
        if chosen:
            self.set_path(chosen)
            if self.on_path_changed:
                self.on_path_changed(chosen)

    def _on_entry_changed(self, event=None) -> None:
        if self.on_path_changed:
            self.on_path_changed(self.get_path())
