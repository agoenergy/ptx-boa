"""Classes that need _generated."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable

import ptxboa.classes._generated
from ptxboa.classes.base import PtxboaProcess, PtxboaTypeBase

if TYPE_CHECKING:
    from ptxboa.classes.base import PtxboaFlow, PtxboaFlowType


@dataclass(frozen=True, slots=True)
class PtxboaAbstractProcessType(PtxboaTypeBase):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType"
    main_flow_type_in: "PtxboaFlowType"


@dataclass(frozen=True, slots=True)
class PtxboaProcessType(PtxboaAbstractProcessType):
    """Process type variable."""

    secondary_flow_types: set["PtxboaFlowType"] = field(default_factory=set)

    def create(self, get_data: Callable, main_flow_out: "PtxboaFlow") -> PtxboaProcess:
        """Create instance."""
        # get parameters data
        eff = ptxboa.classes._generated.PtxboaParameterTypes.EFF.create(
            get_data=get_data
        )

        return PtxboaProcess(dtype=self, eff=eff, main_flow_out=main_flow_out)

    def __post_init__(self):

        self._set_attrs(secondary_flow_types=frozenset(self.secondary_flow_types))


@dataclass(frozen=True, slots=True)
class PtxboaSecondaryProcessType(PtxboaProcessType):
    """Process type variable."""


@dataclass(frozen=True, slots=True)
class PtxboaMarketSecondaryProcessType(PtxboaSecondaryProcessType):
    main_flow_type_in: "PtxboaFlowType" = field(init=False)

    """Get from market."""

    @classmethod
    def create_for_flow_type(cls, flow_type: "PtxboaFlowType"):
        """Create for Flow."""
        # TODO: make singleton for each flow?
        return cls(
            main_flow_type_out=flow_type, code=flow_type.code, name=flow_type.name
        )


@dataclass(frozen=True, slots=True)
class PtxboaProcessChain(PtxboaProcess):
    """Parameter instance variable."""

    dtype: "PtxboaProcessType"
    main_flow_out: "PtxboaFlow" = field(init=False)
    main_flow_in: "PtxboaFlow" = field(init=False)

    main_proceses: tuple[PtxboaProcess, ...]
    secondary_processes: set[PtxboaProcess]

    def __post_init__(self):

        self._set_attrs(
            main_flow_in=self.main_proceses[0].main_flow_in,
            main_flow_out=self.main_proceses[-1].main_flow_out,
            secondary_processes=frozenset(self.secondary_processes),
        )

    def __str__(self) -> str:
        return f"{self.code}({', '.join(str(x) for x in self.main_proceses)})"


def create_pot_sec_provider_for_flow(
    main_process_types: tuple[PtxboaProcessType, ...],
    secondary_process_types: set[PtxboaSecondaryProcessType],
) -> dict["PtxboaFlowType", PtxboaSecondaryProcessType]:
    # get process provider for flows
    pot_sec_provider_for_flow: dict["PtxboaFlowType", PtxboaSecondaryProcessType] = {}

    # fist chain (RES or NG-PROD) can be used for other
    p_first = main_process_types[0]
    # special case: what happens, if output of first main process
    # is also a secondary input? => self referential loop
    if p_first.main_flow_type_out in p_first.secondary_flow_types:
        raise Exception(
            f"Output of first main process is also a secondary input: {p_first}"
        )

    # sec_proc = PtxboaDummySecondaryProcessType.create_for_flow_type( # noqa
    #    flow_type=p_first.main_flow_type_out# noqa
    # )# noqa
    # pot_sec_provider_for_flow[sec_proc.main_flow_type_out] = sec_proc# noqa

    # add provider from other,allowed secondaryprocesses
    for p in secondary_process_types:
        if p.main_flow_type_out in pot_sec_provider_for_flow:
            raise Exception(f"Multiple provider for {p}")
        pot_sec_provider_for_flow[p.main_flow_type_out] = p

    return pot_sec_provider_for_flow


def create_used_secondary_processes(
    process_type: PtxboaProcessType,
    pot_sec_provider_for_flow: dict["PtxboaFlowType", PtxboaSecondaryProcessType],
    pot_market_provider_for_flow: dict[
        "PtxboaFlowType", PtxboaMarketSecondaryProcessType
    ],
) -> dict["PtxboaFlowType", PtxboaSecondaryProcessType]:
    """Also changes pot_sec_provider_for_flow and pot_market_provider_for_flow."""
    result = {}
    for ft in process_type.secondary_flow_types:
        if ft in pot_sec_provider_for_flow:
            # use secondary
            ptype = pot_sec_provider_for_flow[ft]
        else:
            # use market
            if ft not in pot_market_provider_for_flow:
                pot_market_provider_for_flow[ft] = (
                    PtxboaMarketSecondaryProcessType.create_for_flow_type(flow_type=ft)
                )
            ptype = pot_market_provider_for_flow[ft]
        result[ft] = ptype
    return result


def get_used_secondary_process_types(
    main_process_types: tuple[PtxboaProcessType, ...],
    secondary_process_types: set[PtxboaSecondaryProcessType],
) -> tuple[
    set[PtxboaSecondaryProcessType],  # used secondary processes
    list[  # links from main processes to secondary processes
        dict["PtxboaFlowType", PtxboaSecondaryProcessType]
    ],
    dict[  # links between  secondary processes
        PtxboaSecondaryProcessType, dict["PtxboaFlowType", PtxboaSecondaryProcessType]
    ],
]:

    links_main_to_secondary: list[
        dict["PtxboaFlowType", PtxboaSecondaryProcessType]
    ] = []
    links_secondary_to_secondary: dict[  # links between  secondary processes
        PtxboaSecondaryProcessType, dict["PtxboaFlowType", PtxboaSecondaryProcessType]
    ] = {}

    pot_sec_provider_for_flow = create_pot_sec_provider_for_flow(
        main_process_types, secondary_process_types
    )
    pot_market_provider_for_flow: dict[
        "PtxboaFlowType", PtxboaMarketSecondaryProcessType
    ] = {}

    # iterate over chain, add secondary processes as needed

    for pt in main_process_types:
        links_to_secondary = create_used_secondary_processes(
            pt, pot_sec_provider_for_flow, pot_market_provider_for_flow
        )
        links_main_to_secondary.append(links_to_secondary)

    # find all used
    used_secondary_processes: set[PtxboaSecondaryProcessType] = set()
    for x in links_main_to_secondary + list(links_secondary_to_secondary.values()):
        used_secondary_processes = used_secondary_processes | set(x.values())

    return (
        used_secondary_processes,
        links_main_to_secondary,
        links_secondary_to_secondary,
    )


@dataclass(frozen=True, slots=True)
class PtxboaProcessChainType(PtxboaAbstractProcessType):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType" = field(init=False)
    main_flow_type_in: "PtxboaFlowType" = field(init=False)
    main_process_types: tuple[PtxboaProcessType, ...]
    secondary_process_types: set[PtxboaSecondaryProcessType]  # will me modified in init

    def __post_init__(self):

        self._set_attrs(
            main_flow_type_in=self.main_process_types[0].main_flow_type_in,
            main_flow_type_out=self.main_process_types[-1].main_flow_type_out,
        )

        # create links and calculation order

    def __str__(self):
        return f"{self.code}({', '.join(str(x) for x in self.main_process_types)})"

    def create(
        self, get_data: Callable, main_flow_out: "PtxboaFlow"
    ) -> PtxboaProcessChain:
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

        return PtxboaProcessChain(
            dtype=self,
            _processes=tuple(reversed(processes)),
        )
