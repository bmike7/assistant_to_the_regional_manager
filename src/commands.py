import json
import re
import subprocess
import datetime as dt
from dataclasses import asdict, dataclass
from pathlib import Path

import anthropic
import click

from .auth import get_api_key
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


class ISO8601Duration(click.ParamType):
    """
    Click parameter type for parsing simple ISO8601 duration strings.
    
    Supports formats like:
    - P7D (7 days)
    - P1W (1 week)
    - P2W (2 weeks)
    - P30D (30 days)
    """
    name = "duration"
    
    def convert(self, value, param, ctx):
        if isinstance(value, dt.timedelta):
            return value
        
        match = re.match(r"^P(\d+)([DW])$", value.upper())
        if not match:
            self.fail(
                f"Invalid duration format: {value}. "
                "Expected format like P7D (7 days) or P1W (1 week)",
                param,
                ctx
            )
        
        amount = int(match.group(1))
        unit = match.group(2)
        
        if unit == "D":
            return dt.timedelta(days=amount)
        elif unit == "W":
            return dt.timedelta(weeks=amount)
        
        self.fail(f"Unsupported duration unit: {unit}", param, ctx)


def determine_range(period: dt.timedelta | None, day: dt.date | dt.datetime) -> list[dt.date]:
    """
    Determine the date range based on the period parameter.

    Args:
        period: Optional timedelta to look back from the day
        day: The end date for the range (or single day if period is None)

    Returns:
        List of dates to process
    """
    # Normalize day to dt.date if it's a datetime
    end_date = day.date() if isinstance(day, dt.datetime) else day

    if period:
        start_date = end_date - period

        # Generate list of dates
        dates = []
        current_date = start_date
        while current_date <= end_date:
            dates.append(current_date)
            current_date += dt.timedelta(days=1)
        return dates
    return [end_date]


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


@cli.command(help="Summarize what `author` did on given day(s)")
@click.argument("author")
@click.argument(
    "day",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    default=str(dt.date.today() - dt.timedelta(days=1)),
)
@click.option(
    "--period",
    type=ISO8601Duration(),
    default=None,
    help="ISO8601 period to look back (e.g., P7D for 7 days, P1W for 1 week)",
)
@pass_config
def tattletale(cfg: ATTRMConfig, author: str, day: dt.date, period: dt.timedelta | None) -> None:
    if not cfg.exists:
        abort("No configuration, first run: `attrm config`")

    client = anthropic.Anthropic(api_key=get_api_key())
    system_prompt = (
        "You are the assistant to the regional manager, "
        "making sure subordinates fill in their timesheets correctly, "
        "according to their git histories. So given their git histories for "
        "the projects they are working on, summarise in one sentence what "
        "that author did that day. Explain it in a way a non-technical "
        "person can understand it, without telling who did it."
    )

    # Loop over each date
    for current_day in determine_range(period, day):
        for proj in cfg.projects:
            git_log = get_git_history(proj, author, current_day)
            if not git_log.strip():
                continue

            message = client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=1024,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Here is the git history for {author} on {current_day} for project {proj}:"
                        f"\n\n{git_log}\n\nPlease summarize in one sentence what this author did that day.",
                    }
                ],
            )

            content = (
                message.content[0].text
                if hasattr(message.content[0], "text")
                else str(message.content[0])
            )
            report = Summary(project=str(proj), day=str(current_day), summary=content)
            print(json.dumps(asdict(report), indent=2))
