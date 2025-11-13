"""
Assistant To The Regional Manager

Run `attrm login` to set up authentication with your Anthropic API key.
"""

from dataclasses import dataclass
from functools import partial, update_wrapper
from typing import Callable, Generic, Protocol, Self, TypeVar

import click
import cutie

from .config import ATTRMConfig


def abort(msg: str) -> None:
    click.echo(msg)
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
@click.pass_context
def cli(ctx) -> None:
    ctx.ensure_object(dict)
    ctx.obj["config"] = ATTRMConfig()


def pass_ctx(f: Callable, loc: str):
    @click.pass_context
    def _inject_config(ctx, *args, **kwargs):
        return ctx.invoke(f, ctx.obj[loc], *args, **kwargs)

    return update_wrapper(_inject_config, f)


pass_config = partial(pass_ctx, loc="config")
