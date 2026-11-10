#!/usr/bin/env python3
"""MongoDB Dump GUI (Portable)

A portable, cross-platform Desktop GUI for MongoDB Database Tools CLI (mongodump).
"""

import sys
from gui.main_window import MongoDumpApp


def main():
    app = MongoDumpApp()
    app.mainloop()


if __name__ == "__main__":
    main()
