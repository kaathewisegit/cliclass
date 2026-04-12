from abc import ABC
from dataclasses import dataclass, field
from typing import Literal

from cli import CliCommand


@dataclass(slots=True, kw_only=True)
class Langopts(ABC):
    rust: bool = False
    """Run Rust tests"""

    python: bool = False
    website: bool = False


@dataclass(slots=True)
class Run(Langopts):
    "Run stuff"

    id: int
    """docstring"""

    kind: Literal["a", "b"]


@dataclass(slots=True)
class Build(Langopts):
    "Build stuff"

    stuff: str


@dataclass(slots=True)
class Cmd:
    "Main command"

    subcommand: Run | Build = field(metadata={"cli": {"subcommand": True}})

    opt: bool = field(default=False, kw_only=True)


print(CliCommand(Cmd).parse())
