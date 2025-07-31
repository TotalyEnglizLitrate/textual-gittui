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

import os

import click
from click_default_group import DefaultGroup
from platformdirs import user_config_path

from . import config as conf


@click.group(cls=DefaultGroup, default="tui", default_if_no_args=True, invoke_without_command=True)
@click.option("-h", "--help", is_flag=True, help="Show this help message and exit.")
@click.option("-v", "--version", is_flag=True, help="Show the version of Thalia.")
@click.option(
    "-c",
    "--config",
    help=f"Path to the configuration file (defaults to {user_config_path('thalia') / 'config.toml'})",
    default=None,
)
@click.pass_context
def cli(ctx, config, version, help):
    """Thalia CLI"""
    ctx.ensure_object(dict)

    if help:
        click.echo(cli.get_help(ctx))

    if version:
        click.echo(f"Thalia {conf.Settings.__version__}")

    if config is not None:
        # If a config file is mentioned set the config file environment variable to override the default config
        os.environ["THALIA_CONFIG_FILE"] = str(config)
    ctx.obj["settings"] = conf.Settings()
    ctx.obj["config_path"] = config or user_config_path("thalia") / "config.toml"


@cli.command()
@click.pass_context
def tui(ctx):
    # Load the app class and run it with the given settings
    from .tui import app

    thalia = ctx.obj["app"] = app.Thalia(ctx.obj["settings"])
    thalia.run()


@click.pass_context
def get_settings(ctx) -> conf.Settings:
    """Get the settings object from the context."""
    return ctx.obj["settings"]
