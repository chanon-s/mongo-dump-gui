import customtkinter as ctk
from typing import Callable, List, Optional
from tkinter import messagebox


class PresetBar(ctk.CTkFrame):
    """Preset management bar allowing quick switching, saving, and deletion of dump presets."""

    def __init__(
        self,
        master,
        on_preset_selected: Optional[Callable[[str], None]] = None,
        on_save_preset: Optional[Callable[[str], None]] = None,
        on_save_as_preset: Optional[Callable[[str], None]] = None,
        on_delete_preset: Optional[Callable[[str], None]] = None,
        **kwargs
    ):
        super().__init__(master, **kwargs)
        self.on_preset_selected = on_preset_selected
        self.on_save_preset = on_save_preset
        self.on_save_as_preset = on_save_as_preset
        self.on_delete_preset = on_delete_preset

        self.columnconfigure(1, weight=1)

        # Label
        self.lbl_title = ctk.CTkLabel(
            self,
            text="Preset:",
            font=ctk.CTkFont(size=13, weight="bold")
        )
        self.lbl_title.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")

        # Dropdown
        self.dropdown_presets = ctk.CTkOptionMenu(
            self,
            values=["Default"],
            command=self._on_dropdown_change
        )
        self.dropdown_presets.grid(row=0, column=1, padx=5, pady=8, sticky="ew")

        # Buttons Frame
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.grid(row=0, column=2, padx=(5, 10), pady=8, sticky="e")

        self.btn_save = ctk.CTkButton(
            self.btn_frame,
            text="Save",
            width=70,
            command=self._on_save
        )
        self.btn_save.pack(side="left", padx=3)

        self.btn_save_as = ctk.CTkButton(
            self.btn_frame,
            text="Save As...",
            width=85,
            command=self._on_save_as
        )
        self.btn_save_as.pack(side="left", padx=3)

        self.btn_delete = ctk.CTkButton(
            self.btn_frame,
            text="Delete",
            width=70,
            fg_color="#c0392b",
            hover_color="#e74c3c",
            command=self._on_delete
        )
        self.btn_delete.pack(side="left", padx=3)

    def set_presets(self, presets: List[str], current: Optional[str] = None) -> None:
        values = presets if presets else ["Default"]
        self.dropdown_presets.configure(values=values)
        if current and current in values:
            self.dropdown_presets.set(current)
        elif values:
            self.dropdown_presets.set(values[0])

    def get_current_preset(self) -> str:
        return self.dropdown_presets.get()

    def _on_dropdown_change(self, value: str) -> None:
        if self.on_preset_selected:
            self.on_preset_selected(value)

    def _on_save(self) -> None:
        current = self.get_current_preset()
        if self.on_save_preset and current:
            self.on_save_preset(current)

    def _on_save_as(self) -> None:
        dialog = ctk.CTkInputDialog(text="Enter new preset name:", title="Save As New Preset")
        name = dialog.get_input()
        if name and name.strip():
            clean_name = name.strip()
            if self.on_save_as_preset:
                self.on_save_as_preset(clean_name)

    def _on_delete(self) -> None:
        current = self.get_current_preset()
        if current == "Default":
            messagebox.showinfo("Preset", "Cannot delete the Default preset.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete preset '{current}'?"
        )
        if confirm and self.on_delete_preset:
            self.on_delete_preset(current)
