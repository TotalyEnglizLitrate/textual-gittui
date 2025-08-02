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
from collections.abc import Iterator
from pathlib import Path
from typing import cast

import pygit2
from rich.text import Text
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.content import Content
from textual.events import Click
from textual.screen import ModalScreen, Screen
from textual.widget import Widget
from textual.widgets import Button, Footer, Input, ListItem, ListView, Static
from textual_fspicker.parts import DirectoryNavigation
from textual_fspicker.select_directory import CurrentDirectory, SelectDirectory

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
        except (pygit2.GitError, ValueError) as e:
            self.notify(title="Repository creation failed", message=e.args[0], severity="error")
            return

        try:
            with cast(app.Thalia, self.app).cache_db as con:
                con.execute(
                    "INSERT INTO Repositories(Path, last_accessed) VALUES"
                    "(?, strftime('%s','now')) ON CONFLICT(Path) DO UPDATE SET last_accessed=strftime('%s','now')",
                    (str(repo_dir),),
                )
        except (sqlite3.OperationalError, sqlite3.IntegrityError):
            self.notify(
                title="Failed to insert into cache",
                message="Repository might not show up in recently opened list",
                severity="warning",
            )

        self.app.push_screen(WorkspaceScreen(repo))

    @work
    async def action_clone_repo(self) -> None:
        # TODO: Add a configuration option for default clone directory
        # For now, we use the home directory as the default

        res = await self.app.push_screen_wait(CloneModal(default_dir=Path.home(), dashboard=self))
        if res is None:
            return

        url, target_path = res
        try:
            repo = pygit2.clone_repository(url, str(target_path))
        except pygit2.GitError as e:
            self.notify(title="Clone failed", message="\n".join(e.args), severity="error")
            return

        self._open_repo_from_obj(repo, target_path)

    @work
    async def action_open_repo(self) -> None:
        repo_dir = await self.app.push_screen_wait(CustomDirPicker(title="Select Directory for Repository"))
        if not repo_dir:
            self.notify("No directory selected, exiting.")
            return

        self._open_repo(repo_dir=repo_dir)

    def _open_repo(self, repo_dir: Path) -> None:
        try:
            repo = pygit2.repository.Repository(str(repo_dir))
        except pygit2.GitError as e:
            self.notify(e.args[0], title="Unable to open repository", severity="error")
            return

        self._open_repo_from_obj(repo, repo_dir)

    def _open_repo_from_obj(self, repo: pygit2.repository.Repository, repo_path: Path) -> None:
        try:
            with cast(app.Thalia, self.app).cache_db as con:
                con.execute(
                    "INSERT INTO Repositories(Path, last_accessed) VALUES"
                    "(?, strftime('%s','now')) ON CONFLICT(Path) DO UPDATE SET last_accessed=strftime('%s','now')",
                    (str(repo_path),),
                )
        except sqlite3.OperationalError:
            self.notify(
                title="Failed to insert into cache",
                message="Repository might not show up in recently opened list",
                severity="warning",
            )
        except sqlite3.IntegrityError:
            # repo already in cache
            pass

        self.app.push_screen(WorkspaceScreen(repo))


class RepoActions(Widget):
    DEFAULT_CSS = """
    Button {
        margin: 1;
    }
        """
    SCOPED_CSS = True

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Button("📂 Open", variant="primary", name="open")
            yield Button("⤓ Clone", variant="primary", name="clone")
            yield Button("＋Create", variant="primary", name="create")

    @on(Button.Pressed)
    async def handle_button(self, event: Button.Pressed) -> None:
        await self.run_action(f"screen.{event.button.name}_repo")


class RecentRepos(Widget):
    def compose(self) -> ComposeResult:
        repos = (RepositoryEntry(x) for x in self.fetch_recent_repos())
        with Vertical():
            yield Static("Recent Repositories")
            yield ListView(*repos)

    def fetch_recent_repos(self) -> Iterator[Path]:
        con = cast(app.Thalia, self.app).cache_db
        try:
            query = con.execute("SELECT Path FROM Repositories ORDER BY last_accessed DESC;")
        except sqlite3.OperationalError:
            return
        to_rm: list[str] = []
        for repo in query.fetchall():
            repo_path = Path(repo[0])
            if repo_path.exists() and repo_path.is_dir():
                try:
                    pygit2.repository.Repository(repo[0])
                except pygit2.GitError:
                    to_rm.append(repo[0])
                yield repo_path
            else:
                to_rm.append(repo[0])

        if not to_rm:
            return

        try:
            with con:
                con.executemany("DELETE FROM Repositories WHERE Path=?;", [(p,) for p in to_rm])
        except sqlite3.OperationalError:
            pass

    @on(ListView.Selected)
    def open_repo(self, event: ListView.Selected) -> None:
        event.stop()
        assert isinstance(event.item, RepositoryEntry)
        event.item.action_open_repo()


class RepositoryEntry(ListItem):
    def __init__(self, path: Path, **kwargs) -> None:
        self.path = path
        # TODO: Add more info
        children = (Static(Content(path.name).truncate(40)),)
        super().__init__(*children, **kwargs)

    @on(Click)
    def action_open_repo(self) -> None:
        self.query_ancestor(DashboardScreen)._open_repo(self.path)


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

        self.dismiss((self.query_one(DirectoryNavigation).location / input_val).resolve())


class CloneModal(ModalScreen):
    CSS = """
    #clone-modal {
        width: 40%;
        height: 50%;
        align: center middle;
        content-align: center middle;
        padding: 2 2;
    }
    Input {
        margin: 1 0;
    }
    Button {
        margin: 1 1;
    }

    #picked-dir {
        margin: 2 1;
        content-align: left middle;
    }

    #pick-dir {
        dock: right;
    }

    #clone-cancel {
        dock: right;
    }
    """
    SCOPED_CSS = True

    def __init__(self, dashboard: DashboardScreen, default_dir: Path | None = None, **kwargs):
        super().__init__(**kwargs)
        self.default_dir = default_dir or Path.home()
        self.dashboard = dashboard

    def compose(self) -> ComposeResult:
        with Vertical(id="clone-modal"):
            yield Static("Clone Repository", id="clone-title")
            yield Input(placeholder="Repository URL", id="repo-url")
            with Vertical():
                with Horizontal():
                    yield Static(str(self.default_dir), id="picked-dir")
                    yield Button("Browse", variant="default", id="pick-dir", classes="right-align")
                with Horizontal(classes="right-align"):
                    yield Button("Clone", variant="primary", id="clone-confirm")
                    yield Button("Cancel", variant="error", id="clone-cancel")

    @on(Button.Pressed, "#pick-dir")
    @work
    async def pick_directory(self) -> None:
        picked = await self.app.push_screen_wait(CustomDirPicker(title="Select Target Directory for Clone"))
        url = self.query_one("#repo-url", Input).value.strip()

        if picked:
            if picked.exists() and picked.is_dir() and any(picked.iterdir()):
                if url:
                    picked = picked / url.split("/")[-1]
                else:
                    picked = self.default_dir
            self.query_one("#picked-dir", Static).update(str(picked))
            self._picked_dir = picked
            return

        self._picked_dir = self.default_dir
        self.query_one("#picked-dir", Static).update(str(self.default_dir))

    @on(Button.Pressed, "#clone-confirm")
    def on_confirm(self) -> None:
        url = self.query_one("#repo-url", Input).value.strip()
        target = getattr(self, "_picked_dir", self.default_dir)
        if not url or not target:
            self.notify(
                title="Missing info", message="Please provide both URL and target directory.", severity="warning"
            )
            return
        target_path = Path(target).expanduser().resolve()

        # TODO: fix notification not showing up until after the modal is gone
        self.dismiss((url, target_path))
        self.notify(message=f"Cloning {url} into {target_path}")
        return

    @on(Button.Pressed, "#clone-cancel")
    def action_cancel(self) -> None:
        self.dismiss()
