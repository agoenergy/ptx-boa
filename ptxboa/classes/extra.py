"""Classes that need _generated."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

import ptxboa.classes._generated
from ptxboa.classes.base import PtxboaParameter, PtxboaProcess, PtxboaTypeBase

if TYPE_CHECKING:
    from ptxboa.classes.base import PtxboaFlow, PtxboaFlowType


@dataclass(frozen=True, slots=True)
class PtxboaProcessType(PtxboaTypeBase):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType"
    main_flow_type_in: "PtxboaFlowType"
    secondary_flows: tuple["PtxboaFlowType", ...]

    def create(self, get_data: Callable, main_flow_out: "PtxboaFlow") -> PtxboaProcess:
        """Create instance."""
        # get parameters data
        eff = ptxboa.classes._generated.PtxboaParameterTypes.EFF.create(
            get_data=get_data
        )

        return PtxboaProcess(dtype=self, eff=eff, main_flow_out=main_flow_out)


@dataclass(frozen=True, slots=True)
class PtxboaSecondaryProcessType(PtxboaProcessType):
    """Process type variable."""


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
