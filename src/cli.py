"""
Assistant To The Regional Manager
"""

from dataclasses import dataclass
from typing import Generic, Protocol, Self, TypeVar

import click
import cutie


def abort(msg: str) -> None:
    print(msg)
    raise click.Abort()


class HasStr(Protocol):
    def __str__(self) -> str: ...


T = TypeVar("T")


@dataclass
class Option(Generic[T]):
    label: str
    value: T

    @classmethod
    def from_str(cls, obj: HasStr) -> Self:
        return cls(str(obj), obj)


def select(prompt: str, options: list[Option[T]]) -> list[T]:
    print(prompt)
    selected_indices = cutie.select_multiple([o.label for o in options])
    return [o.value for i, o in enumerate(options) if i in selected_indices]


@click.group(help=__doc__)
def cli() -> None: ...
