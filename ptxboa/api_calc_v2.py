import argparse
import logging
from typing import Iterable, Union, cast

import coloredlogs
import matplotlib.pyplot as plt
import networkx as nx

from ptxboa.api_data import DataHandler
from ptxboa.static import FlowCodeType, ProcessCodeType

ProcessStepValuesSorted = [
    "EL_STR",
    "ELY",
    "H2_STR",
    "DERIV",
    "DERIV2",
    "PRE_SHP",
    "SHP",
    "SHP_OWN",
    "POST_SHP",
    "PRE_PPL",
    "PPLS",
    "PPL",
    "PPLX",
    "PPLR",
    "POST_PPL",
    "ELY_I",
    "DERIV_I",
    "DERIV_I2",
]

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
        # return self._is_transport and not self.is_transformation
        return self._is_transport

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
        # secondary: only allow CCS
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
    def main_flow_code_in(self) -> FlowCodeType | None:
        return None

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        return set()

    @property
    def is_initial(self) -> bool:
        return False

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
    def main_flow_code_in(self) -> FlowCodeType | None:
        return self._process_type.main_flow_code_in

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        return self._process_type.secondary_flow_types

    @property
    def is_initial(self) -> bool:
        return self._process_type.is_initial

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

    def initialize_parameters(self, **kwargs):
        super().initialize_parameters()
        # TODO

    def calculate(self, main_flow_out: float):
        super().calculate(main_flow_out=main_flow_out)
        # TODO

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
        is_main_start: bool = False,
        is_main_end: bool = False,
    ):
        self.process: AbstractProcess = process
        self.links_out_to_secondary: list["ProcessGraphNode"] = []
        self.link_out_to_main: Union["ProcessGraphNode", None] = link_out_to_main
        self.is_main_start: bool = is_main_start
        self.is_main_end: bool = is_main_end


def get_chain_parts(
    main_process_codes: list[ProcessCodeType],
) -> list[tuple[str, int, int]]:
    # split and check into export, transport, import
    is_transport = [ProcessTypes[p].is_transport for p in main_process_codes]
    # first and last index
    idx_transport_start = is_transport.index(True)
    idx_transport_end = is_transport.index(False, idx_transport_start)
    if not (0 < idx_transport_start < idx_transport_end):
        raise Exception("Transport")
    return [
        ("export", 0, idx_transport_start),
        ("transport", idx_transport_start, idx_transport_end),
        ("import", idx_transport_end, len(main_process_codes)),
    ]


class AggregateProcess(AbstractProcess):
    def __init__(
        self, process_graph_nodes: list[ProcessGraphNode], name: str | None = None
    ):
        super().__init__()
        self.process_graph_nodes: list[ProcessGraphNode] = process_graph_nodes
        self.name: str | None = name
        self._first_main_node = next(
            n for n in self.process_graph_nodes if n.is_main_start
        )
        self._last_main_node = next(
            n for n in self.process_graph_nodes if n.is_main_end
        )

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        return self._last_main_node.process.main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        return self._first_main_node.process.main_flow_code_in

    def initialize_parameters(self, **kwargs):
        super().initialize_parameters()
        for n in self.process_graph_nodes:
            n.process.initialize_parameters(**kwargs)

    def calculate(self, main_flow_out: float):
        super().calculate(main_flow_out=main_flow_out)

        # in first in reverse order, we use the given main_flow_out
        # for all following, we combine the required flows from all links.
        # if graph iscorrect,these must have been already calculated
        nodes_rev = list(reversed(self.process_graph_nodes))
        for node in nodes_rev:
            if node.is_main_end:
                main_flow_out_current = main_flow_out
            else:
                flow_code = node.process.main_flow_code_out

                main_flow_out_current = 0
                if node.link_out_to_main:
                    logging.info(
                        f"{node.process}: Serve main {flow_code} to {node.link_out_to_main.process}"
                    )
                    main_flow_out_current += (
                        node.link_out_to_main.process.get_main_flow_in()
                    )

                for n in node.links_out_to_secondary:
                    logging.info(
                        f"{node.process}: Serve secondary {flow_code} to {n.process}"
                    )
                    main_flow_out_current += n.process.get_secondary_flow_in(
                        flow_code=flow_code
                    )

                # check
                if not main_flow_out_current:
                    raise ValueError(f"{node.process}: main_flow_out is 0")
            logging.info(f"Calculate: {node.process} for {main_flow_out_current}")
            node.process.calculate(main_flow_out=main_flow_out_current)

            if node.is_main_start:
                self._main_flow_in = node.process.get_main_flow_in()

    @staticmethod
    def create_from_chain(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
    ) -> "AggregateProcess":

        # in reverse order:
        check_use_all_main_process_codes = []
        current_node = None
        process_graph_nodes_rev: list[ProcessGraphNode] = []

        # FIXME: pre/post shipping processes, remove not required

        for name, i, j in reversed(
            get_chain_parts(main_process_codes=main_process_codes)
        ):
            attr = f"allow_in_{name}"
            pcodes: list[ProcessCodeType] = main_process_codes[i:j]
            # check
            if not all(getattr(ProcessTypes[p], attr) for p in pcodes):
                raise Exception(f"Invalid {name} {pcodes}")
            spcodes: set[ProcessCodeType] = {
                p for p in secondary_process_codes if getattr(ProcessTypes[p], attr)
            }
            process = AggregateProcess.create_from_chain_part(
                main_process_codes=pcodes,
                secondary_process_codes=spcodes,
            )
            process.name = name.upper()
            current_node = ProcessGraphNode(
                process=process, link_out_to_main=current_node
            )
            check_use_all_main_process_codes = pcodes + check_use_all_main_process_codes
            process_graph_nodes_rev.append(current_node)

        # check
        if not tuple(check_use_all_main_process_codes) == tuple(main_process_codes):
            raise Exception(
                f"{check_use_all_main_process_codes} != {main_process_codes}"
            )

        process_graph_nodes = list(reversed(process_graph_nodes_rev))
        process_graph_nodes[0].is_main_start = True
        process_graph_nodes[-1].is_main_end = True

        return AggregateProcess(process_graph_nodes=process_graph_nodes)

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
        for i, process_code in enumerate(main_process_codes):
            process_class = ProcessTypes[process_code].process_class
            process = process_class(process_code=process_code)
            main_process_nodes.append(
                ProcessGraphNode(
                    process=process,
                    is_main_start=(i == 0),
                    is_main_end=(i == (len(main_process_codes) - 1)),
                )
            )
        # Link main chain: link: to next
        for i in range(len(main_process_nodes) - 1):
            n1, n2 = main_process_nodes[i : i + 2]
            if n1.process.main_flow_code_out != n2.process.main_flow_code_in:
                logging.error(f"{n1.process} ==> {n2.process}")
            n1.link_out_to_main = n2

        for i, node in enumerate(main_process_nodes):
            if node.process.is_initial:
                if i != 0:
                    raise Exception(
                        f"is_initial process not at beginning: {node.process}"
                    )
                # NOTE: the initial main process will also be provider (EL/NG-G)
                flow_providers[node.process.main_flow_code_out] = node

            add(node)

        return AggregateProcess(process_graph_nodes=process_graph_nodes)

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        if self.name:
            name = self.name
        else:
            procs = [x.process for x in self.process_graph_nodes]
            name = ", ".join(str(x) for x in procs)
        return "[" + name + f"]{s_val}"


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
        cast(ProcessCodeType, chain_data[x])
        for x in ProcessStepValuesSorted
        if chain_data[x]
    ]
    main_process_codes.insert(0, first_process_code)

    chain_process = AggregateProcess.create_from_chain(
        main_process_codes=main_process_codes,
        secondary_process_codes=secondary_process_codes,
    )
    logging.info(chain_process)

    ge, gt, gi = chain_process.process_graph_nodes
    # plot(gt.process)

    chain_process.initialize_parameters()
    chain_process.calculate(1)

    # logging.info(chain_process)


def plot(process: AggregateProcess):

    # Create a directed graph
    G = nx.DiGraph()
    node_labels = {}
    edge_labels = {}
    edge_widths = []

    for node in process.process_graph_nodes:
        G.add_node(node)
        node_labels[node] = str(node.process)

    for node in process.process_graph_nodes:
        if node.link_out_to_main:
            e = (node, node.link_out_to_main)
            G.add_edge(*e)
            edge_labels[e] = node.process.main_flow_code_out
            edge_widths.append(2)
        for n in node.links_out_to_secondary:
            e = (node, n)
            G.add_edge(*e)
            edge_labels[e] = node.process.main_flow_code_out
            edge_widths.append(1)

    # Position nodes using a layout
    pos = nx.spring_layout(G)

    # Draw nodes
    nx.draw(
        G,
        pos,
        with_labels=False,
        node_color="lightblue",
        width=edge_widths,
    )

    # Draw node labels
    nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, font_color="black")

    # Draw edge labels
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=edge_labels, font_size=6, font_color="red"
    )

    # Save to PNG
    plt.savefig("graph.png", dpi=300)
    plt.show()


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
