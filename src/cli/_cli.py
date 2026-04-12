import inspect
from argparse import ArgumentParser, ArgumentTypeError
from collections.abc import Callable
from dataclasses import MISSING, Field, dataclass, fields
from typing import Any, Literal, Optional, Union, get_args, get_origin

from ._docstrings import get_all_item_docstrings


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
        if "cli" in self.field.metadata:
            return self.field.metadata["cli"].get(key)
        else:
            return None

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

    def is_subcommand(self) -> bool:
        return self.get_meta("subcommand") or False

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

    def add_subcommands(self, parser: ArgumentParser):
        subparsers = parser.add_subparsers(dest=self.long())

        type = self.type()
        sub_types = get_args(type) if get_origin(type) is Union else [type]

        for type in sub_types:
            cmd = CliCommand(type)
            subparser = subparsers.add_parser(cmd.name(), help=cmd.help())
            cmd.populate_parser(subparser)

    def add_argument(self, parser: ArgumentParser):
        if self.is_subcommand():
            self.add_subcommands(parser)
            return

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

    def name(self) -> str:
        return self.cls.__name__.lower()

    def help(self) -> Optional[str]:
        return inspect.getdoc(self.cls)

    def parser_kwargs(self) -> dict:
        return {
            "prog": self.name(),
            "description": self.help(),
        }

    def populate_parser(self, parser: ArgumentParser) -> None:
        docstrings = get_all_item_docstrings(self.cls)

        for field in fields(self.cls):
            param = CliParam(field, docstrings.get(field.name))
            param.add_argument(parser)

    def make_parser(self) -> ArgumentParser:
        parser = ArgumentParser(**self.parser_kwargs())
        self.populate_parser(parser)
        return parser

    def unflatten(self, flat_args: dict[str, Any]) -> T:
        init_kwargs = {}
        docstrings = get_all_item_docstrings(self.cls)

        for f in fields(self.cls):
            param = CliParam(f, docstrings.get(f.name))

            if param.is_subcommand():
                selected_sub_name = flat_args.get(f.name)

                ftype = f.type
                sub_types = get_args(ftype) if get_origin(ftype) is Union else [ftype]

                chosen_cls = None
                for t in sub_types:
                    if t is not type(None) and t.__name__.lower() == selected_sub_name:
                        chosen_cls = t
                        break

                if chosen_cls:
                    init_kwargs[f.name] = CliCommand(chosen_cls).unflatten(flat_args)
            else:
                if f.name in flat_args:
                    init_kwargs[f.name] = flat_args[f.name]

        return self.cls(**init_kwargs)

    def parse(self) -> T:
        parser = self.make_parser()
        args = parser.parse_args()
        return self.unflatten(vars(args))
