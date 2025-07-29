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

from textual.binding import BindingType

from . import cli, config


def include_bindings(field: str) -> list[BindingType]:
    fields = field.split(".")
    settings = cli.get_settings()
    while fields:
        if fields[0] not in settings.__pydantic_fields__:
            return []

        settings = getattr(settings, fields[0])
        fields.pop(0)
    if isinstance(settings, config.ScreenBindings):
        return list(settings.get_bindings())

    return []
