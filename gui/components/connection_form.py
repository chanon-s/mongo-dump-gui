import tkinter as tk
import customtkinter as ctk


class ConnectionForm(ctk.CTkFrame):
    """MongoDB Connection Form.
    
    STRICT ZERO-SECRETS PERSISTENCE:
    The Connection URI is maintained strictly in-memory during application runtime.
    It is never serialized or written to any file or OS storage.
    """

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.columnconfigure(1, weight=1)
        self._is_masked = True

        # Label
        self.lbl_uri = ctk.CTkLabel(
            self,
            text="Connection URI:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_uri.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="w")

        # Entry (password masked by default)
        self.entry_uri = ctk.CTkEntry(
            self,
            show="*",
            placeholder_text="mongodb://user:pass@localhost:27017/?authSource=admin"
        )
        self.entry_uri.grid(row=0, column=1, padx=5, pady=10, sticky="ew")

        # Toggle Button
        self.btn_toggle = ctk.CTkButton(
            self,
            text="Show",
            width=70,
            command=self._toggle_mask
        )
        self.btn_toggle.grid(row=0, column=2, padx=(5, 10), pady=10, sticky="e")

    def get_uri(self) -> str:
        return self.entry_uri.get().strip()

    def set_uri(self, uri: str) -> None:
        self.entry_uri.delete(0, tk.END)
        self.entry_uri.insert(0, uri)

    def _toggle_mask(self) -> None:
        self._is_masked = not self._is_masked
        if self._is_masked:
            self.entry_uri.configure(show="*")
            self.btn_toggle.configure(text="Show")
        else:
            self.entry_uri.configure(show="")
            self.btn_toggle.configure(text="Hide")
