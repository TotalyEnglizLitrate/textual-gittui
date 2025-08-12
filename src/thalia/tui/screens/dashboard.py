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

from __future__ import annotations

import asyncio
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
from textual.widgets import Button, Footer, Input, ListItem, ListView, ProgressBar, Static
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

        self._open_repo_from_obj(repo, repo_dir)

    @work
    async def action_clone_repo(self) -> None:
        # TODO: Add a configuration option for default clone directory
        # For now, we use the home directory as the default

        res = await self.app.push_screen_wait(CloneModal(default_dir=Path.home(), dashboard=self))
        if res is None:
            return

        url, target_path = res
        self.notify(f"Cloning {url} into {target_path}")
        repo = await self.app.push_screen_wait(CloneProgressModal(repo_url=url, target_path=target_path))
        if not repo:
            return

        self._open_repo_from_obj(repo, target_path)

    @work
    async def action_open_repo(self) -> None:
        repo_dir = await self.app.push_screen_wait(CustomDirPicker(title="Select Directory for Repository"))
        if not repo_dir:
            self.notify("No directory selected, exiting.")
            return

        self._open_repo(repo_dir)

    def _open_repo(self, repo_dir: Path) -> None:
        try:
            repo = pygit2.repository.Repository(str(repo_dir))
        except pygit2.GitError as e:
            self.notify(e.args[0], title="Unable to open repository", severity="error")
            return

        self._open_repo_from_obj(repo, repo_dir)

    def _open_repo_from_obj(self, repo: pygit2.repository.Repository, repo_dir: Path) -> None:
        try:
            with cast(app.Thalia, self.app).cache_db as con:
                con.execute(
                    "INSERT INTO Repositories(Path, last_accessed) VALUES"
                    "(?, strftime('%s','now')) ON CONFLICT(Path) DO UPDATE SET last_accessed=strftime('%s','now')",
                    (str(repo_dir),),
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
                    yield Path(repo[0])
                except pygit2.GitError:
                    to_rm.append(repo)

        if not to_rm:
            return

        try:
            with con:
                con.executemany("DELETE FROM Repositories WHERE Path=?;", to_rm)
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
                    yield Button("Browse", variant="default", id="pick-dir")
                with Horizontal():
                    yield Button("Clone", variant="primary", id="clone-confirm")
                    yield Button("Cancel", variant="error", id="clone-cancel")

    @on(Button.Pressed, "#pick-dir")
    @work
    async def pick_directory(self) -> None:
        picked: Path | None = await self.app.push_screen_wait(
            CustomDirPicker(title="Select Target Directory for Clone")
        )
        url = self.query_one("#repo-url", Input).value.strip()
        # ensure picked dir can be used for cloning
        if picked is None:
            self.app.notify("No directory selected, using default directory.")
            picked = self.default_dir
        else:
            picked = picked.expanduser().resolve()
            if picked.exists() and any(picked.iterdir()):
                # If the directory exists and is not empty, append the repo name to the path
                if url:
                    picked = picked / url.split("/")[-1]
                    if picked.exists():
                        self.app.notify(
                            title="Directory already exists",
                            message=f"The directory {picked} already exists and is not empty."
                            "Please choose a different directory.",
                            severity="warning",
                        )

                        picked = self.default_dir
                else:
                    picked = self.default_dir

            self.query_one("#picked-dir", Static).update(str(picked))
            self._picked_dir = picked
            return

        self._picked_dir = self.default_dir
        self.query_one("#picked-dir", Static).update(str(self.default_dir))

    @on(Button.Pressed, "#clone-confirm")
    async def on_confirm(self) -> None:
        url = self.query_one("#repo-url", Input).value.strip()
        target = getattr(self, "_picked_dir", self.default_dir)

        if self.check_dir_validity():
            self._picked_dir = target
            self.query_one("#picked-dir", Static).update(str(target))
        else:
            return

        if not url or not target:
            self.app.notify(
                title="Missing info", message="Please provide both URL and target directory.", severity="warning"
            )
            return
        target_path = Path(target).expanduser().resolve()

        self.dismiss((url, target_path))

    @on(Button.Pressed, "#clone-cancel")
    def action_cancel(self) -> None:
        self.app.notify("Clone operation cancelled.")
        if self.check_dir_validity():
            # If the directory is valid, we can dismiss the modal
            self._picked_dir = self.default_dir
            self.query_one("#picked-dir", Static).update(str(self.default_dir))
        self.dismiss(None)

    def check_dir_validity(self) -> bool:
        """
        Check if the directory is valid for cloning and notify the user if it is not.
        """
        path = getattr(self, "_picked_dir", self.default_dir)
        ret = (not path.exists()) or (path.is_dir() and not any(path.iterdir()))

        if not ret:
            self.app.notify(
                title="Invalid Directory",
                message=f"The directory {path} is not valid for cloning. Please choose an empty directory.",
                severity="warning",
            )
        return ret


class CloneProgressModal(ModalScreen):
    CSS = """
    #clone-progress-modal {
        height: 50%;
        width: 50%;
        content-align: center middle;
        align: center middle;
        padding: 2 2;
    }

    #clone-progress-bar {
        align: center middle;
        content-align: center middle;
        margin: 1 0;
        width: 100%;
    }

    #clone-progress-title {
        content-align: center middle;
        align: center middle;
        padding: 1 0;
    }

    #clone-cancel {
        dock: right;
    }
    """
    SCOPED_CSS = True

    class CustomCallBack(pygit2.callbacks.RemoteCallbacks):
        def __init__(self, parent: CloneProgressModal, credentials=None, certificate_check=None):
            super().__init__(credentials, certificate_check)
            self.parent = parent

        def transfer_progress(self, stats):
            progress = self.parent.query_one("#clone-progress-bar", ProgressBar)
            if progress.total == stats.total_objects:
                progress.update(progress=stats.received_objects)
            else:
                progress.update(progress=stats.received_objects, total=stats.total_objects)

    def __init__(self, repo_url: str, target_path: Path, **kwargs):
        super().__init__(**kwargs)
        self.repo_url = repo_url
        self.target_path = target_path
        self.clone_task = None

    def compose(self) -> ComposeResult:
        with Vertical(id="clone-progress-modal"):
            yield Static(f"Cloning {self.repo_url} into {self.target_path}", id="clone-progress-title")
            yield ProgressBar(total=None, id="clone-progress-bar", show_eta=False)
            with Horizontal():
                yield Button("Cancel", variant="error", id="clone-cancel")

    @on(Button.Pressed)
    def handle_button(self, event: Button.Pressed):
        # should be fine if we remove the button check as there's only one button, but checking just in case
        if event.button.id == "clone-cancel" and self.clone_task:
            self.clone_task.cancel()

    @work
    async def on_mount(self) -> None:
        self.clone_task = asyncio.create_task(self._perform_clone())
        try:
            repo = await self.clone_task
        except asyncio.CancelledError:
            self.app.notify("Clone operation was cancelled.", severity="warning")
            repo = None
        except pygit2.GitError as e:
            self.app.notify(title="Clone failed", message="\n".join(e.args), severity="error")
            repo = None
        finally:
            self.dismiss(repo)

    async def _perform_clone(self):
        return await asyncio.to_thread(
            pygit2.clone_repository, self.repo_url, str(self.target_path), callbacks=self.CustomCallBack(self)
        )
