from typing import Iterable, Union, cast

from ptxboa.api_data import DataHandler
from ptxboa.static import FlowCodeType, ProcessCodeType, ProcessStepValues

df_process = DataHandler.get_dimension("process")


class ProcessType:
    def __init__(
        self,
        process_code: ProcessCodeType,
        is_transport: bool,
        is_secondary: bool,
        is_re_generation: bool,
        is_transformation: bool,
        main_flow_code_out: FlowCodeType,
        main_flow_code_in: FlowCodeType | None,
        secondary_flows: Iterable[FlowCodeType] | None,
        **_kwargs,
    ):
        self.process_code: ProcessCodeType = process_code
        self._is_transport: bool = is_transport
        self.is_secondary: bool = is_secondary
        self.is_transformation: bool = is_transformation
        self.is_re_generation: bool = is_re_generation
        self.main_flow_code_out: FlowCodeType = main_flow_code_out
        self.main_flow_code_in: FlowCodeType | None = main_flow_code_in
        self.secondary_flow_types: set[FlowCodeType] = (
            set(secondary_flows) if secondary_flows else set()
        )

    @property
    def is_transport(self) -> bool:
        return self._is_transport and not self.is_transformation

    @property
    def is_initial(self) -> bool:
        return self.is_re_generation or self.process_code == "NG-PROD#B"

    @property
    def process_class(self) -> type["Process"]:
        if self.is_secondary or self.is_re_generation:
            return SecondaryProcess
        else:
            return Process

    @property
    def allow_in_export(self) -> bool:
        return not self.is_transport

    @property
    def allow_in_transport(self) -> bool:
        return self.is_transport and not self.is_secondary

    @property
    def allow_in_import(self) -> bool:
        # secondary: onlyallow CCS
        return self.allow_in_export and (
            not self.is_secondary or self.process_code == "CO2-T+S#B"  # TODO:generalize
        )


ProcessTypes: dict[ProcessCodeType, ProcessType] = {
    p["process_code"]: ProcessType(**cast(dict, p))
    for p in df_process.to_dict(orient="records")
}


class Process:
    def __init__(self, process_code: ProcessCodeType):
        self._process_type: ProcessType = ProcessTypes[process_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        return self._process_type.process_code

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        return self._process_type.main_flow_code_out

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        return self._process_type.secondary_flow_types

    def initialize_parameters(self):
        pass

    def calculate(self, main_flow_out: float):
        pass

    def __str__(self):
        return self.process_code


class SecondaryProcess(Process):
    pass


class VirtualProcessMixin:
    @property
    def process_code(self) -> ProcessCodeType | None:
        return None

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        return set()


class MarketProcess(VirtualProcessMixin, SecondaryProcess):
    def __init__(self, main_flow_code_out: FlowCodeType):
        self._main_flow_code_out: FlowCodeType = main_flow_code_out

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        return self._main_flow_code_out

    def __str__(self):
        return self._main_flow_code_out


class ProcessGraphNode:
    def __init__(
        self, process: Process, link_out_to_main: Union["ProcessGraphNode", None] = None
    ):
        self.process: Process = process
        self.links_out_to_secondary: list["ProcessGraphNode"] = []
        self.link_out_to_main: Union["ProcessGraphNode", None] = link_out_to_main


class AggregateProcess(VirtualProcessMixin, Process):
    def __init__(self, process_graph_nodes_reverse_order: list[ProcessGraphNode]):
        self.process_graph_nodes_reverse_order: list[ProcessGraphNode] = (
            process_graph_nodes_reverse_order
        )

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        last_process = self.process_graph_nodes_reverse_order[0].process
        return last_process.main_flow_code_out

    def initialize_parameters(self, **kwargs):
        for n in self.process_graph_nodes_reverse_order:
            n.process.initialize_parameters(**kwargs)

    def calculate(self, main_flow_out: float):
        for n in self.process_graph_nodes_reverse_order:
            n.process.calculate(main_flow_out=main_flow_out)

    @staticmethod
    def create_from_chain(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
    ) -> "AggregateProcess":
        # split and check into export, transport, import

        # in reverse order:
        check_use_all_main_process_codes = []
        current_node = None
        process_graph_nodes_reverse_order: list[ProcessGraphNode] = []
        for chain_part_rev in ["import", "transport", "export"]:
            attr = f"allow_in_{chain_part_rev}"
            main_process_codes_part: list[ProcessCodeType] = [
                x for x in main_process_codes if getattr(ProcessTypes[x], attr)
            ]
            secondary_process_codes_part: set[ProcessCodeType] = {
                x for x in secondary_process_codes if getattr(ProcessTypes[x], attr)
            }
            check_use_all_main_process_codes = (
                main_process_codes_part + check_use_all_main_process_codes
            )
            process = AggregateProcess.create_from_chain_part(
                main_process_codes=main_process_codes_part,
                secondary_process_codes=secondary_process_codes_part,
            )
            current_node = ProcessGraphNode(
                process=process, link_out_to_main=current_node
            )
            process_graph_nodes_reverse_order.append(current_node)

        return AggregateProcess(
            process_graph_nodes_reverse_order=process_graph_nodes_reverse_order
        )

    @staticmethod
    def create_from_chain_part(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
    ) -> "AggregateProcess":
        process_graph_nodes_reverse_order: list[ProcessGraphNode] = []

        flow_providers: dict[FlowCodeType, ProcessGraphNode] = {}
        secondary_process_codes_by_flow_code: dict[FlowCodeType, ProcessCodeType] = (
            group_by_flow_type_out(secondary_process_codes)
        )

        def create_provider_node(flow_code: FlowCodeType) -> ProcessGraphNode:
            if flow_code in secondary_process_codes_by_flow_code:
                process_code = secondary_process_codes_by_flow_code[flow_code]
                process = SecondaryProcess(process_code=process_code)
            else:
                # we need to create Speccost Market process
                process = MarketProcess(main_flow_code_out=flow_code)
            return ProcessGraphNode(process=process)

        def add(node: ProcessGraphNode):
            # First (!) add dependencies recursively
            for ft in node.process.secondary_flow_types:
                if ft not in flow_providers:
                    new_node = create_provider_node(flow_code=ft)
                    add(new_node)
                    flow_providers[ft] = new_node
                # register
                flow_providers[ft].links_out_to_secondary.append(node)

            # after all dependencies are met: add node
            process_graph_nodes_reverse_order.append(node)

        # initialize nodes for main chain in reverse
        main_process_nodes: list[ProcessGraphNode] = []
        current_node = None
        for process_code in reversed(main_process_codes):
            process = Process(process_code=process_code)
            current_node = ProcessGraphNode(
                process=process, link_out_to_main=current_node
            )
            main_process_nodes.append(current_node)

        # NOTE: the initial main process will also be provider (EL/NG-G)
        first_node, nodes = main_process_nodes[0], main_process_nodes[1:]

        add(first_node)
        flow_providers[first_node.process.main_flow_code_out] = first_node
        for node in nodes:
            add(node)
            first_node = node

        return AggregateProcess(
            process_graph_nodes_reverse_order=list(
                reversed(process_graph_nodes_reverse_order)
            )
        )

    def __str__(self):
        procs = [x.process for x in reversed(self.process_graph_nodes_reverse_order)]
        return "[" + ", ".join(str(x) for x in procs) + "]"


def group_by_flow_type_out(
    process_codes: Iterable[ProcessCodeType],
) -> dict[FlowCodeType, ProcessCodeType]:
    result = {}
    for process_code in process_codes:
        flow_code = ProcessTypes[process_code].main_flow_code_out
        if flow_code in result:
            raise KeyError(f"Multiple items for {flow_code}")
        result[flow_code] = process_code
    return result


def main():
    chain_code = "STL-S__NG-DRI-C_EAF__prod_in_demand"
    first_process_code: ProcessCodeType = "NG-PROD#B"
    secondary_process_codes: set[ProcessCodeType] = {
        "HEATPUMP#B",
        "CCGT-CC#B",
        "CO2-T+S#B",
    }

    chain_data = DataHandler.get_dimension("chain").loc[chain_code].to_dict()
    main_process_codes: list[ProcessCodeType] = [
        cast(ProcessCodeType, chain_data[x]) for x in ProcessStepValues if chain_data[x]
    ]
    main_process_codes.insert(0, first_process_code)

    chain_process = AggregateProcess.create_from_chain(
        main_process_codes=main_process_codes,
        secondary_process_codes=secondary_process_codes,
    )
    print(chain_process)

    chain_process.initialize_parameters()
    chain_process.calculate(1)


main()
