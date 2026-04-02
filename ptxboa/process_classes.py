"""Class based calculation."""

import logging
from typing import Iterable, Union, cast

import matplotlib.pyplot as plt
import networkx as nx

from ptxboa import logger
from ptxboa.api_data import DataHandler
from ptxboa.static import (
    ChainType,
    DataQueryParameterType,
    FlowCodeType,
    ParameterCodeType,
    ParameterCodeValues,
    ProcessCodeType,
    ProcessStepType,
)
from ptxboa.static import ProcessStepValues as ProcessStepValuesSorted
from ptxboa.static import (
    SourceRegionCodeType,
    TargetCountryCodeType,
    TransportType,
)
from ptxboa.static._type_defs import (
    AggregateProcessDataType,
    CalculateDataType,
    ChainDefStatic,
    ParameterGetter,
    ParameterGetters,
    ProcessDataType,
    ProcessStep,
    PtxCalcResult,
)


def _plot_get_pos(
    chain_process: "AggregateProcess",
) -> dict["AbstractProcess", tuple[float, float]]:

    node_pos = {}
    xs: list[float] = [0, 0, 0]
    proc_end_last = None

    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        xs[1] = max(xs[0] + 0.25, xs[0])  # stagger
        xs[2] = max(xs[0], xs[2])

        sgn = 1  # secondary process: offset sign should alternate between -1 and 1

        for process in reversed(list(process_graph.calculate_order)):
            key = process

            # if is_main:
            if process in process_graph.main_processes:
                xs[0] = xs[0] + 2
                x = xs[0]
                y = 0
                if not proc_end_last and process == process_graph.main_processes[0]:
                    y = 0.05  # initial a little closer to secondary
            elif not isinstance(process, MarketProcess):
                #  is secondary
                xs[1] = xs[1] + 1.5
                x = xs[1]
                # non linear disntance for non overlapping arrows
                y = 0.1 + 0.008 * sgn
                sgn = -sgn  # alterante
            else:
                # market
                xs[2] = xs[2] + 1
                x = xs[2]
                y = 0.2

            node_pos[key] = (x, y)

        proc_end_last = process_graph.main_processes[-1]

    return node_pos


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
            logger.error(
                f"{self.process_code}: main_flow_code_in {self.main_flow_code_in} "
                "in secondary_flow_types"
            )
        if self.main_flow_code_out in self.secondary_flow_types:
            logger.error(
                f"{self.process_code}: main_flow_code_out {self.main_flow_code_out} "
                "in secondary_flow_types"
            )
        if self.is_secondary and self.main_flow_code_in:
            logger.warning(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )
        if self.is_initial and self.main_flow_code_in:
            logger.error(
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
    def is_transport_pre_post(self) -> bool:
        """Process is transport pre/post."""
        return self.is_transport and self.is_transformation and not self.is_storage

    @property
    def is_shipping_or_pipeline(self) -> bool:
        """Without pre/post transformation."""
        return self.is_transport and not self.is_transformation and not self.is_storage

    @property
    def process_class(self) -> type["Process"]:
        """Process class.

        So we can dynamically use subclasses.
        """
        if self.is_initial:
            return InitialProcess
        elif self.is_secondary:
            return SecondaryProcess
        elif self.is_storage:
            return StorageProcess
        elif self.is_transport and not self.is_transformation:
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
        return self.is_shipping_or_pipeline

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
    for p in DataHandler.get_dimension("process").to_dict(orient="records")
}


class AbstractProcess:
    _parameter_codes_process: list[ParameterCodeType] = []
    _parameter_codes_process_flow: list[ParameterCodeType] = []

    def __init__(
        self,
        process_step: ProcessStepType | str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        self._main_flow_out: float | None = None  # will be set in calculate()
        self._main_flow_in: float | None = None  # will be set in calculate()
        self._secondary_flows_in: dict[FlowCodeType, float] | None = None
        self.parent_process = parent_process
        self.process_step: ProcessStepType | str | None = process_step

    def get_main_flow_out(self) -> float:
        """Value of main out flow."""
        if self._main_flow_out is None:
            raise Exception("Not calculated yet")
        return self._main_flow_out

    def get_main_flow_in(self) -> float:
        """Value of calculated main in flow."""
        if self._main_flow_in is None:
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
    def main_flow_code_in_or_out(self) -> FlowCodeType:
        """Main flow code in."""
        return self.main_flow_code_in or self.main_flow_code_out

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return set()

    @property
    def _parameter_flow_types(self) -> set[FlowCodeType]:
        """Flow types for which parameter data should be loaded."""
        result = self.secondary_flow_types
        # also add main flow in (for market/initial proces,
        # those dont exist and we need out)
        result.add(self.main_flow_code_in_or_out)
        # FIXME: for testing compatebility, we also add main_flow out,
        # but can be removed later
        result.add(self.main_flow_code_out)

        return result

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

    def _get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        data_lookup_defaults: dict[DataQueryParameterType, str],
        parent_parameters: ProcessDataType | None = None,
    ) -> ProcessDataType:
        """Initialize parameter data for this process."""
        parameters: ProcessDataType = {}
        # load parameters that are process dependent
        for p in self._parameter_codes_process:
            parameters[p] = parameter_getters[p](
                process_code=self.process_code, flow_code=None, **data_lookup_defaults
            )

        # load parameters that are process and flow dependent
        for p in self._parameter_codes_process_flow:
            parameters[p] = {
                f: parameter_getters[p](
                    process_code=self.process_code, flow_code=f, **data_lookup_defaults
                )
                for f in self._parameter_flow_types
            }

        # FIXME: for debugging:
        # parameters["region"] = data_lookup_defaults["source_region_code"]  # noqa

        return _merge_process_data(parameters, parent_parameters)

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        self._main_flow_out = main_flow_out

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        step = f"{self.process_step}=" if self.process_step else ""
        return f"{self.__class__.__name__}({step}{self.process_code}{s_val})"


class Process(AbstractProcess):
    color = "lightblue"
    _parameter_codes_process = ["LIFETIME", "EFF", "FLH", "CAPEX", "OPEX-F", "OPEX-O"]
    _parameter_codes_process_flow = [
        "CH4SHARE",
        "EF_E",
        "EF_M",
        "CBOUND",
        "CONV-OT",
        "CO2CPT-R",
        "CO2CPT-S",
        "CONV",
        "LOSS",
    ]

    def __init__(
        self,
        process_code: ProcessCodeType,
        process_step: ProcessStepType | str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
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

    @property
    def is_re_generation(self) -> bool:
        """Is this re generation process."""
        return self._process_type.is_re_generation

    def _get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        data_lookup_defaults: dict[DataQueryParameterType, str],
        parent_parameters: ProcessDataType | None = None,
    ) -> ProcessDataType:
        """Initialize parameter data for this process."""
        parameters = super()._get_calculation_data(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,
            parent_parameters=parent_parameters,
        )

        # changes

        if "LOSS" in parameters and "EFF" in parameters:
            parameters["LOSS_FLOW"] = parameters.pop("LOSS")
            if self.main_flow_code_in_or_out in parameters["LOSS_FLOW"]:  # type: ignore # noqa
                parameters["LOSS"] = parameters["LOSS_FLOW"].pop(  # type: ignore
                    self.main_flow_code_in_or_out
                )
            # update EFF and CONV for losses
            # TODO: keep original values for information purposes
            # NOTE: calculation: see https://github.com/agoenergy/ptx-boa/issues/581
            if "LOSS" in parameters:
                eff_original = parameters["EFF"]
                parameters["EFF"] = eff_original / (1 + parameters["LOSS"])  # type: ignore # noqa

        if "LOSS_FLOW" in parameters and "CONV" in parameters:
            # LOSS for CONV (if value exists in both)
            loss_flows = parameters.get("LOSS_FLOW", {})
            convs = parameters.get("CONV", {})
            for fc in set(loss_flows) & set(convs):  # type: ignore
                conv_orig = convs[fc]  # type: ignore
                parameters["CONV"][fc] = conv_orig * (1 + loss_flows[fc])  # type: ignore # noqa

        # FIXME: only for temporary test comparison?
        if (
            any(parameters.get("CO2CPT-R", {}).values())  # type: ignore
            or any(parameters.get("CO2CPT-S", {}).values())  # type: ignore
        ) and self.process_code != "CCGT-CC#B":
            logger.warning("TODO: remove dummy CONV for CO2-C")
            parameters["CONV"]["CO2-C"] = 1  # type: ignore

        return parameters

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)
        eff: float = self._parameters.get("EFF")  # type: ignore
        if not eff:
            # logger.warning("EFF = 0") # noqa
            eff = 1

        self._main_flow_in = main_flow_out / eff
        self._secondary_flows_in = {}
        convs = self._parameters.get("CONV", {})  # type: ignore
        for fc in self.secondary_flow_types:
            conv: float = convs.get(fc, 0)  # type: ignore
            value = main_flow_out * conv
            if value < 0:  # ignore (e.g. exothermal heat)
                value = 0
            self._secondary_flows_in[fc] = value


class TransportProcess(Process):
    _parameter_codes_process = ["OPEX-T", "LOSS-T"]
    color = "teal"

    def _get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        data_lookup_defaults: dict[DataQueryParameterType, str],
        parent_parameters: ProcessDataType | None = None,
    ) -> ProcessDataType:
        """Initialize parameter data for this process."""
        parameters = super()._get_calculation_data(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,
            parent_parameters=parent_parameters,
        )
        logger.warning("Calculate transport EFF")
        parameters["EFF"] = 1  # FIXME
        return parameters


class StorageProcess(Process):
    color = "lightsteelblue"


class SecondaryProcess(Process):
    color = "lightgreen"

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return True


class InitialProcess(SecondaryProcess):
    color = "skyblue"


class MarketProcess(AbstractProcess):
    color = "lightgray"
    _parameter_codes_process_flow: list[ParameterCodeType] = ["SPECCOST"]

    def __init__(
        self,
        main_flow_code_out: FlowCodeType,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(parent_process=parent_process)
        self._main_flow_code_out: FlowCodeType = main_flow_code_out

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
        return self.main_flow_code_out  # type: ignore


def _get_chain_sections(
    main_process_codes_steps: list["ProcessStep"],
) -> list[tuple[type["ChainSectionProcess"], int, int]]:
    # split and check into export, transport, import
    is_transport = [
        ProcessTypes[p].allow_in_transport for p, _s in main_process_codes_steps
    ]
    # first and last index
    idx_transport_start = is_transport.index(True)
    try:
        idx_transport_end = is_transport.index(False, idx_transport_start)
    except ValueError:  # no import steps
        idx_transport_end = len(is_transport)

    if not (0 < idx_transport_start < idx_transport_end):
        raise Exception("Transport")
    return [  # export,transport,import
        (ChainExportProcess, 0, idx_transport_start),
        (ChainTransportProcess, idx_transport_start, idx_transport_end),
        (ChainImportProcess, idx_transport_end, len(main_process_codes_steps)),
    ]


class AggregateProcess(AbstractProcess):
    def __init__(
        self,
        process_graph: "ProcessGraph",
        process_step: str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
        self.process_graph: "ProcessGraph" = process_graph

    def get_first_main_process_by_step(self, step: ProcessStepType) -> Process:
        """May raise Exception."""
        # TODO: faster if we create lookup dict first
        return next(
            cast(Process, p) for p in self.full_main_chain if p.process_step == step
        )

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self.process_graph.main_processes[-1].main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self.process_graph.main_processes[0].main_flow_code_in

    @property
    def full_main_chain(self) -> list[Process]:
        """List of the entire main chain (including nested aggregated processes)."""
        result: list[Process] = []
        for proc in self.process_graph.main_processes:
            if isinstance(proc, AggregateProcess):
                result += proc.full_main_chain
            else:
                result.append(proc)  # type: ignore - should be Process

        return result

    @property
    def secondary_processes(self) -> list[SecondaryProcess]:
        """List of all secondary processes (including nested aggregated processes)."""
        result: list[SecondaryProcess] = []
        for proc in self.process_graph.calculate_order:
            if isinstance(proc, AggregateProcess):
                result += proc.secondary_processes  # recursion
            elif (
                proc.is_secondary
                # NOTE initial is modelled as secondary (because it has no inflow)
                and not proc.is_initial
            ):
                result.append(proc)  # type: ignore should be SecondaryProcess

        return result

    def _get_aggregated_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        data_lookup_defaults: dict[DataQueryParameterType, str],
        parent_parameters: ProcessDataType | None = None,
    ) -> AggregateProcessDataType:
        """Initialize parameter data for this process."""
        parameters_self = self._get_calculation_data(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,
            parent_parameters=parent_parameters,
        )

        parameters_procs = {}
        for process in self.process_graph.calculate_order:
            parameters_procs[process] = process._get_calculation_data(
                parameter_getters=parameter_getters,
                data_lookup_defaults=data_lookup_defaults,
                parent_parameters=parameters_self,
            )

        return parameters_self, parameters_procs

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
                    logger.debug(f"{process}: Serve {flow_code} to {proc_target}")
                    main_flow_out_current += (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow_code=flow_code)
                    )

                # check
                if not main_flow_out_current:
                    # logger.warning(f"{process}: main_flow_out is 0") # noqa
                    if main_flow_out_current is None:
                        raise ValueError(f"{process}: main_flow_out is None")
            logger.debug(f"Calculate: {process} for {main_flow_out_current}")
            process.calculate(main_flow_out=main_flow_out_current)

            if process == self.process_graph.main_processes[0]:
                self._main_flow_in = process.get_main_flow_in()

    def get_subprocesses_by_class(
        self, class_or_classes: type | tuple[type]
    ) -> list[AbstractProcess]:
        """Get subprocesses byclass."""
        return [
            p
            for p in self.process_graph.calculate_order
            if isinstance(p, class_or_classes)
        ]

    def plot(self, file_basename: str):
        """Create plot and save as png."""
        # Create a directed graph
        G = nx.DiGraph()
        node_labels = {}
        edge_labels = {}
        edge_widths = {}

        proc_end_last = None
        len_main_total = 0
        for ex_tr_imp in self.process_graph.main_processes:
            ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
            # export / tranport / import  subgraph

            process_graph = ex_tr_imp.process_graph

            # add processes as nodes to DiGraph

            for process in reversed(list(process_graph.calculate_order)):
                label = str(process)

                G.add_node(process)
                node_labels[process] = (
                    label.replace("=", "\n")
                    .replace("(", "\n")
                    .replace(")", "\n")
                    .replace(" ", "\n")
                    .strip()
                )

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
        node_pos = _plot_get_pos(chain_process=self)

        plt.close()
        plt.clf()
        plt.figure(figsize=(len_main_total * scale, 2 * scale))

        # Draw nodes
        nx.draw(
            G,
            node_pos,
            with_labels=False,
            node_color=[cast(Process, k).color for k in G.nodes()],
            width=[edge_widths[k] for k in G.edges()],
            node_size=2000 * scale,
        )

        # Draw node labels
        nx.draw_networkx_labels(
            G, node_pos, labels=node_labels, font_size=6, font_color="black"
        )

        # Draw edge labels
        nx.draw_networkx_edge_labels(
            G,
            node_pos,
            edge_labels=edge_labels,
            font_size=6,
            font_color="black",
            # label_pos=0.5, # noqa
        )

        # Save to PNG
        plt.savefig(f"chain_flowcharts/{file_basename}.png", dpi=150)


class ChainProcess(AggregateProcess):
    _parameter_codes_process = ["CALOR"]  # conversion kg / kwh

    _instances: dict[object, "ChainProcess"] = {}

    @classmethod
    def get_or_create(cls, chain_def: ChainDefStatic) -> "ChainProcess":
        """Get or create static instance."""
        key = chain_def.unique_key
        if key not in cls._instances:
            cls._instances[key] = cls._create(chain_def)
        return cls._instances[key]

    def calculate(self, data: CalculateDataType) -> PtxCalcResult:
        """Calcualte results."""
        result: PtxCalcResult = None  # type: ignore
        return result

    @classmethod
    def _create(cls, chain_def: ChainDefStatic) -> "ChainProcess":
        chain_color = DataHandler.get_chain_color(chain_def.chain_name)

        secondary_process_codes = set(chain_def.secondary_processes.values())

        first_process_code: ProcessCodeType
        if chain_color == "blue":
            first_process_code = "NG-PROD#B"
            secondary_process_codes = secondary_process_codes | {
                "HEATPUMP#B",
                "CCGT-CC#B",
                "CO2-T+S#B",
            }  # type: ignore
        else:
            first_process_code = chain_def.process_code_res

        return ChainProcess(
            transport=chain_def.transport,
            ship_own_fuel=chain_def.ship_own_fuel,
            chain=chain_def.chain_name,
            first_process_code=first_process_code,
            secondary_process_codes=secondary_process_codes,  # type: ignore
        )

    def __init__(
        self,
        chain: ChainType,
        first_process_code: ProcessCodeType,
        secondary_process_codes: set[ProcessCodeType],
        transport: TransportType,
        ship_own_fuel: bool,
    ):
        """Create aggregated process for entire chain."""
        chain_data = DataHandler.get_dimension("chain").loc[chain].to_dict()

        main_process_codes_steps: list["ProcessStep"] = [
            (cast(ProcessCodeType, chain_data[step]), cast(ProcessStepType, step))
            for step in ProcessStepValuesSorted
            if chain_data[step]
        ]

        main_process_codes_steps_filtered = _filter_transport_process_codes(
            main_process_codes_steps,
            transport=transport,
            ship_own_fuel=ship_own_fuel,
        )
        # add initial step
        chain_start_with_res = ProcessTypes[first_process_code].is_re_generation
        initial_step = cast(
            ProcessStepType,
            # TODO: maybe from green/blue?
            ("RES" if chain_start_with_res else "NG_PROD"),
        )
        main_process_codes_steps_filtered.insert(0, (first_process_code, initial_step))

        # for FLH lookup we need these process codes
        self._data_lookup_defaults_static: dict[str, ProcessCodeType | None] = {
            "process_res": (first_process_code if chain_start_with_res else None),
            "process_ely": chain_data["ELY"],
            "process_deriv": chain_data["DERIV"],
        }
        self._data_lookup_defaults: dict | None = None  # will be set in init params

        check_use_all_main_process_codes = []

        # FIXME: pre/post shipping processes, remove not required

        main_processes: list[AbstractProcess] = []

        for ChainSectionProcessClass, i, j in _get_chain_sections(
            main_process_codes_steps=main_process_codes_steps_filtered
        ):
            main_process_codes_steps_part: list["ProcessStep"] = (
                main_process_codes_steps_filtered[i:j]
            )
            if not main_process_codes_steps_part:
                continue

            invalid_processes = [
                p
                for p, _s in main_process_codes_steps_part
                if not ChainSectionProcessClass.process_allowed(p)
            ]
            if invalid_processes:
                raise Exception(
                    f"Processes not allowed in {ChainSectionProcessClass.__name__} "
                    f"{main_process_codes_steps_part}: {invalid_processes}"
                )
            secondary_process_codes_part: set[ProcessCodeType] = {
                p
                for p in secondary_process_codes
                if ChainSectionProcessClass.process_allowed(p)
            }

            process = ChainSectionProcessClass(
                main_process_codes_steps=main_process_codes_steps_part,
                secondary_process_codes=secondary_process_codes_part,
                parent_process=self,
            )
            main_processes.append(process)

            check_use_all_main_process_codes = (
                check_use_all_main_process_codes + main_process_codes_steps_part
            )

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes, secondary_processes=[], parent_process=self
        )

        super().__init__(
            process_graph=process_graph,
            process_step="CHAIN",
        )

        # check (TODO: can be removed later)
        if not tuple(check_use_all_main_process_codes) == tuple(
            main_process_codes_steps_filtered
        ):
            raise Exception(
                f"{check_use_all_main_process_codes} != "
                f"{main_process_codes_steps_filtered}"
            )
        # check (TODO: can be removed later)
        main_process_codes_ = tuple(p.process_code for p in self.full_main_chain)
        if (
            tuple(p for p, s_ in main_process_codes_steps_filtered)
            != main_process_codes_
        ):
            raise Exception(main_process_codes_)

    def get_calculation_data(
        self,
        data_handler: DataHandler,
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
    ) -> CalculateDataType:
        """Get calculation data."""
        parameter_getters = _create_parameter_getters(
            data_handler=data_handler, use_user_data=use_user_data
        )

        data_lookup_defaults = {
            "source_region_code": source_region_code,
            "target_country_code": target_country_code,
        }

        parameters_chain = self._get_calculation_data(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,  # type: ignore
        )

        logger.warning(parameters_chain)

        proc_export: AggregateProcess = self.get_subprocesses_by_class(
            # type: ignore
            ChainExportProcess
        )[0]
        _parameters_export, parameters_export_procs = (
            proc_export._get_aggregated_calculation_data(
                parameter_getters=parameter_getters,
                data_lookup_defaults=data_lookup_defaults,  # type: ignore
            )
        )

        proc_transport: AggregateProcess = self.get_subprocesses_by_class(
            # type: ignore
            ChainTransportProcess
        )[0]
        _parameters_transport, parameters_transport_procs = (
            proc_transport._get_aggregated_calculation_data(
                parameter_getters=parameter_getters,
                data_lookup_defaults=data_lookup_defaults,  # type: ignore
            )
        )

        try:
            proc_import: AggregateProcess = self.get_subprocesses_by_class(
                # type: ignore
                ChainImportProcess
            )[0]
        except Exception:
            proc_import = None  # type: ignore

        if proc_import:
            _parameters_import, parameters_import_procs = (
                proc_import._get_aggregated_calculation_data(
                    parameter_getters=parameter_getters,
                    data_lookup_defaults=data_lookup_defaults,  # type: ignore
                )
            )
        else:
            _parameters_import = {}
            parameters_import_procs = {}

        def get_proc_data(
            process: Process, parameter: ProcessDataType
        ) -> ProcessDataType:
            return parameter | {  # type: ignore
                "process_code": process.process_code,
                "step": process.process_step,
            }

        parameter = _parameters_export
        parameter["SPECCOST"] = {}
        # also aggregate all specccost
        for p in proc_export.get_subprocesses_by_class(MarketProcess):
            parameter["SPECCOST"] = parameter["SPECCOST"] | parameters_export_procs[
                p
            ].get(  # type: ignore # noqa
                "SPECCOST",
                {},
            )

        if proc_import:
            parameter_i = _parameters_import
            parameter_i["SPECCOST"] = {}
            # also aggregate all specccost
            for p in proc_import.get_subprocesses_by_class(MarketProcess):
                parameter_i["SPECCOST"] = parameter_i[
                    "SPECCOST"
                ] | parameters_import_procs[
                    p
                ].get(  # type: ignore # noqa
                    "SPECCOST",
                    {},
                )
        else:
            parameter_i = {}

        secondary_process = {
            p.main_flow_code_out: get_proc_data(p, parameters_export_procs[p])
            for p in proc_export.secondary_processes
        }

        # FXIME: currently, CALOR is read from "parameters", but it is not
        # really part of the export chain part
        parameter["CALOR"] = parameters_chain["CALOR"]

        return {
            "context": data_lookup_defaults,
            "parameter": parameter,
            "parameter_i": parameter_i,
            "main_export_process_chain": [
                get_proc_data(p, parameters_export_procs[p])
                for p in proc_export.full_main_chain
            ],
            "transport_process_chain": [
                get_proc_data(p, parameters_transport_procs[p])
                for p in proc_transport.full_main_chain
            ],
            "main_import_process_chain": (
                [
                    get_proc_data(p, parameters_import_procs[p])
                    for p in proc_import.full_main_chain
                ]
                if proc_import
                else []
            ),
            "secondary_process": secondary_process,
        }


class ChainSectionProcess(AggregateProcess):
    _parameter_codes_process = ["WACC"]  # different in export / import

    def __init__(
        self,
        main_process_codes_steps: list["ProcessStep"],
        secondary_process_codes: set[ProcessCodeType],
        parent_process: Union["AbstractProcess", None] = None,
    ):

        main_processes: list[AbstractProcess] = [
            ProcessTypes[pt].process_class(
                process_code=pt, process_step=ps, parent_process=self
            )
            for pt, ps in main_process_codes_steps
        ]
        secondary_processes: list[Process] = [
            ProcessTypes[pt].process_class(process_code=pt, parent_process=self)
            for pt in secondary_process_codes
        ]

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes,
            secondary_processes=secondary_processes,
            parent_process=self,
        )
        super().__init__(
            process_graph=process_graph,
            parent_process=parent_process,
        )

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return True


class ChainExportProcess(ChainSectionProcess):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_export


class ChainImportProcess(ChainSectionProcess):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_import

    @staticmethod
    def _switch_region(
        data_lookup_defaults: dict[DataQueryParameterType, str],
    ) -> dict[DataQueryParameterType, str]:
        return data_lookup_defaults | {  # type: ignore
            "source_region_code": data_lookup_defaults["target_country_code"],
        }

    def _get_aggregated_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        data_lookup_defaults: dict[DataQueryParameterType, str],
        parent_parameters: ProcessDataType | None = None,
    ) -> AggregateProcessDataType:
        """Initialize parameter data for this process."""
        # when getting data: switch region
        return super()._get_aggregated_calculation_data(
            parameter_getters=parameter_getters,
            data_lookup_defaults=self._switch_region(data_lookup_defaults),
            parent_parameters=parent_parameters,
        )


class ChainTransportProcess(ChainSectionProcess):
    _parameter_codes_process = [
        "CAP-T",
        "DST-S-D",
        "DST-S-DP",
        "SEASHARE",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: ugly
        self.transport: TransportType = (
            "Ship"
            if any(
                cast(Process, p)._process_type.is_shipping for p in self.full_main_chain
            )
            else "Pipeline"
        )
        self.ship_own_fuel: bool = any(
            cast(Process, p)._process_type.is_shipping_own_fuel
            for p in self.full_main_chain
        )

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_transport

    def _get_aggregated_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        data_lookup_defaults: dict[DataQueryParameterType, str],
        parent_parameters: ProcessDataType | None = None,
    ) -> AggregateProcessDataType:
        """Initialize parameter data for this process."""
        # NOTE: dont call super here
        parameters_self = self._get_calculation_data(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,
            parent_parameters=parent_parameters,
        )

        # get transport distances and options
        transport_distances: dict[ProcessStepType, float] = (
            DataHandler._get_transport_distances(
                source_region_code=data_lookup_defaults["source_region_code"],  # type: ignore # noqa
                target_country_code=data_lookup_defaults["target_country_code"],  # type: ignore # noqa
                transport=self.transport,
                ship_own_fuel=self.ship_own_fuel,
                dist_ship=parameters_self["DST-S-D"],  # type: ignore
                dist_pipeline=parameters_self["DST-S-DP"],  # type: ignore
                seashare_pipeline=parameters_self["SEASHARE"],  # type: ignore
                existing_pipeline_cap=parameters_self["CAP-T"],  # type: ignore
            )
        )

        parameters_procs = {}
        for process in self.process_graph.calculate_order:
            dist = transport_distances.get(process.process_step, 0)  # type: ignore

            parameters_procs[process] = process._get_calculation_data(
                parameter_getters=parameter_getters,
                data_lookup_defaults=data_lookup_defaults,
                parent_parameters=_merge_process_data(
                    parent_parameters, {"DIST": dist}
                ),  # type: ignore # noqa
            )

        return parameters_self, parameters_procs


def _group_by_flow_type_out(
    process_codes: Iterable[ProcessCodeType],
) -> dict[FlowCodeType, ProcessCodeType]:
    result = {}
    for process_code in process_codes:
        flow_code = ProcessTypes[process_code].main_flow_code_out
        if flow_code in result:
            raise KeyError(f"Multiple items for {flow_code}")
        result[flow_code] = process_code
    return result


class ProcessGraph:
    _KEY_MAIN = "(MAIN)"  # nust not be a flow code

    def __init__(
        self,
        main_processes: list[AbstractProcess],
        secondary_processes: list[Process],
        parent_process: AbstractProcess | None = None,
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
            # check
            flow_codes_in = (
                {proc_recipient.main_flow_code_in}
                if in_main
                else proc_recipient.secondary_flow_types
            )
            if proc_provider.main_flow_code_out not in flow_codes_in:
                raise Exception(f"Cannot link {proc_provider} => {proc_recipient}")

            if proc_provider not in self.links_out:
                self.links_out[proc_provider] = []
            self.links_out[proc_provider].append((proc_recipient, in_main))
            G.add_edge(proc_provider, proc_recipient)
            logger.debug(
                f"Create link {proc_provider}({proc_provider.main_flow_code_out}) "
                f"{'==>' if in_main else '-->'} {proc_recipient}"
            )

        market_processes: dict[FlowCodeType, MarketProcess] = {}

        def get_or_create_market_process(flow_type: FlowCodeType) -> MarketProcess:
            if flow_type not in market_processes:
                market_processes[flow_type] = MarketProcess(
                    main_flow_code_out=flow_type, parent_process=parent_process
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
                logger.warning(f"flow already proveided, skipping {sec_proc}")
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
                        logger.warning(
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
            logger.info("Dropping unused: %s", [str(x) for x in procs_dropped])
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


def _filter_transport_process_codes(
    main_process_codes_steps: list["ProcessStep"],
    transport: TransportType,
    ship_own_fuel: bool,
) -> list["ProcessStep"]:
    """If shipping: remove pipeline (and pre/post), and vice versa."""
    drop_steps: set[ProcessStepType | str]

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

    logging.debug(
        "Dropping unused processes: %s",
        [f"{s}={p}" for p, s in main_process_codes_steps if s in drop_steps],
    )
    return [(p, s) for p, s in main_process_codes_steps if s not in drop_steps]


def _create_parameter_getters(
    data_handler: DataHandler, use_user_data: bool
) -> ParameterGetters:

    def _get_df(
        parameter_code: ParameterCodeType, process_code: ProcessCodeType | None
    ):
        if (
            parameter_code == "FLH"
            and process_code
            and not ProcessTypes[process_code].is_re_generation
        ):
            # FLH not changed by user_data
            df = data_handler.flh
        else:
            if use_user_data:
                df = data_handler.scenario_data
            else:
                df = data_handler._scenario_data
        return df

    def _get_parameter_keys(
        parameter_code: ParameterCodeType, use_global_default: bool = False
    ) -> list[tuple[DataQueryParameterType, bool]]:
        if parameter_code == "FLH":
            return [
                (x, True)
                for x in [
                    "source_region_code",  # => region
                    "process_res",
                    "process_ely",
                    "process_deriv",
                    "process_code",  # => process_flh
                ]
            ]  # type: ignore
        else:
            dims = set(
                DataHandler.get_dimension("parameter").at[parameter_code, "dimensions"]  # type: ignore # noqa
            )
            return [
                ("parameter_code", True),
                ("process_code", "process_code" in dims),
                ("flow_code", "flow_code" in dims),
                (
                    "source_region_code",
                    "source_region_code" in dims and not use_global_default,
                ),
                ("target_country_code", "target_country_code" in dims),
            ]

    def make_getter(
        parameter_code: ParameterCodeType, use_global_default: bool
    ) -> ParameterGetter:
        keys = _get_parameter_keys(
            parameter_code, use_global_default=use_global_default
        )

        def _get_value(
            process_code: ProcessCodeType | None = None,
            flow_code: FlowCodeType | None = None,
            **data_lookup_defaults,
        ) -> float | None:
            df = _get_df(parameter_code=parameter_code, process_code=process_code)
            # all available key values
            key_vals = data_lookup_defaults | {
                "parameter_code": parameter_code,
                "process_code": process_code,
                "process_flh": process_code,  # for FLH
                "flow_code": flow_code,
            }
            # join only required key_vals in correct order

            key = ",".join([(key_vals.get(k) or "") if use else "" for k, use in keys])

            try:
                value = cast(float, df.at[key, "value"])
            except Exception:
                value = None

            # FIXME: remove later
            key_debug = ",".join(
                [k + "=" + ((key_vals.get(k) or "") if use else "") for k, use in keys]
            )
            if parameter_code == "FLH":
                key_debug = "parameter_code=FLH," + key_debug
            logger.debug("data lookup: %s => %s", key_debug, value)

            return value

        return _get_value

    def make_getter_2(
        parameter_code: ParameterCodeType,
    ) -> ParameterGetter:
        has_global_default = DataHandler.get_dimension("parameter").at[
            parameter_code, "has_global_default"
        ]

        default_value: float = DataHandler.PARAMETER_DEFAULTS.get(parameter_code, 0)

        _get_value_ = make_getter(
            parameter_code=parameter_code, use_global_default=False
        )
        _get_value_global_default = make_getter(
            parameter_code=parameter_code, use_global_default=True
        )

        def get_value(
            process_code: ProcessCodeType | None = None,
            flow_code: FlowCodeType | None = None,
            **kwargs,
        ) -> float:
            value = _get_value_(
                process_code=process_code, flow_code=flow_code, **kwargs
            )
            if value is None and has_global_default:
                value = _get_value_global_default(
                    process_code=process_code, flow_code=flow_code, **kwargs
                )
            if value is None:
                # TODO: get complete key
                # logger.warning("No data for %s", key) # noqa
                value = default_value

            return value

        return get_value

    return {
        parameter_code: make_getter_2(parameter_code)  # type: ignore
        for parameter_code in ParameterCodeValues  # type: ignore
    }


def _merge_process_data(
    parameters: ProcessDataType | None, parent_parameters: ProcessDataType | None = None
) -> ProcessDataType:
    return (parameters or {}) | (parent_parameters or {})
