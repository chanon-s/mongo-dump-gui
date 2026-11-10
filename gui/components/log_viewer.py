import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from typing import Callable, Optional


class LogViewer(ctk.CTkFrame):
    """Execution control and collapsible real-time log viewer."""

    def __init__(
        self,
        master,
        on_start_clicked: Optional[Callable[[], None]] = None,
        on_cancel_clicked: Optional[Callable[[], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_start_clicked = on_start_clicked
        self.on_cancel_clicked = on_cancel_clicked

        self._is_log_expanded = False

        # Top Action Bar
        self.action_bar = ctk.CTkFrame(self, fg_color="transparent")
        self.action_bar.pack(fill="x", padx=10, pady=8)
        self.action_bar.columnconfigure(2, weight=1)

        # Start Dump Button
        self.btn_start = ctk.CTkButton(
            self.action_bar,
            text="Start Dump",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#27ae60",
            hover_color="#2ecc71",
            height=36,
            width=120,
            command=self._on_start
        )
        self.btn_start.grid(row=0, column=0, padx=(0, 5), sticky="w")

        # Cancel Dump Button
        self.btn_cancel = ctk.CTkButton(
            self.action_bar,
            text="Cancel",
            font=ctk.CTkFont(size=13),
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            height=36,
            width=90,
            state="disabled",
            command=self._on_cancel
        )
        self.btn_cancel.grid(row=0, column=1, padx=5, sticky="w")

        # Status text
        self.lbl_status = ctk.CTkLabel(
            self.action_bar,
            text="Status: Ready",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_status.grid(row=0, column=2, padx=10, sticky="w")

        # Show/Hide Log Toggle Button
        self.btn_toggle_log = ctk.CTkButton(
            self.action_bar,
            text="Show Log",
            font=ctk.CTkFont(size=12),
            width=95,
            height=32,
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.toggle_log
        )
        self.btn_toggle_log.grid(row=0, column=3, padx=(5, 0), sticky="e")

        # Collapsible Log Container
        self.log_container = ctk.CTkFrame(self, fg_color="transparent")
        # Starts collapsed (not packed initially)

        # Log Text Box
        self.txt_log = ctk.CTkTextbox(
            self.log_container,
            height=200,
            font=ctk.CTkFont(family="Courier", size=12),
            wrap="word"
        )
        self.txt_log.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Log Tools (Clear & Copy)
        self.log_tools = ctk.CTkFrame(self.log_container, fg_color="transparent")
        self.log_tools.pack(fill="x", padx=10, pady=(0, 8))

        self.btn_clear = ctk.CTkButton(
            self.log_tools,
            text="Clear Log",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#7f8c8d",
            hover_color="#95a5a6",
            command=self.clear_log
        )
        self.btn_clear.pack(side="left", padx=(0, 5))

        self.btn_copy = ctk.CTkButton(
            self.log_tools,
            text="Copy Log",
            width=80,
            height=26,
            font=ctk.CTkFont(size=11),
            fg_color="#34495e",
            hover_color="#2c3e50",
            command=self.copy_log
        )
        self.btn_copy.pack(side="left", padx=5)

    @property
    def is_log_expanded(self) -> bool:
        return self._is_log_expanded

    def toggle_log(self) -> None:
        """Toggles the visibility of the real-time log container."""
        if self._is_log_expanded:
            self.log_container.pack_forget()
            self.btn_toggle_log.configure(text="Show Log")
            self._is_log_expanded = False
        else:
            self.log_container.pack(fill="both", expand=True, padx=0, pady=0)
            self.btn_toggle_log.configure(text="Hide Log")
            self._is_log_expanded = True

    def set_running_state(self, is_running: bool, status_text: str = "") -> None:
        if is_running:
            self.btn_start.configure(state="disabled", fg_color="#7f8c8d")
            self.btn_cancel.configure(state="normal", fg_color="#c0392b", hover_color="#e74c3c")
            self.lbl_status.configure(
                text=status_text or "Status: Running...",
                text_color="#f39c12"  # Amber
            )
        else:
            self.btn_start.configure(state="normal", fg_color="#27ae60")
            self.btn_cancel.configure(state="disabled", fg_color="#7f8c8d")
            self.lbl_status.configure(
                text=status_text or "Status: Ready",
                text_color="#2ecc71" if "completed" in status_text.lower() else ("#e74c3c" if "error" in status_text.lower() or "failed" in status_text.lower() else "white")
            )

    def append_log(self, text: str) -> None:
        self.txt_log.insert(tk.END, text)
        self.txt_log.see(tk.END)

    def clear_log(self) -> None:
        self.txt_log.delete("1.0", tk.END)

    def get_log_text(self) -> str:
        return self.txt_log.get("1.0", tk.END)

    def copy_log(self) -> None:
        text = self.get_log_text().strip()
        if text:
            self.clipboard_clear()
            self.clipboard_append(text)
            messagebox.showinfo("Clipboard", "Log copied to clipboard!")

    def _on_start(self) -> None:
        if self.on_start_clicked:
            self.on_start_clicked()

    def _on_cancel(self) -> None:
        if self.on_cancel_clicked:
            self.on_cancel_clicked()
