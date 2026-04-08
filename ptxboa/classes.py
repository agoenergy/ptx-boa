from __future__ import annotations  # otherwise nx.DiGraph[Process] does not work

from dataclasses import asdict
from typing import Iterable, cast

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from networkx.exception import HasACycle

from ptxboa import logger
from ptxboa.api_data import DataHandler
from ptxboa.static import (
    FlowCodeType,
    ProcessCodeType,
    ProcessStepType,
    ProcessStepValues,  # must be sorted
    SourceRegionCodeType,
    TargetCountryCodeType,
)
from ptxboa.static._type_defs import (
    CalculateDataType,
    ChainDef,
    DataQueryDicType,
    ParameterGetters,
    ProcessDataType,
    ProcessResultCostsType,
    ProcessResultEmissionType,
    ProcessResultFlowsType,
    ProcessStep,
    PtxCalcResult,
    TransportType,
)


class Process:
    def __init__(
        self,
        process_code: ProcessCodeType | FlowCodeType,
        process_step: ProcessStepType | str | None,
        main_flow_code_out: FlowCodeType,
        main_flow_code_in: FlowCodeType | None,
        secondary_flow_types: frozenset[FlowCodeType],
        is_last: bool,
        is_in_import_region: bool,
        is_initial: bool,
        is_market: bool,
        is_secondary: bool,
        is_main: bool,
        is_transport: bool,
    ):

        if is_in_import_region:
            assert not is_initial
            assert not is_transport

        self.process_code: ProcessCodeType | FlowCodeType = process_code
        self.process_step: ProcessStepType | str | None = process_step
        self.main_flow_code_out: FlowCodeType = main_flow_code_out
        self.main_flow_code_in: FlowCodeType | None = main_flow_code_in
        self.secondary_flow_types: frozenset[FlowCodeType] = secondary_flow_types
        self.is_last: bool = is_last
        self.is_in_import_region: bool = is_in_import_region
        self.is_initial: bool = is_initial
        self.is_market: bool = is_market
        self.is_secondary: bool = is_secondary
        self.is_main: bool = is_main
        self.is_transport: bool = is_transport

        # links - will be added by Chain

        self._links_out_in_main: list[Process] = []
        self._links_out_in_secondary: list[Process] = []
        self._link_in_main: Process | None = None
        self._links_in_secondary: dict[FlowCodeType, Process] = {}

    @classmethod
    def create_with_subclass(
        cls,
        process_code: ProcessCodeType | FlowCodeType,
        process_step: ProcessStepType | str | None = None,
        is_last: bool = False,
        is_in_import_region: bool = False,
    ) -> "Process":

        is_market = process_code in DataHandler.dimensions["flow"].index  # is flow code
        ProcessClass: type[Process] = Process

        if is_market:
            main_flow_code_out = cast(FlowCodeType, process_code)
            main_flow_code_in = None
            secondary_flow_types = frozenset()
            is_initial = False
            is_secondary = False
            is_main = False
            is_transport = False
            ProcessClass = ProcessMarket
        else:
            proc_spec = DataHandler.dimensions["process"].loc[process_code]
            main_flow_code_out = proc_spec["main_flow_code_out"]
            main_flow_code_in = proc_spec["main_flow_code_in"]
            secondary_flow_types = frozenset(proc_spec["secondary_flows"])
            is_initial = bool(
                proc_spec["is_re_generation"] or process_code == "NG-PROD#B"
            )  # FIXME

            is_secondary = bool(proc_spec["is_secondary"])
            is_main = not is_secondary
            is_transport = bool(
                proc_spec["is_transport"]
                and not proc_spec["is_transformation"]  # no pre/post
                and not proc_spec["is_secondary"]  # CSS
                and not proc_spec["is_storage"]  # H2/EL Storage
            )
            if is_transport:
                ProcessClass = ProcessTransport
            elif is_secondary:
                ProcessClass = ProcessSecondary

        return ProcessClass(
            process_code=process_code,
            process_step=process_step,
            main_flow_code_out=main_flow_code_out,
            main_flow_code_in=main_flow_code_in,
            secondary_flow_types=secondary_flow_types,
            is_last=is_last,
            is_in_import_region=is_in_import_region,
            is_initial=is_initial,
            is_market=is_market,
            is_secondary=is_secondary,
            is_main=is_main,
            is_transport=is_transport,
        )

    def __str__(self):
        result = f"{self.process_code}"
        if self.process_step:
            result += f", step={self.process_step}"
        if self.is_initial:
            result += ", initial"
        if self.is_last:
            result += ", last"

        return result

    @property
    def color(self) -> str:
        """Color for plotting."""
        return "lightblue"

    def get_parameter_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType: ...

    def calculate_flows(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> ProcessResultFlowsType: ...

    def calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, list[ProcessResultCostsType]],
    ) -> list[ProcessResultCostsType]: ...

    def calculate_emissions(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_emissions: dict[Process, ProcessResultEmissionType],
    ) -> ProcessResultEmissionType: ...


class ProcessSecondary(Process):
    @property
    def color(self) -> str:
        """Color for plotting."""
        return "palegreen"


class ProcessTransport(Process):
    @property
    def color(self) -> str:
        """Color for plotting."""
        return "teal"


class ProcessMarket(Process):
    @property
    def color(self) -> str:
        """Color for plotting."""
        return "lightgray"


class Chain:
    _instances: dict[object, "Chain"] = {}

    def __init__(self, _graph: nx.DiGraph[Process]):
        self._graph: nx.DiGraph[Process] = _graph
        self._all_processes_ordered_forwards: tuple[Process, ...] = tuple(
            nx.topological_sort(self._graph)
        )

        self._processes_by_step: dict[ProcessStepType | str, Process] = {}
        for process in self._all_processes_ordered_forwards:
            process_step = process.process_step
            if not process_step:
                continue
            if process_step in self._processes_by_step:
                logger.error("Duplicate step: %s", process.process_step)
                continue
            self._processes_by_step[process.process_step] = process  # type: ignore

        # add links to processes for faster lookup + checks

        for process in self._graph.nodes():
            for _, other in self._graph.out_edges(process):
                attrs = self._graph.get_edge_data(process, other)
                if attrs["in_main"]:
                    assert process.main_flow_code_out == other.main_flow_code_in
                    process._links_out_in_main.append(other)
                else:
                    assert process.main_flow_code_out in other.secondary_flow_types
                    process._links_out_in_secondary.append(other)
            for other, _ in self._graph.in_edges(process):
                attrs = self._graph.get_edge_data(other, process)
                if attrs["in_main"]:
                    assert not process._link_in_main
                    process._link_in_main = other
                else:
                    assert other.main_flow_code_out not in process._links_in_secondary
                    process._links_in_secondary[other.main_flow_code_out] = other
            assert set(process._links_in_secondary) == set(process.secondary_flow_types)

    @classmethod
    def get_or_create(cls, chain_def: ChainDef) -> "Chain":
        key = chain_def.unique_key
        if key not in cls._instances:
            cls._instances[key] = cls._create(chain_def)
        return cls._instances[key]

    @classmethod
    def _create(cls, chain_def: ChainDef) -> "Chain":

        chain_color = DataHandler.get_chain_color(chain_def.chain_name)
        chain_data = (
            DataHandler.get_dimension("chain").loc[chain_def.chain_name].to_dict()
        )

        secondary_process_codes_export: list[ProcessCodeType] = list(
            chain_def.secondary_processes.values()
        )  # FIXME: not set/dict - we want fixed order
        secondary_process_codes_import: list[ProcessCodeType] = []
        first_process_code: ProcessCodeType
        if chain_color == "blue":
            initial_step = "NG_PROD"
            first_process_code = "NG-PROD#B"
            secondary_process_codes_import = [
                c for c in secondary_process_codes_export if c == "CO2-T+S#B"
            ]
        else:
            assert chain_def.process_res is not None
            initial_step = "RES"
            first_process_code = chain_def.process_res

        dropped_transport_steps = _get_dropped_transport_steps(
            transport=chain_def.transport,
            ship_own_fuel=chain_def.ship_own_fuel,
        )

        main_process_codes_steps: list["ProcessStep"] = [  # type: ignore
            (first_process_code, initial_step)
        ] + [
            (cast(ProcessCodeType, chain_data[process_step]), process_step)
            for process_step in ProcessStepValues
        ]
        # filter
        main_process_codes_steps = [
            (p, s)
            for p, s in main_process_codes_steps
            if p and s not in dropped_transport_steps
        ]

        is_in_import_region = False
        _was_transport = False
        main_processes = []
        for i, (process_code, process_step) in enumerate(main_process_codes_steps):
            process = Process.create_with_subclass(
                process_code=process_code,
                process_step=process_step,
                is_in_import_region=is_in_import_region,
                is_last=(i + 1 == len(main_process_codes_steps)),
            )

            # is_in_import_region: first non-transport step
            if not process.is_transport and _was_transport:
                # FIXME: better way then re-creating process?
                # we cannot change attribtue because of frozen dataclass
                is_in_import_region = True
                process.is_in_import_region = is_in_import_region

            _was_transport = _was_transport or process.is_transport

            main_processes.append(process)

        secondary_processes_export = [
            Process.create_with_subclass(
                process_code=process_code, is_in_import_region=False
            )
            for process_code in secondary_process_codes_export
        ]
        secondary_processes_import = [
            Process.create_with_subclass(
                process_code=process_code, is_in_import_region=True
            )
            for process_code in secondary_process_codes_import
        ]

        _graph = _create_graph(
            main_processes=main_processes,
            secondary_processes_export=secondary_processes_export,
            secondary_processes_import=secondary_processes_import,
        )
        return Chain(_graph=_graph)

    def get_calculation_data(
        self,
        data_handler: "DataHandler",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
    ) -> CalculateDataType:
        parameter_data = self._get_parameter_data_from_processes(
            data_handler=data_handler,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            use_user_data=use_user_data,
        )
        return self._merge_parameter_data(parameter_data=parameter_data)

    def calculate(self, data: CalculateDataType) -> PtxCalcResult:
        parameter_data = self._split_parameter_data(data=data)
        results_flows = self._calculate_flows(parameter_data=parameter_data)
        results_costs = self._calculate_costs(
            parameter_data=parameter_data, results_flows=results_flows
        )
        results_emissions = self._calculate_emissions(
            parameter_data=parameter_data, results_flows=results_flows
        )
        return self._merge_calculation_results(
            parameter_data=parameter_data,
            results_flows=results_flows,
            results_costs=results_costs,
            results_emissions=results_emissions,
        )

    def plot(
        self, file_basename: str, results_flows: dict[Process, ProcessResultFlowsType]
    ):
        """Create plot and save as png."""
        scale = 1
        node_pos = self._plot_get_pos()

        plt.close()
        plt.clf()
        plt.figure(
            figsize=(
                len(list(self._main_processes_ordered_forwards)) * scale * 2,
                2 * scale,
            )
        )

        # Draw nodes
        nx.draw(
            self._graph,
            node_pos,
            with_labels=False,
            node_color=[k.color for k in self._graph.nodes()],
            width=[2 if p.is_main else 1 for p, _p in self._graph.edges()],
            node_size=[
                (1000 if p.is_market else 2000) * scale for p in self._graph.nodes()
            ],
        )

        # Draw node labels
        nx.draw_networkx_labels(
            self._graph,
            node_pos,
            labels={p: p.process_code for p in self._graph.nodes()},
            font_size=6,
            font_color="black",
        )

        # Draw edge labels
        nx.draw_networkx_edge_labels(
            self._graph,
            node_pos,
            edge_labels={
                (p, p_): (p.main_flow_code_out) for p, p_ in self._graph.edges()
            },
            font_size=6,
            font_color="black",
            # label_pos=0.5, # noqa
        )

        # Save to PNG
        plt.savefig(f"chain_flowcharts/{file_basename}.png", dpi=150)

    @property
    def _main_processes_ordered_forwards(self) -> tuple[Process, ...]:
        return tuple(p for p in self._all_processes_ordered_forwards if p.is_main)

    @property
    def _secondary_processes_ordered_forwards(self) -> tuple[Process, ...]:
        return tuple(p for p in self._all_processes_ordered_forwards if p.is_secondary)

    @property
    def _market_processes_ordered_forwards(self) -> tuple[Process, ...]:
        return tuple(p for p in self._all_processes_ordered_forwards if p.is_market)

    @property
    def _all_processes_ordered_backwards(self) -> tuple[Process, ...]:
        return tuple(reversed(self._all_processes_ordered_forwards))

    def _get_default_parameter_values(self) -> DataQueryDicType:
        """For FLH lookup we need these process codes."""
        return {  # type: ignore
            "process_res": self._processes_by_step.get("RES"),
            "process_ely": self._processes_by_step.get("ELY"),
            "process_deriv": self._processes_by_step.get("DERIV"),
        }

    def _get_parameter_getters(
        self,
        data_handler: "DataHandler",
        use_user_data: bool = True,
    ) -> ParameterGetters: ...

    def _get_parameter_data_from_processes(
        self,
        data_handler: "DataHandler",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
    ) -> dict[Process, ProcessDataType]:
        result: dict[Process, ProcessDataType] = {}

        parameter_getters = self._get_parameter_getters(
            data_handler=data_handler, use_user_data=use_user_data
        )
        parameter_getters_default = self._get_default_parameter_values()

        for process in self._all_processes_ordered_forwards:
            parameter_values = parameter_getters_default | cast(
                DataQueryDicType,
                (
                    {
                        "source_region_code": target_country_code,
                        "target_country_code": target_country_code,
                    }  # NOTE: source_region_code
                    if process.is_in_import_region
                    else {
                        "source_region_code": source_region_code,
                        "target_country_code": target_country_code,
                    }
                ),
            )

            result[process] = process.get_parameter_data(
                parameter_getters=parameter_getters, parameter_values=parameter_values
            )
        return result

    def _calculate_flows(
        self, parameter_data: dict[Process, ProcessDataType]
    ) -> dict[Process, ProcessResultFlowsType]:
        results_flows: dict[Process, ProcessResultFlowsType] = {}
        for process in self._all_processes_ordered_backwards:
            results_flows[process] = process.calculate_flows(
                parameter_data=parameter_data, results_flows=results_flows
            )
        return results_flows

    def _calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> dict[Process, list[ProcessResultCostsType]]:
        results_costs: dict[Process, list[ProcessResultCostsType]] = {}
        for process in self._all_processes_ordered_forwards:
            results_costs[process] = process.calculate_costs(
                parameter_data=parameter_data,
                results_flows=results_flows,
                results_costs=results_costs,
            )
        return results_costs

    def _calculate_emissions(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> dict[Process, ProcessResultEmissionType]:
        results_emissions: dict[Process, ProcessResultEmissionType] = {}
        for process in self._all_processes_ordered_forwards:
            results_emissions[process] = process.calculate_emissions(
                parameter_data=parameter_data,
                results_flows=results_flows,
                results_emissions=results_emissions,
            )
        return results_emissions

    def _merge_calculation_results(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, list[ProcessResultCostsType]],
        results_emissions: dict[Process, ProcessResultEmissionType],
    ) -> PtxCalcResult:
        cols_dim_costs = ["process_type", "process_subtype", "cost_type"]
        df_results_cost = _aggregate_results_df(
            pd.DataFrame(
                [
                    asdict(x)
                    for x in [c for costs in results_costs.values() for c in costs]
                ],
                columns=cols_dim_costs + ["values"],
            ),
            cols_dim_costs,
        )
        # TODO from results_emissions
        cols_dim_emissions = [
            "process_type",
            "process_subtype",
            "emission_type",
            "gas_type",
        ]
        df_results_emissions_e_g_co2e = _aggregate_results_df(
            pd.DataFrame(columns=cols_dim_costs + ["values"]), cols_dim_emissions
        )
        df_results_emissions_m_g_co2e = _aggregate_results_df(
            pd.DataFrame(columns=cols_dim_costs + ["values"]), cols_dim_emissions
        )
        results_flows_chain = [
            results_flows[p] for p in self._main_processes_ordered_forwards
        ]
        results_flows_secondary = [
            results_flows[p] for p in self._secondary_processes_ordered_forwards
        ]

        return PtxCalcResult(
            df_results_cost=df_results_cost,
            df_results_emissions_e_g_co2e=df_results_emissions_e_g_co2e,
            df_results_emissions_m_g_co2e=df_results_emissions_m_g_co2e,
            results_flows_chain=results_flows_chain,
            results_flows_secondary=results_flows_secondary,
        )

    def _merge_parameter_data(
        self,
        parameter_data: dict[Process, ProcessDataType],
    ) -> CalculateDataType: ...

    def _split_parameter_data(
        self,
        data: CalculateDataType,
    ) -> dict[Process, ProcessDataType]: ...

    def _plot_get_pos(self) -> dict[Process, tuple[float, float]]:

        node_pos = {}

        x_start_import = None
        sgn = 1  # secondary process: offset sign should alternate between -1 and 1

        # main chain:
        x = 0
        for i, p in enumerate(self._main_processes_ordered_forwards):
            y = 0 if i > 0 else 0.25  # initial: offset a little
            node_pos[p] = (x, y)
            if p.is_in_import_region and x_start_import is None:
                x_start_import = x
            x += 2

        if not x_start_import:
            x_start_import = x

        # secondary
        x_export = 0
        x_import = x_start_import
        for p in self._secondary_processes_ordered_forwards:
            if p.is_in_import_region:
                x_import += 1.5
                x = x_import
            else:
                x_export += 1.5
                x = x_export
            y = 0.5 + 0.05 * sgn
            node_pos[p] = (x, y)
            sgn = -sgn

        # market
        # secondary
        x_export = 0
        x_import = x_start_import
        for p in self._market_processes_ordered_forwards:
            if p.is_in_import_region:
                x_import += 1
                x = x_import
            else:
                x_export += 1
                x = x_export
            y = 1.0
            node_pos[p] = (x, y)

        return node_pos


def _aggregate_results_df(
    df: pd.DataFrame, columns_index: list[str], columns_value: list[str] = ["values"]
) -> pd.DataFrame:
    return df[columns_index + columns_value].groupby(columns_index).sum().reset_index()


def _create_graph(
    main_processes: list[Process],
    secondary_processes_export: list[Process],
    secondary_processes_import: list[Process],
) -> nx.DiGraph[Process]:

    assert main_processes
    initial_proc = main_processes[0]
    assert initial_proc.is_initial
    flow_from_initial_proc = initial_proc.main_flow_code_out
    last_proc = main_processes[-1]
    assert last_proc.is_last

    graph: nx.DiGraph[Process] = nx.DiGraph()

    def add_edge(
        proc_provider: Process,
        proc_recipient: Process,
        in_main: bool,
    ):
        # check if flow_code_out == flow_code_in
        flow_codes_in = (
            {proc_recipient.main_flow_code_in}
            if in_main
            else proc_recipient.secondary_flow_types
        )
        if proc_provider.main_flow_code_out not in flow_codes_in:
            raise TypeError(f"Cannot link {proc_provider} => {proc_recipient}: flow")

        # check that we dont create circular
        if nx.has_path(graph, proc_recipient, proc_provider):
            raise HasACycle(
                f"Cannot link {proc_provider} => {proc_recipient}: circular"
            )

        graph.add_edge(
            proc_provider,
            proc_recipient,
            in_main=in_main,
            flow_code=proc_provider.main_flow_code_out,
        )

        logger.debug(
            f"Create link {proc_provider}({proc_provider.main_flow_code_out}) "
            f"{'==>' if in_main else '-->'} {proc_recipient}"
        )

    def create_and_link_market_process(
        proc_recipient: Process,
        flow_type: FlowCodeType,
        in_main: bool = False,
        is_in_import_region: bool = False,
    ):
        market_process = Process.create_with_subclass(
            process_code=flow_type,
            is_in_import_region=is_in_import_region,
        )
        graph.add_node(market_process)
        add_edge(
            proc_provider=market_process, proc_recipient=proc_recipient, in_main=in_main
        )

    def add_edge_or_create_market(
        proc_provider: Process,
        proc_recipient: Process,
        in_main: bool,
    ):
        try:
            add_edge(
                proc_provider=proc_provider,
                proc_recipient=proc_recipient,
                in_main=in_main,
            )
        except HasACycle:
            create_and_link_market_process(
                proc_recipient=proc_recipient,
                flow_type=proc_provider.main_flow_code_out,
                in_main=in_main,
                is_in_import_region=proc_recipient.is_in_import_region,
            )

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

    # collect all provider of secondary flows (can also come from initial (EL/NG))
    flow_provider_sec_or_initial_export: dict[FlowCodeType, Process] = {}
    flow_provider_sec_or_initial_export[initial_proc.main_flow_code_out] = initial_proc

    for sec_proc in secondary_processes_export:
        if sec_proc.main_flow_code_out in flow_provider_sec_or_initial_export:
            logger.warning("Exp: flow already provided, skipping %s", sec_proc)
            continue
        logger.debug("Exp: provide %s from %s", sec_proc.main_flow_code_out, sec_proc)
        flow_provider_sec_or_initial_export[sec_proc.main_flow_code_out] = sec_proc

    flow_provider_sec_import: dict[FlowCodeType, Process] = {}
    for sec_proc in secondary_processes_import:
        if sec_proc.main_flow_code_out in flow_provider_sec_import:
            logger.warning("Imp: flow already provided, skipping %s", sec_proc)
            continue
        logger.debug("Imp: provide %s from %s", sec_proc.main_flow_code_out, sec_proc)
        flow_provider_sec_import[sec_proc.main_flow_code_out] = sec_proc

    def get_provider(
        flow_code: FlowCodeType, is_in_import_region: bool
    ) -> Process | None:
        providers = (
            flow_provider_sec_import
            if is_in_import_region
            else flow_provider_sec_or_initial_export
        )
        return providers.get(flow_code)

    def link_process(process: Process, prev_main_process: Process | None = None):
        todo = []
        if prev_main_process:
            assert prev_main_process.is_main and process.is_main
            add_edge(prev_main_process, process, in_main=True)
        else:  # either initial or secondary
            if process.is_secondary and process.main_flow_code_in:
                todo.append((process.main_flow_code_in, True))
        for flow_code in sort_flows_b_priority(process.secondary_flow_types):
            todo.append((flow_code, False))

        for flow_code, in_main in todo:
            provider = get_provider(
                flow_code=flow_code, is_in_import_region=process.is_in_import_region
            )
            if provider:
                add_edge_or_create_market(
                    proc_provider=provider, proc_recipient=process, in_main=in_main
                )
            else:
                create_and_link_market_process(
                    proc_recipient=process,
                    flow_type=flow_code,
                    in_main=in_main,
                    is_in_import_region=process.is_in_import_region,
                )

    # add nodes
    graph.add_nodes_from(main_processes)
    graph.add_nodes_from(secondary_processes_export)
    graph.add_nodes_from(secondary_processes_import)

    # link up secondaries
    for process in secondary_processes_import + secondary_processes_export:
        link_process(process)

    # link up main
    prev_main_process = None
    for process in main_processes:
        link_process(process, prev_main_process=prev_main_process)
        prev_main_process = process

    # optionally: find and drop processes with no path to last
    procs_old = set(graph.nodes)
    graph = cast(
        nx.DiGraph, graph.subgraph(nx.ancestors(graph, last_proc) | {last_proc})
    )
    all_procs_final = set(graph.nodes)
    procs_dropped = procs_old - all_procs_final
    if procs_dropped:
        # dont warn about dropped market processes
        procs_dropped = {p for p in procs_dropped if not p.is_market}
        logger.warning("Dropped unused: %s", [str(x) for x in procs_dropped])

    return graph


def _get_dropped_transport_steps(
    transport: TransportType,
    ship_own_fuel: bool,
) -> set[ProcessStepType | str]:
    """If shipping: remove pipeline (and pre/post), and vice versa."""
    # TODO: remove hard coded
    if transport == "Pipeline":
        drop_steps = {
            "PRE_SHP",
            "POST_SHP",
            "SHP",
            "SHP_OWN",
        }
    elif transport == "Ship":
        drop_steps = {
            "PRE_PPL",
            "PPLS",
            "PPL",
            "PPLX",
            "PPLR",
            "POST_PPL",
        }
        if ship_own_fuel:
            drop_steps = drop_steps | {"SHP"}
        else:
            drop_steps = drop_steps | {"SHP_OWN"}
    else:
        raise NotImplementedError(transport)

    return drop_steps
