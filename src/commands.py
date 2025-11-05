import json
import subprocess
import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path

import click
from langchain.agents import create_agent

from .cli import ATTRMConfig, Option, abort, cli, pass_config, select


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


@cli.command(help="Configures which `git` repositories you want to report on")
@pass_config
def config(cfg: ATTRMConfig) -> None:
    search_path = input("Where are your repositories located?: ~/")
    cfg.update_dirs(search_git_repositories(Path.home() / search_path))
    cfg.save()


@cli.command(help="Summarize what `author` did on given day")
@click.argument("author")
@click.argument(
    "day",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(dt.date.today() - dt.timedelta(days=1)),
)
@pass_config
def tattletale(cfg: ATTRMConfig, author: str, day: dt.date) -> None:
    if not cfg.exists:
        abort("No configuration, first run: `attrm config`")

    for proj in cfg.projects:
        question = f"What did '{author}' do on {day} on the following project: {proj}?"
        result = agent.invoke({"messages": [{"role": "user", "content": question}]})
        content = result["messages"][-1].content

        report = Summary(project=str(proj), day=str(day), summary=content)
        print(json.dumps(asdict(report), indent=2))
