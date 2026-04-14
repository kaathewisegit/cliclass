import pytest

from cliclass import CliCommand


def test_is_dataclass():
    # primitives
    with pytest.raises(TypeError, match="str is not a dataclass"):
        CliCommand(str)
    with pytest.raises(TypeError, match="int is not a dataclass"):
        CliCommand(int)
    with pytest.raises(TypeError, match="NoneType is not a dataclass"):
        CliCommand(type(None))

    class A: ...

    with pytest.raises(TypeError, match="A is not a dataclass"):
        CliCommand(A)


def test_is_type():
    with pytest.raises(TypeError, match="object `1` is not a type"):
        CliCommand(1)  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError, match="object `hi` is not a type"):
        CliCommand("hi")  # ty: ignore[invalid-argument-type]
    with pytest.raises(TypeError, match="object `None` is not a type"):
        CliCommand(None)  # ty: ignore[invalid-argument-type]

    class A: ...

    with pytest.raises(TypeError, match=r"object .* is not a type"):
        CliCommand(A())  # ty: ignore[invalid-argument-type]
