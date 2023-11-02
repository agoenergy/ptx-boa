# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import pandas as pd


def get_from_dict(dct, key, msg=None):
    """Raise detailed KeyError."""
    try:
        return dct[key]
    except KeyError:
        msg = f"{msg}: " if msg else ""
        raise KeyError(f"{msg}'{key}' not in {list(dct)}.")


def get_from_df(df, key, msg=None):
    """Raise detailed KeyError."""
    try:
        return df.loc[key]
    except KeyError:
        msg = f"{msg}: " if msg else ""
        raise KeyError(f"{msg}'{key}' not in {list(df.index)}.")


def pmt(r, n, v):
    if r == 0:
        return v / n
    else:
        return v * r / (1 - (1 / (1 + r) ** n))


class PtxCalc:
    def __init__(
        self,
        data_handler,
    ):
        self.data_handler = data_handler

    def calculate(
        self,
        secproc_co2_code,
        secproc_water_code,
        chain,
        process_code_res,
        source_region_code,
        target_country_code,
        use_ship,
        ship_own_fuel,
        output_unit,
    ):
        """Calculate results."""
        # get process codes for selected chain
        chain_dim = self.data_handler.get_dimension("chain")
        process_dim = self.data_handler.get_dimension("process")
        chain_attrs = get_from_df(chain_dim, chain, "chains")
        process_code_ely = chain_attrs["ELY"]
        process_code_deriv = chain_attrs["DERIV"]
        chain_flow_out = chain_attrs["FLOW_OUT"]

        assert output_unit in {"USD/MWh", "USD/t"}

        if output_unit == "USD/t":
            output_factor = (
                self.data_handler.get_parameter_value(
                    parameter_code="CALOR", flow_code=chain_flow_out
                )
                * 1000
            )
        else:
            output_factor = 1000  # kWh => MWh

        # some flows are grouped into their own output category (but not all)
        # so we load the mapping from the data
        flow_dim = self.data_handler.get_dimension("flow")
        flow_code_to_result_process_type = dict(
            flow_dim.loc[flow_dim["result_process_type"] != "", "result_process_type"]
        )
        secondary_processes = {}
        if secproc_water_code:
            secondary_processes["H2O-L"] = secproc_water_code
        if secproc_co2_code:
            secondary_processes["CO2-G"] = secproc_co2_code

        def get_parameter_value(
            parameter_code, process_code="", flow_code="", default=None
        ):
            try:
                return self.data_handler.get_parameter_value(
                    parameter_code=parameter_code,
                    process_code=process_code,
                    flow_code=flow_code,
                    source_region_code=source_region_code,
                    target_country_code=target_country_code,
                    process_code_ely=process_code_ely,
                    process_code_deriv=process_code_deriv,
                    process_code_res=process_code_res,
                )
            except Exception:
                if default is not None:
                    return default
                raise

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        main_output_value = 1  # start with normalized value of 1
        sum_el = main_output_value
        results = []

        wacc = get_parameter_value("WACC")

        dist_pipeline = get_parameter_value("DST-S-DP", default=0)
        dist_transport_land = 0
        use_retrofitted_pipeline = False
        no_transport = source_region_code == target_country_code  # only China

        if dist_pipeline and not use_ship:
            use_ship = False
            seashare_pipeline = get_parameter_value("SEASHARE", default=0)
            dist_transport_sea = dist_pipeline * seashare_pipeline
            dist_transport_land = dist_pipeline * (1 - seashare_pipeline)
            existing_pipeline_cap = get_parameter_value("CAP-T", default=0)
            if existing_pipeline_cap > 0:
                use_retrofitted_pipeline = True
        else:
            dist_transport_land = 0
            if no_transport:
                use_ship = False
                dist_transport_sea = 0
            else:
                use_ship = True
                dist_ship = get_parameter_value("DST-S-D", default=0)
                # TODO:
                dist_transport_sea = dist_ship

        def create_capex_opex(result_process_type, process_code, main_output_value):
            flh = get_parameter_value(
                "FLH", process_code=process_code, default=7000
            )  # TODO
            liefetime = get_parameter_value(
                "LIFETIME", process_code=process_code, default=20  # TODO
            )
            capex = get_parameter_value(
                "CAPEX", process_code=process_code, default=0
            )  # TODO
            opex_f = get_parameter_value("OPEX-F", process_code=process_code, default=0)
            opex_o = get_parameter_value("OPEX-O", process_code=process_code, default=0)

            capacity = main_output_value / flh
            capex = capacity * capex
            capex_ann = pmt(wacc, liefetime, capex)
            opex = opex_f * capacity + opex_o * main_output_value

            results.append((result_process_type, process_code, "CAPEX", capex_ann))
            results.append((result_process_type, process_code, "OPEX", opex))

        def create_capex_opex_sec(result_process_type, process_code, main_output_value):
            # no FLH
            liefetime = get_parameter_value(
                "LIFETIME", process_code=process_code, default=20  # TODO
            )
            capex = get_parameter_value(
                "CAPEX", process_code=process_code, default=0
            )  # TODO
            opex_f = get_parameter_value("OPEX-F", process_code=process_code, default=0)
            opex_o = get_parameter_value("OPEX-O", process_code=process_code, default=0)

            capacity = main_output_value  # no FLH
            capex = capacity * capex
            capex_ann = pmt(wacc, liefetime, capex)
            opex = opex_f * capacity + opex_o * main_output_value

            results.append((result_process_type, process_code, "CAPEX", capex_ann))
            results.append((result_process_type, process_code, "OPEX", opex))

        def create_opex_transp(
            result_process_type, process_code, main_output_value, distance
        ):
            # TODO: maybe should be input, not output value
            opex_t = get_parameter_value("OPEX-T", process_code=process_code, default=0)
            opex_o = get_parameter_value("OPEX-O", process_code=process_code, default=0)
            opex_ot = opex_t * distance
            opex = (opex_o + opex_ot) * main_output_value
            results.append((result_process_type, process_code, "OPEX", opex))

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
                process_code = chain_attrs[process_step]

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
            if not process_code:
                continue
            elif is_shipping and not use_ship:
                continue
            elif is_pipeline and use_ship:
                continue
            elif ship_own_fuel and process_step == "SHP":
                continue
            elif not ship_own_fuel and process_step == "SHP-OWN":
                continue
            elif use_retrofitted_pipeline and process_step in {"PPLS", "PPL"}:
                continue
            elif not use_retrofitted_pipeline and process_step in {"PPLX", "PPLR"}:
                continue
            elif is_transport and no_transport:
                continue

            if is_transport:
                if use_ship:
                    dist_transport = dist_transport_sea
                else:  # pipeline
                    is_land = process_code.split("-")[-1] in {"L", "LR"}
                    if is_land:
                        dist_transport = dist_transport_land
                    else:
                        dist_transport = dist_transport_sea
                loss_t = get_parameter_value("LOSS-T", process_code=process_code)
                eff = 1 - loss_t * dist_transport
            else:
                eff = get_parameter_value("EFF", process_code=process_code, default=1)

            main_input_value = main_output_value
            main_output_value = main_input_value * eff

            process_attrs = get_from_df(process_dim, process_code, "process")

            if not is_transport:
                create_capex_opex(
                    process_attrs["result_process_type"],
                    process_code,
                    main_output_value,
                )
            else:
                create_opex_transp(
                    process_attrs["result_process_type"],
                    process_code,
                    main_output_value,
                    distance=dist_transport,
                )

            secondary_flows = process_attrs["secondary_flows"].split("/")
            for flow_code in secondary_flows:
                conv = get_parameter_value(
                    parameter_code="CONV",
                    process_code=process_code,
                    flow_code=flow_code,
                    default=0,
                )
                if conv <= 0:
                    continue
                flow_value = main_output_value * conv
                if flow_code in secondary_processes:
                    sec_process_code = secondary_processes[flow_code]
                    sec_process_attrs = get_from_df(
                        process_dim, sec_process_code, "process"
                    )

                    sec_result_process_type = sec_process_attrs["result_process_type"]
                    create_capex_opex_sec(
                        sec_result_process_type,
                        sec_process_code,
                        flow_value,
                    )

                    sec_secondary_flows = sec_process_attrs["secondary_flows"].split(
                        "/"
                    )
                    for sec_flow_code in sec_secondary_flows:
                        sec_conv = get_parameter_value(
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

                        sec_speccost = get_parameter_value(
                            "SPECCOST", flow_code=sec_flow_code
                        )
                        sec_flow_cost = sec_flow_value * sec_speccost
                        sec_result_process_type = flow_code_to_result_process_type.get(
                            sec_flow_code, sec_process_attrs["result_process_type"]
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
                    speccost = get_parameter_value("SPECCOST", flow_code=flow_code)
                    if flow_code == "EL":
                        sum_el += flow_value
                        # TODO: in this case: no cost?
                    flow_cost = flow_value * speccost

                    # TODO: not nice
                    if is_transport:
                        flow_cost = flow_cost * dist_transport

                    result_process_type = flow_code_to_result_process_type.get(
                        flow_code, process_attrs["result_process_type"]
                    )

                    results.append(
                        (result_process_type, process_code, "FLOW", flow_cost)
                    )

        # TODO: fist one should be renamed to result_process_type
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        # convert results in Dataframe (maybe aggregate some?)

        results = pd.DataFrame(
            results,
            columns=dim_columns + ["values"],
        )

        # TODO: maybe not required: aggregate over all key columns
        # in case some processes create data with the same categories

        # no longer required: results = results.loc[results["values"] > 0]

        # TODO: apply output_unit conversion on
        # simple sacling (TODO: EL, UNIT)
        norm_factor = sum_el / main_output_value
        results["values"] = results["values"] * norm_factor * output_factor

        # storage factor on final costs
        storage_factor = get_parameter_value("STR-CF")
        # apply storage_factor to everything except Transport
        selector = ~(
            (results["process_type"] == "Transportation (Pipeline)")
            | (results["process_type"] == "Transportation (Ship)")
        )
        cost_wo_storage = results.loc[selector, "values"].sum()
        cost_storage = cost_wo_storage * storage_factor
        results = pd.concat(
            [
                results,
                pd.DataFrame(
                    [("Electricity and H2 storage", "Storage", "OPEX", cost_storage)],
                    columns=dim_columns + ["values"],
                ),
            ],
            ignore_index=True,
        )

        return results
