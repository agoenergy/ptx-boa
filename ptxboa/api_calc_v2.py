import argparse
import logging
from typing import Iterable, Union, cast

import coloredlogs

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
        if self.is_initial:
            return InitialProcess
        elif self.is_secondary:
            return SecondaryProcess
        elif self.is_transport:
            return TransportProcess
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


class AbstractProcess:
    def __init__(self):
        self._main_flow_out: float | None = None  # will be set in calculate()
        self._main_flow_in: float | None = None  # will be set in calculate()
        self._secondary_flows_in: dict[FlowCodeType, float] | None = None

    def get_main_flow_out(self) -> float:
        if not self._main_flow_out:  # 0 or None
            raise Exception("Not calculated yet")
        return self._main_flow_out

    def get_main_flow_in(self) -> float:
        if not self._main_flow_in:  # 0 or None
            raise Exception("Not calculated yet, or main_flow_in does not exist")
        return self._main_flow_in

    def get_secondary_flow_in(self, flow_code: FlowCodeType) -> float:
        if not self._secondary_flows_in:
            raise Exception("Not calculated yet")
        return self._secondary_flows_in[flow_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        return None

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        raise NotImplementedError

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        return set()

    def initialize_parameters(self):
        pass

    def calculate(self, main_flow_out: float):
        self._main_flow_out = main_flow_out

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        return f"{self.__class__.__name__}({self.process_code}{s_val})"


class Process(AbstractProcess):
    def __init__(self, process_code: ProcessCodeType):
        super().__init__()
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
        super().initialize_parameters()

    def calculate(self, main_flow_out: float):
        super().calculate(main_flow_out=main_flow_out)
        eff = 0.9
        self._main_flow_in = main_flow_out / eff
        conv = 0.7
        self._secondary_flows_in = {
            fc: main_flow_out * conv for fc in self.secondary_flow_types
        }


class TransportProcess(Process):
    pass


class SecondaryProcess(Process):
    pass


class InitialProcess(SecondaryProcess):
    pass


class MarketProcess(AbstractProcess):
    def __init__(self, main_flow_code_out: FlowCodeType):
        super().__init__()
        self._main_flow_code_out: FlowCodeType = main_flow_code_out

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        return self._main_flow_code_out

    @property
    def process_code(self) -> ProcessCodeType | None:
        return self.main_flow_code_out  # type:ignore


class ProcessGraphNode:
    def __init__(
        self,
        process: AbstractProcess,
        link_out_to_main: Union["ProcessGraphNode", None] = None,
    ):
        self.process: AbstractProcess = process
        self.links_out_to_secondary: list["ProcessGraphNode"] = []
        self.link_out_to_main: Union["ProcessGraphNode", None] = link_out_to_main


class AggregateProcess(AbstractProcess):
    def __init__(self, process_graph_nodes: list[ProcessGraphNode]):
        super().__init__()
        self.process_graph_nodes: list[ProcessGraphNode] = process_graph_nodes

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        last_process = self.process_graph_nodes[-1].process
        return last_process.main_flow_code_out

    def initialize_parameters(self, **kwargs):
        for n in self.process_graph_nodes:
            n.process.initialize_parameters(**kwargs)

    def calculate(self, main_flow_out: float):
        self.main_flow_out = main_flow_out
        # in first in reverse order, we use the given main_flow_out
        # for all following, we combine the required flows from all links.
        # if graph iscorrect,these must have been already calculated
        nodes_rev = list(reversed(self.process_graph_nodes))
        first_node, nodes = (
            nodes_rev[0],
            nodes_rev[1:],
        )
        logging.info(f"Calculate: {first_node.process}")
        first_node.process.calculate(main_flow_out=main_flow_out)
        for node in nodes:
            logging.info(f"Calculate: {node.process}")

            main_flow_out = 0
            if node.link_out_to_main:
                logging.info(
                    f"{node.process}: Serve main {self.main_flow_code_out} from {node.link_out_to_main.process}"
                )
                main_flow_out += node.link_out_to_main.process.get_main_flow_in()

            for n in node.links_out_to_secondary:
                logging.info(
                    f"{node.process}: Serve secondary {self.main_flow_code_out} from {n.process}"
                )
                main_flow_out += n.process.get_secondary_flow_in(
                    flow_code=self.main_flow_code_out
                )

            node.process.calculate(main_flow_out=main_flow_out)

    @staticmethod
    def create_from_chain(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
    ) -> "AggregateProcess":
        # split and check into export, transport, import

        # in reverse order:
        check_use_all_main_process_codes = []
        current_node = None
        process_graph_nodes_rev: list[ProcessGraphNode] = []
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
            process_graph_nodes_rev.append(current_node)

        return AggregateProcess(
            process_graph_nodes=list(reversed(process_graph_nodes_rev))
        )

    @staticmethod
    def create_from_chain_part(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
    ) -> "AggregateProcess":
        process_graph_nodes: list[ProcessGraphNode] = []

        flow_providers: dict[FlowCodeType, ProcessGraphNode] = {}
        secondary_process_codes_by_flow_code: dict[FlowCodeType, ProcessCodeType] = (
            group_by_flow_type_out(secondary_process_codes)
        )

        def create_provider_node(flow_code: FlowCodeType) -> ProcessGraphNode:
            if flow_code in secondary_process_codes_by_flow_code:
                process_code = secondary_process_codes_by_flow_code[flow_code]
                process_class = ProcessTypes[process_code].process_class
                process = process_class(process_code=process_code)
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
            process_graph_nodes.append(node)

        # initialize nodes for main chain
        main_process_nodes: list[ProcessGraphNode] = []
        for process_code in main_process_codes:
            process_class = ProcessTypes[process_code].process_class
            process = process_class(process_code=process_code)
            main_process_nodes.append(ProcessGraphNode(process=process))
        # Link main chain: link: to next
        for i in range(len(main_process_nodes) - 1):
            main_process_nodes[i].link_out_to_main = main_process_nodes[i + 1]

        for i, node in enumerate(main_process_nodes):
            if i == 0:
                # NOTE: the initial main process will also be provider (EL/NG-G)
                flow_providers[node.process.main_flow_code_out] = node

            add(node)

        return AggregateProcess(process_graph_nodes=process_graph_nodes)

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        procs = [x.process for x in self.process_graph_nodes]
        return "[" + ", ".join(str(x) for x in procs) + f"]{s_val}"


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
    logging.info(chain_process)

    chain_process.initialize_parameters()
    chain_process.calculate(1)

    logging.info(chain_process)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--loglevel",
        "-l",
        choices=["debug", "info", "warning", "error"],
        default="info",
    )
    # parse args
    kwargs = vars(ap.parse_args())
    # logging
    coloredlogs.install(
        level=getattr(logging, kwargs.pop("loglevel").upper()),
        fmt="[%(asctime)s %(levelname)7s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        field_styles={
            "asctime": {"color": "white"},
            "levelname": {"color": "white"},
        },
        level_styles={
            "debug": {"color": "blue"},
            "info": {"color": "green"},
            "warning": {"color": "yellow"},
            "error": {"color": "red"},
        },
    )

    main(**kwargs)
