"""export some results for new blue chain for evaluation.

- creates one result for each blue chain
- combine intermediate results for flows, emissions, costs
- save in excel: one sheet per result, one column per process



"""

from typing import Any, Iterable

import pandas as pd

from ptxboa.api import PtxboaAPI
from ptxboa.api_calc import get_secproc_step
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler


def flatten_dict(v: Any, key_prefix: None | str = None) -> Iterable[tuple[str, Any]]:
    if isinstance(v, list):
        raise NotImplementedError(v)
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            yield from flatten_dict(
                v2, key_prefix=k2 if key_prefix is None else f"{key_prefix}:{k2}"
            )
    else:  # scalar
        if not key_prefix:
            raise NotImplementedError(v)
        yield (key_prefix, v)


def list_to_dict_by_step(d: list) -> dict:
    return {(s.get("step") or s.get("process_step")): s for s in d}


STEPS = [
    "NG_PROD",
    # "EL_STR",
    # "H2_STR",
    "ELY",
    "DERIV",
    "DERIV2",
    # "CO2_TS",
    "PRE_SHP",
    "SHP",
    "SHP_OWN",
    "POST_SHP",
    "PRE_PPL",
    "PPLS",
    "PPL",
    "PPLX",
    "PPLR",
    "POST_PPL",
    "ELY_I",
    "DERIV_I",
    "DERIV_I2",
    # "CO2_TS_I",
    "SECONDARY:Carbon",
    "SECONDARY:CO2 transport and storage",
    "SECONDARY:Electricity generation",
    "SECONDARY:Heat",
    "SECONDARY:Water",
]

rows = [
    "0:settings:chain",
    "0:settings:country",
    "0:settings:output_unit_cost",
    "0:settings:output_unit_data",
    "0:settings:region",
    "0:settings:scenario",
    "0:settings:secproc_co2",
    "0:settings:secproc_water",
    "0:settings:transport",
    "0:process:main_flow_code_in",
    "0:process:main_flow_code_out",
    "0:process:process_code",
    "1:parameter:CALOR",
    "1:parameter:SPECCOST:CO2-G",
    "1:parameter:SPECCOST:DIESEL-L",
    "1:parameter:SPECCOST:EL",
    "1:parameter:SPECCOST:H2O-L",
    "1:parameter:SPECCOST:HEAT",
    "1:parameter:SPECCOST:IOP-S",
    "1:parameter:SPECCOST:N2-G",
    "1:parameter:SPECCOST:NG-G",
    "1:parameter:WACC",
    "2:data:CAPEX",
    "2:data:CBOUND:B-DRI-S",
    "2:data:CBOUND:CO2-G",
    "2:data:CBOUND:NG-G",
    "2:data:CH4SHARE:NG-G",
    "2:data:CO2CPT-R:CH4-G",
    "2:data:CO2CPT-R:NG-G",
    "2:data:CO2CPT-S:CH4-G",
    "2:data:CO2CPT-S:NG-G",
    "2:data:CONV-OT:BFUEL-L",
    "2:data:CONV-OT:NG-L",
    "2:data:CONV:CO2-C",
    "2:data:CONV:CO2-G",
    "2:data:CONV:DIESEL-L",
    "2:data:CONV:EL",
    "2:data:CONV:HEAT",
    "2:data:CONV:IOP-S",
    "2:data:CONV:NG-G",
    "2:data:DIST",
    "2:data:EF_E:CH3OH-L",
    "2:data:EF_E:CH4-G",
    "2:data:EF_E:CO2-C",
    "2:data:EF_E:CO2-G",
    "2:data:EF_E:DIESEL-L",
    "2:data:EF_E:EL",
    "2:data:EF_E:HEAT",
    "2:data:EF_E:NG-G",
    "2:data:EF_E:NG-L",
    "2:data:EF_M:CH3OH-L",
    "2:data:EF_M:CH4-G",
    "2:data:EF_M:CO2-C",
    "2:data:EF_M:CO2-G",
    "2:data:EF_M:DIESEL-L",
    "2:data:EF_M:EL",
    "2:data:EF_M:HEAT",
    "2:data:EF_M:NG-G",
    "2:data:EF_M:NG-L",
    "2:data:EFF",
    "2:data:FLH",
    "2:data:LIFETIME",
    "2:data:LOSS_FLOW:NG-G",
    "2:data:LOSS",
    "2:data:OPEX-F",
    "2:data:OPEX-O",
    "2:data:OPEX-T",
    # "2:data:process_code", # noqa
    # "2:data:step", # noqa
    "3:flows:emissions:ch4_direct_co2e_e",
    "3:flows:emissions:ch4_direct_co2e_m",
    "3:flows:emissions:ch4_direct_e",
    "3:flows:emissions:ch4_direct_m",
    "3:flows:emissions:co2_bound_in_product_e",
    "3:flows:emissions:co2_bound_in_product_last_proc_e",
    "3:flows:emissions:co2_bound_in_product_last_proc_m",
    "3:flows:emissions:co2_bound_in_product_m",
    "3:flows:emissions:co2_captured_e",
    "3:flows:emissions:co2_captured_m",
    "3:flows:emissions:co2_direct_e",
    "3:flows:emissions:co2_direct_m",
    "3:flows:emissions:co2_in_flows_e",
    "3:flows:emissions:co2_in_flows_m",
    "3:flows:emissions:co2_indirect_scope2_e",
    "3:flows:emissions:co2_indirect_scope2_m",
    "3:flows:emissions:co2e_total_direct_e",
    "3:flows:emissions:co2e_total_direct_m",
    "3:flows:flows:BFUEL-L",
    "3:flows:flows:CO2-C",
    "3:flows:flows:CO2-G",
    "3:flows:flows:DIESEL-L",
    "3:flows:flows:EL",
    "3:flows:flows:HEAT",
    "3:flows:flows:IOP-S",
    "3:flows:flows:NG-G",
    "3:flows:flows:NG-L",
    "3:flows:main_input",
    "3:flows:main_output",
    # "3:flows:process_code", # noqa
    # "3:flows:process_step", # noqa
    "4:costs:CAPEX",
    "4:costs:FLOW",
    "4:costs:OPEX",
]


df_proc = DataHandler.get_dimension("process")

sec_proc = {
    "Electricity generation": df_proc.loc["CCGT-CC#B"],
    "CO2 transport and storage": df_proc.loc["CO2-T+S#B"],
    "Carbon": df_proc.loc["DAC#B"],
    "Water": df_proc.loc["DESAL"],
    "Heat": df_proc.loc["HEATPUMP#B"],
}


def get_secproc_process(secproc_step: str) -> str:
    proc_cls = secproc_step.split(":")[1]
    if proc_cls == "Electricity":
        proc_cls = "Electricity generation"  # ??
    return sec_proc[proc_cls]["process_code"]


def main(xlsx_filepath: str):
    # create one result for each chain
    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    chains = api.get_dimension("chain", tool_version_color="blue")
    results: dict[str, pd.DataFrame] = {}

    all_row_keys = set()

    for idx, (_, chain) in enumerate(chains.iterrows()):
        chain_flow_out = chain["flow_out"]
        flow_out_unit = api.get_dimension("flow").loc[chain_flow_out, "unit"]
        if flow_out_unit.lower().startswith("kwh"):  # type:ignore
            output_unit = "USD/MWh"
            output_unit_cost = "USD/kWh"  # unconverted
            output_unit_data = "X/kWh"
        elif flow_out_unit.lower().startswith("kg"):  # type:ignore
            output_unit = "USD/t"
            output_unit_cost = "USD/kg"  # unconverted
            output_unit_data = "X/kg"
        else:
            raise Exception()

        settings = {
            "chain": chain["chain"],
            "scenario": "2040 (medium)",
            "region": "Algeria",
            "country": "Germany",
            "transport": "Ship",
            "secproc_co2": sec_proc["Carbon"]["process_name"],
            "secproc_water": sec_proc["Water"]["process_name"],
        }

        res = api.calculate(
            **settings,
            res_gen=None,
            ship_own_fuel=False,
            tool_version_color="blue",
            output_unit=output_unit,
            optimize_flh=False,
        )

        data_general = (
            dict(flatten_dict(settings, "0:settings"))
            | dict(
                flatten_dict(res.todo_data["parameter"], "1:parameter")  # type:ignore
            )
            | {
                "0:settings:output_unit_cost": output_unit_cost,
                "0:settings:output_unit_data": output_unit_data,
            }
        )
        all_row_keys = all_row_keys | set(data_general)
        pd_series = [pd.Series(data_general, name="")]

        secondary_process_steps = list(
            res.todo_data["secondary_process"].values()  # type:ignore
        )

        for s in secondary_process_steps:
            s["step"] = get_secproc_step(process_code=s["process_code"])

        data_steps = list_to_dict_by_step(
            res.todo_data["main_export_process_chain"]  # type:ignore
            + res.todo_data["transport_process_chain"]  # type:ignore
            + res.todo_data["main_import_process_chain"]  # type:ignore
            + secondary_process_steps
        )

        results_flows_steps = list_to_dict_by_step(
            res.todo_results_flows  # type:ignore
        )

        df_costs: pd.DataFrame = res.todo_df_results_cost_unscaled  # type:ignore

        for step in STEPS:
            d_data = dict(
                flatten_dict(
                    data_steps.pop(step) if step in data_steps else {}, "2:data"
                )
            )
            d_flows = dict(
                flatten_dict(
                    (
                        results_flows_steps.pop(step)
                        if step in results_flows_steps
                        else {}
                    ),
                    "3:flows",
                )
            )

            if not step.startswith("SECONDARY"):
                process_code = chain[step]
            else:
                process_code = get_secproc_process(step)

            if process_code:
                d_data["0:process:process_code"] = process_code
                d_data["0:process:main_flow_code_in"] = api.get_dimension(
                    "process"
                ).loc[process_code, "main_flow_code_in"]
                d_data["0:process:main_flow_code_out"] = api.get_dimension(
                    "process"
                ).loc[process_code, "main_flow_code_out"]

                process_code_cost = process_code
                if "IMPORT" in step:
                    process_code_cost += " (import)"

                idx_c = df_costs["process_subtype"] == process_code_cost

                d_costs = dict(
                    flatten_dict(
                        dict(
                            df_costs.loc[idx_c]
                            .groupby(["cost_type"])
                            .sum(["values"])["values"]
                            .items()
                        ),
                        "4:costs",
                    )
                )
                df_costs = df_costs.loc[~idx_c]
            else:
                d_costs = {}

            pd_series.append(pd.Series(d_data | d_flows | d_costs, name=step))

            all_row_keys = all_row_keys | set(d_data)
            all_row_keys = all_row_keys | set(d_flows)
            all_row_keys = all_row_keys | set(d_costs)

        # check all datahas been used
        assert not data_steps, data_steps.keys()
        assert not results_flows_steps, results_flows_steps.keys()
        assert df_costs.empty, set(df_costs["process_subtype"])

        df = pd.concat(pd_series, axis=1)
        df = df.reindex(rows)

        sheet_name = f"{idx}_" + chain["chain_name"][:28].replace("*", "")
        results[sheet_name] = df

    all_row_keys = all_row_keys - {
        "3:flows:process_code",
        "3:flows:process_step",
        "2:data:process_code",
        "2:data:step",
    }

    assert all_row_keys == set(rows), (
        (all_row_keys - set(rows)),
        (set(rows) - all_row_keys),
    )

    with pd.ExcelWriter(xlsx_filepath) as xlsx:
        for sheet_name, df in results.items():
            df.to_excel(xlsx, sheet_name=sheet_name)


if __name__ == "__main__":
    main("test_blue.xlsx")
