/*
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
*/
{
  lib,
  pkgs,
  pythonSet,
  pyproject-nix,
  workspace,
  ...
}: let
  inherit (pkgs.callPackage pyproject-nix.build.util {}) mkApplication;
in {
  default =
    mkApplication {
      venv = pythonSet.mkVirtualEnv "thalia-env" workspace.deps.default;
      package = pythonSet.textual-thalia;
    }
    // {
      meta = {
        description = "A git tui built with textual";
        homepage = "https://github.com/TotalyEnglizLitrate/textual-thalia";
        maintainers = with lib.maintainers; [TotalyEnglizLitrate];
        license = lib.licenses.gpl3Plus;
      };
    };
}
