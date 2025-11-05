import importlib
import pkgutil
from contextlib import suppress
from pathlib import Path

from src.cli import cli


def load_commands() -> None:
    here = Path(__file__).parent
    for mod in pkgutil.walk_packages([str(here)], prefix="src."):
        if mod.name.endswith("commands"):
            with suppress(ImportError):
                importlib.import_module(mod.name)


def main():
    load_commands()
    try:
        cli()
    except NotImplementedError as exc:
        print(f"Not (yet) implemented: {exc}")
