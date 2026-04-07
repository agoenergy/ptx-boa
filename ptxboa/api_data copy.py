"""Handle data queries for api calculation."""

import logging
from dataclasses import asdict
from typing import Iterable, Literal, Union, cast

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from ptxboa import (
    api_calc,
    logger,
)
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
    ResultClassType,
    ResultCostType,
    SourceRegionCodeType,
    TargetCountryCodeType,
    TransportType,
)
from ptxboa.static._type_defs import (
    CalculateDataType,
    ChainDefStatic,
    DataQueryDicType,
    ParameterGetter,
    ParameterGetters,
    ProcessDataType,
    ProcessResultCostsType,
    ProcessResultEmissionType,
    ProcessResultFlowsType,
    ProcessStep,
    PtxCalcResult,
)
from tests.utils import (
    drop_null_nested,
)

ProcessStepsPipeline: set[ProcessStepType] = {
    "PPLS",
    "PPL",
    "PPLX",
    "PPLR",
}
ChainSegmentType = Literal["Export", "Transport", "Import"]


def _get_secproc_data(
    secondary_processes: dict,
    pg: "_ParameterGetter",
    has_ccs: bool,
    used_flows_main_export: set,
) -> tuple[dict, set, set]:
    result = {}
    used_flows_secondary: set[FlowCodeType] = set()
    provided_flows_secondary: set[FlowCodeType] = set()
    for flow_code, process_code in secondary_processes.items():
        if not process_code:
            continue
        if flow_code == "CO2-C":
            if not has_ccs:
                continue
        else:
            if flow_code not in used_flows_main_export:
                continue

        pp = pg.get_process_params(process_code)
        pp["process_code"] = process_code

        result[flow_code] = pp
        used_flows_secondary = used_flows_secondary | set(pp["CONV"])
        provided_flows_secondary.add(flow_code)

    return result, used_flows_secondary, provided_flows_secondary


class _ParameterGetter:
    def __init__(
        self,
        data_handler,
        source_region_code,
        target_country_code,
        process_res,
        process_ely,
        process_deriv,
        df_processes,
        df_flows,
        use_user_data: bool = True,
    ):
        self.data_handler = data_handler
        self.source_region_code = source_region_code
        self.target_country_code = target_country_code
        self.process_res = process_res
        self.process_ely = process_ely
        self.process_deriv = process_deriv
        self.df_processes = df_processes
        self.df_flows = df_flows
        self.use_user_data = use_user_data

    def get_parameter_value_w_default(
        self,
        parameter_code: ParameterCodeType,
        process_code: ProcessCodeType | Literal[""] = "",
        flow_code: FlowCodeType | Literal[""] = "",
        default: float | None = None,
    ):
        return self.data_handler._get_parameter_value(
            parameter_code=parameter_code,
            process_code=process_code,
            flow_code=flow_code,
            source_region_code=self.source_region_code,
            target_country_code=self.target_country_code,
            process_res=self.process_res,
            process_ely=self.process_ely,
            process_deriv=self.process_deriv,
            default=default,
            use_user_data=self.use_user_data,
        )

    def get_secondary_flows(self, process_code: ProcessCodeType) -> list[FlowCodeType]:
        flows = self.df_processes.loc[process_code, "secondary_flows"]
        flows = [x for x in flows if x]
        return flows

    def get_secondary_and_main_flows(
        self, process_code: ProcessCodeType
    ) -> list[FlowCodeType]:
        flows = self.get_secondary_flows(process_code)
        proc = self.df_processes.loc[process_code]
        for flow in [proc.main_flow_code_out, proc.main_flow_code_in]:
            if flow and flow not in flows:
                flows.append(flow)
        return list(flows)

    def get_flow_co2_params(
        self, process_code: ProcessCodeType, parameter_code: ParameterCodeType
    ) -> dict:
        result = {}
        flow_codes = self.get_secondary_and_main_flows(process_code)
        for flow_code in flow_codes:
            # new: loss can reduce the effective conversion rate
            value = self.get_parameter_value_w_default(
                parameter_code, flow_code=flow_code, default=0
            )
            if value:
                result[flow_code] = value
        return result

    def get_flow_co2_params_w_process(
        self, process_code: ProcessCodeType, parameter_code: ParameterCodeType
    ) -> dict:
        result = {}
        flow_codes = self.get_secondary_and_main_flows(process_code)
        for flow_code in flow_codes:
            # new: loss can reduce the effective conversion rate
            value = self.get_parameter_value_w_default(
                parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if value:
                result[flow_code] = value
        return result

    def get_flow_loss_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        for flow_code in self.get_secondary_flows(process_code):
            # new: loss can reduce the effective conversion rate
            loss = self.get_parameter_value_w_default(
                "LOSS", process_code=process_code, flow_code=flow_code, default=0
            )
            if loss:
                result[flow_code] = loss
        return result

    def get_flow_conv_params(
        self,
        process_code: ProcessCodeType,
        flow_loss_params: dict[FlowCodeType, float] | None = None,
    ) -> dict:
        flow_loss_params = flow_loss_params or {}
        result = {}
        for flow_code in self.get_secondary_flows(process_code):
            conv = self.get_parameter_value_w_default(
                parameter_code="CONV",
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if conv <= 0:
                # currently negative flows (i.e. additional output)
                # has no value
                continue

            # new: loss can reduce the effective conversion rate
            loss = flow_loss_params.get(flow_code)
            if loss:
                # see https://github.com/agoenergy/ptx-boa/issues/581
                conv = conv * (1 + loss)

            result[flow_code] = conv
        return result

    def get_flow_conv_ot_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        for flow_code in self.get_secondary_flows(process_code):
            conv_ot = self.get_parameter_value_w_default(
                parameter_code="CONV-OT",
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if conv_ot <= 0:
                continue
            result[flow_code] = conv_ot
        return result

    def get_process_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        result["EFF"] = self.get_parameter_value_w_default(
            "EFF",
            process_code=process_code,
            default=DataHandler.PARAMETER_DEFAULTS.get("EFF", 0),
        )
        # loss that effects main efficiency: get parameter for
        # main in flow
        main_flow_code_in = self.df_processes.loc[process_code, "main_flow_code_in"]

        # special case NG-PROD#B: has no main_flow_code_in
        if process_code == "NG-PROD#B":
            main_loss_param = self.get_parameter_value_w_default(
                "LOSS",
                process_code=process_code,
                flow_code=self.df_processes.loc[process_code, "main_flow_code_out"],
                default=0,
            )
        else:
            main_loss_param = self.get_parameter_value_w_default(
                "LOSS",
                process_code=process_code,
                flow_code=main_flow_code_in,
                default=0,
            )
        flow_loss_params = self.get_flow_loss_params(process_code)
        if main_loss_param:
            # see https://github.com/agoenergy/ptx-boa/issues/581
            result["EFF"] = result["EFF"] / (1 + main_loss_param)
            result["LOSS"] = main_loss_param

        result["FLH"] = self.get_parameter_value_w_default(
            "FLH",
            process_code=process_code,
            default=DataHandler.PARAMETER_DEFAULTS.get("FLH", 0),
        )
        result["LIFETIME"] = self.get_parameter_value_w_default(
            "LIFETIME",
            process_code=process_code,
            default=DataHandler.PARAMETER_DEFAULTS.get("LIFETIME", 20),
        )
        result["CAPEX"] = self.get_parameter_value_w_default(
            "CAPEX", process_code=process_code, default=0
        )  # TODO
        result["OPEX-F"] = self.get_parameter_value_w_default(
            "OPEX-F", process_code=process_code, default=0
        )
        result["OPEX-O"] = self.get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )
        result["CONV"] = self.get_flow_conv_params(
            process_code, flow_loss_params=flow_loss_params
        )
        if flow_loss_params:
            result["LOSS_FLOW"] = flow_loss_params

        # additional parameters for co2
        for param in ["CH4SHARE", "EF_M", "EF_E"]:
            value = self.get_flow_co2_params(
                process_code,
                parameter_code=param,  # type: ignore
            )
            if value:
                result[param] = value

        for param in ["CO2CPT-R", "CO2CPT-S", "CBOUND"]:
            value = self.get_flow_co2_params_w_process(
                process_code,
                parameter_code=param,  # type: ignore
            )
            if value:
                result[param] = value

        return result

    def get_transport_process_params(
        self, process_code: ProcessCodeType, dist_transport: float
    ) -> dict:
        result = {}

        loss_t = self.get_parameter_value_w_default(
            "LOSS-T", process_code=process_code, default=0
        )
        result["DIST"] = dist_transport  # TODO: `DIST` not official parameter
        result["EFF"] = 1 - loss_t * dist_transport
        result["OPEX-T"] = self.get_parameter_value_w_default(
            "OPEX-T", process_code=process_code, default=0
        )
        result["OPEX-O"] = self.get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )
        # CONV-OT => CONV? FIXME
        result["CONV-OT"] = self.get_flow_conv_ot_params(process_code)
        result["CONV"] = self.get_flow_conv_params(process_code)
        return result

    def get_flow_params(
        self,
        parameter_code: ParameterCodeType,
        flow_codes: Iterable[FlowCodeType],
        defaults: None | dict = None,
    ):
        defaults = defaults or {}
        result = {}
        for flow_code in flow_codes:
            result[flow_code] = self.get_parameter_value_w_default(
                parameter_code, flow_code=flow_code, default=defaults.get(flow_code)
            )
        return result

    def get_flow_params_for_proc_if_exist(
        self, parameter_code: ParameterCodeType, flow_codes: Iterable[FlowCodeType]
    ):
        result = {}
        for flow_code in flow_codes:
            value = self.get_parameter_value_w_default(
                parameter_code,
                flow_code=flow_code,
                default=0,
            )
            if value:
                result[flow_code] = value
        return result


AggregateProcessDataType = tuple[ProcessDataType, dict["Process", ProcessDataType]]


def _plot_get_pos(
    chain_process: "AggregateProcess",
) -> dict["AbstractProcess", tuple[float, float]]:

    node_pos = {}
    xs: list[float] = [0, 0, 0]
    proc_end_last = None

    for ex_tr_imp in chain_process.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp._process_graph

        # add processes as nodes to DiGraph

        xs[1] = max(xs[0] + 0.25, xs[0])  # stagger
        xs[2] = max(xs[0], xs[2])

        sgn = 1  # secondary process: offset sign should alternate between -1 and 1

        for process in reversed(list(process_graph.all_processes_ordered_backwards)):
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

        if process_graph.main_processes:
            proc_end_last = process_graph.main_processes[-1]

    return node_pos


class ProcessType:
    def __init__(
        self,
        process_code: ProcessCodeType,
        result_process_type: ResultClassType,
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
        self.result_process_type: ResultClassType = result_process_type
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
        self.parent_process = parent_process
        self.process_step: ProcessStepType | str | None = process_step

        self._links_out_main: list["AbstractProcess"] = []
        self._links_out_secondary: list["AbstractProcess"] = []
        self._link_in_main: Union["AbstractProcess", None] = None
        self._links_in_secondary: dict[FlowCodeType, "AbstractProcess"] = {}

    @property
    def is_last(self) -> bool:
        return False

    @property
    def links_out(self) -> Iterable[tuple["AbstractProcess", bool]]:
        for p in self._links_out_main:
            yield p, True
        for p in self._links_out_secondary:
            yield p, False

    def _get_main_flow_out(self) -> float:
        """Value of main out flow."""
        return None  # type: ignore

    def _get_main_flow_in(self) -> float:
        """Value of calculated main in flow."""
        return None  # type: ignore

    def _get_secondary_flow_in(self, flow_code: FlowCodeType) -> float:
        """Value of calculated secondary in flow for given flow type."""
        return None  # type: ignore

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

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType:
        """Load parameter data for this process."""
        data: ProcessDataType = {}
        # load parameters that are process dependent
        for p in self._parameter_codes_process:
            data[p] = parameter_getters[p](
                process_code=self.process_code, flow_code=None, **parameter_values
            )

        # load parameters that are process and flow dependent
        for p in self._parameter_codes_process_flow:
            data[p] = {
                f: parameter_getters[p](
                    process_code=self.process_code, flow_code=f, **parameter_values
                )
                for f in self._parameter_flow_types
            }

        return data

    def _get_calculation_data_from_chain(
        self,
        data_by_process_step: dict[ProcessStepType, ProcessDataType],
        data_parameter: ProcessDataType,
        data_secondary_process: dict[FlowCodeType, ProcessDataType],
    ) -> ProcessDataType:
        # TODO: this is really ugly, but we need it as a legacy to the
        # old data structure

        # main processes: get data py process_step
        # OR: we could also get it by process_code, but we have no
        # builtin check that they have to be unique.
        # on the other hand, process_step mightalso not be unique later on.

        # grab WACC from parameters

        # FIXME: special case: for compatibility with older chain: we dopped
        # pipeline steps with DIST=0

        # secondary process: grab by flow_code out

        # market process: only grab SPECCOST
        raise NotImplementedError(type(self))

    def calculate_flows(
        self,
        process_data: ProcessDataType,
        results_flows: dict["AbstractProcess", ProcessResultFlowsType],
    ) -> ProcessResultFlowsType:
        """Calculate all process values based on desired output flow."""
        raise NotImplementedError()

    def __str__(self):
        step = f"{self.process_step}=" if self.process_step else ""
        return f"{self.__class__.__name__}({step}{self.process_code})"


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
    def is_import_region(self) -> bool:
        return self.parent_process._is_import_region

    def create_result_cost(
        self, cost_type: ResultCostType, values: float, flow: float
    ) -> ProcessResultCostsType:
        return ProcessResultCostsType(
            process_type=self.result_process_type,
            process_subtype=self.process_code,
            cost_type=cost_type,
            values=values,
            value_rel_per_flow=values / flow if flow else 0,
        )

    @property
    def result_process_type(self) -> ResultClassType:
        """Result process type."""
        return self._process_type.result_process_type  # type:ignore

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

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType:
        """Get parameter data for this process."""
        data = super().get_calculation_data(
            parameter_getters=parameter_getters, parameter_values=parameter_values
        )

        # changes

        if "LOSS" in data:
            data["LOSS_FLOW"] = data.pop("LOSS")
            if "EFF" in data and self.main_flow_code_in_or_out in data["LOSS_FLOW"]:  # type: ignore # noqa
                data["LOSS"] = data["LOSS_FLOW"].pop(  # type: ignore
                    self.main_flow_code_in_or_out
                )
            # update EFF and CONV for losses
            # TODO: keep original values for information purposes
            # NOTE: calculation: see https://github.com/agoenergy/ptx-boa/issues/581
            if "LOSS" in data:
                eff_original = data["EFF"]
                data["EFF"] = eff_original / (1 + data["LOSS"])  # type: ignore # noqa

        if "LOSS_FLOW" in data and "CONV" in data:
            # LOSS for CONV (if value exists in both)
            loss_flows = data.get("LOSS_FLOW", {})
            convs = data.get("CONV", {})
            for fc in set(loss_flows) & set(convs):  # type: ignore
                conv_orig = convs[fc]  # type: ignore
                data["CONV"][fc] = conv_orig * (1 + loss_flows[fc])  # type: ignore # noqa

        # FIXME: only for temporary test comparison?
        if (
            any(data.get("CO2CPT-R", {}).values())  # type: ignore
            or any(data.get("CO2CPT-S", {}).values())  # type: ignore
        ) and self.process_code != "CCGT-CC#B":
            logger.warning("TODO: remove dummy CONV for CO2-C")
            data["CONV"]["CO2-C"] = 1  # type: ignore

        # CONV/CONV-OT drop <= 0
        for parameter_code in ["CONV", "CONV-OT"]:
            data[parameter_code] = {
                k: v
                for k, v in data[parameter_code].items()  # type: ignore should be dict
                if v and v > 0
            }

        return data

    def _get_calculation_data_from_chain(
        self,
        data_by_process_step: dict[ProcessStepType, ProcessDataType],
        data_parameter: ProcessDataType,
        data_secondary_process: dict[FlowCodeType, ProcessDataType],
    ) -> ProcessDataType:

        data = data_by_process_step[self.process_step]  # type: ignore
        # add WACC
        data["WACC"] = data_parameter["WACC"]
        return data

    @property
    def is_last(self) -> bool:
        # FIXME: better way
        return not self._links_out_main and not self._links_out_secondary

    def calculate_flows(
        self,
        process_data: ProcessDataType,
        results_flows: dict["AbstractProcess", ProcessResultFlowsType],
    ) -> ProcessResultFlowsType:
        """Calculate all process values based on desired output flow."""
        # calculate flows

        main_flow_out = (
            1
            if self.is_last
            else _get_sum_main_flow_out(process=self, results_flows=results_flows)
        )

        eff: float = process_data.get("EFF")  # type: ignore

        if not eff:
            if not self.is_secondary:
                logger.error("EFF = %s: %s", eff, self)
                eff = 1
        if not eff:
            main_flow_in = None
        else:
            main_flow_in = main_flow_out / eff

        secondary_flows_in = {}
        convs = process_data.get("CONV", {})  # type: ignore
        for fc in self.secondary_flow_types:
            conv: float = convs.get(fc, 0)  # type: ignore
            value = main_flow_out * conv
            if value < 0:  # ignore (e.g. exothermal heat)
                value = 0
            secondary_flows_in[fc] = value

        # calculate cost

        return ProcessResultFlowsType(
            main_flow_out=main_flow_out,
            main_flow_in=main_flow_in,
            secondary_flows_in=secondary_flows_in,
        )

    def _get_calculate_costs_market(
        self,
        process_parameters: ProcessDataType,
        result_flows: ProcessResultFlowsType,
        result_costs: dict[
            AbstractProcess, ProcessResultCostsType | list[ProcessResultCostsType]
        ],
    ) -> list[ProcessResultCostsType]:
        results = []
        for flow_code, process_market in self._links_in_secondary.items():
            if not isinstance(process_market, MarketProcess):
                continue
            flow = result_flows.secondary_flows_in[flow_code]
            if not flow:
                continue
            result_costs[process_market].values

        return results

    def calculate_costs(
        self,
        process_parameters: ProcessDataType,
        result_flows: ProcessResultFlowsType,
        result_costs: dict[
            AbstractProcess, ProcessResultCostsType | list[ProcessResultCostsType]
        ],
    ) -> list[ProcessResultCostsType]:
        """Calculate costs."""
        parameters = process_parameters
        lifetime: int = parameters["LIFETIME"]  # type: ignore
        flh: float = parameters["FLH"]  # type: ignore
        capex_rel: float = parameters["CAPEX"]  # type: ignore
        opex_f: float = parameters["OPEX-F"]  # type: ignore
        opex_o: float = parameters["OPEX-O"]  # type: ignore
        wacc: float = parameters["WACC"]  # type: ignore
        main_flow_out: float = result_flows.main_flow_out

        if "CAP_F" in parameters:
            # Storage unit: capacity
            # TODO: double check units (division by 8760 h)?
            cap_f: float = parameters["CAP_F"]  # type: ignore
            capacity = main_flow_out * cap_f / 8760
        else:
            capacity = main_flow_out / flh

        capex = capacity * capex_rel
        capex_ann = api_calc.annuity(wacc, lifetime, capex)
        opex = opex_f * capacity + opex_o * main_flow_out

        return [
            self.create_result_cost(cost_type="OPEX", values=opex, flow=main_flow_out),
            self.create_result_cost(
                cost_type="CAPEX", values=capex_ann, flow=main_flow_out
            ),
        ] + self._get_calculate_costs_market()

    def calculate_emissions(
        self,
        process_parameters: dict[AbstractProcess, ProcessDataType],
        result_flows: dict[AbstractProcess, ProcessResultFlowsType],
        result_emissions: dict[AbstractProcess, ProcessResultEmissionType],
    ) -> ProcessResultEmissionType:
        """Calculate emissions."""
        return ProcessResultEmissionType()


class TransportProcess(Process):
    _parameter_codes_process = ["OPEX-T", "LOSS-T", "OPEX-O"]
    color = "teal"

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType:
        """Get parameter data for this process."""
        data = super().get_calculation_data(
            parameter_getters=parameter_getters, parameter_values=parameter_values
        )

        # FIXME: we very inefficiently get transport distances every time
        # from parent node

        # FIXME: instead of parent_process(None) -> explicitly link to
        # transport section
        data_all_transports = self.parent_process.get_calculation_data(  # type: ignore
            parameter_getters=parameter_getters, parameter_values=parameter_values
        )
        dist_transport = data_all_transports["DIST"].get(self.process_step, 0)  # type: ignore # noqa

        loss_t = data.get("LOSS-T", 0)

        data["EFF"] = 1 - loss_t * dist_transport
        data["DIST"] = dist_transport

        # FIXME: OPEX-O in transport?
        return data

    def calculate_costs(
        self,
        process_parameters: ProcessDataType,
        result_flows: ProcessResultFlowsType,
        result_costs: dict[
            AbstractProcess, ProcessResultCostsType | list[ProcessResultCostsType]
        ],
    ) -> list[ProcessResultCostsType]:
        """Calculate costs."""
        parameters = process_parameters

        opex_t: float = parameters.get("OPEX-T", 0)  # type: ignore
        dist_transport: float = parameters.get("DIST", 0)  # type: ignore
        opex_o: float = parameters.get("OPEX-O", 0)  # type: ignore

        main_flow_out: float = result_flows.main_flow_out

        opex_ot = opex_t * dist_transport
        opex = (opex_o + opex_ot) * main_flow_out

        # get specccost
        speccost_sum = 0
        for flow_code, process_market in self._links_in_secondary.items():
            if not isinstance(process_market, MarketProcess):
                continue
            flow = result_flows.secondary_flows_in[flow_code]
            speccost: float = process_parameters[process_market]["SPECCOST"][flow_code]  # type: ignore # noqa
            speccost_sum += speccost * flow

        return [
            self.create_result_cost(cost_type="OPEX", values=opex, flow=main_flow_out)
        ] + self._get_calculate_costs_market()


class StorageProcess(Process):
    color = "lightsteelblue"


class SecondaryProcess(Process):
    color = "lightgreen"

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return True

    def _get_calculation_data_from_chain(
        self,
        data_by_process_step: dict[ProcessStepType, ProcessDataType],
        data_parameter: ProcessDataType,
        data_secondary_process: dict[FlowCodeType, ProcessDataType],
    ) -> ProcessDataType:

        data = data_secondary_process[self.main_flow_code_out]
        # add WACC
        data["WACC"] = data_parameter["WACC"]
        return data


class InitialProcess(SecondaryProcess):
    color = "skyblue"

    # FIXME: should not be subclass of SecondaryProcess
    def _get_calculation_data_from_chain(
        self,
        data_by_process_step: dict[ProcessStepType, ProcessDataType],
        data_parameter: ProcessDataType,
        data_secondary_process: dict[FlowCodeType, ProcessDataType],
    ) -> ProcessDataType:
        data = data_by_process_step[self.process_step]  # type: ignore
        # add WACC
        data["WACC"] = data_parameter["WACC"]
        return data


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

    def calculate_flows(
        self,
        process_data: ProcessDataType,
        results_flows: dict["AbstractProcess", ProcessResultFlowsType],
    ) -> ProcessResultFlowsType:
        """Calculate results."""
        main_flow_out = (
            1
            if self.is_last
            else _get_sum_main_flow_out(process=self, results_flows=results_flows)
        )
        return ProcessResultFlowsType(
            main_flow_out=main_flow_out, main_flow_in=None, secondary_flows_in={}
        )

    def calculate_costs(
        self,
        process_parameters: ProcessDataType,
        result_flows: ProcessResultFlowsType,
        result_costs: dict[
            AbstractProcess, ProcessResultCostsType | list[ProcessResultCostsType]
        ],
    ) -> list[ProcessResultCostsType]:
        """Calculate costs."""

        speccost: float = process_parameters["SPECCOST"][self.main_flow_code_out]  # type: ignore # noqa
        main_flow_out: float = result_flows.main_flow_out

        return [
            ProcessResultCostsType(
                # process_type: ResultClassType = # TODO? # noqa
                # process_subtype=self.main_flow_code_out, # noqa
                cost_type="FLOW",
                values=speccost * main_flow_out,
                value_rel_per_flow=speccost,
            )
        ]

    def calculate_emissions(
        self,
        process_parameters: dict[AbstractProcess, ProcessDataType],
        result_flows: dict[AbstractProcess, ProcessResultFlowsType],
        result_emissions: dict[AbstractProcess, ProcessResultEmissionType],
    ) -> ProcessResultEmissionType:
        """Calculate emissions."""
        return ProcessResultEmissionType()

    def _get_calculation_data_from_chain(
        self,
        data_by_process_step: dict[ProcessStepType, ProcessDataType],
        data_parameter: ProcessDataType,
        data_secondary_process: dict[FlowCodeType, ProcessDataType],
    ) -> ProcessDataType:

        return {
            "SPECCOST": {
                self.main_flow_code_out: data_parameter.get("SPECCOST", {}).get(  # type: ignore # noqa
                    self.main_flow_code_out
                )
            }
        }

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
) -> list[tuple[type["ChainSection"], int, int]]:
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
        (ChainSectionExport, 0, idx_transport_start),
        (ChainSectionTransport, idx_transport_start, idx_transport_end),
        (ChainSectionImport, idx_transport_end, len(main_process_codes_steps)),
    ]


class AggregateProcess(AbstractProcess):
    def __init__(
        self,
        process_graph: "ProcessGraph",
        process_step: str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
        self._process_graph: "ProcessGraph" = process_graph

    def get_first_main_process_by_step(self, step: ProcessStepType) -> Process:
        """May raise Exception."""
        # TODO: faster if we create lookup dict first
        return next(
            cast(Process, p) for p in self.full_main_chain if p.process_step == step
        )

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self.main_processes[-1].main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self.main_processes[0].main_flow_code_in

    @property
    def full_main_chain(self) -> list[Process]:
        """List of the entire main chain."""
        result: list[Process] = []
        for proc in self.main_processes:
            if isinstance(proc, AggregateProcess):
                result += proc.full_main_chain
            else:
                result.append(proc)  # type: ignore - should be Process

        return result

    @property
    def main_processes(self) -> list[AbstractProcess]:
        """List all main proceeses."""
        return self._process_graph.main_processes

    @property
    def all_processes(self) -> Iterable[AbstractProcess]:
        """List of all processes."""
        return self.all_processes_ordered_forwards

    @property
    def all_processes_ordered_backwards(self) -> Iterable[AbstractProcess]:
        """List of all processes."""
        return self._process_graph.all_processes_ordered_backwards

    @property
    def all_processes_ordered_forwards(self) -> Iterable[AbstractProcess]:
        """List of all processes."""
        return self._process_graph.all_processes_ordered_forwards

    @property
    def secondary_processes(self) -> list[SecondaryProcess]:
        """List of all secondary processes."""
        result: list[SecondaryProcess] = []
        for proc in self.all_processes:
            if isinstance(proc, AggregateProcess):
                result += proc.secondary_processes  # recursion
            elif (
                proc.is_secondary
                # NOTE initial is modelled as secondary (because it has no inflow)
                and not proc.is_initial
            ):
                result.append(proc)  # type: ignore should be SecondaryProcess

        return result

    @property
    def secondary_processes_by_flow_code(self) -> dict[FlowCodeType, SecondaryProcess]:
        """List of all secondary processes."""
        return {p.main_flow_code_out: p for p in self.secondary_processes}

    @property
    def market_processes_by_flow_code(self) -> dict[FlowCodeType, MarketProcess]:
        """List of all secondary processes."""
        return {
            p.main_flow_code_out: p
            for p in self.all_processes
            if isinstance(p, MarketProcess)
        }

    @property
    def main_processes_by_step(self) -> dict[ProcessStepType | str, AbstractProcess]:
        """If exists: get process by step code."""
        return {p.process_step: p for p in self.main_processes if p.process_step}

    def get_subprocesses_by_class(
        self, class_or_classes: type | tuple[type]
    ) -> list[AbstractProcess]:
        """Get subprocesses byclass."""
        return [p for p in self.all_processes if isinstance(p, class_or_classes)]

    def plot(self, file_basename: str, result_flows: dict):
        """Create plot and save as png."""
        # Create a directed graph
        G = nx.DiGraph()
        node_labels = {}
        edge_labels = {}
        edge_widths = {}

        proc_end_last = None
        len_main_total = 0
        for ex_tr_imp in self.main_processes:
            ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
            # export / tranport / import  subgraph

            process_graph = ex_tr_imp._process_graph

            # add processes as nodes to DiGraph

            for process in reversed(list(ex_tr_imp.all_processes)):
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
                            result_flows[proc_target].main_flow_in
                            if in_main
                            else result_flows[proc_target].secondary_flows_in.get(flow)
                        )
                        value_str = f"\n{value:.2E}"
                    except Exception:
                        value_str = ""
                    edge_labels[e] = f"{flow}{value_str}"
                    edge_widths[e] = 2 if in_main else 1

            if process_graph.main_processes:
                if proc_end_last:
                    # link from previous subpgraph
                    proc_start = process_graph.main_processes[0]
                    e = (proc_end_last, proc_start)
                    G.add_edge(*e)
                    edge_labels[e] = proc_end_last.main_flow_code_out
                    try:
                        edge_labels[
                            e
                        ] += f"\n{result_flows[proc_start].main_flow_in:.2E}"
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


class Chain(AggregateProcess):
    _instances: dict[object, "Chain"] = {}

    @property
    def all_processes_ordered_backwards(self) -> list[AbstractProcess]:
        """All processes backwards."""
        result: list[AbstractProcess] = []
        section: ChainSection
        for section in [
            self.section_import,
            self.section_transport,
            self.section_export,
        ]:
            result += list(section.all_processes_ordered_backwards)
        return result

    @property
    def all_processes_ordered_forwards(self) -> list[AbstractProcess]:
        """All processes forward."""
        result: list[AbstractProcess] = []
        section: ChainSection
        for section in [
            self.section_export,
            self.section_transport,
            self.section_import,
        ]:
            result += list(section.all_processes_ordered_forwards)
        return result

    @classmethod
    def get_or_create(cls, chain_def: ChainDefStatic) -> "Chain":
        """Get or create static instance."""
        key = chain_def.unique_key
        if key not in cls._instances:
            cls._instances[key] = cls._create(chain_def)
        return cls._instances[key]

    def calculate(self, data: CalculateDataType) -> PtxCalcResult:
        """Calcualte results."""
        process_parameters = self._get_process_parameters(data=data)

        result_flows = self.calculate_flows(process_parameters=process_parameters)
        result_costs = self.calculate_costs(
            process_parameters=process_parameters, result_flows=result_flows
        )
        result_emissions = self.calculate_emissions(
            process_parameters=process_parameters, result_flows=result_flows
        )

        result = PtxCalcResult(
            df_results_cost=_create_df_results_cost(result_costs=result_costs),
            df_results_emissions_e_g_co2e=_create_df_results_emissions_e_g_co2e(
                result_emissions=result_emissions
            ),
            df_results_emissions_m_g_co2e=_create_df_results_emissions_m_g_co2e(
                result_emissions=result_emissions
            ),
            results_flows_chain=_create_results_flows_chain(result_flows=result_flows),
            results_flows_secondary=_create_results_flows_secondary(
                result_flows=result_flows
            ),
        )

        return result

    def _get_process_parameters(
        self, data: CalculateDataType
    ) -> dict[AbstractProcess, ProcessDataType]:
        # iterate over all subprocesses in correct order
        # (last to first)
        # aggregate results in output format

        # TODO: it would be nicer to have one Graph, instead of 3 subgraphs
        # for export, transport, import

        results: dict[AbstractProcess, ProcessDataType] = {}

        data_by_process_step: dict[ProcessStepType, ProcessDataType] = {}
        for x in (
            data["main_export_process_chain"]
            + data["main_transport_process_chain"]
            + data["main_import_process_chain"]
        ):
            step = x.get("step")
            if not step:
                logger.error("empty process_step for %s", x.get("process_code"))
                continue
            elif step in data_by_process_step:
                logger.error(
                    "duplicate process_step %s, for %s", step, x.get("process_code")
                )
                continue
            data_by_process_step[step] = x
        # FIXME: see ProcessStepsPipeline
        for step in ProcessStepsPipeline:
            if step not in data_by_process_step:
                # add dummy data
                data_by_process_step[step] = {"EFF": 1}

        # section: ChainSectionProcess
        # for section in [
        #    self.section_import,
        #    self.section_transport,
        #    self.section_export,
        # ]:
        for process in self.all_processes_ordered_backwards:
            is_import = process.is_import_region
            data_parameter = (
                data["parameter_import"] if is_import else data["parameter"]
            )
            data_secondary_process = (
                data["secondary_process_import"]
                if is_import
                else data["secondary_process"]
            )

            process_data = process._get_calculation_data_from_chain(
                data_by_process_step=data_by_process_step,
                data_parameter=data_parameter,
                data_secondary_process=data_secondary_process,
            )
            results[process] = process_data  # type: ignore
        return results

    def calculate_flows(
        self, process_parameters: dict[AbstractProcess, ProcessDataType]
    ) -> dict[AbstractProcess, ProcessResultFlowsType]:
        """Calcualte results."""
        # iterate over all subprocesses in correct order
        # (last to first)
        # aggregate results in output format

        # TODO: it would be nicer to have one Graph, instead of 3 subgraphs
        # for export, transport, import

        results_flows: dict[AbstractProcess, ProcessResultFlowsType] = {}

        # all_processes_ordered_backwards ensures that process.calculate()
        # is only called if all that depend on it have been already calculated.
        for process in self.all_processes_ordered_backwards:
            process_result = process.calculate_flows(
                process_data=process_parameters[process], results_flows=results_flows
            )
            if not process_result.main_flow_out:
                logger.warning(f"main_flow_out = 0 for {process}")

            assert process not in results_flows  # FIXME: remove later
            results_flows[process] = process_result

        return results_flows

    def calculate_costs(
        self,
        process_parameters: dict[AbstractProcess, ProcessDataType],
        result_flows: dict[AbstractProcess, ProcessResultFlowsType],
    ) -> dict[AbstractProcess, list[ProcessResultCostsType]]:
        """Calculate costs."""

        result_costs: dict[
            AbstractProcess, ProcessResultCostsType | list[ProcessResultCostsType]
        ] = {}
        for p in self.all_processes_forwards:
            result_costs[p] = p.calculate_costs(
                process_parameters=process_parameters[p],
                result_flows=result_flows[p],
                result_costs=result_costs,
            )

        return result_costs

    def calculate_emissions(
        self,
        process_parameters: dict[AbstractProcess, ProcessDataType],
        result_flows: dict[AbstractProcess, ProcessResultFlowsType],
    ) -> dict[AbstractProcess, ProcessResultEmissionType]:
        """Calculate emissions."""
        # processes need previously calcualted emissions
        result_emissions: dict[AbstractProcess, ProcessResultEmissionType] = {}

        for p in self.all_processes_forwards:
            result_emissions[p] = p.calculate_emissions(
                process_parameters=process_parameters,
                result_flows=result_flows,
                result_emissions=result_emissions,
            )

        return result_emissions

    @classmethod
    def _create(cls, chain_def: ChainDefStatic) -> "Chain":
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
            first_process_code = chain_def.process_res  # type: ignore

        return Chain(
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
        self._process_res_ely_deriv: DataQueryDicType = {
            "process_res": (first_process_code if chain_start_with_res else None),
            "process_ely": chain_data["ELY"],
            "process_deriv": chain_data["DERIV"],
        }

        check_use_all_main_process_codes = []

        # FIXME: pre/post shipping processes, remove not required

        main_processes: list[AbstractProcess] = []

        for ChainSectionProcessClass, i, j in _get_chain_sections(
            main_process_codes_steps=main_process_codes_steps_filtered
        ):
            main_process_codes_steps_part: list["ProcessStep"] = (
                main_process_codes_steps_filtered[i:j]
            )

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

            # only import may be empty
            if not main_process_codes_steps_part:
                if ChainSectionProcessClass is ChainSectionImport:
                    flow_code = main_processes[-1].main_flow_code_out
                    process = ChainSectionImportDummy(
                        flow_code=flow_code, parent_process=self
                    )
                else:
                    raise Exception("Empty chain")
            else:
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

        self.section_export: ChainSectionExport = main_processes[0]  # type:ignore
        self.section_transport: ChainSectionTransport = main_processes[1]  # type:ignore
        self.section_import: ChainSectionImport = main_processes[2]  # type:ignore

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
        todo_transport_re_post_as_transport: bool = True,
    ) -> CalculateDataType:
        """Get calculation data."""
        # FIXME: speedup later with new parameter_getters
        # parameter_getters = _create_parameter_getters_TODO( # noqa
        #    data_handler=data_handler, use_user_data=use_user_data  # noqa
        # )  # noqa

        def make_parameter_getters(parameter_code):
            default = data_handler.PARAMETER_DEFAULTS.get(parameter_code, 0)

            def x(**kwargs):
                return data_handler._get_parameter_value(
                    parameter_code=parameter_code,
                    **kwargs,
                    default=default,
                    use_user_data=use_user_data,
                )

            return x

        parameter_getters = {}
        for p in ParameterCodeValues:
            parameter_getters[p] = make_parameter_getters(p)

        def _add_step_and_code(
            process: AbstractProcess, data: ProcessDataType
        ) -> ProcessDataType:
            return data | {  # type: ignore
                "process_code": process.process_code,
                "step": process.process_step,
            }

        # _process_res_ely_deriv: for FLH lookup
        parameter_values: DataQueryDicType = self._process_res_ely_deriv
        parameter_values_export: DataQueryDicType = parameter_values | cast(
            DataQueryDicType, {"source_region_code": source_region_code}
        )
        parameter_values_transport: DataQueryDicType = parameter_values | cast(
            DataQueryDicType,
            {
                "source_region_code": source_region_code,
                "target_country_code": target_country_code,
            },
        )
        parameter_values_import: DataQueryDicType = parameter_values | cast(
            DataQueryDicType,
            {"source_region_code": target_country_code},  # NOTE: switched in import
        )

        main_export_process_chain_procs = self.section_export.main_processes
        main_transport_process_chain_procs = self.section_transport.main_processes
        main_import_process_chain_procs = self.section_import.main_processes

        if todo_transport_re_post_as_transport:
            # FIXME: remove after validation:
            # move PRE/POST into transport
            pps_pre = [
                p
                for p in main_export_process_chain_procs
                if p.process_step in {"PRE_PPL", "PRE_SHP"}
            ]
            main_export_process_chain_procs = [
                p
                for p in main_export_process_chain_procs
                if p.process_step not in {"PRE_PPL", "PRE_SHP"}
            ]
            pps_post = [
                p
                for p in main_import_process_chain_procs
                if p.process_step in {"POST_PPL", "POST_SHP"}
            ]
            main_import_process_chain_procs = [
                p
                for p in main_import_process_chain_procs
                if p.process_step not in {"POST_PPL", "POST_SHP"}
            ]
            main_transport_process_chain_procs = (
                pps_pre + main_transport_process_chain_procs + pps_post
            )

        main_export_process_chain = [
            _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values_export,
                ),
            )
            for p in main_export_process_chain_procs
        ]

        main_transport_process_chain = [
            _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values_transport,
                ),
            )
            for p in main_transport_process_chain_procs
        ]
        # FIXME: compatibility with old test - should we keep it?
        # remove pipeline steps without DIST.
        # in new system, statically created chains will still have those
        # but they should not create any cost
        main_transport_process_chain = [
            x
            for x in main_transport_process_chain
            if x.get("DIST") or (x["step"] not in ProcessStepsPipeline)
        ]

        main_import_process_chain = [
            _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values_import,
                ),
            )
            for p in main_import_process_chain_procs
        ]

        secondary_process = {
            f: _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values_export,
                ),
            )
            for f, p in self.section_export.secondary_processes_by_flow_code.items()
        }

        secondary_process_import = {
            f: _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values_import,
                ),
            )
            for f, p in self.section_import.secondary_processes_by_flow_code.items()
        }

        market_process = {  # for export + transport
            f: p.get_calculation_data(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values_export,
            )
            for f, p in self.section_export.market_processes_by_flow_code.items()
        } | {
            f: p.get_calculation_data(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values_export,
            )
            for f, p in self.section_transport.market_processes_by_flow_code.items()
        }

        market_process_i = {
            f: p.get_calculation_data(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values_import,
            )
            for f, p in self.section_import.market_processes_by_flow_code.items()
        }

        parameter = self.section_export.get_calculation_data(
            parameter_getters=parameter_getters,
            parameter_values=parameter_values_export,
        ) | {
            "SPECCOST": {f: d["SPECCOST"][f] for f, d in market_process.items()}  # type: ignore # noqa
        }
        parameter_import = self.section_import.get_calculation_data(
            parameter_getters=parameter_getters,
            parameter_values=parameter_values_import,
        ) | {
            "SPECCOST": {
                f: d["SPECCOST"][f]  # type: ignore # noqa
                for f, d in market_process_i.items()
            }
        }

        # FIXME: remove later: always add SPECCOST for EL
        speccosts_required_for_opt: list[FlowCodeType] = ["EL"]
        flow_code: FlowCodeType
        for flow_code in speccosts_required_for_opt:
            if flow_code not in parameter["SPECCOST"]:  # type: ignore # noqa: assume its dict
                parameter["SPECCOST"][flow_code] = MarketProcess(  # type: ignore # noqa: assume its dict
                    main_flow_code_out=flow_code
                ).get_calculation_data(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values_export,
                )[
                    "SPECCOST"
                ][
                    flow_code
                ]  # type: ignore # noqa: assume its dict

        flh_opt_process = {}

        # FIXME: we only need these for optimize_flh,
        # but old tests require them always
        # if optimize_flh: # noqa
        if True:
            # api_optimize.py: always wants SPECCOST for certain flows
            speccosts_required_for_opt: list[FlowCodeType] = [
                "CO2-G",
                "H2O-L",
                "HEAT",
                "N2-G",
            ]
            flow_code: FlowCodeType
            for flow_code in speccosts_required_for_opt:
                if flow_code not in parameter["SPECCOST"]:  # type: ignore # noqa: assume its dict
                    parameter["SPECCOST"][flow_code] = MarketProcess(  # type: ignore # noqa: assume its dict
                        main_flow_code_out=flow_code
                    ).get_calculation_data(
                        parameter_getters=parameter_getters,
                        parameter_values=parameter_values_export,
                    )[
                        "SPECCOST"
                    ][
                        flow_code
                    ]  # type: ignore # noqa: assume its dict

            # when optimzing for RES=RES-HYBR, optimizer needs data for
            # "PV-FIX" and "WIND-ON"
            if main_export_process_chain[0]["process_code"] == "RES-HYBR":
                procs_required_for_opt: list[ProcessCodeType] = ["PV-FIX", "WIND-ON"]
                for process_code in procs_required_for_opt:
                    flh_opt_process[process_code] = Process(
                        process_code=process_code
                    ).get_calculation_data(
                        parameter_getters=parameter_getters,
                        parameter_values=parameter_values_export,
                    )

        # FIXME remove later or update test data
        # gapfill parameter_import from parameter, old data did not have some parameters
        # for import countries
        parameter_import = drop_null_nested(parameter_import)
        parameter_import = parameter | parameter_import  # type: ignore
        for key in ["SPECCOST"]:
            parameter_import[key] = parameter[key] | parameter_import[key]  # type: ignore # noqa

        result: CalculateDataType = {
            "context": {
                "source_region_code": source_region_code,
                "target_country_code": target_country_code,
            },
            "parameter": parameter,
            "parameter_import": parameter_import,
            "main_export_process_chain": main_export_process_chain,
            "main_transport_process_chain": main_transport_process_chain,
            "main_import_process_chain": main_import_process_chain,
            "secondary_process": secondary_process,
            "secondary_process_import": secondary_process_import,
            "flh_opt_process": flh_opt_process,
        }

        return result


class ChainSection(AggregateProcess):
    # FIXME: should we remove it later?

    _parameter_codes_process = ["WACC"]  # different in export / import
    _is_import_region: bool = False

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


class ChainSectionExport(ChainSection):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_export


class ChainSectionImport(ChainSection):
    _is_import_region: bool = True

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_import


class ChainSectionImportDummy(ChainSectionImport):
    def __init__(
        self,
        flow_code: FlowCodeType,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(
            main_process_codes_steps=[],
            secondary_process_codes=set(),
            parent_process=parent_process,
        )
        self._flow_code_in_out: FlowCodeType = flow_code

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._flow_code_in_out

    @property
    def main_flow_code_in(self) -> FlowCodeType:
        """Main flow code in."""
        return self._flow_code_in_out


class ChainSectionTransport(ChainSection):
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

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType:
        """Get parameter data for this process."""
        data = super().get_calculation_data(
            parameter_getters=parameter_getters, parameter_values=parameter_values
        )

        # get transport distances and options
        transport_distances: dict[ProcessStepType, float] = (
            DataHandler._get_transport_distances(
                source_region_code=parameter_values["source_region_code"],  # type: ignore # noqa
                target_country_code=parameter_values["target_country_code"],  # type: ignore # noqa
                transport=self.transport,
                ship_own_fuel=self.ship_own_fuel,
                dist_ship=data["DST-S-D"],  # type: ignore
                dist_pipeline=data["DST-S-DP"],  # type: ignore
                seashare_pipeline=data["SEASHARE"],  # type: ignore
                existing_pipeline_cap=data["CAP-T"],  # type: ignore
            )
        )

        return data | {"DIST": transport_distances}  # type: ignore


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

        # all_processes_ordered_backwards - includes
        # main, secondary, tertiary(market) processes
        self.all_processes_ordered_backwards: Iterable[AbstractProcess] = []
        # bool - is_main
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
        flow_from_initial_proc: FlowCodeType | None = None
        first_proc = self.main_processes[0] if self.main_processes else None
        if first_proc and first_proc.is_initial:
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

        for p_from in main_processes:
            for f in p_from.secondary_flow_types:
                add_required_flows_proc(p_from, f, in_main=False)
        for p_from in secondary_processes:
            for f in p_from.secondary_flow_types:
                add_required_flows_proc(p_from, f, in_main=False)
            if p_from.main_flow_code_in:
                # TODO: technically, secondary flows should not have main_flow_code_in
                # but some have them anyways?
                add_required_flows_proc(p_from, p_from.main_flow_code_in, in_main=True)

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
        if main_processes:
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
        last_proc = self.main_processes[-1] if self.main_processes else None
        if last_proc:
            G = cast(nx.DiGraph, G.subgraph(nx.ancestors(G, last_proc) | {last_proc}))
        all_procs_final = set(G.nodes)

        procs_dropped = procs_old - all_procs_final
        if procs_dropped:
            logger.info("Dropping unused: %s", [str(x) for x in procs_dropped])
            # drop from links_out
            # TODO: maybe use Digraph? - this is very ugly
            for k, vs in self.links_out.items():
                self.links_out[k] = [(p, m) for p, m in vs if p not in procs_dropped]

        # not all have links_out, but we fill the dict to prevent key errors
        for p in all_procs_final - set(self.links_out):
            self.links_out[p] = []

        # also create links in lookup
        # bool - is_main
        self.links_in: dict[AbstractProcess, list[tuple[AbstractProcess, bool]]] = {
            p: [] for p in all_procs_final
        }
        for p_from, targets in self.links_out.items():
            for p_to, is_main in targets:
                self.links_in[p_to].append((p_from, is_main))

        # also add links to processes
        for p_from, targets in self.links_out.items():
            flow_code = p_from.main_flow_code_out
            for p_to, is_main in targets:
                if is_main:
                    p_from._links_out_main.append(p_to)
                    assert p_to._link_in_main is None
                    p_to._link_in_main = p_from
                else:
                    p_from._links_out_secondary.append(p_to)
                    assert flow_code not in p_to._links_in_secondary
                    p_to._links_in_secondary[flow_code] = p_from

        # all_processes_ordered_backwards includes
        # main, secondary, tertiary(market) processes
        self.all_processes_ordered_forwards = list(nx.topological_sort(G))
        self.all_processes_ordered_backwards = list(
            reversed(self.all_processes_ordered_forwards)
        )

        # check (TODO: can be removed later)
        missing_main = set(self.main_processes) - set(
            self.all_processes_ordered_backwards
        )
        if missing_main:
            raise Exception(f"missing_main: {missing_main}")

        # check (TODO: can be removed later)
        # check all_processes_ordered_backwards: on call, all
        # targets of outbound links need to be finished
        _check_is_calculated: set[AbstractProcess] = set()
        for p_from in self.all_processes_ordered_backwards:
            for p_to, _is_main in self.links_out[p_from]:  # noqa: B020
                if p_to not in _check_is_calculated:
                    raise Exception(f"{p_from}: {p_to} not yet calculated (backwards)")
            _check_is_calculated.add(p_from)

        # check (TODO: can be removed later)
        # check all_processes_ordered_forwards: on call, all
        # sources of inbound links need to be finished
        _check_is_calculated: set[AbstractProcess] = set()
        for p_to in self.all_processes_ordered_forwards:
            for p_from, _is_main in self.links_in[p_from]:  # noqa: B020
                if p_from not in _check_is_calculated:
                    raise Exception(f"{p_to}: {p_from} not yet calculated (forwards)")
            _check_is_calculated.add(p_to)


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


def _create_parameter_getters_TODO(
    data_handler: DataHandler, use_user_data: bool
) -> ParameterGetters:
    # FIXME: FLH lookup not correct

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
            **kwargs: str | None,
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


def _get_pos_flow(value: float | None, context) -> float:
    if value is None:
        logger.error("flow value should not be None: %s", context)
        return 0
    elif value == 0:
        logger.warning("flow value should not be 0: %s", context)
        return 0
    elif value < 0:
        logger.debug("Dropping neg. flow value: %s", context)
        return 0
    return value


def _create_df_results_cost(
    result_costs: dict[AbstractProcess, list[ProcessResultCostsType]],
) -> pd.DataFrame:
    costs = [c for costs in result_costs.values() for c in costs]
    return pd.DataFrame([asdict(x) for x in costs])


def _create_df_results_emissions_e_g_co2e(
    result_emissions: dict[AbstractProcess, ProcessResultEmissionType],
) -> pd.DataFrame:
    return pd.DataFrame()


def _create_df_results_emissions_m_g_co2e(
    result_emissions: dict[AbstractProcess, ProcessResultEmissionType],
) -> pd.DataFrame:
    return pd.DataFrame()


def _create_results_flows_chain(
    result_flows: dict[AbstractProcess, ProcessResultFlowsType],
) -> list:
    result = []
    return result


def _create_results_flows_secondary(
    result_flows: dict[AbstractProcess, ProcessResultFlowsType],
) -> list:
    result = []
    return result


# calculate required output
def _get_sum_main_flow_out(
    process: AbstractProcess,
    results_flows: dict[AbstractProcess, ProcessResultFlowsType],
) -> float:
    main_flow_out = 0.0
    flow_code = process.main_flow_code_out
    # for process_target, is_main in graph.links_out[process]:
    for process_target, is_main in process.links_out:
        # process_target is already calculated
        results_target = results_flows[process_target]
        if is_main:
            main_flow_out += _get_pos_flow(
                results_target.main_flow_in,
                f"{process} => {process_target}",
            )
        else:
            main_flow_out += _get_pos_flow(
                results_target.secondary_flows_in.get(flow_code),
                f"{process} => {process_target}",
            )
    return main_flow_out
