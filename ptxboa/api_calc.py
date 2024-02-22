# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import logging

import pandas as pd

from ptxboa.api_data import CalculateDataType, DataHandler

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
    def __init__(self, data_handler: DataHandler):
        self.data_handler = data_handler

    def calculate(self, data: CalculateDataType) -> pd.DataFrame:
        """Calculate results."""
        # get process codes for selected chain
        df_processes = self.data_handler.get_dimension("process")
        df_flows = self.data_handler.get_dimension("flow")

        # some flows are grouped into their own output category (but not all)
        # so we load the mapping from the data

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        # get general parameters
        parameters = data["parameter"]
        wacc = parameters["WACC"]
        storage_factor = parameters["STR-CF"]

        # start main chain calculation
        main_output_value = 1  # start with normalized value of 1

        sum_el = main_output_value
        results = []

        for step_data in data["main_process_chain"] + data["transport_process_chain"]:
            process_step = step_data["step"]
            process_code = step_data["process_code"]
            is_shipping = process_step in {"PRE_SHP", "SHP", "SHP-OWN", "POST_SHP"}
            is_pipeline = process_step in {
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

                if not (is_shipping or is_pipeline):
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

                if not (is_shipping or is_pipeline):
                    results.append(
                        (
                            "Electricity and H2 storage",
                            process_code,
                            "OPEX",
                            opex * storage_factor,
                        )
                    )

            for flow_code, conv in step_data["CONV"].items():
                flow_value = main_output_value * conv

                sec_process_data = data["secondary_process"].get(flow_code)

                if sec_process_data:
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
                    if not (is_shipping or is_pipeline):
                        results.append(
                            (
                                "Electricity and H2 storage",
                                sec_process_code,
                                "OPEX",  # NOTE: in old app,storage is always OPEX
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
                        if not (is_shipping or is_pipeline):
                            results.append(
                                (
                                    "Electricity and H2 storage",
                                    sec_process_code,
                                    "OPEX",  # NOTE: in old app,storage is always OPEX
                                    sec_flow_cost * storage_factor,
                                )
                            )

                else:
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
                    if not (is_shipping or is_pipeline):
                        results.append(
                            (
                                "Electricity and H2 storage",
                                process_code,
                                "OPEX",  # NOTE: in old app,storage is always OPEX
                                flow_cost * storage_factor,
                            )
                        )

        # add additional storage cost

        # convert to DataFrame
        # TODO: fist one should be renamed to result_process_type
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        results = pd.DataFrame(results, columns=dim_columns + ["values"])

        # normalization
        norm_factor = sum_el / main_output_value
        results["values"] = results["values"] * norm_factor

        return results
