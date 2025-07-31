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

from pygit2.repository import Repository
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Static

from ... import binding_loader


class WorkspaceScreen(Screen):
    BINDINGS = binding_loader.include_bindings("workspace")

    def __init__(
        self, repo: Repository, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        self._repo = repo
        super().__init__(name, id, classes)

    @property
    def repo(self) -> Repository:
        return self._repo

    def compose(self) -> ComposeResult:
        yield Static("I don't know what this is going to look like yet")
