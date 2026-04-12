import subprocess
import sys
from dataclasses import dataclass, field

from cli import CliCommand


def exec(cmd: str, **kwargs):
    result = subprocess.run(cmd, shell=True, **kwargs)

    if result.returncode != 0:
        sys.exit(f"Command `{cmd}` failed with exit code {result.returncode}")

    return result


@dataclass
class Check:
    def run(self):
        exec("ruff check --extend-select F401 ")
        exec("ty check")


@dataclass
class Test:
    def run(self):
        exec("pytest")


@dataclass
class Toolkit:
    subcommand: Check | Test = field(metadata={"cli": {"subcommand": True}})

    def run(self):
        self.subcommand.run()


toolkit = CliCommand(Toolkit).parse()
toolkit.run()
