import json
from dataclasses import asdict, dataclass, field
from functools import singledispatchmethod
from pathlib import Path

from platformdirs import PlatformDirs as PDirs


class ATTRMEncoder(json.JSONEncoder):
    @singledispatchmethod
    def default(self, obj):
        return super().default(obj)

    @default.register
    def _(self, value: Path):
        return str(value)


class PlatformDirs(PDirs):
    @property
    def user_config_file(self) -> Path:
        return super().user_config_path / "attrm.json"


dirs = PlatformDirs("attrm", "mikebijl")


@dataclass
class Config:
    dirs: list[Path] = field(default_factory=list)


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

