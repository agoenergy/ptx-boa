"""Classes for main process chain calculation."""

import logging
from dataclasses import asdict, dataclass
from typing import Optional

import pandas as pd

from ptxboa.api_data import DataHandler
from ptxboa.static._types import CalculateDataType
from ptxboa.utils import annuity, rescale_dict

logger = logging.getLogger()


@dataclass(slots=True)
class ResultsFlows:
    process_step: str
    main_input: float
    main_output: float
    flows: dict[str, float]
    emissions: Optional[dict[str, float]] = None


def calculate_emissions(
    results_flows: ResultsFlows,
    step_data: dict,
    main_flow_code_in: str,
    main_flow_code_out: str,
) -> dict:
    # TODO: speedup by not having to load process object every time?

    CH4SHARE = step_data.get("CH4SHARE", {})
    CO2BOUND = step_data.get("CO2BOUND", {})

    CO2CPT = step_data.get("CO2CPT-R", 0) * step_data.get("CO2CPT-S", 0)
    EF_M = step_data.get("EF_M", {})

    METHANE_COeq = 29.8  # TODO

    # see https://github.com/agoenergy/ptx-boa/issues/581
    # Losses, interpreted as additional to net
    main_input_gross = results_flows.main_input
    factor_loss_main = step_data.get("LOSS", 0)
    main_input_net = main_input_gross / (1 + factor_loss_main)
    main_input_loss = main_input_net * factor_loss_main

    co2_bound_output = results_flows.main_output * CO2BOUND.get(main_flow_code_out, 0)

    co2_indirect = 0  # TODO: should we pass it on from step to step?
    co2_bound_input = main_input_net * CO2BOUND.get(main_flow_code_in, 0)
    co2_emission_direct = main_input_loss * CO2BOUND.get(main_flow_code_in, 0)
    methane_emission_direct = main_input_loss * CH4SHARE.get(main_flow_code_in, 0)

    parameters_loss_flow = step_data.get("LOSS_FLOW", {})
    for flow_code, flow_input_gross in results_flows.flows.items():
        # ignore negative flows
        if flow_input_gross <= 0:
            continue
        factor_loss_flow = parameters_loss_flow.get(flow_code, 0)
        flow_input_net = flow_input_gross / (1 + factor_loss_flow)
        flow_input_loss = flow_input_net * factor_loss_flow

        co2_indirect += flow_input_gross * EF_M.get(flow_code, 0)
        co2_bound_input += flow_input_net * CO2BOUND.get(flow_code, 0)
        co2_emission_direct += flow_input_loss * CO2BOUND.get(flow_code, 0)
        methane_emission_direct += flow_input_loss * CH4SHARE.get(main_flow_code_in, 0)

    co2_bound_delta = co2_bound_output - co2_bound_input
    co2_captured = co2_bound_delta * CO2CPT
    co2_emission_from_bound = co2_bound_delta - co2_captured

    co2e_emission_direct = co2_emission_direct + methane_emission_direct * METHANE_COeq

    return {
        "co2_indirect": co2_indirect,
        "co2_bound_output": co2_bound_output,
        "co2_captured": co2_captured,
        "co2_emission_from_bound": co2_emission_from_bound,
        "co2_emission_direct": co2_emission_direct,
        "co2e_emission_direct": co2e_emission_direct,
    }


class PtxCalc:
    """Main module for chain calculation."""

    @staticmethod
    def calculate(data: CalculateDataType) -> tuple[list, pd.DataFrame]:
        """Calculate results."""
        df_processes = DataHandler.get_dimension("process")
        df_flows = DataHandler.get_dimension("flow")

        # get general parameters
        parameters = data["parameter"]
        wacc = parameters["WACC"]

        # start main chain calculation
        main_output_value = 1  # start with normalized value of 1

        # pre-calculate main_output_value before transport
        # for correct scaling of storeages.
        # storage units use capacity factor CAP_F
        # per produced unit (before transport losses)
        main_output_value_before_transport = main_output_value
        for step_data in data["main_export_process_chain"]:
            main_output_value_before_transport *= step_data["EFF"]

        # accumulate needed electric input
        step_before_transport = True
        sum_el = main_output_value
        results_cost = []
        results_flows_chain: list[ResultsFlows] = []

        # iterate over steps in chain
        for step_data in (
            data["main_export_process_chain"]
            + data["transport_process_chain"]
            + data["main_import_process_chain"]
        ):
            process_step = step_data["step"]
            process_code = step_data["process_code"]
            is_transport = process_step in {
                "SHP",
                "SHP_OWN",
                "PPLS",
                "PPL",
                "PPLX",
                "PPLR",
            }
            result_process_type = df_processes.at[process_code, "result_process_type"]

            eff = step_data["EFF"]

            main_input_value = main_output_value
            # storage efficiency must not affect main chain scaling factors:
            if process_code not in ["EL-STR", "H2-STR"]:
                main_output_value = main_input_value * eff

            results_flows = ResultsFlows(
                process_step=process_step,
                main_input=main_input_value,
                main_output=main_output_value,
                flows={},
            )
            results_flows_chain.append(results_flows)

            opex_o = step_data["OPEX-O"]

            if not is_transport:
                flh = step_data["FLH"]
                lifetime = step_data["LIFETIME"]
                capex_rel = step_data["CAPEX"]
                opex_f = step_data["OPEX-F"]

                if "CAP_F" in step_data:
                    # Storage unit: capacity
                    # TODO: double check units (division by 8760 h)?
                    capacity = (
                        main_output_value_before_transport * step_data["CAP_F"] / 8760
                    )
                else:
                    capacity = main_output_value / flh

                capex = capacity * capex_rel
                capex_ann = annuity(wacc, lifetime, capex)
                opex = opex_f * capacity + opex_o * main_output_value

                results_cost.append(
                    (result_process_type, process_code, "CAPEX", capex_ann)
                )
                results_cost.append((result_process_type, process_code, "OPEX", opex))

            else:
                step_before_transport = False
                opex_t = step_data["OPEX-T"]
                dist_transport = step_data["DIST"]
                opex_ot = opex_t * dist_transport
                opex = (opex_o + opex_ot) * main_output_value
                results_cost.append((result_process_type, process_code, "OPEX", opex))

            # create flows for process step
            for flow_code, conv in step_data["CONV"].items():
                flow_value = main_output_value * conv
                results_flows.flows[flow_code] = flow_value

                sec_process_data = data["secondary_process"].get(flow_code)

                if sec_process_data:
                    # use secondary process
                    sec_process_code = sec_process_data["process_code"]
                    sec_result_process_type = df_processes.at[
                        sec_process_code, "result_process_type"
                    ]

                    # no FLH
                    lifetime = sec_process_data["LIFETIME"]
                    capex = sec_process_data["CAPEX"]
                    opex_f = sec_process_data["OPEX-F"]
                    opex_o = sec_process_data["OPEX-O"]

                    capacity = flow_value  # no FLH
                    capex = capacity * capex
                    capex_ann = annuity(wacc, lifetime, capex)
                    opex = opex_f * capacity + opex_o * flow_value

                    results_cost.append(
                        (sec_result_process_type, sec_process_code, "CAPEX", capex_ann)
                    )
                    results_cost.append(
                        (sec_result_process_type, sec_process_code, "OPEX", opex)
                    )

                    for sec_flow_code, sec_conv in sec_process_data["CONV"].items():
                        sec_flow_value = flow_value * sec_conv

                        # electricity before transport will be handled by RES step
                        # after transport: market
                        if sec_flow_code == "EL" and step_before_transport:
                            sum_el += sec_flow_value
                            # do not add SPECCOST below
                            continue

                        sec_speccost = parameters["SPECCOST"][sec_flow_code]
                        sec_flow_cost = sec_flow_value * sec_speccost

                        sec_result_process_type = (
                            df_flows.at[sec_flow_code, "result_process_type"]
                            or sec_result_process_type
                        )

                        results_cost.append(
                            (
                                sec_result_process_type,
                                sec_process_code,
                                "FLOW",
                                sec_flow_cost,
                            )
                        )

                else:
                    # use market
                    speccost = parameters["SPECCOST"][flow_code]

                    # electricity before transport will be handled by RES step
                    # after transport: market
                    if flow_code == "EL" and step_before_transport:
                        sum_el += flow_value
                        # do not add SPECCOST below
                        continue

                    flow_cost = flow_value * speccost

                    if is_transport:
                        flow_cost = flow_cost * dist_transport

                    flow_result_process_type = (
                        df_flows.at[flow_code, "result_process_type"]
                        or result_process_type
                    )

                    results_cost.append(
                        (flow_result_process_type, process_code, "FLOW", flow_cost)
                    )

            proc = df_processes.loc[process_code]

            results_flows.emissions = calculate_emissions(
                results_flows,
                step_data,
                proc.main_flow_code_in,
                proc.main_flow_code_out,
            )

        # convert to DataFrame
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        results_cost = pd.DataFrame(results_cost, columns=dim_columns + ["values"])

        # sum over dim_columns
        results_cost = results_cost.groupby(dim_columns).sum().reset_index()

        # normalization:
        # scale so that we start with 1 EL input,
        # rescale so that we have 1 unit output
        norm_factor = 1 / main_output_value
        results_cost["values"] = results_cost["values"] * norm_factor

        # rescale values
        for results_flows in results_flows_chain:
            results_flows.main_output *= norm_factor
            results_flows.main_input *= norm_factor
            results_flows.flows = rescale_dict(results_flows.flows, norm_factor)
            if results_flows.emissions:
                results_flows.emissions = rescale_dict(
                    results_flows.emissions, norm_factor
                )

        # rescale again ONLY RES to account for additionally needed electricity
        # sum_el is larger than 1.0

        # TODO: for blue hydrogen chains, there is no RES
        idx = results_cost["process_type"] == "Electricity generation"
        if not idx.any():
            # TODO: in blue tool, we have no RES process, so should not warn
            pass
        else:
            norm_factor_el = sum_el
            results_cost.loc[idx, "values"] = (
                results_cost.loc[idx, "values"] * norm_factor_el
            )
            # rescale values
            for results_flows in [
                rf for rf in results_flows_chain if rf.process_step == "RES"
            ]:
                results_flows.main_output *= norm_factor_el
                results_flows.main_input *= norm_factor_el
                results_flows.flows = rescale_dict(results_flows.flows, norm_factor_el)
                if results_flows.emissions:
                    results_flows.emissions = rescale_dict(
                        results_flows.emissions, norm_factor_el
                    )

        # TODO: currently for testing, we return dicts, not ResultsFlows
        results_flows_chain_ = [asdict(rf) for rf in results_flows_chain]
        return results_flows_chain_, results_cost
