"""Base classes and class factories."""

from dataclasses import dataclass, field
from typing import Callable

import ptxboa.classes._generated


@dataclass(frozen=True, slots=True)
class PtxboaBase:
    """Project base class."""

    code: str
    name: str

    def __str__(self) -> str:
        return self.code


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
class PtxboaProcess(PtxboaInstanceBase):
    """Parameter instance variable."""

    dtype: "PtxboaProcessType"
    eff: PtxboaParameter
    main_flow_out: "PtxboaFlow"
    main_flow_in: "PtxboaFlow" = field(init=False)

    def __post_init__(self):

        # check
        if self.dtype.main_flow_type_out != self.main_flow_out.dtype:
            raise TypeError(
                f"{self.dtype.main_flow_type_out} != {self.main_flow_out.dtype}"
            )

        main_flow_in = self.dtype.main_flow_type_in.create(
            self.main_flow_out.value / self.eff.value
        )

        object.__setattr__(
            self,
            "main_flow_in",
            main_flow_in,
        )

    def __str__(self) -> str:
        return f"{self.code}({self.main_flow_in} = {self.eff} => {self.main_flow_out})"


@dataclass(frozen=True, slots=True)
class PtxboaProcessType(PtxboaTypeBase):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType"
    main_flow_type_in: "PtxboaFlowType"

    def create(self, get_data: Callable, main_flow_out: "PtxboaFlow") -> PtxboaProcess:
        """Create instance."""
        # get parameters data
        eff = ptxboa.classes._generated.PtxboaParameterTypes.EFF.create(
            get_data=get_data
        )

        return PtxboaProcess(dtype=self, eff=eff, main_flow_out=main_flow_out)


@dataclass(frozen=True, slots=True)
class PtxboaProcessTree(PtxboaProcess):
    """Parameter instance variable."""

    dtype: "PtxboaProcessType"
    eff: PtxboaParameter = field(init=False)
    main_flow_out: "PtxboaFlow" = field(init=False)
    main_flow_in: "PtxboaFlow" = field(init=False)

    _processes: tuple[PtxboaProcess, ...]

    def __post_init__(self):

        # TODO: this might not work if its an actual graph
        first_process = self._processes[0]  # noqa
        last_process = self._processes[-1]  # noqa

        object.__setattr__(
            self,
            "main_flow_in",
            first_process.main_flow_in,
        )
        object.__setattr__(
            self,
            "main_flow_out",
            last_process.main_flow_out,
        )
        object.__setattr__(
            self,
            "eff",
            PtxboaParameter(
                dtype=ptxboa.classes._generated.PtxboaParameterTypes.EFF,
                value=last_process.main_flow_out.value
                / first_process.main_flow_in.value,
            ),
        )

    def __str__(self) -> str:
        return f"{self.code}({', '.join(str(x) for x in self._processes)})"


@dataclass(frozen=True, slots=True)
class PtxboaProcessTreeType(PtxboaProcessType):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType" = field(init=False)
    main_flow_type_in: "PtxboaFlowType" = field(init=False)

    process_types: tuple[PtxboaProcessType, ...]

    def __post_init__(self):
        if not self.process_types:
            raise Exception("No processes.")

        # TODO: this might not work if its an actual graph
        first_process_type = self.process_types[0]
        last_process_type = self.process_types[-1]

        object.__setattr__(
            self, "main_flow_type_in", first_process_type.main_flow_type_in
        )
        object.__setattr__(
            self, "main_flow_type_out", last_process_type.main_flow_type_out
        )

    def __str__(self):
        return f"{self.code}({', '.join(str(x) for x in self.process_types)})"

    def create(
        self, get_data: Callable, main_flow_out: "PtxboaFlow"
    ) -> PtxboaProcessTree:
        """Create instance."""
        # IMPORTANT: initialize backwards

        current_main_out: PtxboaFlow = main_flow_out
        processes = []
        for process_type in reversed(self.process_types):
            process = process_type.create(
                get_data=get_data, main_flow_out=current_main_out
            )
            processes.append(process)
            current_main_out = process.main_flow_in

        return PtxboaProcessTree(
            dtype=self,
            _processes=tuple(reversed(processes)),
        )


@dataclass(frozen=True, slots=True)
class PtxboaSecondaryProcessType(PtxboaProcessType):
    """Process type variable."""


@dataclass(frozen=True, slots=True)
class PtxboaFlow(PtxboaValue):
    """Flow instance variable."""


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

    from_region: PtxboaRegion
    to_region: PtxboaRegion

    def __post_init__(self):
        code = f"{self.from_region} => {self.to_region}"
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "name", code)

    def __str__(self) -> str:
        return f"Route({self.code})"
