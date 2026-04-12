def test_readme(capsys):
    from dataclasses import dataclass, field
    from typing import Literal

    from cliclass import CliCommand

    @dataclass
    class Cmd:
        verbose: bool = field(default=False, kw_only=True)
        color: Literal["auto", "never", "always"] = field(default="auto", kw_only=True)

        file: str

    cli = CliCommand(Cmd)

    res = cli.parse(["--verbose", "path/to/file"])
    assert res == Cmd(verbose=True, file="path/to/file")

    res = cli.parse(["--color=never", "f"])
    assert res == Cmd(color="never", file="f")

    try:
        cli.parse(["--color=always"])
    except SystemExit:
        stderr = capsys.readouterr().err
        assert "error: the following arguments are required: file" in stderr
