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

import os
from collections.abc import Iterator
from pathlib import Path

from platformdirs import user_config_path
from pydantic import BaseModel, Field, PrivateAttr, field_validator
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, SettingsConfigDict, TomlConfigSettingsSource
from rich.errors import StyleSyntaxError
from rich.style import Style
from textual.binding import Binding, BindingError, InvalidBinding
from textual.keys import _character_to_key


class BindingTypeModel(BaseModel):
    key: str | tuple[str, str] | tuple[str, str, str] = Field()
    """Keybind: see textual.binding.BindingType"""

    action: str = Field(default="")
    """A valid action for a screen, invalid values are automatically discarded"""

    show: bool = Field(True)
    """Whether to show keybind in footer or not"""


class ScreenBindings(BaseModel):
    bindings: list[BindingTypeModel] = Field()
    """The bindings for a given context"""

    _actions: dict[str, str] = PrivateAttr({})

    @field_validator("bindings")
    @classmethod
    def validate_bindings(cls, bindings: list[BindingTypeModel]) -> list[BindingTypeModel]:
        """Validates and filters bindings based on the defined actions."""
        # the type checker still thinks this is a dict and not a Field wrapping a dict
        return [binding for binding in bindings if cls._actions.get_default().get(binding.action) is not None]  # type: ignore

    def get_bindings(self) -> Iterator[Binding]:
        """Modified version of textual.binding.Binding.make_bindings classmethod"""
        bindings = self.bindings
        for binding in bindings:
            _binding: Binding
            if isinstance(binding.key, tuple):
                if len(binding.key) not in (2, 3):
                    raise BindingError(f"BINDINGS must contain a tuple of two or three strings, not {binding!r}")
                _binding = Binding(",".join(binding.key), action=binding.action)
            else:
                _binding = Binding(binding.key, action=binding.action)

            for key in _binding.key.split(","):
                key = key.strip()
                if not key:
                    raise InvalidBinding(f"Can not bind empty string in {_binding.key!r}")
                if len(key) == 1:
                    key = _character_to_key(key)

                yield Binding(
                    key=key, action=binding.action, description=self._actions[binding.action], show=binding.show
                )


class DashboardSettings(BaseModel):
    text: str = Field(
        default=(
            "████████ ██   ██  █████  ██      ██  █████  \n"
            "   ██    ██   ██ ██   ██ ██      ██ ██   ██ \n"
            "   ██    ███████ ███████ ██      ██ ███████ \n"
            "   ██    ██   ██ ██   ██ ██      ██ ██   ██ \n"
            "   ██    ██   ██ ██   ██ ███████ ██ ██   ██ \n"
        )
    )
    """The Text shown on top of the dashboard."""

    text_style: str = Field(default="#8AADF4")
    """The styling of the dashboard text, '#8AADF4' by default, it can be any valid rich style string."""

    @field_validator("text_style")
    @classmethod
    def check_style(cls, text_style: str) -> str:
        """Validator for text style"""
        try:
            Style.parse(text_style)
        except StyleSyntaxError:
            # the type checker still thinks this is a string and not a Field wrapping a string
            return text_style.get_default()  # type: ignore
        return text_style

    class Bindings(ScreenBindings):
        _actions = {
            "open_repo": "Open Repository",
            "clone_repo": "Clone Repository",
            "create_repo": "Create Repository",
        }

    bindings: Bindings = Field(
        default=Bindings(
            bindings=[
                BindingTypeModel(key="o", action="open_repo", show=True),
                BindingTypeModel(key="c", action="clone_repo", show=True),
                BindingTypeModel(key="n", action="create_repo", show=True),
            ]
        )
    )
    """Dashboard Bindings"""


class WorkspaceSettings(BaseModel):
    """Settings for the workspace screen."""

    class Bindings(ScreenBindings):
        _actions = {
            "amend_commit": "Amend Last Commit",
            "commit": "Commit Changes",
            "push": "Push Changes",
            "pull": "Pull Changes",
            "stash": "Stash Changes",
            "ignore": "Ignore File",
            "open_file": "Open File",
            "branch_manager": "Open Branch Manager",
            "stash_manager": "Open Stash Manager",
        }

    bindings: Bindings = Field(
        default=Bindings(
            bindings=[
                BindingTypeModel(key="a", action="amend_commit", show=False),
                BindingTypeModel(key="c", action="commit", show=False),
                BindingTypeModel(key="p", action="push", show=False),
                BindingTypeModel(key="l", action="pull", show=False),
                BindingTypeModel(key="s", action="stash", show=False),
                BindingTypeModel(key="i", action="ignore", show=False),
                BindingTypeModel(key="o", action="open_file", show=False),
                BindingTypeModel(key="b", action="branch_manager", show=False),
                BindingTypeModel(key="t", action="stash_manager", show=False),
            ]
        )
    )
    """Workspace Bindings"""


class GlobalBindings(ScreenBindings):
    _actions = {"quit": "Quit the app"}


class Settings(BaseSettings):
    """Settings for the Thalia application."""

    __version__: str = "0.1.0"
    """The version of Thalia, used for display purposes."""

    dashboard: DashboardSettings = Field(default_factory=DashboardSettings)
    """Settings for the dashboard screen."""

    workspace: WorkspaceSettings = Field(default_factory=WorkspaceSettings)
    """Settings for the workspace screen."""

    bindings: GlobalBindings = Field(
        default=GlobalBindings(
            bindings=[
                BindingTypeModel(key=("q", "ctrl+c"), action="quit", show=True),
            ]
        )
    )
    """Global keybinds"""

    config_dir: Path = Field(default_factory=lambda: user_config_path("thalia"))
    """The directory where Thalia stores its data."""

    theme_dir: Path = Field(default_factory=lambda: user_config_path("thalia") / "themes")
    """The directory where Thalia stores its themes."""

    config_file: Path = Field(default_factory=lambda: user_config_path("thalia") / "config.toml")
    """The path to the Thalia configuration file."""

    @field_validator("config_dir", "theme_dir", "config_file")
    @classmethod
    def validate_paths(cls, path: Path) -> Path:
        """Ensures the provided paths are absolute and exist."""
        if not path.is_absolute():
            raise ValueError(f"Path {path} must be absolute.")
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
        return path

    model_config = SettingsConfigDict(
        env_prefix="THALIA_",
        env_nested_delimiter=":",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="forbid",
        strict=True,
        validate_assignment=True,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        config_from_env = os.getenv("THALIA_CONFIG_FILE")
        default_sources = (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        )

        if config_from_env:
            conf_file = Path(config_from_env).resolve()
        else:
            return default_sources

        if conf_file.exists():
            return (
                init_settings,
                TomlConfigSettingsSource(settings_cls, conf_file),
                env_settings,
                dotenv_settings,
                file_secret_settings,
            )
        return default_sources
