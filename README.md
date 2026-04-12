`cliclass` is a library which automatically generates CLI interfaces
from Python dataclasses.  Inspired by [Clypi][clypi] and [`clap`][clap],
it creates an argument parser which returns a given class:

```python
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
```

`cliclass` uses the [`metadata` field][metadata] of the Python dataclass
interface for additional configurations.  This means that unlike other
libraries `cliclass` can be used with classes from modules which do not
depend on `cliclass`.  This allows one to create a library with core
data structures and then export them as CLIs from a secondary module
which can depends on `cliclass` via a dependency group.


[clypi]: https://danimelchor.github.io/clypi/
[clap]: https://github.com/clap-rs/clap
[metadata]: https://docs.python.org/3/library/dataclasses.html#:~:text=metadata:
