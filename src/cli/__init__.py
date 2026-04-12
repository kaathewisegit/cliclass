import ast
import inspect
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Callable
from dataclasses import MISSING, Field, dataclass, fields
from typing import Any, Literal, Optional, TypeAliasType, get_args, get_origin


def make_literal_parser(literal) -> Callable[[str], str]:
    args = get_args(literal)
    for arg in args:
        if not isinstance(arg, str):
            raise TypeError(
                "Literal annotations only support `str`.  Use a custom parser for other types"
            )

    def literal_parser(input: str) -> str:
        if input not in args:
            raise ArgumentTypeError(f"expected one of {args}, got {input}")
        return input

    return literal_parser


@dataclass(slots=True)
class CliParam[T]:
    field: Field
    docstring: Optional[str]

    def name(self) -> str:
        return self.field.name

    def positional(self) -> bool:
        return not self.field.kw_only

    def get_meta[U](self, key: str) -> Optional[U]:
        return self.field.metadata.get(key) if self.field.metadata else None

    def long(self) -> str:
        return self.get_meta("long") or self.field.name.replace("_", "-")

    def short(self) -> Optional[str]:
        return self.get_meta("short")

    def type(self):
        return self.field.type

    def help(self) -> Optional[str]:
        return self.get_meta("help") or self.docstring

    def parser[U](self) -> Optional[Callable[[str], U]]:
        if self.get_meta("parser"):
            return self.get_meta("parser")

        if get_origin(self.type()) is Literal:
            return make_literal_parser(self.type())

        return None

    def flags(self) -> list[str]:
        if self.positional():
            return [self.name()]
        else:
            out = []
            if self.short():
                out.append(f"-{self.short()}")
            out.append(f"--{self.long()}")
            return out

    def action(self) -> Literal["store", "store_true", "count"]:
        if self.type() is bool:
            return "store_true"
        else:
            return "store"

    def required(self) -> bool:
        return (
            self.field.default is MISSING
            and self.field.default_factory is MISSING
            and not self.positional()
        )

    def add_argument(self, parser: ArgumentParser):
        kwargs = {}

        if self.required():
            kwargs["required"] = True

        if not self.positional():
            kwargs["action"] = self.action()

        if self.action() != "store_true":
            kwargs["type"] = self.parser()

        if self.help:
            kwargs["help"] = self.help()

        parser.add_argument(*self.flags(), **kwargs)


@dataclass(slots=True)
class CliCommand[T]:
    cls: type[T]

    def make_parser(self) -> ArgumentParser:
        parser = ArgumentParser(
            prog=self.cls.__name__,
            description=inspect.getdoc(self.cls),
        )

        docstrings = get_all_item_docstrings(self.cls)

        parameters = [CliParam(f, docstrings.get(f.name)) for f in fields(self.cls)]
        for param in parameters:
            param.add_argument(parser)

        return parser

    def parse(self) -> T:
        parser = self.make_parser()
        args = parser.parse_args()
        return self.cls(**vars(args))


def get_item_docstrings(cls, docstrings: dict[str, str]):
    source = inspect.getsource(cls)
    tree = ast.parse(source)

    class_def = tree.body[0]
    assert isinstance(class_def, ast.ClassDef)

    for i, node in enumerate(class_def.body):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            attr_name = node.target.id
            # add if the next statement is a constant string
            if i + 1 < len(class_def.body):
                next_node = class_def.body[i + 1]
                if isinstance(next_node, ast.Expr) and isinstance(
                    next_node.value, ast.Constant
                ):
                    if isinstance(next_node.value.value, str):
                        docstrings[attr_name] = inspect.cleandoc(next_node.value.value)

    return docstrings


def get_all_item_docstrings(cls) -> dict[str, str]:
    """Applies `get_item_docstrings` recursively to base classes"""

    docstrings = {}

    for base in reversed(cls.__mro__):
        if base.__module__ == "builtins":
            continue

        try:
            get_item_docstrings(base, docstrings)
        except TypeError, OSError, StopIteration:
            # source code not available
            continue

    return docstrings
