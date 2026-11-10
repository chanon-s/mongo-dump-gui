import tkinter as tk
import customtkinter as ctk
import pytest
from core.models import DumpOptions
from core.config import ConfigManager
from gui.components.options_form import OptionsForm
from gui.components.connection_form import ConnectionForm
from gui.components.path_bar import PathBar
from gui.components.preset_bar import PresetBar

@pytest.fixture(scope="module")
def root_window():
    ctk.set_appearance_mode("Dark")
    root = ctk.CTk()
    root.withdraw()  # Off-screen for tests
    yield root
    try:
        root.destroy()
    except Exception:
        pass

def test_options_form_get_set(root_window):
    frame = ctk.CTkFrame(root_window)
    options_form = OptionsForm(frame)
    
    test_opts = DumpOptions(
        db="analytics",
        collection="events",
        output_mode="archive",
        output_path="/backups/analytics.dump",
        gzip=True,
        num_parallel_collections=8,
        read_preference="secondary",
        exclude_collections="cache,sessions"
    )
    options_form.set_options(test_opts)
    
    extracted = options_form.get_options()
    assert extracted.db == "analytics"
    assert extracted.collection == "events"
    assert extracted.output_mode == "archive"
    assert extracted.output_path == "/backups/analytics.dump"
    assert extracted.gzip is True
    assert extracted.num_parallel_collections == 8
    assert extracted.read_preference == "secondary"
    assert extracted.exclude_collections == "cache,sessions"

def test_connection_form_uri(root_window):
    frame = ctk.CTkFrame(root_window)
    conn_form = ConnectionForm(frame)
    conn_form.set_uri("mongodb://localhost:27017")
    assert conn_form.get_uri() == "mongodb://localhost:27017"

def test_path_bar_set_get(root_window):
    frame = ctk.CTkFrame(root_window)
    path_bar = PathBar(frame, on_path_changed=lambda p: None)
    path_bar.set_path("/usr/local/bin/mongodump")
    assert path_bar.get_path() == "/usr/local/bin/mongodump"
