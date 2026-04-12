import ast
import inspect


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
