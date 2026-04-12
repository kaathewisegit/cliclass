from abc import ABC
from dataclasses import dataclass, field
from typing import Literal

import pytest

from cli import CliCommand


@dataclass(kw_only=True)
class Langopts(ABC):
    rust: bool = False
    """Run Rust tests"""

    python: bool = False
    website: bool = False


@dataclass
class Run(Langopts):
    "Run stuff"

    id: int
    """docstring"""

    kind: Literal["a", "b"]


@dataclass
class Build(Langopts):
    "Build stuff"

    stuff: str


@dataclass(kw_only=True)
class CommonOpts(ABC):
    verbose: bool = False
    timeout: int = 30


@dataclass
class Deploy(Langopts, CommonOpts):
    """Deploy the project"""

    env: Literal["dev", "prod"]
    region: str = "us-east-1"


@dataclass(slots=True)
class AppCmd:
    subcommand: Run | Build | Deploy = field(metadata={"cli": {"subcommand": True}})
    debug: bool = field(default=False, kw_only=True)

    import pytest


def test_deploy_full_args():
    cli = CliCommand(AppCmd)
    args = ["deploy", "prod", "eu-west-1", "--rust", "--verbose", "--timeout", "60"]

    res = cli.parse(args)

    assert isinstance(res.subcommand, Deploy)
    assert res.subcommand.env == "prod"
    assert res.subcommand.region == "eu-west-1"
    assert res.subcommand.rust is True
    assert res.subcommand.verbose is True
    assert res.subcommand.timeout == 60


def test_deploy_defaults():
    cli = CliCommand(AppCmd)
    res = cli.parse(["deploy", "dev"])
    assert isinstance(res.subcommand, Deploy)
    assert res.subcommand.region == "us-east-1"
    assert res.subcommand.verbose is False


def test_top_level_debug():
    cli = CliCommand(AppCmd)
    res = cli.parse(["--debug", "run", "1", "a"])
    assert res.debug is True
    assert isinstance(res.subcommand, Run)


def test_invalid_literal_choice():
    cli = CliCommand(AppCmd)
    with pytest.raises(SystemExit):
        cli.parse(["deploy", "staging"])  # not in Literal


def test_type_coercion_timeout():
    cli = CliCommand(AppCmd)
    res = cli.parse(["deploy", "dev", "--timeout", "100"])
    assert isinstance(res.subcommand, Deploy)
    assert res.subcommand.timeout == 100


def test_no_subcommand_provided():
    cli = CliCommand(AppCmd)
    with pytest.raises(SystemExit):
        cli.parse([])


def test_unknown_flag():
    cli = CliCommand(AppCmd)
    with pytest.raises(SystemExit):
        cli.parse(["build", "stuff", "--unknown-flag"])
