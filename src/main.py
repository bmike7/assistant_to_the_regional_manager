"""
Assistant To The Regional Manager
"""

import json
import subprocess
import datetime as dt
from dataclasses import asdict, dataclass, field
from functools import singledispatchmethod
from pathlib import Path
from typing import Generic, Protocol, Self, TypeVar

import click
import cutie
from langchain.agents import create_agent
from platformdirs import PlatformDirs as PDirs


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


class PlatformDirs(PDirs):
    @property
    def user_config_file(self) -> Path:
        return super().user_config_path / "attrm.json"


dirs = PlatformDirs("attrm", "mikebijl")


@dataclass
class Config:
    dirs: list[Path] = field(default_factory=list)


class ATTRMEncoder(json.JSONEncoder):
    @singledispatchmethod
    def default(self, obj):
        return super().default(obj)

    @default.register
    def _(self, value: Path):
        return str(value)


@dataclass
class ATTRMConfig:
    def __init__(self) -> None:
        self.path = dirs.user_config_file
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            config = json.loads(self.path.read_text())
            self.config = Config(**config)
        else:
            self.config = Config()

    def update_dirs(self, repos: list[Path]) -> None:
        self.config.dirs = repos

    def save(self) -> None:
        self.path.write_text(
            json.dumps(
                asdict(self.config),
                cls=ATTRMEncoder,
                indent=2,
            )
        )

    @property
    def projects(self) -> list[Path]:
        return self.config.dirs


@dataclass
class Summary:
    project: str
    day: str
    summary: str


def get_git_history(project: Path, author: str, day: dt.date) -> str:
    """
    Gets the git history for given author on specified day.
    """
    return subprocess.run(
        [
            "git",
            "log",
            "--branches",
            f"--after={day}",
            f"--before={day + dt.timedelta(days=1)}",
            "--author",
            author,
        ],
        capture_output=True,
        text=True,
        check=True,
        cwd=project,
    ).stdout


# TO-DO: look into localai
agent = create_agent(
    model="gpt-4.1",
    tools=[get_git_history],
    system_prompt="You are the assistant to the regional manager, "
    "making sure subordinates fill in their timesheets correctly, "
    "according to their git histories. So given their git histories for "
    "the projects they are working on, summarise in one sentence what "
    "that author did that day. Explain it in a way a non-technical "
    "person can understand it.",
)


def abort(msg: str) -> None:
    print(msg)
    raise click.Abort()


# TO-DO: work with a config file: loop over configured repositories
@click.group(help=__doc__)
def cli() -> None: ...


def select(prompt: str, options: list[Option[T]]) -> list[T]:
    print(prompt)
    selected_indices = cutie.select_multiple([o.label for o in options])
    return [o.value for i, o in enumerate(options) if i in selected_indices]


def search_git_repositories(search_path: Path) -> list[Path]:
    candidates = subprocess.run(
        [
            "find",
            str(search_path),
            "-name",
            ".git",
        ],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    candidates = [Option.from_str(Path(c).parent) for c in candidates]
    return select("Track following repos:", candidates)


@cli.command()
def config() -> None:
    config = ATTRMConfig()
    search_path = input("Where are your repositories located?: ~/")
    config.update_dirs(search_git_repositories(Path.home() / search_path))
    config.save()


@cli.command()
@click.argument("author")
@click.argument(
    "day",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(dt.date.today()),
)
def tattletale(author: str, day: dt.date) -> None:
    config = ATTRMConfig()
    if not config.path.exists():
        abort("No configuration, first run: `attrm config`")
    for project in config.projects:
        question = (
            f"What did '{author}' do on {day} on the following project: {project}?"
        )
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        print(
            json.dumps(
                asdict(
                    Summary(
                        project=str(project),
                        day=str(day),
                        summary=result["messages"][-1].content,
                    )
                ),
                indent=2,
            )
        )
