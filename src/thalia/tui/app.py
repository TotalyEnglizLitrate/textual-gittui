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

from textual.app import App
from textual.binding import Binding

from thalia.tui.screens.dashboard import DashboardScreen


class Thalia(App):
    """A terminal-based Git UI."""

    CSS = """
    Screen {
        align: center middle;
        overflow: hidden;
    }
    """

    BINDINGS = [
        Binding(key="q,ctrl+c", action="quit", description="Quit", show=True),
    ]

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.push_screen(DashboardScreen())
