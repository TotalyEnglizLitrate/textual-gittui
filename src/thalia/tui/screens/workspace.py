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
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Footer, Static

from ... import binding_loader


class WorkspaceScreen(Screen):
    CSS = """
    #left_panel {
        width: 20%;
    }
    #middle_panel {
        width: 60%;
    }
    #right_panel {
        width: 20%;
    }

    BranchList, StashList{
        height: 50%;
    }

    WorkTree, CommitHistory {
        height: 50%;
    }
    """

    BINDINGS = binding_loader.include_bindings("workspace.bindings")

    def __init__(
        self, repo: Repository, name: str | None = None, id: str | None = None, classes: str | None = None
    ) -> None:
        super().__init__(name, id, classes)
        self._repo = repo

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="left_panel"):
                yield BranchList()
                yield StashList()

            yield FileView(id="middle_panel")

            with Vertical(id="right_panel"):
                yield WorkTree()
                yield CommitHistory()
        yield Footer()

    def action_amend_commit(self) -> None:
        self.notify("Placeholder: Amend Last Commit")

    def action_commit(self) -> None:
        self.notify("Placeholder: Commit Changes")

    def action_push(self) -> None:
        self.notify("Placeholder: Push Changes")

    def action_pull(self) -> None:
        self.notify("Placeholder: Pull Changes")

    def action_stash(self) -> None:
        self.notify("Placeholder: Stash Changes")

    def action_ignore(self) -> None:
        self.notify("Placeholder: Ignore File")

    def action_open_file(self) -> None:
        self.notify("Placeholder: Open File")

    def action_branch_manager(self) -> None:
        self.notify("Placeholder: Open Branch Manager")

    def action_stash_manager(self) -> None:
        self.notify("Placeholder: Open Stash Manager")


class CommitHistory(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Commit History")


class WorkTree(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Workspace Files")


class BranchList(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Branches")


class StashList(Widget):
    def compose(self) -> ComposeResult:
        yield Static("Stashes")


class FileView(Widget):
    def compose(self) -> ComposeResult:
        yield Static("File View")
