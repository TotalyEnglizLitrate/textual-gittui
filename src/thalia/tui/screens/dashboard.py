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
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.events import Click
from textual.screen import Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, ListItem, ListView, Static

from ... import binding_loader
from .. import app


class DashboardScreen(Screen):
    DEFAULT_CSS = """
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

    # TODO:
    # implement a dirpicker/find one by the community
    # figure out libgit2
    def action_create_repo(self) -> None:
        self.app.notify("Placeholder - create_repo")

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
