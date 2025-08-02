"""
Copyright (C) 2025 Narendra S

This file is a part of the Thalia project

Thalia is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Thalia is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Thalia.  If not, see <https://www.gnu.org/licenses/>.
"""

import sqlite3
from pathlib import Path

from platformdirs import user_cache_path
from textual.app import App

from .. import binding_loader
from .. import config as conf
from .screens import dashboard


class Thalia(App):
    """A terminal-based Git UI."""

    CSS = """
    Screen {
        align: center middle;
        overflow: hidden;
    }
    """

    BINDINGS = binding_loader.include_bindings("bindings")

    def __init__(
        self, settings: conf.Settings, cache_db: sqlite3.Connection, cache_dir: Path | None = None, **kwargs
    ) -> None:
        """Initialize the Thalia app."""
        self.settings = settings
        self.cache_dir = cache_dir or user_cache_path("thalia")
        self.cache_db = cache_db

        try:
            with cache_db:
                schema = """
                CREATE TABLE IF NOT EXISTS Repositories(
                    Path TEXT PRIMARY KEY NOT NULL UNIQUE,
                    last_accessed INTEGER NOT NULL DEFAULT (strftime('%s','now'))
                )
                """
                cache_db.execute(schema)
        except sqlite3.OperationalError:
            exit(1)

        super().__init__(**kwargs)

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.push_screen(dashboard.DashboardScreen(id="dashboard"))
