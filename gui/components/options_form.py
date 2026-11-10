import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from core.models import DumpOptions


class OptionsForm(ctk.CTkFrame):
    """Configuration form for operational mongodump options."""

    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.columnconfigure(1, weight=1)
        self.columnconfigure(3, weight=1)

        # Row 0: Database & Collection
        self.lbl_db = ctk.CTkLabel(self, text="Database:")
        self.lbl_db.grid(row=0, column=0, padx=(10, 5), pady=6, sticky="w")
        self.entry_db = ctk.CTkEntry(self, placeholder_text="Leave blank to dump all databases")
        self.entry_db.grid(row=0, column=1, padx=(0, 10), pady=6, sticky="ew")

        self.lbl_col = ctk.CTkLabel(self, text="Collection:")
        self.lbl_col.grid(row=0, column=2, padx=(10, 5), pady=6, sticky="w")
        self.entry_col = ctk.CTkEntry(self, placeholder_text="Optional: specific collection")
        self.entry_col.grid(row=0, column=3, padx=(0, 10), pady=6, sticky="ew")

        # Row 1: Exclude Collections & Read Preference
        self.lbl_exclude = ctk.CTkLabel(self, text="Exclude Collections:")
        self.lbl_exclude.grid(row=1, column=0, padx=(10, 5), pady=6, sticky="w")
        self.entry_exclude = ctk.CTkEntry(self, placeholder_text="Comma-separated e.g. logs,temp")
        self.entry_exclude.grid(row=1, column=1, padx=(0, 10), pady=6, sticky="ew")

        self.lbl_read_pref = ctk.CTkLabel(self, text="Read Preference:")
        self.lbl_read_pref.grid(row=1, column=2, padx=(10, 5), pady=6, sticky="w")
        self.dropdown_read_pref = ctk.CTkOptionMenu(
            self,
            values=["primaryPreferred", "primary", "secondaryPreferred", "secondary", "nearest"]
        )
        self.dropdown_read_pref.grid(row=1, column=3, padx=(0, 10), pady=6, sticky="ew")

        # Row 2: Output Format Mode & Parallel Collections
        self.lbl_mode = ctk.CTkLabel(self, text="Output Format:")
        self.lbl_mode.grid(row=2, column=0, padx=(10, 5), pady=6, sticky="w")

        self.seg_mode = ctk.CTkSegmentedButton(
            self,
            values=["Directory", "Single Archive File"],
            command=self._on_mode_changed
        )
        self.seg_mode.set("Directory")
        self.seg_mode.grid(row=2, column=1, padx=(0, 10), pady=6, sticky="ew")

        self.lbl_parallel = ctk.CTkLabel(self, text="Parallel Jobs (-j):")
        self.lbl_parallel.grid(row=2, column=2, padx=(10, 5), pady=6, sticky="w")
        self.entry_parallel = ctk.CTkEntry(self, width=60)
        self.entry_parallel.insert(0, "4")
        self.entry_parallel.grid(row=2, column=3, padx=(0, 10), pady=6, sticky="w")

        # Row 3: Output Path & Gzip
        self.lbl_path = ctk.CTkLabel(self, text="Output Path:")
        self.lbl_path.grid(row=3, column=0, padx=(10, 5), pady=6, sticky="w")

        self.path_container = ctk.CTkFrame(self, fg_color="transparent")
        self.path_container.grid(row=3, column=1, columnspan=2, padx=0, pady=6, sticky="ew")
        self.path_container.columnconfigure(0, weight=1)

        self.entry_out_path = ctk.CTkEntry(self.path_container, placeholder_text="./dump")
        self.entry_out_path.grid(row=0, column=0, padx=(0, 5), sticky="ew")

        self.btn_browse_out = ctk.CTkButton(
            self.path_container,
            text="Browse...",
            width=80,
            command=self._on_browse_output
        )
        self.btn_browse_out.grid(row=0, column=1, padx=(0, 10), sticky="e")

        self.chk_gzip = ctk.CTkCheckBox(self, text="Compress with Gzip (--gzip)")
        self.chk_gzip.select()
        self.chk_gzip.grid(row=3, column=3, padx=(0, 10), pady=6, sticky="w")

    def _on_mode_changed(self, value: str) -> None:
        current_path = self.entry_out_path.get().strip()
        if value == "Single Archive File":
            if not current_path or current_path.endswith("/dump") or current_path.endswith("\\dump"):
                self.entry_out_path.delete(0, tk.END)
                self.entry_out_path.insert(0, "./backup.archive")
        else:
            if current_path.endswith(".archive") or current_path.endswith(".dump"):
                self.entry_out_path.delete(0, tk.END)
                self.entry_out_path.insert(0, "./dump")

    def _on_browse_output(self) -> None:
        if self.seg_mode.get() == "Single Archive File":
            chosen = filedialog.asksaveasfilename(
                title="Select Archive Output File",
                defaultextension=".archive",
                filetypes=[("Archive files", "*.archive *.dump"), ("All files", "*.*")]
            )
        else:
            chosen = filedialog.askdirectory(title="Select Output Directory")

        if chosen:
            self.entry_out_path.delete(0, tk.END)
            self.entry_out_path.insert(0, chosen)

    def get_options(self) -> DumpOptions:
        parallel = 4
        try:
            parallel = int(self.entry_parallel.get().strip())
        except ValueError:
            pass

        mode = "archive" if self.seg_mode.get() == "Single Archive File" else "dir"
        out_path = self.entry_out_path.get().strip()
        if not out_path:
            out_path = "./backup.archive" if mode == "archive" else "./dump"

        return DumpOptions(
            db=self.entry_db.get().strip(),
            collection=self.entry_col.get().strip(),
            output_mode=mode,
            output_path=out_path,
            gzip=bool(self.chk_gzip.get()),
            num_parallel_collections=parallel,
            read_preference=self.dropdown_read_pref.get(),
            exclude_collections=self.entry_exclude.get().strip()
        )

    def set_options(self, options: DumpOptions) -> None:
        self.entry_db.delete(0, tk.END)
        self.entry_db.insert(0, options.db or "")

        self.entry_col.delete(0, tk.END)
        self.entry_col.insert(0, options.collection or "")

        self.entry_exclude.delete(0, tk.END)
        self.entry_exclude.insert(0, options.exclude_collections or "")

        if options.output_mode == "archive":
            self.seg_mode.set("Single Archive File")
        else:
            self.seg_mode.set("Directory")

        self.entry_out_path.delete(0, tk.END)
        self.entry_out_path.insert(0, options.output_path or "")

        if options.gzip:
            self.chk_gzip.select()
        else:
            self.chk_gzip.deselect()

        self.entry_parallel.delete(0, tk.END)
        self.entry_parallel.insert(0, str(options.num_parallel_collections or 4))

        if options.read_preference:
            self.dropdown_read_pref.set(options.read_preference)
