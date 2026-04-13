"""Classes for main process chain calculation."""

from __future__ import annotations  # otherwise nx.DiGraph[Process] does not work

from dataclasses import asdict
from typing import Iterable, cast

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from networkx.exception import HasACycle

from ptxboa import logger
from ptxboa.api_data import DataHandler
from ptxboa.static import ProcessStepValues  # must be sorted
from ptxboa.static import (
    EmissionType,
    FlowCodeType,
    ParameterCodeType,
    ParameterCodeValues,
    ProcessCodeType,
    ProcessStepType,
    ResultClassType,
    ResultCostType,
    ResultEmissionType,
    ResultGasType,
    SourceRegionCodeType,
    TargetCountryCodeType,
)
from ptxboa.static._type_defs import (
    CalculateDataType,
    ChainDef,
    DataQueryDicType,
    ParameterGetters,
    ProcessDataType,
    ProcessEmissionType,
    ProcessEmissionType_E_M,
    ProcessResultCostsType,
    ProcessResultEmissionType,
    ProcessResultFlowsType,
    ProcessStep,
    PtxCalcResult,
    TransportType,
)
from ptxboa.utils import annuity, calculate_net_loss


class Process:
    _parameter_codes_process = [
        "WACC",
        "LIFETIME",
        "EFF",
        "FLH",
        "CAPEX",
        "OPEX-F",
        "OPEX-O",
    ]
    _parameter_codes_process_flow_sec_or_main = [
        "CH4SHARE",
        "EF_E",
        "EF_M",
        "CBOUND",
        "LOSS",
        "CO2CPT-R",
        "CO2CPT-S",
    ]
    _parameter_codes_process_flow_sec = [
        "CONV",
    ]

    def __init__(
        self,
        process_code: ProcessCodeType | FlowCodeType,
        process_step: ProcessStepType | str | None,
        main_flow_code_out: FlowCodeType,
        main_flow_code_in: FlowCodeType | None,
        secondary_flow_types: frozenset[FlowCodeType],
        is_last: bool,
        is_in_import_segment: bool,
        is_initial: bool,
        is_market: bool,
        is_secondary: bool,
        is_main: bool,
        is_main_in_transport_segment: bool,
        result_process_type: ResultClassType | None,
    ):
        # checks
        if is_in_import_segment:
            assert not is_initial
            assert not is_main_in_transport_segment
        if main_flow_code_in and main_flow_code_in in secondary_flow_types:
            logger.error(
                "%s has %s as main and secondary input", process_code, main_flow_code_in
            )
            secondary_flow_types = frozenset(
                x for x in secondary_flow_types if x != main_flow_code_in
            )

        self.process_code: ProcessCodeType | FlowCodeType = process_code
        self.process_step: ProcessStepType | str | None = process_step
        self.main_flow_code_out: FlowCodeType = main_flow_code_out
        self.main_flow_code_in: FlowCodeType | None = main_flow_code_in
        self.secondary_flow_types: frozenset[FlowCodeType] = secondary_flow_types
        self.is_last: bool = is_last
        self.is_in_import_segment: bool = is_in_import_segment
        self.is_initial: bool = is_initial
        self.is_market: bool = is_market
        self.is_secondary: bool = is_secondary
        self.is_main: bool = is_main
        self.is_main_in_transport_segment: bool = is_main_in_transport_segment
        self.result_process_type: ResultClassType | None = result_process_type

        # links - will be added by Chain

        self._links_out_in_main: list[Process] = []
        self._links_out_in_secondary: list[Process] = []
        self._link_in_main: Process | None = None
        self._links_in_secondary: dict[FlowCodeType, Process] = {}

    @property
    def is_in_export_segment(self) -> bool:
        """Is in export segment."""
        return not (self.is_in_import_segment or self.is_main_in_transport_segment)

    @classmethod
    def create_with_subclass(
        cls,
        process_code: ProcessCodeType | FlowCodeType,
        process_step: ProcessStepType | str | None = None,
        is_last: bool = False,
        is_in_import_segment: bool = False,
    ) -> "Process":
        """Create appropriate subclass of Process."""
        is_market = process_code in DataHandler.dimensions["flow"].index  # is flow code
        ProcessClass: type[Process] = Process

        if is_market:
            main_flow_code_out = cast(FlowCodeType, process_code)
            flow_spec = DataHandler.dimensions["flow"].loc[main_flow_code_out]
            main_flow_code_in = None
            secondary_flow_types = frozenset()
            is_initial = False
            is_secondary = False
            is_main = False
            is_main_in_transport_segment = False
            ProcessClass = ProcessMarket
            result_process_type = flow_spec["result_process_type"]
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
            is_main_in_transport_segment = bool(
                proc_spec["is_transport"]
                and not proc_spec["is_transformation"]  # no pre/post
                and not proc_spec["is_secondary"]  # CSS
                and not proc_spec["is_storage"]  # H2/EL Storage
            )
            if is_main_in_transport_segment:
                ProcessClass = ProcessTransport
            elif is_secondary:
                ProcessClass = ProcessSecondary
            result_process_type = proc_spec["result_process_type"]

        return ProcessClass(
            process_code=process_code,
            process_step=process_step,
            main_flow_code_out=main_flow_code_out,
            main_flow_code_in=main_flow_code_in,
            secondary_flow_types=secondary_flow_types,
            is_last=is_last,
            is_in_import_segment=is_in_import_segment,
            is_initial=is_initial,
            is_market=is_market,
            is_secondary=is_secondary,
            is_main=is_main,
            is_main_in_transport_segment=is_main_in_transport_segment,
            result_process_type=result_process_type,
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
    def _main_flow_code_in_or_out(self) -> FlowCodeType:
        """Main flow code in, or out if it does not exist."""
        return self.main_flow_code_in or self.main_flow_code_out

    @property
    def _parameter_flow_types_sec_or_main(self) -> set[FlowCodeType]:
        """Flow types for which parameter data should be loaded."""
        result = set(self.secondary_flow_types)
        # also add main flow in (for market/initial proces,
        # those dont exist and we need out)
        result.add(self._main_flow_code_in_or_out)
        return result

    @property
    def color(self) -> str:
        """Color for plotting."""
        return "lightblue"

    def get_parameter_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType:
        """Create data for calculation."""
        data: ProcessDataType = {}
        # load parameters that are process dependent

        process_code: ProcessCodeType = self.process_code  # type: ignore

        for p in self._parameter_codes_process:
            data[p] = parameter_getters[p](
                process_code=process_code, flow_code=None, **parameter_values
            )

        # load parameters that are process and flow dependent
        # secondary or main flows
        for p in self._parameter_codes_process_flow_sec_or_main:
            data[p] = {
                f: parameter_getters[p](
                    process_code=process_code, flow_code=f, **parameter_values
                )
                for f in self._parameter_flow_types_sec_or_main
            }

        # load parameters that are process and flow dependent
        # secondary flows
        for p in self._parameter_codes_process_flow_sec:
            data[p] = {
                f: parameter_getters[p](
                    process_code=process_code, flow_code=f, **parameter_values
                )
                for f in self.secondary_flow_types
            }

        self._inplace_correct_eff_and_conv_with_loss(data)

        return data

    def _inplace_correct_eff_and_conv_with_loss(self, data: ProcessDataType) -> None:
        LOSS: dict = data.get("LOSS", {})  # type: ignore
        main_flow_code: FlowCodeType = self._main_flow_code_in_or_out
        if main_flow_code in LOSS:  # correct EFF
            # see https://github.com/agoenergy/ptx-boa/issues/581
            data["EFF"] = data["EFF"] / (1 + LOSS[main_flow_code])
        conv: float
        CONV: dict = data.get("CONV", {})  # type: ignore
        for flow_code, conv in CONV.items():
            if conv <= 0:
                # currently negative flows (i.e. additional output)
                conv = 0
            if flow_code in LOSS:
                # new: loss can reduce the effective conversion rate
                # see https://github.com/agoenergy/ptx-boa/issues/581
                data["CONV"][flow_code] = conv * (1 + LOSS[flow_code])  # type: ignore

    @property
    def is_css(self) -> bool:
        """Is CSS process."""
        # FIXME: get from process data? or from main_flow
        # return self.main_flow_code_out == "CO2-C" # noqa
        return self.process_code == "CO2-T+S#B"

    def calculate_flows(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> ProcessResultFlowsType:
        """Calculate flows."""
        # main_flow_out: sum of outgoing
        if self.is_last:
            main_flow_out = 1
        else:
            main_flow_out = 0
            for p in self._links_out_in_main:
                main_flow_out += results_flows[p].main_flow_in  # type: ignore - this one must have a value # noqa
            for p in self._links_out_in_secondary:
                main_flow_out += results_flows[p].secondary_flows_in[
                    self.main_flow_code_out
                ]
            if not main_flow_out:
                logger.warning("Process with main_flow_out = 0: %s", self)

        if not self.main_flow_code_in:
            main_flow_in = None
        # TODO: we had this in the old tool - should be removed?
        # I think its because of the FLH optimizer that does optimize Storage?
        # elif self.process_code in ["EL-STR", "H2-STR"]: # noqa
        #    main_flow_in = main_flow_out  # noqa
        else:
            eff: float = parameter_data[self].get("EFF") or 0  # type:ignore
            if eff <= 0:
                logger.error("Process with eff = %s: %s", eff, self)
                eff = 1

            main_flow_in = main_flow_out / eff

        secondary_flows_in = {}
        for flow_code in self.secondary_flow_types:
            conv: float = (
                parameter_data[self].get("CONV", {}).get(flow_code) or 0  # type:ignore
            )
            if conv == 0:
                logger.warning("Process with conv = 0 %s / %s", self, flow_code)
            elif conv < 0:
                conv = 0
            secondary_flows_in[flow_code] = main_flow_out * conv

        return ProcessResultFlowsType(
            main_flow_out=main_flow_out,
            main_flow_in=main_flow_in,
            secondary_flows_in=secondary_flows_in,
        )

    def _create_result_cost(
        self, cost_type: ResultCostType, values: float
    ) -> ProcessResultCostsType:
        return ProcessResultCostsType(
            process_type=self.result_process_type,  # type: ignore : only None for market  # noqa
            process_subtype=self.process_code,
            cost_type=cost_type,
            values=values,
        )

    def _create_result_emission(
        self, emission_type: ResultEmissionType, gas_type: ResultGasType, values: float
    ) -> ProcessResultEmissionType:
        return ProcessResultEmissionType(
            process_type=self.result_process_type,  # type: ignore : only None for market # noqa
            process_subtype=self.process_code,
            emission_type=emission_type,
            gas_type=gas_type,
            values=values,
        )

    def calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, list[ProcessResultCostsType]],
    ) -> list[ProcessResultCostsType]:
        """Calculate costs."""
        parameters = parameter_data[self]
        flows = results_flows[self]

        lifetime: int = parameters["LIFETIME"]  # type: ignore
        flh: float = parameters["FLH"]  # type: ignore
        capex_rel: float = parameters["CAPEX"]  # type: ignore
        opex_f: float = parameters["OPEX-F"]  # type: ignore
        opex_o: float = parameters["OPEX-O"]  # type: ignore
        wacc: float = parameters["WACC"]  # type: ignore
        main_flow_out: float = flows.main_flow_out

        if "CAP_F" in parameters:
            # Storage unit: capacity
            # TODO: double check units (division by 8760 h)?
            cap_f: float = parameters["CAP_F"]  # type: ignore
            capacity = main_flow_out * cap_f / 8760

        elif self.is_secondary and self.main_flow_code_out not in {"EL", "HEAT"}:
            # TODO: get from units in process specs
            # secondary processes like Water, DAC: capacity is main_flow_out
            capacity = main_flow_out
        else:
            capacity = main_flow_out / flh

        capex = capacity * capex_rel
        capex_ann = annuity(wacc, lifetime, capex)
        opex = opex_f * capacity + opex_o * main_flow_out

        return [
            self._create_result_cost(cost_type="OPEX", values=opex),
            self._create_result_cost(cost_type="CAPEX", values=capex_ann),
        ]

    def _calculate_emissions(
        self,
        parameter_data: ProcessDataType,
        flows_in_gross: dict[FlowCodeType, float],
        EF_co2_g_per_flow: dict[FlowCodeType, float],
        main_flow_out: float,
    ) -> ProcessEmissionType_E_M:

        # constants: TODO: globally defined
        FLOW_CO2_INDIRECT = {"HEAT", "EL"}
        G_CH4_PER_KWH = 68.75469807
        CH4_TO_CO2EQ = 29.8
        CO2_PER_C = 3.664446295  # 44.01 / 12.01

        # use parameter_data.get() because not always available (like trasnport)
        LOSS = parameter_data.get("LOSS", {})
        CH4SHARE = parameter_data.get("CH4SHARE", {})
        CO2CPT_R = parameter_data.get("CO2CPT-R", {})
        CO2CPT_S = parameter_data.get("CO2CPT-S", {})
        CBOUND_kg_c_per_output = parameter_data.get("CBOUND", {})

        # calculate direct ch4 losses
        ch4_kwh_direct_loss = 0
        flows_in_net: dict[FlowCodeType, float] = {}
        for flow_code, value_gross in flows_in_gross.items():
            # at first: set to value_gross, so we can use "continue"
            # if we dont want to change it
            flows_in_net[flow_code] = value_gross

            if not value_gross:
                continue

            loss_factor: float = LOSS.get(flow_code, 0)  # type:ignore
            if not loss_factor:
                continue

            ch4_kwh_per_flow: float = CH4SHARE.get(flow_code)  # type:ignore
            if not ch4_kwh_per_flow:
                if flow_code in ("CH4-G", "CH4-L"):
                    logger.warning("missing CH4SHARE for CH4 - should be 1?")
                    ch4_kwh_per_flow = 1
                else:
                    logger.warning("missing CH4SHARE for %s", flow_code)
                    ch4_kwh_per_flow = 0
                    continue

            value_net, value_loss = calculate_net_loss(
                value_gross=value_gross, loss_factor=loss_factor
            )
            flows_in_net[flow_code] = value_net
            ch4_kwh_direct_loss += value_loss * ch4_kwh_per_flow

        ch4_g_direct_loss = ch4_kwh_direct_loss * G_CH4_PER_KWH
        ch4_direct_co2e_g = ch4_g_direct_loss * CH4_TO_CO2EQ

        # calculate capture, direct, indirect, bound
        co2_g_direct_sum_in = 0
        co2_g_indirect_scope2 = 0
        co2_captured = 0
        co2_g_bound_in_product = 0

        for flow_code, flow in flows_in_net.items():
            if not flow:
                continue
            co2_g_per_flow = EF_co2_g_per_flow.get(flow_code, 0)
            co2_g = co2_g_per_flow * flow
            if flow_code in FLOW_CO2_INDIRECT:
                # indirect emissions
                co2_g_indirect_scope2 += co2_g
            else:
                # direct emission
                co2_g_direct_sum_in += co2_g
                # capture
                co2cpt: float = CO2CPT_R.get(flow_code, 0) * CO2CPT_S.get(flow_code, 0)  # type: ignore # noqa
                co2_captured += co2_g * co2cpt
                # bound
                bound_kg_c_per_output: float = CBOUND_kg_c_per_output.get(flow_code, 0)  # type: ignore # noqa
                # only add if EFF exist (EFF_FLAG)
                # TODO: special case B-DRI-S - generalized rule?
                allow_cbound = bool(co2_g_per_flow) or flow_code in {"B-DRI-S"}
                if allow_cbound:
                    co2_g_bound_in_product += (
                        bound_kg_c_per_output * 1000 * CO2_PER_C * main_flow_out
                    )

        co2_g_direct = co2_g_direct_sum_in - co2_g_bound_in_product - co2_captured
        if co2_g_direct < 0:
            logger.error("co2_g_direct < 0")
            co2_g_direct = 0

        if not main_flow_out:
            co2_bound_in_product_per_output = 0
        else:
            co2_bound_in_product_per_output = co2_g_bound_in_product / main_flow_out

        return ProcessEmissionType_E_M(
            co2_direct=co2_g_direct,
            co2_indirect_scope2=co2_g_indirect_scope2,
            ch4_direct_co2e=ch4_direct_co2e_g,
            co2_captured=co2_captured,
            co2_bound_in_product=co2_g_bound_in_product,
            co2_bound_in_product_per_output=co2_bound_in_product_per_output,
        )

    def calculate_emissions(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_emissions: dict[Process, ProcessEmissionType | None],
    ) -> ProcessEmissionType | None:
        """Calculate emissions."""
        result: ProcessEmissionType = {}

        EM_2_PARAM: dict[EmissionType, ParameterCodeType] = {
            "emission": "EF_E",
            "mass": "EF_M",
        }

        # get all in flows (main & secondary)
        flows_in_main_and_secondary: dict[FlowCodeType, float] = results_flows[
            self
        ].secondary_flows_in.copy()
        if self.main_flow_code_in is not None:
            flows_in_main_and_secondary[self.main_flow_code_in] = (
                results_flows[self].main_flow_in or 0
            )

        # for all in flows: rel. get bound in product for mass/emission
        for em, param_ef in EM_2_PARAM.items():
            g_co2_per_flows: dict[FlowCodeType, float] = {}

            for flow_code, proc in self._links_in_secondary.items():
                res = results_emissions[proc]
                if res:
                    g_co2_per_flow = res[em].co2_bound_in_product_per_output
                else:
                    g_co2_per_flow = None
                if not g_co2_per_flow:
                    # use emission factor, if not bound in co2
                    params = parameter_data[self].get(param_ef, {})
                    g_co2_per_flow = params.get(flow_code, 0)  # type: ignore
                g_co2_per_flows[flow_code] = g_co2_per_flow  # type: ignore

            if self._link_in_main:
                proc = self._link_in_main
                flow_code = self.main_flow_code_in

                # also for main flow in: # TODO: reuse code fromabove
                res = results_emissions[proc]
                if res:
                    g_co2_per_flow = res[em].co2_bound_in_product_per_output
                else:
                    g_co2_per_flow = None
                if not g_co2_per_flow:
                    # use emission factor, if not bound in co2
                    params = parameter_data[self].get(param_ef, {})
                    g_co2_per_flow = params.get(flow_code, 0)  # type: ignore
                g_co2_per_flows[flow_code] = g_co2_per_flow  # type: ignore

            result[em] = self._calculate_emissions(
                parameter_data=parameter_data[self],
                flows_in_gross=flows_in_main_and_secondary,
                EF_co2_g_per_flow=g_co2_per_flows,
                main_flow_out=results_flows[self].main_flow_out,
            )

        return result


class ProcessSecondary(Process):
    @property
    def color(self) -> str:
        """Color for plotting."""
        return "palegreen"


class ProcessTransport(Process):
    _parameter_codes_process = ["OPEX-T", "LOSS-T", "OPEX-O"] + [
        # NOTE: these are the same for all transport steps - maybe get only once?
        "CAP-T",
        "DST-S-D",
        "DST-S-DP",
        "SEASHARE",
    ]

    _parameter_codes_process_flow_sec_or_main = [
        "EF_E",
        "EF_M",
    ]
    _parameter_codes_process_flow_sec = [
        "CONV",  # FXIME: should be CONV-OT?
        "CONV-OT",
    ]

    @property
    def color(self) -> str:
        """Color for plotting."""
        return "teal"

    def calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, list[ProcessResultCostsType]],
    ) -> list[ProcessResultCostsType]:
        """Calculate costs."""
        parameters = parameter_data[self]
        flows = results_flows[self]

        opex_t: float = parameters.get("OPEX-T", 0)  # type: ignore
        dist_transport: float = parameters.get("DIST", 0)  # type: ignore
        opex_o: float = parameters.get("OPEX-O", 0)  # type: ignore

        main_flow_out: float = flows.main_flow_out

        opex_ot = opex_t * dist_transport
        opex = (opex_o + opex_ot) * main_flow_out

        return [self._create_result_cost(cost_type="OPEX", values=opex)]

    def _get_parameter_data_dist(
        self,
        source_region_is_target_reason: bool,
        data: ProcessDataType,
    ) -> float:
        if source_region_is_target_reason:
            return 0

        dist_ship: float = data.get("DST-S-D", 0)  # type: ignore
        dist_pipeline: float = data.get("DST-S-DP", 0)  # type: ignore
        seashare_pipeline: float = data.get("SEASHARE", 0)  # type: ignore
        existing_pipeline_cap: float = data.get("CAP-T", 0)  # type: ignore

        if self.process_step == "PPLX":
            return dist_pipeline * seashare_pipeline if existing_pipeline_cap else 0
        elif self.process_step == "PPLR":
            return (
                dist_pipeline * (1 - seashare_pipeline) if existing_pipeline_cap else 0
            )
        elif self.process_step == "PPLS":
            return 0 if existing_pipeline_cap else dist_pipeline * seashare_pipeline
        elif self.process_step == "PPL":
            return (
                0 if existing_pipeline_cap else dist_pipeline * (1 - seashare_pipeline)
            )
        elif self.process_step == "SHP_OWN":
            return dist_ship
        elif self.process_step == "SHP":
            return dist_ship
        else:
            raise NotImplementedError(self.process_step)

    def get_parameter_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType:
        """Create data for calculation."""
        data = super().get_parameter_data(
            parameter_getters=parameter_getters, parameter_values=parameter_values
        )

        dist_transport = self._get_parameter_data_dist(
            source_region_is_target_reason=(
                parameter_values["source_region_code"]
                == parameter_values["target_country_code"]
            ),
            data=data,
        )

        loss_t: float = data.get("LOSS-T", 0)  # type: ignore

        data["EFF"] = 1 - loss_t * dist_transport
        data["DIST"] = dist_transport

        # FIXME CONV in transport?
        for flow_code, conv in data["CONV"].items():  # type: ignore
            if not conv:
                continue

            if data["CONV-OT"].get(flow_code):  # type: ignore
                logger.error(
                    "%s / %s: CONV instead of CONV-OT (already defined) "
                    "in transport input data: %s",
                    self,
                    flow_code,
                    conv,
                )
            else:
                logger.error(
                    "%s / %s: CONV instead of CONV-OT (overwriting) "
                    "in transport input data: %s",
                    self,
                    flow_code,
                    conv,
                )
                data["CONV-OT"][flow_code] = conv  # type: ignore

        # create CONV from DIST * CONV-OT
        for flow_code, conv_ot in data["CONV-OT"].items():  # type: ignore
            if not conv_ot:
                continue
            data["CONV"][flow_code] = conv_ot * dist_transport  # type: ignore

        # FIXME: OPEX-O in transport?
        return data


class ProcessMarket(Process):
    _parameter_codes_process = []
    _parameter_codes_process_flow_sec = []
    _parameter_codes_process_flow_sec_or_main = ["SPECCOST"]

    @property
    def color(self) -> str:
        """Color for plotting."""
        return "lightgray"

    def calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, list[ProcessResultCostsType]],
    ) -> list[ProcessResultCostsType]:
        """Calculate costs."""
        parameters = parameter_data[self]

        speccost: float = parameters["SPECCOST"][self.main_flow_code_out]  # type: ignore # noqa
        # create costs not once for main flow out,but instead
        # for all recipients
        result = []

        process_flows: dict[Process, float] = {}
        for p in self._links_out_in_main:
            process_flows[p] = results_flows[p].main_flow_in  # type: ignore
        for p in self._links_out_in_secondary:
            process_flows[p] = results_flows[p].secondary_flows_in[
                self.main_flow_code_out
            ]

        for p, flow in process_flows.items():
            value = flow * speccost
            result.append(
                ProcessResultCostsType(
                    process_type=self._get_result_process_type(target_process=p),
                    process_subtype=p.process_code,  # accounted in main process
                    cost_type="FLOW",
                    values=value,
                )
            )

        return result

    def _get_result_process_type(self, target_process: Process) -> ResultClassType:
        return self.result_process_type or target_process.result_process_type  # type: ignore # noqa - one of these must be set

    def calculate_emissions(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_emissions: dict[Process, ProcessEmissionType | None],
    ) -> ProcessEmissionType | None:
        """Calculatae emissions."""
        return None


class PtxCalc:
    _instances: dict[object, "PtxCalc"] = {}

    def _create_all_processes_ordered_forwards(self) -> tuple[Process, ...]:
        return tuple(nx.topological_sort(self._graph))

    def _create_processes_by_step(self) -> dict[ProcessStepType | str, Process]:
        processes_by_step: dict[ProcessStepType | str, Process] = {}
        for process in self._all_processes_ordered_forwards:
            process_step = process.process_step
            if not process_step:
                continue
            if process_step in processes_by_step:
                logger.error("Duplicate step: %s", process.process_step)
                continue
            processes_by_step[process.process_step] = process  # type: ignore
        return processes_by_step

    def _link_processes(self) -> None:
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

    def _create_css_subgraph_processes_ordered_backwards(
        self,
    ) -> tuple[Process, ...]:
        """Subgraphs should only be css process + market processes."""
        processes: list[Process] = []
        for p in self._secondary_processes_ordered_forwards:
            if not p.is_css:
                continue
            processes.append(p)
            # get subgraph
            for pm in nx.ancestors(self._graph, p):
                assert pm.is_market
                processes.append(pm)
        return tuple(processes)

    def __init__(self, _graph: nx.DiGraph[Process]):
        self._graph: nx.DiGraph[Process] = _graph
        self._all_processes_ordered_forwards = (
            self._create_all_processes_ordered_forwards()
        )
        self._processes_by_step = self._create_processes_by_step()
        self._css_subgraph_processes_ordered_backwards = (
            self._create_css_subgraph_processes_ordered_backwards()
        )
        # add links to processes for faster lookup + checks
        self._link_processes()
        # save initial and last process
        self.initial_process = self._main_processes_ordered_forwards[0]
        self.last_process = self._main_processes_ordered_forwards[-1]
        assert self.initial_process.is_initial, self.initial_process
        assert self.last_process.is_last, self.last_process

    @classmethod
    def get_or_create(cls, chain_def: ChainDef) -> "PtxCalc":
        """Get or create calculation instance.

        We can re-use existing instances because this instance
        represents a chain (without source/target regions), without
        parameter data.
        """
        key = chain_def.unique_key
        if key not in cls._instances:
            cls._instances[key] = cls._create(chain_def)
        return cls._instances[key]

    @classmethod
    def _create(cls, chain_def: ChainDef) -> "PtxCalc":

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

        is_in_import_segment = False
        _was_transport = False
        main_processes = []
        for i, (process_code, process_step) in enumerate(main_process_codes_steps):
            process = Process.create_with_subclass(
                process_code=process_code,
                process_step=process_step,
                is_in_import_segment=is_in_import_segment,
                is_last=(i + 1 == len(main_process_codes_steps)),
            )

            # is_in_import_segment: first non-transport step
            if not process.is_main_in_transport_segment and _was_transport:
                # FIXME: better way then re-creating process?
                # we cannot change attribtue because of frozen dataclass
                is_in_import_segment = True
                process.is_in_import_segment = is_in_import_segment

            _was_transport = _was_transport or process.is_main_in_transport_segment

            main_processes.append(process)

        secondary_processes_export = [
            Process.create_with_subclass(
                process_code=process_code, is_in_import_segment=False
            )
            for process_code in secondary_process_codes_export
        ]
        secondary_processes_import = [
            Process.create_with_subclass(
                process_code=process_code, is_in_import_segment=True
            )
            for process_code in secondary_process_codes_import
        ]

        _graph = _create_graph(
            main_processes=main_processes,
            secondary_processes_export=secondary_processes_export,
            secondary_processes_import=secondary_processes_import,
        )
        return PtxCalc(_graph=_graph)

    def get_calculation_data(
        self,
        data_handler: "DataHandler",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
    ) -> CalculateDataType:
        """Create data for calculation."""
        parameter_getters = self._get_parameter_getters(
            data_handler=data_handler, use_user_data=use_user_data
        )
        parameter_values: DataQueryDicType = {
            "source_region_code": source_region_code,
            "target_country_code": target_country_code,
        }

        parameter_data = self._get_parameter_data_from_processes(
            parameter_getters=parameter_getters,
            parameter_values=parameter_values,
        )

        flh_opt_process: dict[ProcessCodeType, ProcessDataType] = {}
        speccost_for_flh_opt: dict[FlowCodeType, float] = {}

        # FIXME: only if we we optimize:
        if True:
            speccost_for_flh_opt = self._get_speccost_for_flh_opt(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values,
            )
            # only if we optimize for RES-HYBR
            if self.initial_process.process_code == "RES-HYBR":
                flh_opt_process = self._get_parameter_data_flh_opt_process_for_res_hybr(
                    parameter_getters=parameter_getters,
                    parameter_values=parameter_values,
                )

        return self._merge_parameter_data(
            parameter_data=parameter_data,
            context=parameter_values,
            flh_opt_process=flh_opt_process,
            speccost_for_flh_opt=speccost_for_flh_opt,
        )

    def _calculate(self, data: CalculateDataType) -> dict:
        """Calculate results.

        Calculation order:

        - backwards calculate flows (except CO2-C - maybe remove from CONV) for output 1
        - if blue tool:
          - forward calcualte emission (because of bound in product)
          - calculate css flows
        - calculate costs

        """
        parameter_data = self._split_parameter_data(data=data)
        results_flows = self._calculate_flows_backwards(parameter_data=parameter_data)

        # TODO: only if blue tool
        results_emissions = self._calculate_emissions_forwards(
            parameter_data=parameter_data, results_flows=results_flows
        )
        self._update_flows_with_css(
            results_flows=results_flows,
            parameter_data=parameter_data,
            results_emissions=results_emissions,
        )

        results_costs = self._calculate_costs(
            parameter_data=parameter_data, results_flows=results_flows
        )

        return {
            "parameter_data": parameter_data,
            "results_flows": results_flows,
            "results_costs": results_costs,
            "results_emissions": results_emissions,
        }

    def calculate(self, data: CalculateDataType) -> PtxCalcResult:
        """Calculate results."""
        results = self._calculate(data=data)
        return self._merge_calculation_results(**results)

    def plot(
        self,
        file_basename: str,
        edge_values: dict[tuple[Process, Process], float] | None = None,
        dpi: int = 150,
    ):
        """Create plot and save as png."""
        scale_distance = 2
        node_pos = self._plot_get_pos()

        def _get_label_str(item) -> str:
            if isinstance(item, float):
                return f"{item:.2E}"
            return str(item)

        def _get_label(*items) -> str:
            return "\n".join(_get_label_str(x) for x in items)

        def _get_edge_label(p1: Process, p2: Process) -> str:
            items = []
            items.append(p1.main_flow_code_out)
            if edge_values and (p1, p2) in edge_values:
                items.append(edge_values.get((p1, p2)))
            return _get_label(*items)

        plt.close()
        plt.clf()
        plt.figure(
            figsize=(
                len(list(self._main_processes_ordered_forwards)) * scale_distance * 2,
                2 * scale_distance,
            )
        )

        # Draw nodes
        nx.draw(
            self._graph,
            node_pos,
            with_labels=False,
            node_color=[k.color for k in self._graph.nodes()],
            width=[
                (
                    2
                    if self._graph.get_edge_data(p, p_)["in_main"]
                    and p.is_main
                    and p_.is_main
                    else 1
                )
                for p, p_ in self._graph.edges()
            ],
            node_size=[
                (1000 if p.is_market else 2000) * scale_distance
                for p in self._graph.nodes()
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
            edge_labels={pp: _get_edge_label(*pp) for pp in self._graph.edges()},
            font_size=6,
            font_color="black",
            # label_pos=0.5, # noqa
        )

        # Save to PNG
        plt.savefig(f"chain_flowcharts/{file_basename}.png", dpi=dpi)

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
            key: (
                self._processes_by_step[step].process_code
                if step in self._processes_by_step
                else None
            )
            for key, step in {
                "process_res": "RES",
                "process_ely": "ELY",
                "process_deriv": "DERIV",
            }.items()
        }

    def _get_parameter_getters(
        self,
        data_handler: "DataHandler",
        use_user_data: bool = True,
    ) -> ParameterGetters:

        default_parameter_values = self._get_default_parameter_values()

        def make_parameter_getters(parameter_code):
            default = data_handler.PARAMETER_DEFAULTS.get(parameter_code, 0)

            def _get_parameter_value(**kwargs):

                return data_handler._get_parameter_value(
                    parameter_code=parameter_code,
                    **kwargs,  # type: ignore
                    **default_parameter_values,
                    default=default,
                    use_user_data=use_user_data,
                )

            return _get_parameter_value

        parameter_getters = {}
        for p in ParameterCodeValues:
            parameter_getters[p] = make_parameter_getters(p)

        return parameter_getters

    def _get_parameter_data_flh_opt_process_for_res_hybr(
        self,
        parameter_getters: ParameterGetters,
        parameter_values: DataQueryDicType,
    ) -> dict[ProcessCodeType, ProcessDataType]:
        flh_opt_process = {}

        procs_required_for_opt_res_hybr: list[ProcessCodeType] = ["PV-FIX", "WIND-ON"]

        # when optimzing for RES=RES-HYBR, optimizer needs data for
        # "PV-FIX" and "WIND-ON"
        for process_code in procs_required_for_opt_res_hybr:
            process = Process.create_with_subclass(process_code=process_code)
            parameter_data = process.get_parameter_data(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values,
            )
            flh_opt_process[process_code] = parameter_data

        return flh_opt_process

    def _get_speccost_for_flh_opt(
        self,
        parameter_getters: ParameterGetters,
        parameter_values: DataQueryDicType,
    ) -> dict[FlowCodeType, float]:
        speccost_for_flh_opt = {}

        # api_optimize.py: always wants SPECCOST for certain flows
        SPECCOSTS_REQUIRED_FOR_OPT: list[FlowCodeType] = [
            "CO2-G",
            "H2O-L",
            "HEAT",
            "N2-G",
        ]

        flow_code: FlowCodeType
        for flow_code in SPECCOSTS_REQUIRED_FOR_OPT:
            parameter_data = Process.create_with_subclass(
                process_code=flow_code
            ).get_parameter_data(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values,
            )
            speccost_for_flh_opt[flow_code] = parameter_data["SPECCOST"][  # type:ignore
                flow_code
            ]

        return speccost_for_flh_opt

    def _get_parameter_data_from_processes(
        self,
        parameter_getters: ParameterGetters,
        parameter_values: DataQueryDicType,
    ) -> dict[Process, ProcessDataType]:
        result: dict[Process, ProcessDataType] = {}

        parameter_values_export_transport = parameter_values
        parameter_values_import: DataQueryDicType = parameter_values | {  # type:ignore
            # Switched!
            "source_region_code": parameter_values["target_country_code"]
        }

        for process in self._all_processes_ordered_forwards:
            parameter_values_sel = (
                parameter_values_import
                if process.is_in_import_segment
                else parameter_values_export_transport
            )
            result[process] = process.get_parameter_data(
                parameter_getters=parameter_getters,
                parameter_values=parameter_values_sel,
            )
        return result

    def _update_flows_with_css(
        self,
        results_flows: dict[Process, ProcessResultFlowsType],
        parameter_data: dict[Process, ProcessDataType],
        results_emissions: dict[Process, ProcessEmissionType | None],
    ):
        """Inplace update flows for CSS subgraphs.

        - for all emission where we have css: set CO2-C flow
        - recalculate flows for CSS subgraphs
          (should only be Process + Market processes)

        """
        # for all emission where we have css: set CO2-C flow
        for process, emissions in results_emissions.items():
            # TODO: mass or emission?
            # mass makes more sense, should be the same anyways
            co2_g_captured: float = emissions["mass"].co2_captured if emissions else 0
            if co2_g_captured:
                if "CO2-C" not in process.secondary_flow_types:
                    logger.error("CO2 captured where we dont expect it: %s", process)
                    continue
                # flows main unit is always kg
                co2_kg_captured = co2_g_captured / 1000
                results_flows[process].secondary_flows_in["CO2-C"] = co2_kg_captured

        # recalculate flows for CSS subgraphs
        for process in self._css_subgraph_processes_ordered_backwards:
            results_flows[process] = process.calculate_flows(
                parameter_data=parameter_data, results_flows=results_flows
            )

    def _calculate_flows_backwards(
        self, parameter_data: dict[Process, ProcessDataType]
    ) -> dict[Process, ProcessResultFlowsType]:
        results_flows: dict[Process, ProcessResultFlowsType] = {}
        for process in self._all_processes_ordered_backwards:
            # TODO: optionally skip or add empty for CSS subgraphs, as they must be
            # calculated again later. but make sure we wont get key violations
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

    def _calculate_emissions_forwards(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> dict[Process, ProcessEmissionType | None]:
        results_emissions: dict[Process, ProcessEmissionType | None] = {}
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
        results_emissions: dict[Process, ProcessEmissionType | None],
    ) -> PtxCalcResult:
        cols_dim_costs = ["process_type", "process_subtype", "cost_type"]

        df_results_cost = pd.DataFrame(
            [asdict(x) for x in [c for costs in results_costs.values() for c in costs]],
            columns=cols_dim_costs + ["values"],
        )
        df_results_cost = _aggregate_results_df(
            df_results_cost,
            cols_dim_costs,
        )

        # TODO from results_emissions
        cols_dim_emissions = [
            "process_type",
            "process_subtype",
            "emission_type",
            "gas_type",
        ]

        # mass balance
        df_results_emissions_m_g_co2e = pd.DataFrame(
            [
                asdict(x)
                for x in self._merge_emission_results(
                    results_emissions=results_emissions, etype="mass"
                )
            ],
            columns=cols_dim_emissions + ["values"],
        )
        df_results_emissions_m_g_co2e = _aggregate_results_df(
            df_results_emissions_m_g_co2e, cols_dim_emissions
        )

        # emissions balance
        df_results_emissions_e_g_co2e = pd.DataFrame(
            [
                asdict(x)
                for x in self._merge_emission_results(
                    results_emissions=results_emissions, etype="emission"
                )
            ],
            columns=cols_dim_emissions + ["values"],
        )
        df_results_emissions_e_g_co2e = _aggregate_results_df(
            df_results_emissions_e_g_co2e, cols_dim_emissions
        )

        results_flows_chain = [
            _add_step_and_code(p, asdict(results_flows[p]))
            for p in self._main_processes_ordered_forwards
        ]
        results_flows_secondary = [
            _add_step_and_code(p, asdict(results_flows[p]))
            for p in self._secondary_processes_ordered_forwards
        ]

        return PtxCalcResult(
            df_results_cost=df_results_cost,
            df_results_emissions_e_g_co2e=df_results_emissions_e_g_co2e,
            df_results_emissions_m_g_co2e=df_results_emissions_m_g_co2e,
            results_flows_chain=results_flows_chain,
            results_flows_secondary=results_flows_secondary,
        )

    def _merge_emission_results(
        self,
        results_emissions: dict[Process, ProcessEmissionType | None],
        etype: EmissionType,
    ) -> list[ProcessResultEmissionType]:
        results: list[ProcessResultEmissionType] = []

        for process, result_e_m in results_emissions.items():
            if not result_e_m:
                # some (like market) dont have emissions
                continue
            result = result_e_m[etype]
            results.append(
                process._create_result_emission(
                    emission_type="indirect",
                    gas_type="CO2",
                    values=result.co2_indirect_scope2,
                )
            )
            results.append(
                process._create_result_emission(
                    emission_type="direct",
                    gas_type="CH4",
                    values=result.ch4_direct_co2e,
                )
            )
            results.append(
                process._create_result_emission(
                    emission_type="direct",
                    gas_type="CO2",
                    values=result.co2_direct,
                )
            )

        # for last process, add co2_bound_in_product
        results.append(
            ProcessResultEmissionType(
                # TODO: "Bound in product" as constant somewhere
                process_type="Bound in product",
                process_subtype="Bound in product",
                emission_type="direct",
                gas_type="CO2",
                values=results_emissions[self.last_process][  # type: ignore - should exist # noqa
                    "mass"
                ].co2_bound_in_product,
            )
        )

        return results

    def _merge_parameter_data(
        self,
        parameter_data: dict[Process, ProcessDataType],
        flh_opt_process: dict[ProcessCodeType, ProcessDataType],
        speccost_for_flh_opt: dict[FlowCodeType, float],
        context: DataQueryDicType,
    ) -> CalculateDataType:

        main_export_process_chain = [
            _add_step_and_code(p, parameter_data[p])
            for p in self._main_processes_ordered_forwards
            if p.is_in_export_segment
        ]

        main_transport_process_chain = [
            _add_step_and_code(p, parameter_data[p])
            for p in self._main_processes_ordered_forwards
            if p.is_main_in_transport_segment
        ]

        main_import_process_chain = [
            _add_step_and_code(p, parameter_data[p])
            for p in self._main_processes_ordered_forwards
            if p.is_in_import_segment
        ]

        secondary_process_import = {
            p.main_flow_code_out: _add_step_and_code(p, parameter_data[p])
            for p in self._secondary_processes_ordered_forwards
            if not p.is_in_export_segment  # no secondary processes in transport segment
        }

        secondary_process = {
            p.main_flow_code_out: _add_step_and_code(p, parameter_data[p])
            for p in self._secondary_processes_ordered_forwards
            if p.is_in_export_segment  # no secondary processes in transport segment
        }

        # parameter: merge speccost, add wacc
        # in export+transport sections and import section
        speccost = speccost_for_flh_opt.copy()
        parameter = {
            "WACC": parameter_data[self.initial_process]["WACC"],
            "SPECCOST": speccost,
        }
        for p in self._market_processes_ordered_forwards:
            if p.is_in_import_segment:
                # only export + transport segment
                continue
            for f, v in parameter_data[p]["SPECCOST"].items():  # type: ignore
                parameter["SPECCOST"][f] = v

        parameter_import = {
            "WACC": parameter_data[self.last_process].get("WACC", parameter["WACC"]),
            # FIXME remove later or update test data
            # gapfill parameter_import from parameter, old data did not
            # have some parameters for import countries
            "SPECCOST": parameter["SPECCOST"].copy(),
        }
        for p in self._market_processes_ordered_forwards:
            if not p.is_in_import_segment:
                continue
            for f, v in parameter_data[p]["SPECCOST"].items():  # type: ignore
                parameter_import["SPECCOST"][f] = v

        result: CalculateDataType = {
            "context": context,
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

    def _split_parameter_data(
        self,
        data: CalculateDataType,
    ) -> dict[Process, ProcessDataType]:
        parameter_data: dict[Process, ProcessDataType] = {}
        # TODO: data for main processes is list for each segment (exp, transp, imp)
        # we can get them by
        # - position (assuming order has not been messed with)
        # - they all SHOULD have a unique step - but thats not certain in the future
        # - process codes SHOULD also be unique, at least per segment, but thats
        #   also not guaranteed - there could be chains with multiple H2 storages

        for i, p in enumerate(
            p for p in self._main_processes_ordered_forwards if p.is_in_export_segment
        ):
            parameter_data[p] = data["main_export_process_chain"][i]
        for i, p in enumerate(
            p
            for p in self._main_processes_ordered_forwards
            if p.is_main_in_transport_segment
        ):
            parameter_data[p] = data["main_transport_process_chain"][i]
        for i, p in enumerate(
            p for p in self._main_processes_ordered_forwards if p.is_in_import_segment
        ):
            parameter_data[p] = data["main_import_process_chain"][i]

        # secondary processes: not in transport
        for p in self._secondary_processes_ordered_forwards:
            pdata = (
                data["secondary_process_import"]
                if p.is_in_import_segment
                else data["secondary_process"]
            )
            parameter_data[p] = pdata[p.main_flow_code_out]

        # market processes: if in transport - use data from exportsegment
        for p in self._market_processes_ordered_forwards:
            pdata = (
                data["parameter_import"]
                if p.is_in_import_segment
                else data["parameter"]
            )
            parameter_data[p] = {
                "SPECCOST": {
                    p.main_flow_code_out: pdata["SPECCOST"][p.main_flow_code_out]
                }
            }

        assert set(parameter_data) == set(self._graph.nodes())

        return parameter_data

    def _plot_get_pos(self) -> dict[Process, tuple[float, float]]:

        node_pos = {}

        x_start_import = None
        sgn = 1  # secondary process: offset sign should alternate between -1 and 1

        # main chain:
        x = 0
        for i, p in enumerate(self._main_processes_ordered_forwards):
            y = 0 if i > 0 else 0.25  # initial: offset a little
            node_pos[p] = (x, y)
            if p.is_in_import_segment and x_start_import is None:
                x_start_import = x
            x += 2

        if not x_start_import:
            x_start_import = x

        # secondary
        x_export = 0
        x_import = x_start_import
        for p in self._secondary_processes_ordered_forwards:
            if p.is_in_import_segment:
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
            if p.is_in_import_segment:
                x_import += 1
                x = x_import
            else:
                x_export += 1
                x = x_export
            y = 1.0
            node_pos[p] = (x, y)

        return node_pos


def _aggregate_results_df(
    df: pd.DataFrame, columns_index: list[str], columns_value: list[str] | None = None
) -> pd.DataFrame:
    columns_value = columns_value or ["values"]
    columns_all = columns_index + columns_value
    if df.empty:
        return pd.DataFrame(columns=columns_all)
    # drop if values is 0 ?
    # df = df.loc[~(df["values"] == 0)] # noqa
    return df[columns_all].groupby(columns_index).sum().reset_index()


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
        is_in_import_segment: bool = False,
    ):
        market_process = Process.create_with_subclass(
            process_code=flow_type,
            is_in_import_segment=is_in_import_segment,
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
        except HasACycle as exc:
            logger.warning(exc)
            create_and_link_market_process(
                proc_recipient=proc_recipient,
                flow_type=proc_provider.main_flow_code_out,
                in_main=in_main,
                is_in_import_segment=proc_recipient.is_in_import_segment,
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
        flow_code: FlowCodeType, is_in_import_segment: bool
    ) -> Process | None:
        providers = (
            flow_provider_sec_import
            if is_in_import_segment
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
                flow_code=flow_code, is_in_import_segment=process.is_in_import_segment
            )
            # special case: CSS (`CO2-T+S#B`) secondary processes can only get
            # their flows like EL from market, otherwise it can create loops
            if process.is_css:
                provider = None  # so we will use market process

            if provider:
                add_edge_or_create_market(
                    proc_provider=provider, proc_recipient=process, in_main=in_main
                )
            else:
                create_and_link_market_process(
                    proc_recipient=process,
                    flow_type=flow_code,
                    in_main=in_main,
                    is_in_import_segment=process.is_in_import_segment,
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


def _add_step_and_code(process: Process, data: ProcessDataType) -> ProcessDataType:
    return data | {  # type: ignore
        "process_code": process.process_code,
        "step": process.process_step,
    }
