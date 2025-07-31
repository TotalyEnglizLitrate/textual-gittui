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

from collections.abc import Iterator
from pathlib import Path
from typing import cast

import platformdirs
import pygit2
from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Input, ListItem, ListView, Static
from textual_fspicker import SelectDirectory
from textual_fspicker.parts import DirectoryNavigation
from textual_fspicker.select_directory import CurrentDirectory

from ... import binding_loader
from .. import app
from .workspace import WorkspaceScreen


class DashboardScreen(Screen):
    CSS = """
    #dash-name {
        dock: top;
        padding: 4 0;
        content-align: center top;
    }

    #dash {
        align: center middle;
        width: 50%;
    }

    #recent-repos {
        content-align: center middle;
        width: 70%;
        height: 50%;
    }

    #repo-actions {
        content-align: left middle;
        width: 30%;
        margin: 0 10;
    }
    """
    SCOPED_CSS = True

    BINDINGS = binding_loader.include_bindings("dashboard.bindings")

    def compose(self) -> ComposeResult:
        _app = cast(app.Thalia, self.app)
        yield Static(
            Text(
                _app.settings.dashboard.text,
                _app.settings.dashboard.text_style,
            ),
            id="dash-name",
        )
        with Horizontal(id="dash"):
            yield RecentRepos(id="recent-repos")
            yield RepoActions(id="repo-actions")
        yield Footer()

    @work
    async def action_create_repo(self) -> None:
        repo_dir = await self.app.push_screen_wait(CustomDirPicker(title="Select Directory for Repository"))
        if not repo_dir:
            self.notify("No directory selected, exiting.")
            return
        flags = pygit2.enums.RepositoryInitFlag
        try:
            repo = pygit2.init_repository(repo_dir, flags=flags.NO_REINIT | flags.MKDIR)
        except ValueError as e:
            self.notify(title="Repository creation failed", message=e.args[0], severity="error")
            return
        self.app.push_screen(WorkspaceScreen(repo))

    def action_clone_repo(self) -> None:
        self.app.notify("Placeholder - clone_repo")

    def action_open_repo(self) -> None:
        self.app.notify("Placeholder - open_repo")


class RepoActions(Widget):
    DEFAULT_CSS = """
    Button {
        margin: 1;
    }
        """
    SCOPED_CSS = True

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Button("📂 Open", variant="primary", id="open")
            yield Button("⤓ Clone", variant="primary", id="clone")
            yield Button("＋Create", variant="primary", id="create")

    @on(Button.Pressed)
    async def handle_button(self, event: Button.Pressed) -> None:
        await self.run_action(f"screen.{event.button.id}_repo")


class RecentRepos(Widget):
    def compose(self) -> ComposeResult:
        repos = list(self.fetch_recent_repos())
        with Vertical():
            yield Static("Recent Repositories")
            yield ListView(*repos)

    def fetch_recent_repos(self) -> Iterator[ListItem]:
        cache_dir = Path(platformdirs.user_cache_dir("thalia"))
        if cache_dir.exists():
            for file, _, _ in cache_dir.walk():
                # TODO: add git dir check once that's implemented
                if file.is_symlink() and file.resolve().is_dir():
                    yield RepositoryEntry(file.resolve())


class RepositoryEntry(ListItem):
    def __init__(
        self,
        path: Path,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
        markup: bool = True,
    ) -> None:
        self.path = path
        # TODO: Add more info
        children = (Static(path.name),)
        super().__init__(*children, name=name, id=id, classes=classes, disabled=disabled, markup=markup)

    @on(Click)
    def action_open_repo(self) -> None:
        raise NotImplementedError


class CustomDirPicker(SelectDirectory):
    CSS = """
        Input {
            width: 40%;
        }
        """

    def _input_bar(self) -> ComposeResult:
        yield CurrentDirectory()
        yield Input(Path(self._location).name)

    def on_mount(self) -> None:
        navigation = self.query_one(DirectoryNavigation)
        navigation.show_files = False

    @on(Button.Pressed, "#select")
    @on(Input.Submitted)
    def _select_directory(self, event: Button.Pressed | Input.Submitted) -> None:
        event.stop()
        match event:
            case Input.Submitted():
                input_val = Path(event.value)
            case Button.Pressed():
                input_val = self.query_one(Input).value
                if not input_val:
                    self.dismiss(self.query_one(DirectoryNavigation).location)

                input_val = Path(input_val)

        if input_val.is_absolute():
            self.dismiss(input_val)
        self.dismiss((self.query_one(DirectoryNavigation).location / input_val).absolute())
