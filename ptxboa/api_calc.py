"""Classes for main process chain calculation."""

import logging
from dataclasses import asdict, dataclass
from typing import Optional

import pandas as pd

from ptxboa.api_data import DataHandler
from ptxboa.static._type_defs import CalculateDataType
from ptxboa.utils import annuity, rescale_dict

logger = logging.getLogger()


@dataclass(slots=True)
class ResultsFlows:
    process_code: str
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
    last_emissions: dict | None = None,
) -> dict:
    # TODO: speed up by not having to load process object every time?

    # flows_in:
    # CH3OH-L
    # CHX-L
    # DRI-S
    # H2-G
    # H2-L
    # NG-G
    # NG-L
    # NH3-L

    # flows_out: flows_in  and STL-S # noqa

    # flows_sec:

    # CH4-G
    # CO2-G
    # DIESEL-L
    # EL: indirect # noqa
    # HEAT: indirect # noqa
    # IOP-S
    # NG-G

    # EFF*:
    # BFUEL-L (unused?)
    # CH3OH-L (unused?)
    # CH4-G
    # CH4-L
    # CO2-C
    # CO2-G
    # DIESEL-L
    # EL
    # HEAT
    # NG-G
    # NG-L

    ch4_to_co2eq = 29.8
    g_co2_per_kg_C = 3664.446295
    g_ch4_per_kwh_lhv = 68.75469807

    FLOW_CO2_INDIRECT = {"HEAT", "EL"}  # TODO: from database?
    FLOW_CO2_ONLY_WHEN_EFF_TODO = {"NG-G", "CH4-G"}  # TODO: any others?
    FLOW_CO2_OTHER = {"STL-S"}
    is_transformation_changing_cbound = step_data["step"] in {
        "NG_PROD",
        "ELY",
        "DERIV",
        "DERIV2",
        "ELY_I",
        "DERIV_I",
        "DERIV_I2",
    }

    all_flows = results_flows.flows.copy()

    process_code = step_data["process_code"]

    # special case NG-PROD#B: has no main_flow_code_in
    if process_code == "NG-PROD#B":
        main_flow_code_in = main_flow_code_out

    if main_flow_code_in in all_flows:
        logger.error("Main flow codes (in) should not be in secondary flows")

    all_flows[main_flow_code_in] = results_flows.main_input

    CH4_KWH_PER_OUTPUT = step_data.get("CH4SHARE", {})  # only NG-G ?

    CBOUND_KG_C_PER_OUTPUT = step_data.get("CBOUND", {})  # in kgC/output
    # CH3OHSYC#B    CH3OH-L NG-G
    # CH3OHSYN#B    CH3OH-L CO2-G
    # EAF#B         STL-S   B-DRI-S
    # EFUELSYN#B    CHX-L   CO2-G
    # EFUELSYNC#B   CHX-L   NG-G
    # NG-DRI-C#B    DRI-S   CH4-G
    # NG-DRI-C#B    DRI-S   NG-G
    # NG-PROD#B     NG-G    NG-G
    if (
        main_flow_code_out in CBOUND_KG_C_PER_OUTPUT
        and main_flow_code_out not in results_flows.flows
        and process_code != "NG-PROD#B"
    ):
        logger.warning(
            "TODO: can CBOUND be set on main_flow_code_out %s %s?",
            process_code,
            main_flow_code_out,
        )

    # co2 capture fraction
    CO2CPTR_FRACTION = step_data.get("CO2CPT-R", {})  # only in NG-G or CH4-G
    CO2CPTS_FRACTION = step_data.get("CO2CPT-S", {})  # only in
    CO2CPT_FRACTION = {
        f: CO2CPTR_FRACTION.get(f, 0) * CO2CPTS_FRACTION.get(f, 0) for f in all_flows
    }

    # LOSS: only NG-G? - should also be CH4?
    LOSS_MAIN = step_data.get("LOSS", 0)
    LOSS_FLOW = step_data.get("LOSS_FLOW", {})

    _EF_M = step_data.get("EF_M", {})
    _EF_E = step_data.get("EF_E", {})

    EF_EM = {
        "M": {
            "INDIRECT": {k: v for k, v in _EF_M.items() if k in FLOW_CO2_INDIRECT},
            "DIRECT": {k: v for k, v in _EF_M.items() if k not in FLOW_CO2_INDIRECT},
        },
        "E": {
            "INDIRECT": {k: v for k, v in _EF_E.items() if k in FLOW_CO2_INDIRECT},
            "DIRECT": {k: v for k, v in _EF_E.items() if k not in FLOW_CO2_INDIRECT},
        },
    }

    # EF_E:
    # CH3OH-L
    # CH4-G
    # CH4-L
    # CO2-C
    # CO2-G
    # DIESEL-L
    # EL
    # HEAT
    # NG-G
    # NG-L

    # EF_M
    # BFUEL-L
    # CH3OH-L
    # CH4-G
    # CH4-L
    # CO2-C
    # CO2-G
    # DIESEL-L
    # EL
    # HEAT
    # NG-G
    # NG-L

    results_flows.main_input = results_flows.main_input

    def get_ch4_g_from_ng_loss(flow_code: str, loss_kwh_ng: float):
        # only NG-G?
        if not loss_kwh_ng:
            return 0
        ch4share = CH4_KWH_PER_OUTPUT.get(flow_code, 0)
        if not ch4share:
            logger.error(f"MISSING CH4SHARE for {flow_code}")
        return loss_kwh_ng * ch4share * g_ch4_per_kwh_lhv

    result = {}
    for em in ["e", "m"]:
        _EF = EF_EM[em.upper()]
        EF_DIRECT = _EF["DIRECT"]
        EF_INDIRECT = _EF["INDIRECT"]  # noqa

        def get_captured(flow_code: str, flow_net: float):
            return (
                flow_net
                * CO2CPT_FRACTION.get(flow_code, 0)
                * EF_DIRECT.get(flow_code, 0)
            )

        def get_in_co2(flow_code: str, flow_net: float):
            return flow_net * EF_DIRECT.get(flow_code, 0)

        main_input_net, main_input_loss = calculate_net_loss(
            results_flows.main_input, LOSS_MAIN
        )

        # co2_bound_in_product_last_proc: # row 46/54
        if last_emissions:
            co2_g_bound_last = last_emissions[f"co2_bound_in_product_{em}"]
        else:
            co2_g_bound_last = 0
        cbound_kg_c_per_output = CBOUND_KG_C_PER_OUTPUT.get(main_flow_code_in, 0)

        # row 47/55: FIXME: isnt this redundant to bound in product?
        co2_in_flows = get_in_co2(main_flow_code_in, main_input_net)

        co2_captured = get_captured(main_flow_code_in, main_input_net)  # row 48/56

        # line 65: ch4 leakage
        ch4_g_direct = get_ch4_g_from_ng_loss(main_flow_code_in, main_input_loss)

        for flow_code, flow_input_gross in results_flows.flows.items():
            # ignore negative flows
            if flow_input_gross <= 0:
                continue
            factor_loss_flow = LOSS_FLOW.get(flow_code, 0)

            flow_input_net, flow_input_loss = calculate_net_loss(
                flow_input_gross, factor_loss_flow
            )

            co2_in_flows += get_in_co2(flow_code, flow_input_net)
            ch4_g_direct += get_ch4_g_from_ng_loss(flow_code, flow_input_loss)
            co2_captured += get_captured(flow_code, flow_input_net)  # row 48/56

            cbound = CBOUND_KG_C_PER_OUTPUT.get(flow_code, 0)
            if cbound:
                # FLAG
                if flow_code in FLOW_CO2_ONLY_WHEN_EFF_TODO or (
                    flow_code in FLOW_CO2_OTHER and EF_DIRECT.get(flow_code, 0) > 0
                ):
                    cbound_kg_c_per_output += cbound

        if is_transformation_changing_cbound:
            # FIXME: this is not correct in excel (J57)
            co2_g_bound_in_product_out = (  # row 49/57
                results_flows.main_output * g_co2_per_kg_C * cbound_kg_c_per_output
            )
        else:
            if not results_flows.main_input:
                logger.error("main_input = 0 for non transformation step")
                co2_g_bound_in_product_out = co2_g_bound_last
            else:
                co2_g_bound_in_product_out = (
                    co2_g_bound_last
                    / results_flows.main_input
                    * results_flows.main_output
                )

        # indirect emissions (use EF_E for E and M balance?, only for HEAT and EL?)
        co2_indirect_scope2 = sum(
            flow_input_gross * EF_EM["E"]["INDIRECT"].get(flow_code, 0)
            for flow_code, flow_input_gross in results_flows.flows.items()
            # if flow_code in FLOW_CO2_INDIRECT
        )

        # simple sums / differences
        co2_direct = (  # row 51/59
            co2_g_bound_last - co2_g_bound_in_product_out + co2_in_flows - co2_captured
        )
        ch4_direct_co2e = ch4_g_direct * ch4_to_co2eq  # row 66
        co2e_total_direct = ch4_direct_co2e + co2_direct  # row 69/70

        result[f"co2_bound_in_product_last_proc_{em}"] = co2_g_bound_last  # row 46/54
        result[f"co2_in_flows_{em}"] = co2_in_flows  # row 47/55:
        result[f"co2_captured_{em}"] = co2_captured  # row 48/56:
        result[f"co2_bound_in_product_{em}"] = co2_g_bound_in_product_out  # row 49/57
        result[f"co2_direct_{em}"] = co2_direct  # row 51/59
        result[f"co2_indirect_scope2_{em}"] = co2_indirect_scope2  # 62
        result[f"ch4_direct_{em}"] = ch4_g_direct  # line 65
        result[f"ch4_direct_co2e_{em}"] = ch4_direct_co2e  # line 66
        result[f"co2e_total_direct_{em}"] = co2e_total_direct  # line 69/70

    return result


class PtxCalc:
    """Main module for chain calculation."""

    @staticmethod
    def calculate(
        data: CalculateDataType,
    ) -> tuple[list, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
        results_cost_items: list[tuple] = []
        results_emissions_e_g_co2e = []
        results_emissions_m_g_co2e = []

        results_flows_chain: list[ResultsFlows] = []
        last_emissions = {}

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
                process_code=process_code,
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

                results_cost_items.append(
                    (result_process_type, process_code, "CAPEX", capex_ann)
                )
                results_cost_items.append(
                    (result_process_type, process_code, "OPEX", opex)
                )

            else:
                step_before_transport = False
                opex_t = step_data["OPEX-T"]
                dist_transport = step_data["DIST"]
                opex_ot = opex_t * dist_transport
                opex = (opex_o + opex_ot) * main_output_value
                results_cost_items.append(
                    (result_process_type, process_code, "OPEX", opex)
                )

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

                    results_cost_items.append(
                        (sec_result_process_type, sec_process_code, "CAPEX", capex_ann)
                    )
                    results_cost_items.append(
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

                        results_cost_items.append(
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

                    results_cost_items.append(
                        (flow_result_process_type, process_code, "FLOW", flow_cost)
                    )

            proc = df_processes.loc[process_code]

            last_emissions = calculate_emissions(
                results_flows,
                step_data,
                proc.main_flow_code_in,
                proc.main_flow_code_out,
                last_emissions=last_emissions,
            )
            results_flows.emissions = last_emissions

            results_emissions_e_g_co2e.append(
                (
                    result_process_type,
                    process_code,
                    "indirect",
                    "CO2",
                    last_emissions["co2_indirect_scope2_e"],
                )
            )
            results_emissions_e_g_co2e.append(
                (
                    result_process_type,
                    process_code,
                    "direct",
                    "CO2",
                    last_emissions["co2_direct_e"],
                )
            )
            results_emissions_e_g_co2e.append(
                (
                    result_process_type,
                    process_code,
                    "direct",
                    "CH4",
                    last_emissions["ch4_direct_co2e_e"],
                )
            )

            results_emissions_m_g_co2e.append(
                (
                    result_process_type,
                    process_code,
                    "indirect",
                    "CO2",
                    last_emissions["co2_indirect_scope2_m"],
                )
            )
            results_emissions_m_g_co2e.append(
                (
                    result_process_type,
                    process_code,
                    "direct",
                    "CO2",
                    last_emissions["co2_direct_m"],
                )
            )
            results_emissions_m_g_co2e.append(
                (
                    result_process_type,
                    process_code,
                    "direct",
                    "CH4",
                    last_emissions["ch4_direct_co2e_m"],
                )
            )

        # add final emissions bound
        results_emissions_e_g_co2e.append(
            (
                "Bound in product",
                "Bound in product",
                "direct",
                "CO2",
                last_emissions["co2_bound_in_product_e"],
            )
        )
        results_emissions_m_g_co2e.append(
            (
                "Bound in product",
                "Bound in product",
                "direct",
                "CO2",
                last_emissions["co2_bound_in_product_m"],
            )
        )

        # convert to DataFrame
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        df_results_cost = pd.DataFrame(
            results_cost_items, columns=dim_columns + ["values"]
        )
        # sum over dim_columns
        df_results_cost = df_results_cost.groupby(dim_columns).sum().reset_index()

        dim_columns_emission = [
            "process_type",
            "process_subtype",
            "emission_type",
            "gas_type",
        ]
        df_results_emissions_e_g_co2e = (
            pd.DataFrame(
                results_emissions_e_g_co2e, columns=dim_columns_emission + ["values"]
            )
            .groupby(dim_columns_emission)
            .sum()
            .reset_index()
        )
        df_results_emissions_m_g_co2e = (
            pd.DataFrame(
                results_emissions_m_g_co2e, columns=dim_columns_emission + ["values"]
            )
            .groupby(dim_columns_emission)
            .sum()
            .reset_index()
        )

        # normalization:
        # scale so that we start with 1 EL input,
        # rescale so that we have 1 unit output
        norm_factor = 1 / main_output_value
        df_results_cost["values"] = df_results_cost["values"] * norm_factor
        df_results_emissions_e_g_co2e["values"] = (
            df_results_emissions_e_g_co2e["values"] * norm_factor
        )
        df_results_emissions_m_g_co2e["values"] = (
            df_results_emissions_m_g_co2e["values"] * norm_factor
        )

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
        idx = df_results_cost["process_type"] == "Electricity generation"
        if not idx.any():
            # TODO: in blue tool, we have no RES process, so should not warn
            pass
        else:
            norm_factor_el = sum_el
            df_results_cost.loc[idx, "values"] = (
                df_results_cost.loc[idx, "values"] * norm_factor_el
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

        return (
            results_flows_chain_,
            df_results_cost,
            df_results_emissions_e_g_co2e,
            df_results_emissions_m_g_co2e,
        )


def calculate_net_loss(value_gross: float, loss_factor: float) -> tuple[float, float]:
    """Losses, interpreted as additional to net.

    see https://github.com/agoenergy/ptx-boa/issues/581
    """
    value_net = value_gross / (1 + loss_factor)
    value_loss = value_net * loss_factor
    return value_net, value_loss
