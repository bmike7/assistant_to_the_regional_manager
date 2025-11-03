"""
Assistant To The Regional Manager
"""

import json
import subprocess
import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path

import click
from langchain.agents import create_agent


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


# TO-DO: work with a config file: loop over configured repositories
@click.group(help=__doc__)
def cli() -> None: ...


@cli.command()
@click.argument("project", type=Path)
@click.argument("author")
@click.argument(
    "day",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(dt.date.today()),
)
def tattletale(project: Path, author: str, day: dt.date) -> None:
    question = f"What did '{author}' do on {day} on the following project: {project}?"
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


if __name__ == "__main__":
    cli()
