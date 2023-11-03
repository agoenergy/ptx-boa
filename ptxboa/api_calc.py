# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import logging

import pandas as pd

from ptxboa.api_data import DataHandler


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


def calculate(
    data_handler: DataHandler,
    secondary_processes: dict,
    chain: dict,
    process_code_res: str,
    source_region_code: str,
    target_country_code: str,
    use_ship: bool,
    ship_own_fuel: bool,
) -> pd.DataFrame:
    """Calculate results."""
    # get process codes for selected chain
    df_processes = data_handler.get_dimension("process")
    df_flows = data_handler.get_dimension("flow")

    process_code_ely = chain["ELY"]
    process_code_deriv = chain["DERIV"]

    def get_parameter_value_w_default(
        parameter_code, process_code="", flow_code="", default=None
    ):
        try:
            return data_handler.get_parameter_value(
                parameter_code=parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                source_region_code=source_region_code,
                target_country_code=target_country_code,
                process_code_res=process_code_res,
                process_code_ely=process_code_ely,
                process_code_deriv=process_code_deriv,
            )
        except Exception:
            if default is not None:
                return default
            raise

    # some flows are grouped into their own output category (but not all)
    # so we load the mapping from the data

    # iterate over main chain, update the value in the main flow
    # and accumulate result data from each process

    wacc = get_parameter_value_w_default("WACC")

    dist_pipeline = get_parameter_value_w_default(
        "DST-S-DP",
        default=0,
    )
    dist_transport_land = 0
    use_retrofitted_pipeline = False
    no_transport = source_region_code == target_country_code  # only China

    if dist_pipeline and not use_ship:
        use_ship = False
        seashare_pipeline = get_parameter_value_w_default("SEASHARE", default=0)
        dist_transport_sea = dist_pipeline * seashare_pipeline
        dist_transport_land = dist_pipeline * (1 - seashare_pipeline)
        existing_pipeline_cap = get_parameter_value_w_default("CAP-T", default=0)
        if existing_pipeline_cap > 0:
            use_retrofitted_pipeline = True
    else:
        dist_transport_land = 0
        if no_transport:
            use_ship = False
            dist_transport_sea = 0
        else:
            use_ship = True
            dist_ship = get_parameter_value_w_default("DST-S-D", default=0)
            # TODO:
            dist_transport_sea = dist_ship

    def create_capex_opex_sec(result_process_type, process_code, main_output_value):
        # no FLH
        liefetime = get_parameter_value_w_default(
            "LIFETIME", process_code=process_code, default=20  # TODO
        )
        capex = get_parameter_value_w_default(
            "CAPEX", process_code=process_code, default=0
        )  # TODO
        opex_f = get_parameter_value_w_default(
            "OPEX-F", process_code=process_code, default=0
        )
        opex_o = get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )

        capacity = main_output_value  # no FLH
        capex = capacity * capex
        capex_ann = annuity(wacc, liefetime, capex)
        opex = opex_f * capacity + opex_o * main_output_value

        results.append((result_process_type, process_code, "CAPEX", capex_ann))
        results.append((result_process_type, process_code, "OPEX", opex))

    main_output_value = 1  # start with normalized value of 1
    main_flow_code_out = ""
    sum_el = main_output_value
    results = []

    for process_step in [
        "RES",
        "ELY",
        "DERIV",
        "PRE_SHP",
        "SHP",
        "SHP-OWN",
        "POST_SHP",
        "PRE_PPL",
        "PPLS",
        "PPL",
        "PPLX",
        "PPLR",
        "POST_PPL",
    ]:
        if process_step == "RES":
            process_code = process_code_res
        else:
            process_code = chain[process_step]
            if not process_code:
                continue

        # TODO: precalculate in data
        is_shipping = process_step in {"PRE_SHP", "SHP", "SHP-OWN", "POST_SHP"}
        is_retrofitted = process_step in {"PPLX", "PPLR"}
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
        is_own_fuel = process_step == "SHP-OWN"
        is_land = process_code.split("-")[-1] in {"L", "LR"}

        # filter if process can be skipped
        if is_shipping and not use_ship:
            continue
        elif is_pipeline and use_ship:
            continue
        elif ship_own_fuel and is_shipping and is_transport and not is_own_fuel:
            continue
        elif not ship_own_fuel and is_own_fuel:
            continue
        elif (
            use_retrofitted_pipeline
            and not is_retrofitted
            and is_pipeline
            and is_transport
        ):
            continue
        elif not use_retrofitted_pipeline and is_retrofitted:
            continue
        elif is_transport and no_transport:
            continue

        if is_transport:
            if use_ship:
                dist_transport = dist_transport_sea
            else:  # pipeline
                if is_land:
                    dist_transport = dist_transport_land
                else:
                    dist_transport = dist_transport_sea
            loss_t = get_parameter_value_w_default("LOSS-T", process_code=process_code)
            eff = 1 - loss_t * dist_transport
        else:
            eff = get_parameter_value_w_default(
                "EFF", process_code=process_code, default=1
            )

        # check
        ds_process = df_processes.loc[process_code]
        main_flow_code_in = ds_process["main_flow_code_in"]
        if main_flow_code_in != main_flow_code_out:
            logging.error(
                f"process {process_step}={process_code} has "
                f"main_flow_code_in {main_flow_code_in}, "
                f"last output was {main_flow_code_out}"
            )
        main_flow_code_out = ds_process["main_flow_code_out"]

        main_input_value = main_output_value
        main_output_value = main_input_value * eff
        result_process_type = ds_process["result_process_type"]

        opex_o = get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )

        if not is_transport:
            flh = get_parameter_value_w_default(
                "FLH", process_code=process_code, default=7000
            )  # TODO
            liefetime = get_parameter_value_w_default(
                "LIFETIME", process_code=process_code, default=20  # TODO
            )
            capex = get_parameter_value_w_default(
                "CAPEX", process_code=process_code, default=0
            )  # TODO
            opex_f = get_parameter_value_w_default(
                "OPEX-F", process_code=process_code, default=0
            )

            capacity = main_output_value / flh
            capex = capacity * capex
            capex_ann = annuity(wacc, liefetime, capex)
            opex = opex_f * capacity + opex_o * main_output_value

            results.append((result_process_type, process_code, "CAPEX", capex_ann))
            results.append((result_process_type, process_code, "OPEX", opex))

        else:
            opex_t = get_parameter_value_w_default(
                "OPEX-T", process_code=process_code, default=0
            )
            opex_ot = opex_t * dist_transport
            opex = (opex_o + opex_ot) * main_output_value
            results.append((result_process_type, process_code, "OPEX", opex))

        secondary_flows = ds_process["secondary_flows"].split("/")
        for flow_code in secondary_flows:
            conv = get_parameter_value_w_default(
                parameter_code="CONV",
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if conv <= 0:
                continue
            flow_value = main_output_value * conv
            sec_process_code = secondary_processes.get(flow_code)
            if sec_process_code:
                sec_process_attrs = df_processes.loc[sec_process_code]

                sec_result_process_type = sec_process_attrs["result_process_type"]

                # no FLH
                liefetime = get_parameter_value_w_default(
                    "LIFETIME", process_code=sec_process_code, default=20  # TODO
                )
                capex = get_parameter_value_w_default(
                    "CAPEX", process_code=sec_process_code, default=0
                )  # TODO
                opex_f = get_parameter_value_w_default(
                    "OPEX-F", process_code=sec_process_code, default=0
                )
                opex_o = get_parameter_value_w_default(
                    "OPEX-O", process_code=sec_process_code, default=0
                )

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

                sec_secondary_flows = sec_process_attrs["secondary_flows"].split("/")
                for sec_flow_code in sec_secondary_flows:
                    sec_conv = get_parameter_value_w_default(
                        parameter_code="CONV",
                        process_code=sec_process_code,
                        flow_code=sec_flow_code,
                        default=0,
                    )
                    if sec_conv <= 0:
                        continue
                    sec_flow_value = flow_value * sec_conv
                    if sec_flow_code == "EL":
                        sum_el += sec_flow_value
                        # TODO: in this case: no cost?

                    sec_speccost = get_parameter_value_w_default(
                        "SPECCOST", flow_code=sec_flow_code
                    )
                    sec_flow_cost = sec_flow_value * sec_speccost

                    sec_result_process_type = (
                        df_flows.at[sec_flow_code, "result_process_type"]
                        or sec_process_attrs["result_process_type"]
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
                speccost = get_parameter_value_w_default(
                    "SPECCOST", flow_code=flow_code
                )
                if flow_code == "EL":
                    sum_el += flow_value
                    # TODO: in this case: no cost?
                flow_cost = flow_value * speccost

                # TODO: not nice
                if is_transport:
                    flow_cost = flow_cost * dist_transport

                result_process_type = (
                    df_flows.at[flow_code, "result_process_type"]
                    or ds_process["result_process_type"]
                )

                results.append((result_process_type, process_code, "FLOW", flow_cost))

    # add additional storage cost
    cost_wo_storage = sum(
        r[3]
        for r in results
        if r[0] not in {"Transportation (Pipeline)", "Transportation (Ship)"}
    )
    storage_factor = get_parameter_value_w_default("STR-CF")
    cost_storage = cost_wo_storage * storage_factor
    results.append(("Electricity and H2 storage", "Storage", "OPEX", cost_storage))

    # convert to DataFrame
    # TODO: fist one should be renamed to result_process_type
    dim_columns = ["process_type", "process_subtype", "cost_type"]
    results = pd.DataFrame(results, columns=dim_columns + ["values"])

    # normalization
    norm_factor = sum_el / main_output_value
    results["values"] = results["values"] * norm_factor

    return results
