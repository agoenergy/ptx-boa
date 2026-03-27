"""Classes that need _generated."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Callable, Iterable, Union, cast

import ptxboa.classes._generated
from ptxboa.classes.base import (
    PtxboaBase,
    PtxboaFlow,
    PtxboaFlowNullType,
    PtxboaProcess,
    PtxboaTypeBase,
)

if TYPE_CHECKING:
    from ptxboa.classes.base import PtxboaFlowType


@dataclass(frozen=True, slots=True)
class PtxboaAbstractProcessType(PtxboaTypeBase):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType"
    main_flow_type_in: "PtxboaFlowType"
    secondary_flow_types: frozenset["PtxboaFlowType"] = field(init=False)

    def __post_init__(self):
        self._set_attrs(secondary_flow_types=frozenset())


@dataclass(frozen=True, slots=True)
class PtxboaProcessType(PtxboaAbstractProcessType):
    """Process type variable."""

    secondary_flow_types: frozenset["PtxboaFlowType"] = field(default_factory=frozenset)

    def create(self, get_data: Callable, main_flow_out: "PtxboaFlow") -> PtxboaProcess:
        """Create instance."""
        # get parameters data

        return PtxboaProcess(dtype=self, main_flow_out=main_flow_out)

    def __post_init__(self):
        self._set_attrs(secondary_flow_types=frozenset(self.secondary_flow_types))


@dataclass(frozen=True, slots=True)
class PtxboaTransportProcessType(PtxboaProcessType):
    """Process type variable."""


@dataclass(frozen=True, slots=True)
class PtxboaSecondaryProcessType(PtxboaProcessType):
    """Process type variable."""

    @property
    def can_use_in_import(self) -> bool:
        """Can use in import(."""
        # TODO :from data? Currently, we only allow CSS
        return self == ptxboa.classes._generated.PtxboaProcessTypes.CO2_T_S_B

    @property
    def can_use_in_transport(self) -> bool:
        """Can use in transport."""
        return False

    @property
    def can_use_in_export(self) -> bool:
        """Can use in export."""
        return True


@dataclass(frozen=True, slots=True)
class PtxboaMarketSecondaryProcessType(PtxboaSecondaryProcessType):
    main_flow_type_in: "PtxboaFlowType" = field(init=False)

    def __post_init__(self):
        self._set_attrs(
            main_flow_type_in=PtxboaFlowNullType,
        )

    @classmethod
    def create_for_flow_type(cls, flow_type: "PtxboaFlowType"):
        """Create for Flow."""
        # TODO: make singleton for each flow?
        return cls(
            main_flow_type_out=flow_type, code=flow_type.code, name=flow_type.name
        )

    def __str__(self):
        return f"Market({self.main_flow_type_out})"


@dataclass(frozen=True, slots=True)
class PtxboaProcessChain(PtxboaProcess):
    """Parameter instance variable."""

    dtype: "PtxboaProcessType"
    main_flow_out: "PtxboaFlow" = field(init=False)
    main_flow_in: "PtxboaFlow" = field(init=False)

    main_proceses: tuple[PtxboaProcess, ...]
    secondary_processes: frozenset[PtxboaProcess]

    def __post_init__(self):
        self._set_attrs(
            main_flow_in=self.main_proceses[0].main_flow_in,
            main_flow_out=self.main_proceses[-1].main_flow_out,
            secondary_processes=frozenset(self.secondary_processes),
        )

    def __str__(self) -> str:
        return f"{self.code}({', '.join(str(x) for x in self.main_proceses)})"


@dataclass(frozen=True, slots=True)
class CallOrderNode:
    index: int | PtxboaSecondaryProcessType  # int in main chain
    dtype: PtxboaAbstractProcessType
    links_out_to_secondary: list["CallOrderNode"] = field(default_factory=list)
    link_out_to_main: Union["CallOrderNode", None] = None

    def __str__(self) -> str:
        s = f"{self.index}:{self.dtype}"
        if self.link_out_to_main:
            s += f" --> {self.link_out_to_main} {self.dtype}"
        for x in self.links_out_to_secondary:
            s += f" --> {x.index} {x.dtype}"

        return s


def group_by_flow_type_out(
    items: Iterable[PtxboaAbstractProcessType],
) -> dict["PtxboaFlowType", PtxboaAbstractProcessType]:
    result = {}
    for item in items:
        key = item.main_flow_type_out
        if key in result:
            raise KeyError(f"Multiple items for {key}")
        result[key] = item
    return result


def create_secondary_process_types(
    main_process_types: tuple[PtxboaAbstractProcessType, ...],
    secondary_process_types: frozenset[PtxboaSecondaryProcessType],
) -> list[CallOrderNode]:
    flow_providers: dict[PtxboaFlowType, CallOrderNode] = {}
    # a new node can onlybe addedif all secondary flows have a provider that can
    # be linked to
    # we go through main chain and add nodes, and recursively add dependencies first

    # proxy node for main Chain
    main_process_nodes = {}
    next_node = None
    # initialize in reverse
    for i, t in reversed(list(enumerate(main_process_types))):
        node = CallOrderNode(index=i, dtype=t, link_out_to_main=next_node)
        main_process_nodes[i] = node
        next_node = node

    # secondary_process_types by flow: TODO: check if multiple options?
    secondary_process_types_by_flow = group_by_flow_type_out(secondary_process_types)

    result = []  # convert to tuple at end

    def create_provider(flow_type: "PtxboaFlowType") -> CallOrderNode:
        if flow_type in secondary_process_types_by_flow:
            dtype = cast(
                PtxboaSecondaryProcessType,
                secondary_process_types_by_flow.pop(flow_type),
            )
        else:
            # we need to create Speccost Market process
            dtype = PtxboaMarketSecondaryProcessType.create_for_flow_type(
                flow_type=flow_type
            )
        return CallOrderNode(index=dtype, dtype=dtype)

    def add(node: CallOrderNode):
        # First (!) add dependencies recursively
        for ft in node.dtype.secondary_flow_types:
            if ft not in flow_providers:
                new_node = create_provider(flow_type=ft)
                add(new_node)
                flow_providers[ft] = new_node
            # register
            flow_providers[ft].links_out_to_secondary.append(node)

        # after all dependencies are met: add node
        result.append(node)

    # NOTE: the initial main process will also be provider (EL/NG-G)
    first_node, nodes = (
        main_process_nodes[0],
        [main_process_nodes[i] for i in range(1, len(main_process_nodes))],
    )
    add(first_node)
    flow_providers[first_node.dtype.main_flow_type_out] = first_node
    for node in nodes:
        add(node)
        first_node = node

    return list(reversed(result))


@dataclass(frozen=True, slots=True)
class PtxboaProcessChainType(PtxboaAbstractProcessType):
    """Process type variable."""

    main_flow_type_out: "PtxboaFlowType" = field(init=False)
    main_flow_type_in: "PtxboaFlowType" = field(init=False)
    main_process_types: tuple[PtxboaAbstractProcessType, ...]
    secondary_process_types: frozenset[
        PtxboaSecondaryProcessType
    ]  # will me modified in init
    _call_order: tuple[CallOrderNode, ...] = field(init=False)

    def __post_init__(self):
        # create links and calculation order, change secondary_process_types
        # we need call order for secondary_process_types
        # and indices in main_process_types
        # and for each the processes it feeds into
        _call_order = create_secondary_process_types(
            main_process_types=self.main_process_types,
            secondary_process_types=self.secondary_process_types,
        )

        # only used secondary_process_types
        secondary_process_types = [
            x.index
            for x in _call_order
            if isinstance(x.index, PtxboaSecondaryProcessType)
        ]
        # FIXME: why cant i convert to set?
        # secondary_process_types = set(secondary_process_types) # noqa

        self._set_attrs(
            main_flow_type_in=self.main_process_types[0].main_flow_type_in,
            main_flow_type_out=self.main_process_types[-1].main_flow_type_out,
            _call_order=_call_order,
            secondary_process_types=secondary_process_types,
            secondary_flow_types=frozenset(),
        )

    def __str__(self):
        main = " == ".join(str(x) for x in self.main_process_types)
        sec = "".join(" +" + str(x) for x in self.secondary_process_types)
        return f"{self.code}({main}{sec})"

    def create(
        self, get_data: Callable, main_flow_out: "PtxboaFlow"
    ) -> PtxboaProcessChain:
        """Create instance."""
        # IMPORTANT: initialize backwards
        all_processes: dict[int | PtxboaSecondaryProcessType, PtxboaProcess] = {}

        for idx, node in enumerate(self._call_order):
            flow_type = node.dtype.main_flow_type_out
            if idx > 0:
                # sum outputs of previously initialized processes
                main_flow_out = PtxboaFlow(dtype=flow_type, value=0)
                if node.link_out_to_main:
                    process = all_processes[node.link_out_to_main.index]
                    main_flow_out += process.main_flow_in
                for target in node.links_out_to_secondary:
                    main_flow_out += all_processes[target.index].secondary_flows_in[
                        flow_type
                    ]
            # initialize process
            process = node.dtype.create(get_data=get_data, main_flow_out=main_flow_out)
            all_processes[node.index] = process

        # separate all_processes
        main_proceses = tuple(
            all_processes[i] for i in range(len(self.main_process_types))
        )
        secondary_processes = frozenset(
            all_processes[i] for i in self.secondary_process_types
        )

        return PtxboaProcessChain(
            dtype=self,
            main_proceses=main_proceses,
            secondary_processes=secondary_processes,
        )


@dataclass(frozen=True, slots=True)
class PtxboaChainTemplate(PtxboaBase):
    flow_type_out: "PtxboaFlowType"

    # TODO: should be frozen (dict are sorted since 3.7)
    # steps: dict["PtxboaStep", "PtxboaProcessType"] # noqa
    process_types: tuple["PtxboaProcessType", ...]

    def split_export_transport_import(
        self,
    ) -> tuple[
        tuple["PtxboaProcessType", ...],  # exports
        tuple["PtxboaProcessType", ...],  # transports
        tuple["PtxboaProcessType", ...],  # imports
    ]:
        """Split process_types in 3 parts."""
        is_transport = [
            isinstance(x, PtxboaTransportProcessType) for x in self.process_types
        ]
        # split in: all False, all True, all False
        idx_first_transport = is_transport.index(True)
        idx_first_import = is_transport.index(False, idx_first_transport)

        if not (
            all(x is False for x in is_transport[:idx_first_transport])
            and all(
                x is True for x in is_transport[idx_first_transport:idx_first_import]
            )
            and all(x is False for x in is_transport[idx_first_import:])
        ):
            raise Exception(f"Transport/NonTransport not correct: {is_transport}")
        return (
            tuple(self.process_types[:idx_first_transport]),
            tuple(self.process_types[idx_first_transport:idx_first_import]),
            tuple(self.process_types[idx_first_import:]),
        )


@dataclass(frozen=True, slots=True)
class PtxboaChainGreenTemplate(PtxboaChainTemplate):
    pass


@dataclass(frozen=True, slots=True)
class PtxboaChainBlueTemplate(PtxboaChainTemplate):
    pass
