"""Base classes and class factories."""

from dataclasses import dataclass
from typing import ClassVar, Optional, cast

from typing_extensions import Self  # for python 3.11+: from typing import Self


class AbstractBase:
    @classmethod
    def _find_subclass_by_name(cls, class_name: str) -> type[Self]:
        if cls.__name__ == class_name:
            return cls
        for subclass in cls.__subclasses__():
            try:
                return subclass._find_subclass_by_name(class_name=class_name)
            except NotImplementedError:
                pass
        raise NotImplementedError(class_name)

    @classmethod
    def _create_subclass(
        cls, class_name: str, template_class_name: str | None = None, **class_attrs
    ) -> type[Self]:

        base_class = (
            cls._find_subclass_by_name(template_class_name)
            if template_class_name
            else cls
        )

        # Create new class
        new_class = type(class_name, (base_class,), class_attrs)

        # Apply dataclass decorator
        # new_cls = dataclass(new_cls, frozen=True, slots=True) # noqa: E800

        # type cast for IDE hints
        new_class = cast(type[Self], new_class)

        return new_class

    @property
    def classname(self) -> str:
        """Class name."""
        return self.__class__.__name__


@dataclass(frozen=True, slots=True)
class PtxboaBase(AbstractBase):
    """Project base class."""

    code: ClassVar[str]
    name: ClassVar[str]


@dataclass(frozen=True, slots=True)
class PtxboaValue(PtxboaBase):
    """Single value container."""

    value: Optional[float] = 0


@dataclass(frozen=True, slots=True)
class PtxboaFlow(PtxboaValue):
    """Flow variable."""


@dataclass(frozen=True, slots=True)
class PtxboaParameter(PtxboaValue):
    """Input Parameter."""


@dataclass(frozen=True, slots=True)
class PtxboaProcess(PtxboaBase):
    """Primitive Process."""


@dataclass(frozen=True, slots=True)
class PtxboaRegion(PtxboaBase):
    """Region/Country."""

    code: str
    name: str
