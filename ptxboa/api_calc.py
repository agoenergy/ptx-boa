# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""


import pandas as pd

from ptxboa.api_data import DataHandler
from ptxboa.static._types import CalculateDataType
from ptxboa.utils import annuity


class PtxCalc:

    @staticmethod
    def calculate(data: CalculateDataType) -> pd.DataFrame:
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
        for step_data in data["main_process_chain"]:
            main_output_value_before_transport *= step_data["EFF"]

        # accumulate needed electric input
        step_before_transport = True
        sum_el = main_output_value
        results = []

        # iterate over steps in chain
        for step_data in data["main_process_chain"] + data["transport_process_chain"]:
            process_step = step_data["step"]
            process_code = step_data["process_code"]
            is_transport = process_step in {
                "SHP",
                "SHP-OWN",
                "PPLS",
                "PPL",
                "PPLX",
                "PPLR",
            }
            result_process_type = df_processes.at[process_code, "result_process_type"]

            eff = step_data["EFF"]

            # storage efficiency must not affect main chain scaling factors:
            if process_code not in ["EL-STR", "H2-STR"]:
                main_input_value = main_output_value
                main_output_value = main_input_value * eff

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

                results.append((result_process_type, process_code, "CAPEX", capex_ann))
                results.append((result_process_type, process_code, "OPEX", opex))

            else:
                step_before_transport = False
                opex_t = step_data["OPEX-T"]
                dist_transport = step_data["DIST"]
                opex_ot = opex_t * dist_transport
                opex = (opex_o + opex_ot) * main_output_value
                results.append((result_process_type, process_code, "OPEX", opex))

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
                    lifetime = sec_process_data["LIFETIME"]
                    capex = sec_process_data["CAPEX"]
                    opex_f = sec_process_data["OPEX-F"]
                    opex_o = sec_process_data["OPEX-O"]

                    capacity = flow_value  # no FLH
                    capex = capacity * capex
                    capex_ann = annuity(wacc, lifetime, capex)
                    opex = opex_f * capacity + opex_o * flow_value

                    results.append(
                        (sec_result_process_type, sec_process_code, "CAPEX", capex_ann)
                    )
                    results.append(
                        (sec_result_process_type, sec_process_code, "OPEX", opex)
                    )

                    for sec_flow_code, sec_conv in sec_process_data["CONV"].items():
                        sec_flow_value = flow_value * sec_conv

                        # electricity before transport will be handled by RES step
                        # after transport: market
                        if sec_flow_code == "EL":
                            if step_before_transport:
                                sum_el += sec_flow_value
                            else:
                                # do not add SPECCOST below
                                continue

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

                else:
                    # use market
                    speccost = parameters["SPECCOST"][flow_code]

                    # electricity before transport will be handled by RES step
                    # after transport: market
                    if flow_code == "EL":
                        if step_before_transport:
                            sum_el += sec_flow_value
                        else:
                            # do not add SPECCOST below
                            continue

                    flow_cost = flow_value * speccost

                    if is_transport:
                        flow_cost = flow_cost * dist_transport

                    flow_result_process_type = (
                        df_flows.at[flow_code, "result_process_type"]
                        or result_process_type
                    )

                    results.append(
                        (flow_result_process_type, process_code, "FLOW", flow_cost)
                    )

        # convert to DataFrame
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        results = pd.DataFrame(results, columns=dim_columns + ["values"])

        # sum over dim_columns
        results = results.groupby(dim_columns).sum().reset_index()

        # normalization:
        # scale so that we start with 1 EL input,
        # rescale so that we have 1 unit output
        norm_factor = 1 / main_output_value
        results["values"] = results["values"] * norm_factor

        # rescale again ONLY RES to account for additionally needed electricity
        # sum_el is larger than 1.0
        norm_factor_el = sum_el
        idx = results["process_type"] == "Electricity generation"
        assert idx.any()  # must have at least one entry
        results.loc[idx, "values"] = results.loc[idx, "values"] * norm_factor_el

        return results
