from abc import ABC
from dataclasses import dataclass, field
from typing import Literal

from cli import get_item_docstrings, parse_into


@dataclass(slots=True, kw_only=True)
class Langopts(ABC):
    rust: bool = False
    """Run Rust tests"""

    python: bool = False
    website: bool = False


@dataclass(slots=True)
class C(Langopts):
    id: int = field(metadata={"nested": {"a": True}})
    """docstring"""

    kind: Literal["a", "b"]


print(parse_into(C))
