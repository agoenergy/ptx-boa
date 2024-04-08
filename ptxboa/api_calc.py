# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import logging

import pandas as pd

from ptxboa.api_data import DataHandler
from ptxboa.static._types import CalculateDataType

logger = logging.getLogger()


def annuity(rate: float, periods: int, value: float) -> float:
    """Calculate annuity.

    Parameters
    ----------
    rate: float
        interest rate per period
    periods: int
        number of periods
    value: float
        present value of an ordinary annuity

    Returns
    -------
    : float
        value of each payment

    """
    if rate == 0:
        return value / periods
    else:
        return value * rate / (1 - (1 / (1 + rate) ** periods))


class PtxCalc:

    @staticmethod
    def calculate(data: CalculateDataType) -> pd.DataFrame:
        """Calculate results."""
        df_processes = DataHandler.get_dimension("process")
        df_flows = DataHandler.get_dimension("flow")

        # get general parameters
        parameters = data["parameter"]
        wacc = parameters["WACC"]
        storage_factor = parameters["STR-CF"]

        # start main chain calculation
        main_output_value = 1  # start with normalized value of 1

        # accumulate needed electric input
        sum_el = main_output_value
        results = []

        # iterate over steps in chain
        for step_data in data["main_process_chain"] + data["transport_process_chain"]:
            process_step = step_data["step"]
            process_code = step_data["process_code"]
            is_shipping_or_pre_post = process_step in {
                "PRE_SHP",
                "SHP",
                "SHP-OWN",
                "POST_SHP",
            }
            is_pipeline_or_pre_post = process_step in {
                "PRE_PPL",
                "PPLS",
                "PPL",
                "PPLX",
                "PPLR",
                "POST_PPL",
            }
            is_transport = process_step in {
                "SHP",
                "SHP-OWN",
                "PPLS",
                "PPL",
                "PPLX",
                "PPLR",
            }
            result_process_type = df_processes.at[process_code, "result_process_type"]

            main_input_value = main_output_value

            eff = step_data["EFF"]
            main_output_value = main_input_value * eff
            opex_o = step_data["OPEX-O"]

            if not is_transport:
                flh = step_data["FLH"]
                liefetime = step_data["LIFETIME"]
                capex = step_data["CAPEX"]
                opex_f = step_data["OPEX-F"]
                capacity = main_output_value / flh
                capex = capacity * capex
                capex_ann = annuity(wacc, liefetime, capex)
                opex = opex_f * capacity + opex_o * main_output_value

                results.append((result_process_type, process_code, "CAPEX", capex_ann))
                results.append((result_process_type, process_code, "OPEX", opex))

                if not (is_shipping_or_pre_post or is_pipeline_or_pre_post):
                    # no storage factor in transport pre/post
                    results.append(
                        (
                            "Electricity and H2 storage",
                            process_code,
                            "OPEX",  # NOTE: in old app,storage is always OPEX
                            capex_ann * storage_factor,
                        )
                    )
                    results.append(
                        (
                            "Electricity and H2 storage",
                            process_code,
                            "OPEX",
                            opex * storage_factor,
                        )
                    )
            else:
                opex_t = step_data["OPEX-T"]
                dist_transport = step_data["DIST"]
                opex_ot = opex_t * dist_transport
                opex = (opex_o + opex_ot) * main_output_value
                results.append((result_process_type, process_code, "OPEX", opex))

                if not (is_shipping_or_pre_post or is_pipeline_or_pre_post):
                    results.append(
                        (
                            "Electricity and H2 storage",
                            process_code,
                            "OPEX",
                            opex * storage_factor,
                        )
                    )
            # create flows for process step
            for flow_code, conv in step_data["CONV"].items():
                flow_value = main_output_value * conv

                sec_process_data = data["secondary_process"].get(flow_code)

                if sec_process_data:
                    # use secondary process
                    sec_process_code = sec_process_data["process_code"]
                    sec_result_process_type = df_processes.at[
                        sec_process_code, "result_process_type"
                    ]

                    # no FLH
                    liefetime = sec_process_data["LIFETIME"]
                    capex = sec_process_data["CAPEX"]
                    opex_f = sec_process_data["OPEX-F"]
                    opex_o = sec_process_data["OPEX-O"]

                    capacity = flow_value  # no FLH
                    capex = capacity * capex
                    capex_ann = annuity(wacc, liefetime, capex)
                    opex = opex_f * capacity + opex_o * flow_value

                    results.append(
                        (sec_result_process_type, sec_process_code, "CAPEX", capex_ann)
                    )
                    results.append(
                        (sec_result_process_type, sec_process_code, "OPEX", opex)
                    )
                    if not (is_shipping_or_pre_post or is_pipeline_or_pre_post):
                        results.append(
                            (
                                "Electricity and H2 storage",
                                sec_process_code,
                                "OPEX",  # NOTE: in old app, storage is always OPEX
                                capex_ann * storage_factor,
                            )
                        )
                        results.append(
                            (
                                "Electricity and H2 storage",
                                sec_process_code,
                                "OPEX",
                                opex * storage_factor,
                            )
                        )

                    for sec_flow_code, sec_conv in sec_process_data["CONV"].items():
                        sec_flow_value = flow_value * sec_conv
                        if sec_flow_code == "EL":
                            sum_el += sec_flow_value
                            # TODO: in this case: no cost?

                        sec_speccost = parameters["SPECCOST"][sec_flow_code]
                        sec_flow_cost = sec_flow_value * sec_speccost

                        sec_result_process_type = (
                            df_flows.at[sec_flow_code, "result_process_type"]
                            or sec_result_process_type
                        )

                        results.append(
                            (
                                sec_result_process_type,
                                sec_process_code,
                                "FLOW",
                                sec_flow_cost,
                            )
                        )
                        if not (is_shipping_or_pre_post or is_pipeline_or_pre_post):
                            results.append(
                                (
                                    "Electricity and H2 storage",
                                    sec_process_code,
                                    "OPEX",  # NOTE: in old app, storage is always OPEX
                                    sec_flow_cost * storage_factor,
                                )
                            )

                else:
                    # use market
                    speccost = parameters["SPECCOST"][flow_code]
                    if flow_code == "EL":
                        sum_el += flow_value
                        # TODO: in this case: no cost?
                    flow_cost = flow_value * speccost

                    # TODO: not nice
                    if is_transport:
                        flow_cost = flow_cost * dist_transport

                    flow_result_process_type = (
                        df_flows.at[flow_code, "result_process_type"]
                        or result_process_type
                    )

                    results.append(
                        (flow_result_process_type, process_code, "FLOW", flow_cost)
                    )
                    if not (is_shipping_or_pre_post or is_pipeline_or_pre_post):
                        results.append(
                            (
                                "Electricity and H2 storage",
                                process_code,
                                "OPEX",  # NOTE: in old app, storage is always OPEX
                                flow_cost * storage_factor,
                            )
                        )

        # convert to DataFrame
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        results = pd.DataFrame(results, columns=dim_columns + ["values"])

        # normalization:
        # scale so that we star twith 1 EL input,
        # rescale so that we have 1 unit output
        norm_factor = sum_el / main_output_value
        results["values"] = results["values"] * norm_factor

        return results
