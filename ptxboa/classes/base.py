"""Base classes and class factories."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ptxboa.classes.extra import PtxboaAbstractProcessType, PtxboaProcessType


@dataclass(frozen=True, slots=True)
class PtxboaBase:
    """Project base class."""

    code: str
    name: str

    def __str__(self) -> str:
        return self.code

    def _set_attrs(self, **attrs) -> None:
        """Note: Should only be called in __post_init__."""
        for name, value in attrs.items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class PtxboaTypeBase(PtxboaBase):
    """Project base class."""

    def create(self) -> "PtxboaInstanceBase":
        """Create instance."""
        return PtxboaInstanceBase(dtype=self)


@dataclass(frozen=True, slots=True)
class PtxboaInstanceBase:
    """Project base class."""

    dtype: PtxboaTypeBase

    @property
    def code(self) -> str:
        """code."""
        return self.dtype.code

    @property
    def name(self) -> str:
        """name."""
        return self.dtype.name

    def _set_attrs(self, **attrs) -> None:
        """Note: Should only be called in __post_init__."""
        for name, value in attrs.items():
            object.__setattr__(self, name, value)


@dataclass(frozen=True, slots=True)
class PtxboaValue(PtxboaInstanceBase):
    """Parameter instance variable."""

    value: float

    def __str__(self) -> str:
        return f"{self.code}({self.value:.4f})"


@dataclass(frozen=True, slots=True)
class PtxboaParameter(PtxboaValue):
    """Parameter instance variable."""


@dataclass(frozen=True, slots=True)
class PtxboaParameterType(PtxboaTypeBase):
    """Parameter type variable."""

    def create(self, get_data: Callable) -> PtxboaParameter:
        """Create instance."""
        value = get_data()
        return PtxboaParameter(dtype=self, value=value)


@dataclass(frozen=True, slots=True)
class PtxboaAbstractProcess(PtxboaInstanceBase):
    """Parameter instance variable."""

    dtype: "PtxboaAbstractProcessType"
    main_flow_out: "PtxboaFlow"
    main_flow_in: "PtxboaFlow" = field(init=False)
    secondary_flows_in: dict["PtxboaFlowType", "PtxboaFlow"] = field(init=False)

    def __post_init__(self):
        # check
        if self.dtype.main_flow_type_out != self.main_flow_out.dtype:
            raise TypeError(
                f"{self.dtype.main_flow_type_out} != {self.main_flow_out.dtype}"
            )

    def __str__(self) -> str:
        return f"{self.code}( ==> {self.main_flow_out})"


@dataclass(frozen=True, slots=True)
class PtxboaProcess(PtxboaAbstractProcess):
    """Parameter instance variable."""

    dtype: "PtxboaProcessType"
    eff: PtxboaParameter = field(init=False)
    main_flow_out: "PtxboaFlow"
    main_flow_in: "PtxboaFlow" = field(init=False)

    def __post_init__(self):
        # load parameters # FIXME noqa
        # eff = ptxboa.classes._generated.PtxboaParameterTypes.EFF.create( # FIXME noqa
        #    get_data=get_data # FIXME noqa
        # ) # FIXME noqa
        eff = 1

        main_flow_in = self.dtype.main_flow_type_in.create(
            self.main_flow_out.value / eff
        )

        # FIXME: from data
        convs = {ft: 1 for ft in self.dtype.secondary_flow_types}  # FIXME # noqa

        secondary_flows_in = {
            ft: PtxboaFlow(dtype=ft, value=self.main_flow_out.value * conv)
            for ft, conv in convs.items()
        }

        self._set_attrs(
            main_flow_in=main_flow_in, secondary_flows_in=secondary_flows_in, eff=eff
        )

    def __str__(self) -> str:
        return f"{self.code}({self.main_flow_in} = {self.eff} => {self.main_flow_out})"


@dataclass(frozen=True, slots=True)
class PtxboaFlow(PtxboaValue):
    """Flow instance variable."""

    def __add__(self, other: "PtxboaFlow") -> "PtxboaFlow":
        if self.dtype != other.dtype:
            raise TypeError()
        return PtxboaFlow(dtype=self.dtype, value=self.value + other.value)


@dataclass(frozen=True, slots=True)
class PtxboaFlowType(PtxboaTypeBase):
    """Flow type variable."""

    def create(self, value: float) -> "PtxboaFlow":
        """Create instance."""
        return PtxboaFlow(dtype=self, value=value)


PtxboaFlowNullType = PtxboaFlowType(code="", name="")


@dataclass(frozen=True, slots=True)
class PtxboaRegion(PtxboaBase):
    """Region/Country."""


@dataclass(frozen=True, slots=True)
class PtxboaRoute(PtxboaBase):
    """from region to country."""

    code: str = field(init=False)
    name: str = field(init=False)

    region_from: PtxboaRegion
    region_to: PtxboaRegion

    def __post_init__(self):
        code = f"{self.region_from} => {self.region_to}"
        self._set_attrs(code=code, name=code)

    def __str__(self) -> str:
        return f"Route({self.code})"


@dataclass(frozen=True, slots=True)
class PtxboaStep(PtxboaBase):
    pass


class PtxboaEnum:
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._by_code: dict[str, PtxboaBase] = {}
        cls._by_name: dict[str, PtxboaBase] = {}
        cls._in_order: list[PtxboaBase] = []
        for item in cls.__dict__.values():
            if not isinstance(item, PtxboaBase):
                continue

            cls._in_order.append(item)
            if item.code in cls._by_code:
                raise KeyError(item.code)
            cls._by_code[item.code] = item
            if item.name in cls._by_name:
                raise KeyError(item.code)
            cls._by_name[item.name] = item

    @classmethod
    def get_all(cls) -> tuple[PtxboaBase, ...]:
        """Get all."""
        return tuple(cls._in_order)

    @classmethod
    def get_by_code(cls, code: str):
        """Get by code."""
        return cls._by_code[code]

    @classmethod
    def get_by_name(cls, name: str):
        """Get by name."""
        return cls._by_name[name]


class PtxboaSteps(PtxboaEnum):
    EL_STR = PtxboaStep(code="EL_STR", name="EL_STR")
    ELY = PtxboaStep(code="ELY", name="ELY")
    H2_STR = PtxboaStep(code="H2_STR", name="H2_STR")
    DERIV = PtxboaStep(code="DERIV", name="DERIV")
    DERIV2 = PtxboaStep(code="DERIV2", name="DERIV2")
    PRE_SHP = PtxboaStep(code="PRE_SHP", name="PRE_SHP")
    PRE_PPL = PtxboaStep(code="PRE_PPL", name="PRE_PPL")
    POST_SHP = PtxboaStep(code="POST_SHP", name="POST_SHP")
    POST_PPL = PtxboaStep(code="POST_PPL", name="POST_PPL")
    SHP = PtxboaStep(code="SHP", name="SHP")
    SHP_OWN = PtxboaStep(code="SHP_OWN", name="SHP_OWN")
    PPLS = PtxboaStep(code="PPLS", name="PPLS")
    PPL = PtxboaStep(code="PPL", name="PPL")
    PPLX = PtxboaStep(code="PPLX", name="PPLX")
    PPLR = PtxboaStep(code="PPLR", name="PPLR")
    ELY_I = PtxboaStep(code="ELY_I", name="ELY_I")
    DERIV_I = PtxboaStep(code="DERIV_I", name="DERIV_I")
    DERIV_I2 = PtxboaStep(code="DERIV_I2", name="DERIV_I2")


@dataclass(frozen=True, slots=True)
class PtxboaTransportType(PtxboaBase):
    is_shipping: bool
    is_own_fuel: bool


class PtxboaTransportTypes(PtxboaEnum):
    SHP = PtxboaTransportType(
        code="SHP", name="Shipping", is_shipping=True, is_own_fuel=False
    )
    SHP_OWN = PtxboaTransportType(
        code="SHP_OWN", name="Shipping (own fuel)", is_shipping=True, is_own_fuel=False
    )
    PPL = PtxboaTransportType(
        code="PPL", name="Pipeline", is_shipping=False, is_own_fuel=True
    )
