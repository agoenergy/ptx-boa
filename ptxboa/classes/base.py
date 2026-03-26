"""Base classes and class factories."""

from dataclasses import dataclass, field
from typing import Callable, ClassVar, Iterable, cast

from typing_extensions import Self  # for python 3.11+: from typing import Self

import ptxboa.classes._generated  # noqa


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


@dataclass(frozen=True, slots=True)
class PtxboaBase(AbstractBase):
    """Project base class."""

    code: ClassVar[str]
    name: ClassVar[str]

    def __str__(self) -> str:
        return self.code

    def __post_init__(self):
        # field_names = [f.name for f in fields(self) if not f.init] # noqa
        for fieldname, value in self._calculate().items():
            object.__setattr__(self, fieldname, value)

    def _calculate(self) -> dict:
        return {}


@dataclass(frozen=True, slots=True)
class PtxboaValue(PtxboaBase):
    """Single value container."""

    value: float

    def __str__(self) -> str:
        return f"{self.code}({self.value:.4f})"


@dataclass(frozen=True, slots=True)
class PtxboaFlow(PtxboaValue):
    """Flow variable."""

    code: ClassVar[str] = ""
    name: ClassVar[str] = ""


@dataclass(frozen=True, slots=True)
class PtxboaFlowNull(PtxboaFlow):
    """No flow."""


@dataclass(frozen=True, slots=True)
class PtxboaParameter(PtxboaValue):
    """Input Parameter.

    value will be read set in __post_init__
    """

    value: float = field(init=False)
    _get_data: Callable[..., float]

    def _calculate(self) -> dict:
        return {"value": self._get_data()}


@dataclass(frozen=True, slots=True)
class PtxboaRegion(PtxboaBase):
    """Region/Country."""

    code: str
    name: str


@dataclass(frozen=True, slots=True)
class PtxboaRoute(PtxboaBase):
    """from region to country."""

    code: str = field(init=False)
    name: str = field(init=False)

    from_region: PtxboaRegion
    to_region: PtxboaRegion

    def _calculate(self) -> dict:
        code = f"{self.from_region.code}->{self.to_region.code}"
        return {
            "code": code,
            "name": code,
        }


@dataclass(frozen=True, slots=True)
class PtxboaAbstractProcess(PtxboaValue):
    """Abstract Process."""

    main_flow_type_in: ClassVar[type[PtxboaFlow]]
    main_flow_type_out: ClassVar[type[PtxboaFlow]]

    main_flow_var_in: PtxboaFlow = field(init=False)
    main_flow_var_out: PtxboaFlow = field(init=False)
    _get_data: Callable[..., float]

    def __str__(self) -> str:
        return f"{self.code}({self.main_flow_var_in} => {self.main_flow_var_out})"

    def _calculate(self) -> dict:
        return {
            "main_flow_var_in": self.main_flow_type_in(self.value),
            "main_flow_var_out": self.main_flow_type_out(self.value),
        }


@dataclass(frozen=True, slots=True)
class PtxboaProcess(PtxboaAbstractProcess):
    """Primitive Process."""

    eff: PtxboaParameter = field(init=False)

    def __str__(self) -> str:
        return f"{self.code}({self.main_flow_var_in} ={self.eff}=> {self.main_flow_var_out})"  # noqa

    def _calculate(self) -> dict:
        eff = ptxboa.classes._generated.PtxboaParameters.EFF(_get_data=self._get_data)

        return {
            "eff": eff,
            "main_flow_var_in": self.main_flow_type_in(self.value / eff.value),
            "main_flow_var_out": self.main_flow_type_out(self.value),
        }


@dataclass(frozen=True, slots=True)
class PtxboaCompositeProcess(PtxboaAbstractProcess):
    """Composite Process."""


@dataclass(frozen=True, slots=True)
class PtxboaChainExport(PtxboaCompositeProcess):
    """PtxboaChainExport."""


@dataclass(frozen=True, slots=True)
class PtxboaChainImport(PtxboaCompositeProcess):
    """PtxboaChainExport."""


@dataclass(frozen=True, slots=True)
class PtxboaChainTransport(PtxboaCompositeProcess):
    """PtxboaChainExport."""


@dataclass(frozen=True, slots=True)
class PtxboaChain(PtxboaCompositeProcess):
    """PtxboaChain."""

    process_types: ClassVar[tuple[type[PtxboaProcess]]]

    process_vars: tuple[PtxboaProcess] = field(init=False)

    @classmethod
    def _create_subclass(
        cls,
        class_name: str,
        code: str,
        name: str,
        process_types: Iterable[type[PtxboaProcess]],
        template_class_name: str | None = None,
    ) -> type[Self]:

        process_types = tuple(process_types)
        if not process_types:
            raise Exception("Empty Chain")

        class_attrs = {
            "code": code,
            "name": name,
            "process_types": process_types,
            "main_flow_type_in": process_types[0].main_flow_type_in,
            "main_flow_type_out": process_types[-1].main_flow_type_out,
        }
        # NOTE: cannot user super()._create_subclass because of dataclass
        return super(PtxboaChain, cls)._create_subclass(
            class_name=class_name,
            template_class_name=template_class_name,
            **class_attrs,
        )

    def _calculate(self) -> dict:
        # IMPORTANT: we init from last to first
        value = self.value
        processes = []
        for ProcessType in reversed(self.process_types):
            process = ProcessType(value, _get_data=self._get_data)
            processes.append(process)
            value = process.main_flow_var_in.value
        return {"process_vars": tuple(reversed(processes))}

    def __str__(self) -> str:
        parts = [str(p) for p in self.process_vars]
        return f"{self.code}({', '.join(parts)})"


@dataclass(frozen=True, slots=True)
class PtxboaProcessMarket(PtxboaBase):
    """PtxboaProcessMarket."""
