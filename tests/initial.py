from abc import ABC
from dataclasses import dataclass, field
from typing import Literal

import pytest

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


def test_build_subcommand():
    cli = CliCommand(Cmd)
    result = cli.parse(["build", "my_app"])
    assert isinstance(result.subcommand, Build)
    assert result.subcommand.stuff == "my_app"
    assert result.subcommand.rust is False  # default from Langopts


def test_run_subcommand_positionals():
    cli = CliCommand(Cmd)
    result = cli.parse(["run", "42", "a"])
    assert isinstance(result.subcommand, Run)
    assert result.subcommand.id == 42
    assert result.subcommand.kind == "a"


def test_inherited_flags():
    cli = CliCommand(Cmd)
    result = cli.parse(["build", "my_app", "--rust", "--website"])
    assert result.subcommand.rust is True
    assert result.subcommand.website is True
    assert result.subcommand.python is False


def test_top_level_option():
    cli = CliCommand(Cmd)
    result = cli.parse(["--opt", "build", "stuff"])
    assert isinstance(result.subcommand, Build)
    assert result.opt is True
    assert result.subcommand.stuff == "stuff"


def test_invalid_literal_kind():
    cli = CliCommand(Cmd)
    with pytest.raises(SystemExit):
        cli.parse(["run", "1", "c"])


def test_missing_required_argument():
    cli = CliCommand(Cmd)
    with pytest.raises(SystemExit):
        cli.parse(["build"])


def test_type_conversion():
    cli = CliCommand(Cmd)
    result = cli.parse(["run", "100", "b"])
    assert isinstance(result.subcommand, Run)
    assert result.subcommand.id == 100
    assert isinstance(result.subcommand.id, int)
