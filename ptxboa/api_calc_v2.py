"""Class based calculation."""

import argparse
import logging
from dataclasses import dataclass
from typing import Iterable, cast

import coloredlogs
import matplotlib.pyplot as plt
import networkx as nx

from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from ptxboa.static import (
    FlowCodeType,
    ProcessCodeType,
    ProcessStepType,
    ProcessStepValues,
    ScenarioType,
    SourceRegionCodeType,
    TargetCountryCodeType,
    TransportType,
)

ProcessStepValuesSorted = ProcessStepValues
assert tuple(ProcessStepValuesSorted) == (
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
)

df_process = DataHandler.get_dimension("process")
df_chain = DataHandler.get_dimension("chain")
df_parameter = DataHandler.get_dimension("parameter")


class ProcessType:
    def __init__(
        self,
        process_code: ProcessCodeType,
        is_transport: bool,
        is_secondary: bool,
        is_re_generation: bool,
        is_transformation: bool,
        is_storage: bool,
        is_pipeline: bool,
        is_pipeline_retrofitted: bool,
        is_pipeline_sea: bool,
        is_shipping: bool,
        is_shipping_own_fuel: bool,
        main_flow_code_out: FlowCodeType,
        main_flow_code_in: FlowCodeType | None,
        secondary_flows: Iterable[FlowCodeType] | None,
        **_kwargs,
    ):
        self.process_code: ProcessCodeType = process_code
        self.is_transport: bool = is_transport  # includes pre/post transformation
        self.is_secondary: bool = is_secondary
        self.is_transformation: bool = is_transformation
        self.is_storage: bool = is_storage
        self.is_re_generation: bool = is_re_generation
        self.is_pipeline: bool = is_pipeline
        self.is_pipeline_retrofitted: bool = is_pipeline_retrofitted
        self.is_pipeline_sea: bool = is_pipeline_sea
        self.is_shipping: bool = is_shipping
        self.is_shipping_own_fuel: bool = is_shipping_own_fuel
        self.main_flow_code_out: FlowCodeType = main_flow_code_out
        self.main_flow_code_in: FlowCodeType | None = main_flow_code_in
        self.secondary_flow_types: set[FlowCodeType] = (
            set(secondary_flows) if secondary_flows else set()
        )

        # checks
        if self.main_flow_code_in in self.secondary_flow_types:
            logging.error(
                f"{self.process_code}: main_flow_code_in {self.main_flow_code_in} "
                "in secondary_flow_types"
            )
        if self.main_flow_code_out in self.secondary_flow_types:
            logging.error(
                f"{self.process_code}: main_flow_code_out {self.main_flow_code_out} "
                "in secondary_flow_types"
            )
        if self.is_secondary and self.main_flow_code_in:
            logging.warning(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )
        if self.is_initial and self.main_flow_code_in:
            logging.error(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return self.is_re_generation or self.process_code == "NG-PROD#B"

    @property
    def process_class(self) -> type["Process"]:
        """Process class.

        So we can dynamically use subclasses.
        """
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
        """Is process allowed in export."""
        return not self.allow_in_transport or self.is_secondary

    @property
    def allow_in_transport(self) -> bool:
        """Is process allowed in transport."""
        return (
            self.is_transport  # includes pre/post transformation
            and not self.is_secondary
            and not self.is_storage
        )

    @property
    def allow_in_import(self) -> bool:
        """Is process allowed in import."""
        # secondary: only allow CCS
        return self.allow_in_export and (
            # CSS is onlyallowed secondary(?) # TODO:generalize?
            not self.is_secondary
            or self.process_code == "CO2-T+S#B"
        )


ProcessTypes: dict[ProcessCodeType, ProcessType] = {
    p["process_code"]: ProcessType(**cast(dict, p))
    for p in df_process.to_dict(orient="records")
}


class AbstractProcess:
    def __init__(
        self,
        process_step: ProcessStepType | str | None = None,
    ):
        self._main_flow_out: float | None = None  # will be set in calculate()
        self._main_flow_in: float | None = None  # will be set in calculate()
        self._secondary_flows_in: dict[FlowCodeType, float] | None = None
        self.process_step: ProcessStepType | str | None = process_step

    def get_main_flow_out(self) -> float:
        """Value of main out flow."""
        if not self._main_flow_out:  # 0 or None
            raise Exception("Not calculated yet")
        return self._main_flow_out

    def get_main_flow_in(self) -> float:
        """Value of calculated main in flow."""
        if not self._main_flow_in:  # 0 or None
            raise Exception("Not calculated yet, or main_flow_in does not exist")
        return self._main_flow_in

    def get_secondary_flow_in(self, flow_code: FlowCodeType) -> float:
        """Value of calculated secondary in flow for given flow type."""
        if self._secondary_flows_in is None:
            raise Exception(f"Not calculated yet: {self}")
        return self._secondary_flows_in[flow_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return None

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        raise NotImplementedError

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return None

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return set()

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return False

    @property
    def is_transport(self) -> bool:
        """Is this a transport process."""
        return False

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return False

    def initialize_parameters(self, data_handler: DataHandler):
        """Initialize parameetr data for this process."""
        pass

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        self._main_flow_out = main_flow_out

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        step = f"{self.process_step}=" if self.process_step else ""
        return f"{self.__class__.__name__}({step}{self.process_code}{s_val})"


class Process(AbstractProcess):
    def __init__(
        self, process_code: ProcessCodeType, process_step: ProcessStepType | None = None
    ):
        super().__init__(process_step=process_step)
        self._process_type: ProcessType = ProcessTypes[process_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return self._process_type.process_code

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._process_type.main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self._process_type.main_flow_code_in

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return self._process_type.secondary_flow_types

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return self._process_type.is_initial

    @property
    def is_transport(self) -> bool:
        """Is this a transport process."""
        return self._process_type.is_transport

    def initialize_parameters(self, data_handler: DataHandler):
        """Initialize parameetr data for this process."""
        super().initialize_parameters(data_handler=data_handler, **kwargs)

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
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
    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return True


class InitialProcess(SecondaryProcess):
    pass


class MarketProcess(AbstractProcess):
    def __init__(self, main_flow_code_out: FlowCodeType):
        super().__init__()
        self._main_flow_code_out: FlowCodeType = main_flow_code_out

    def initialize_parameters(self, data_handler: DataHandler, **kwargs):
        """Initialize parameetr data for this process."""
        super().initialize_parameters(data_handler=data_handler, **kwargs)
        # TODO

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)
        # TODO

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._main_flow_code_out

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return self.main_flow_code_out  # type:ignore


def get_chain_parts(
    main_process_codes: list[ProcessCodeType],
) -> list[tuple[str, int, int]]:
    # split and check into export, transport, import
    is_transport = [ProcessTypes[p].allow_in_transport for p in main_process_codes]
    # first and last index
    idx_transport_start = is_transport.index(True)
    try:
        idx_transport_end = is_transport.index(False, idx_transport_start)
    except ValueError:  # no import steps
        idx_transport_end = len(is_transport)

    if not (0 < idx_transport_start < idx_transport_end):
        raise Exception("Transport")
    return [
        ("export", 0, idx_transport_start),
        ("transport", idx_transport_start, idx_transport_end),
        ("import", idx_transport_end, len(main_process_codes)),
    ]


class AggregateProcess(AbstractProcess):
    def __init__(self, process_graph: "ProcessGraph", process_step: str | None = None):
        super().__init__(process_step=process_step)
        self.process_graph: "ProcessGraph" = process_graph

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self.process_graph.main_processes[-1].main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self.process_graph.main_processes[0].main_flow_code_in

    @property
    def full_main_chain(self) -> list[AbstractProcess]:
        """List of the entire main chain (including nested aggregated processes)."""
        result: list[AbstractProcess] = []
        for proc in self.process_graph.main_processes:
            if isinstance(proc, AggregateProcess):
                result += proc.full_main_chain
            else:
                result.append(proc)

        return result

    def initialize_parameters(self, data_handler: DataHandler, **kwargs):
        """Initialize parameetr data for this process."""
        super().initialize_parameters(data_handler=data_handler, **kwargs)
        for process in self.process_graph.calculate_order:
            process.initialize_parameters(data_handler=data_handler, **kwargs)

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)

        # in first in reverse order, we use the given main_flow_out
        # for all following, we combine the required flows from all links.
        # if graph iscorrect,these must have been already calculated
        for process in self.process_graph.calculate_order:
            if process == self.process_graph.main_processes[-1]:
                # is last in main chain
                main_flow_out_current = main_flow_out
            else:
                main_flow_out_current = 0  # calculate
                flow_code = process.main_flow_code_out

                for proc_target, in_main in self.process_graph.links_out.get(
                    process, []
                ):
                    logging.info(f"{process}: Serve {flow_code} to {proc_target}")
                    main_flow_out_current += (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow_code=flow_code)
                    )

                # check
                if not main_flow_out_current:
                    if main_flow_out_current is None:
                        raise ValueError(f"{process}: main_flow_out is None")
                    else:
                        logging.warning(f"{process}: main_flow_out is 0")
            logging.info(f"Calculate: {process} for {main_flow_out_current}")
            process.calculate(main_flow_out=main_flow_out_current)

            if process == self.process_graph.main_processes[0]:
                self._main_flow_in = process.get_main_flow_in()

    @staticmethod
    def create_from_chain(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
        process_step: str | None = None,
        main_process_steps: list[ProcessStepType | None] | None = None,
    ) -> "AggregateProcess":
        """Create aggregated process for entire chain."""
        check_use_all_main_process_codes = []

        # FIXME: pre/post shipping processes, remove not required

        main_processes: list[AbstractProcess] = []

        for part_name, i, j in get_chain_parts(main_process_codes=main_process_codes):
            attr = f"allow_in_{part_name}"
            pcodes: list[ProcessCodeType] = main_process_codes[i:j]
            if not pcodes:
                # no steps ==> skip this
                continue
            # check
            invalid_processes = [
                p for p in pcodes if not getattr(ProcessTypes[p], attr)
            ]
            if invalid_processes:
                raise Exception(f"Invalid {part_name} {pcodes}: {invalid_processes}")
            spcodes: set[ProcessCodeType] = {
                p for p in secondary_process_codes if getattr(ProcessTypes[p], attr)
            }

            scodes = main_process_steps[i:j] if main_process_steps else None
            process = AggregateProcess.create_from_chain_part(
                main_process_codes=pcodes,
                secondary_process_codes=spcodes,
                process_step=part_name.upper(),  # e.g. "IMPORT","EXPORT", "TRANSPORT"
                main_process_steps=scodes,
            )
            main_processes.append(process)

            check_use_all_main_process_codes = check_use_all_main_process_codes + pcodes

        # check
        if not tuple(check_use_all_main_process_codes) == tuple(main_process_codes):
            raise Exception(
                f"{check_use_all_main_process_codes} != {main_process_codes}"
            )

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes, secondary_processes=[]
        )

        return AggregateProcess(process_graph=process_graph, process_step=process_step)

    @staticmethod
    def create_from_chain_part(
        main_process_codes: list[ProcessCodeType],
        secondary_process_codes: set[ProcessCodeType],
        process_step: str | None = None,
        main_process_steps: list[ProcessStepType | None] | None = None,
    ) -> "AggregateProcess":
        """Create an aggregated process with subprocesses.

        Usually for export / transport / import

        THe main problem ishow to connect secondary processes
        without creating loops, while at the same time following some
        specific rules / requirements.
        """
        if not main_process_steps:
            main_process_steps = [None for _ in range(len(main_process_codes))]
        else:
            if len(main_process_steps) != len(main_process_codes):
                raise Exception("list length mismatch for main_process_steps")

        main_processes: list[AbstractProcess] = [
            ProcessTypes[pt].process_class(process_code=pt, process_step=ps)
            for pt, ps in zip(main_process_codes, main_process_steps)
        ]
        secondary_processes: list[Process] = [
            ProcessTypes[pt].process_class(process_code=pt)
            for pt in secondary_process_codes
        ]

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes, secondary_processes=secondary_processes
        )
        result = AggregateProcess(
            process_graph=process_graph, process_step=process_step
        )
        return result


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


@dataclass
class Settings:
    scenario: ScenarioType
    region: SourceRegionCodeType
    country: TargetCountryCodeType
    transport: TransportType
    ship_own_fuel: bool
    first_process_code: ProcessCodeType
    chain_code: str
    secondary_process_codes: set[ProcessCodeType]


def create_permutations(scenario: ScenarioType) -> Iterable[Settings]:

    # secproc_co2: SecProcCO2Type | None # noqa
    # secproc_water: SecProcH2OType | None # noqa
    # chain: ChainNameType # noqa
    # res_gen: ResGenType | None # noqa
    region: SourceRegionCodeType = "DZA"
    country: TargetCountryCodeType = "DEU"
    # transport: TransportType # noqa
    # ship_own_fuel: bool # noqa
    transports: list[tuple[TransportType, bool]] = [
        ("Pipeline", False),
        ("Ship", False),
        ("Ship", True),
    ]
    for chain_spec in df_chain.to_dict(orient="records"):
        chain_code = chain_spec["chain"]
        first_process_code: ProcessCodeType
        secondary_process_codes: set[ProcessCodeType]
        if chain_spec["is_blue"]:
            first_process_code = "NG-PROD#B"
            secondary_process_codes = {"HEATPUMP#B", "CCGT-CC#B", "CO2-T+S#B", "DAC#B"}
        elif chain_spec["is_green"]:
            first_process_code = "RES-HYBR"
            secondary_process_codes = {"DAC", "DESAL"}
        else:
            continue
        for transport, ship_own_fuel in transports:
            if transport == "Pipeline" and not chain_spec["can_pipeline"]:
                continue
            if transport == "Ship" and ship_own_fuel and not chain_spec["SHP_OWN"]:
                continue
            yield Settings(
                scenario=scenario,
                country=country,
                region=region,
                first_process_code=first_process_code,
                secondary_process_codes=secondary_process_codes,
                chain_code=chain_code,
                ship_own_fuel=ship_own_fuel,
                transport=transport,
            )


class ProcessGraph:
    _KEY_MAIN = "(MAIN)"  # nust not be a flow code

    def __init__(
        self,
        main_processes: list[AbstractProcess],
        secondary_processes: list[Process],
    ):
        self.main_processes: list[AbstractProcess] = main_processes

        # calculate_order: includes main, secondary, tertiary(market) processes
        self.calculate_order: Iterable[AbstractProcess] = []
        self.links_out: dict[AbstractProcess, list[tuple[AbstractProcess, bool]]] = {}

        G = nx.DiGraph()
        G.add_nodes_from(main_processes)
        G.add_nodes_from(secondary_processes)

        def add_link_out(
            proc_provider: AbstractProcess,
            proc_recipient: AbstractProcess,
            in_main: bool,
        ):
            if proc_provider not in self.links_out:
                self.links_out[proc_provider] = []
            self.links_out[proc_provider].append((proc_recipient, in_main))
            G.add_edge(proc_provider, proc_recipient)
            logging.info(
                f"Create link {proc_provider}({proc_provider.main_flow_code_out}) "
                f"{'==>' if in_main else '-->'} {proc_recipient}"
            )

        market_processes: dict[FlowCodeType, MarketProcess] = {}

        def get_or_create_market_process(flow_type: FlowCodeType) -> MarketProcess:
            if flow_type not in market_processes:
                market_processes[flow_type] = MarketProcess(
                    main_flow_code_out=flow_type
                )
                G.add_node(market_processes[flow_type])
            return market_processes[flow_type]

        # collect all provider of secondary flows (can also come from initial (EL/NG))
        flow_provider_sec_or_initial: dict[FlowCodeType, AbstractProcess] = {}
        first_proc = self.main_processes[0]
        flow_from_initial_proc: FlowCodeType | None = None
        if first_proc.is_initial:
            flow_provider_sec_or_initial[first_proc.main_flow_code_out] = first_proc
            flow_from_initial_proc = first_proc.main_flow_code_out
        for sec_proc in secondary_processes:
            if sec_proc.main_flow_code_out in flow_provider_sec_or_initial:
                logging.warning(f"flow already proveided, skipping {sec_proc}")
                continue
            flow_provider_sec_or_initial[sec_proc.main_flow_code_out] = sec_proc

        # collect required flows
        required_flows_procs: dict[FlowCodeType, list[tuple[AbstractProcess, bool]]] = (
            {}
        )

        def add_required_flows_proc(
            proc: AbstractProcess, flow: FlowCodeType, in_main: bool
        ):
            if flow not in required_flows_procs:
                required_flows_procs[flow] = []
            required_flows_procs[flow].append((proc, in_main))

        for p in main_processes:
            for f in p.secondary_flow_types:
                add_required_flows_proc(p, f, in_main=False)
        for p in secondary_processes:
            for f in p.secondary_flow_types:
                add_required_flows_proc(p, f, in_main=False)
            if p.main_flow_code_in:
                # TODO: technically, secondary flows should not have main_flow_code_in
                # but some have them anyways?
                add_required_flows_proc(p, p.main_flow_code_in, in_main=True)

        # match required and provided flows in specific order without creating loops
        # specific order is important so we get a deterministic graph
        def sort_flows_b_priority(
            flow_codes: Iterable[FlowCodeType],
        ) -> Iterable[FlowCodeType]:
            flow_codes_todo = set(flow_codes)
            # FIXME: better way to set priority

            for f in [flow_from_initial_proc, "CO2-C", "EL", "HEAT"]:
                if f in flow_codes_todo:
                    yield f
                    flow_codes_todo.remove(f)

            yield from sorted(flow_codes_todo)

        # link main chain
        for i in range(len(main_processes) - 1):
            add_link_out(main_processes[i], main_processes[i + 1], in_main=True)

        for flow in sort_flows_b_priority(required_flows_procs):
            for proc_target, in_main in required_flows_procs[flow]:
                # try to get from secondary
                prov_sec = flow_provider_sec_or_initial.get(flow)
                if prov_sec:
                    # try to add without loop
                    if nx.has_path(G, proc_target, prov_sec):
                        logging.warning(
                            f"Could not add link {prov_sec} ={flow}=> {proc_target} "
                            "because it would create a loop. fall back on market"
                        )
                        prov_sec = None  # use market
                if not prov_sec:
                    prov_sec = get_or_create_market_process(flow)
                add_link_out(prov_sec, proc_target, in_main=in_main)

        # optional: subgraph to drop unused secondary

        procs_old = set(G.nodes)
        last_proc = self.main_processes[-1]
        G = cast(nx.DiGraph, G.subgraph(nx.ancestors(G, last_proc) | {last_proc}))
        procs_new = set(G.nodes)

        procs_dropped = procs_old - procs_new
        if procs_dropped:
            logging.warning("Dropping unused: %s", [str(x) for x in procs_dropped])
            # drop from links_out
            # TODO: maybe use Digraph? - this is very ugly
            for k, vs in self.links_out.items():
                self.links_out[k] = [(p, m) for p, m in vs if p not in procs_dropped]

        # calculate_order: includes main, secondary, tertiary(market) processes
        self.calculate_order = list(reversed(list(nx.topological_sort(G))))

        # check (TODO:can be removed later)
        missing_main = set(self.main_processes) - set(self.calculate_order)
        if missing_main:
            raise Exception(f"missing_main: {missing_main}")


def create_permutation_names(permutations: Iterable[Settings]) -> dict[str, Settings]:
    def create_name(settings: Settings) -> str:
        name = (
            f"{settings.chain_code}_{settings.transport}"
            f"{'_OWN' if settings.ship_own_fuel else ''}"
        )
        name = name.replace(" ", "_")
        return name

    result: dict[str, Settings] = {}
    for settings in permutations:
        name = create_name(settings)
        if name in result:
            raise KeyError(name)
        result[name] = settings
    return result


def filter_transport_process_codes(
    main_process_codes: list[ProcessCodeType],
    transport: TransportType,
    ship_own_fuel: bool,
) -> list[ProcessCodeType]:
    """Filter transportation mode."""
    if transport == "Pipeline":

        def filter_proc(p: ProcessType):
            return p.is_pipeline or not p.is_transport

    elif transport == "Ship":
        if ship_own_fuel:

            def filter_proc(p: ProcessType):
                return p.is_shipping_own_fuel or not p.is_transport

        else:

            def filter_proc(p: ProcessType):
                return (
                    p.is_shipping and not p.is_shipping_own_fuel
                ) or not p.is_transport

    else:
        raise NotImplementedError(transport)

    return [p for p in main_process_codes if filter_proc(ProcessTypes[p])]


def create_chain_process(settings: Settings) -> AggregateProcess:

    chain_data = DataHandler.get_dimension("chain").loc[settings.chain_code].to_dict()

    main_process_codes: list[ProcessCodeType] = [
        cast(ProcessCodeType, chain_data[x])
        for x in ProcessStepValuesSorted
        if chain_data[x]
    ]
    main_process_steps: list[ProcessStepType | None] = [
        cast(ProcessStepType, x) for x in ProcessStepValuesSorted if chain_data[x]
    ]

    main_process_codes = filter_transport_process_codes(
        main_process_codes,
        transport=settings.transport,
        ship_own_fuel=settings.ship_own_fuel,
    )

    main_process_codes.insert(0, settings.first_process_code)

    # for FLH lookup we need these process codes
    param_flh_kwargs: dict[str, ProcessCodeType | None] = {
        "process_code_res": chain_data["RES"],
        "process_code_ely": chain_data["ELY"],
        "process_code_deriv": chain_data["DERIV"],
    }

    chain_process = AggregateProcess.create_from_chain(
        main_process_codes=main_process_codes,
        secondary_process_codes=settings.secondary_process_codes,
        process_step="CHAIN",
        main_process_steps=main_process_steps,
    )

    # check (TODO: can be removed later)
    main_process_codes_ = tuple(p.process_code for p in chain_process.full_main_chain)
    if tuple(main_process_codes) != main_process_codes_:
        raise Exception(main_process_codes_)

    return chain_process


def plot_get_pos(
    chain_process: AggregateProcess,
) -> dict[AbstractProcess, tuple[float, float]]:

    node_pos = {}
    xs: list[float] = [0, 0, 0]
    proc_end_last = None

    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        xs[1] = max(xs[0] + 0.25, xs[0])  # stagger
        xs1_start = xs[1]
        xs[2] = max(xs[0], xs[2])

        for process in reversed(list(process_graph.calculate_order)):
            key = process

            # if is_main:
            if process in process_graph.main_processes:
                xs[0] = xs[0] + 1
                x = xs[0]
                y = 0
                if not proc_end_last and process == process_graph.main_processes[0]:
                    y = 0.05  # initial a little closer to secondary
            elif not isinstance(process, MarketProcess):
                #  is secondary
                xs[1] = xs[1] + 1
                x = xs[1]
                # non linear disntance for non overlapping arrows

                ampl = (x - xs1_start) * 0.01
                sgn = (x - xs1_start) % 2 - 1
                y = 0.1 + ampl * sgn
            else:
                # market
                xs[2] = xs[2] + 1
                x = xs[2]
                y = 0.2

            node_pos[key] = (x, y)

        proc_end_last = process_graph.main_processes[-1]

    return node_pos


def plot(chain_process: AggregateProcess, name: str):

    # Create a directed graph
    G = nx.DiGraph()
    node_labels = {}
    node_colors = {}
    edge_labels = {}
    edge_widths = {}

    proc_end_last = None
    len_main_total = 0
    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        for process in reversed(list(process_graph.calculate_order)):
            key = process
            G.add_node(key)
            node_labels[key] = (
                str(key)
                .replace("=", "\n")
                .replace("(", "\n")
                .replace(")", "\n")
                .replace(" ", "\n")
                .strip()
            )

            # if is_main:
            if process in process_graph.main_processes:
                node_colors[process] = "lightblue"
            elif not isinstance(process, MarketProcess):
                node_colors[process] = "lightgreen"
            else:
                node_colors[process] = "lightgray"

            for proc_target, in_main in process_graph.links_out.get(process, []):
                flow = process.main_flow_code_out
                e = (process, proc_target)
                G.add_edge(*e)
                try:
                    value = (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow)
                    )
                    value_str = f"\n{value:.4f}"
                except Exception:
                    value_str = ""
                edge_labels[e] = f"{flow}{value_str}"
                edge_widths[e] = 2 if in_main else 1

        if proc_end_last:
            # link from previous subpgraph
            proc_start = process_graph.main_processes[0]
            e = (proc_end_last, proc_start)
            G.add_edge(*e)
            edge_labels[e] = proc_end_last.main_flow_code_out
            try:
                edge_labels[e] += f"\n{proc_start.get_main_flow_in():.4f}"
            except Exception:  # not calculated yet, # noqa: S110
                pass
            edge_widths[e] = 2

        proc_end_last = process_graph.main_processes[-1]

        len_main_total += len(process_graph.main_processes)

    scale = 3

    # node_pos = nx.circular_layout(G) # noqa
    node_pos = plot_get_pos(chain_process=chain_process)

    plt.close()
    plt.clf()
    plt.figure(figsize=(len_main_total * scale, 2 * scale))

    # Draw nodes
    nx.draw(
        G,
        node_pos,
        with_labels=False,
        node_color=[node_colors[k] for k in G.nodes()],
        width=[edge_widths[k] for k in G.edges()],
        node_size=2000 * scale,
    )

    # Draw node labels
    nx.draw_networkx_labels(
        G, node_pos, labels=node_labels, font_size=8, font_color="black"
    )

    # Draw edge labels
    nx.draw_networkx_edge_labels(
        G,
        node_pos,
        edge_labels=edge_labels,
        font_size=6,
        font_color="black",
        label_pos=0.7,  # closer to beginning (1 ist start?)
    )

    # Save to PNG
    plt.savefig(f"chain_flowcharts/{name}.png", dpi=300)


def main():
    scenario: ScenarioType = "2040 (medium)"
    data_handler = DataHandler(scenario=scenario, data_dir=DEFAULT_DATA_DIR)
    permutations = create_permutation_names(create_permutations(scenario=scenario))

    for i, (name, settings) in enumerate(permutations.items()):
        if name != "Methane_(SOEC)_Pipeline":
            continue

        logging.info(f"{i + 1}/{len(permutations)}: {settings}")
        logging.info(name)
        chain_process = create_chain_process(settings=settings)
        logging.info(
            " => ".join(str(p.process_code) for p in chain_process.full_main_chain)
        )
        chain_process.initialize_parameters(data_handler=data_handler)
        chain_process.calculate(1)
        plot(chain_process, name=name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--loglevel",
        "-l",
        choices=["debug", "info", "warning", "error"],
        default="warning",
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
