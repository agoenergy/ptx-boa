"""export some results for new blue chain for evaluation.

- creates one result for each blue chain
- combine intermediate results for flows, emissions, costs
- save in excel: one sheet per result, one column per process

"""

from typing import Any, Iterable

import pandas as pd

from ptxboa.api import PtxboaAPI
from ptxboa.api_data import DEFAULT_DATA_DIR


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
    "PRE_PPL",
    "SHP",
    "SHP_OWN",
    "PPLS",
    "PPL",
    "PPLX",
    "PPLR",
    "POST_SHP",
    "POST_PPL",
    "ELY_I",
    "DERIV_I",
    "DERIV_I2",
    # "CO2_TS_I",
]

rows = [
    "0:settings:chain",
    "0:settings:country",
    "0:settings:region",
    "0:settings:scenario",
    "0:settings:transport",
    "0:process:process_code",
    "0:process:main_flow_code_in",
    "0:process:main_flow_code_out",
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
    "2:data:CONV:CO2-G",
    "2:data:CONV:DIESEL-L",
    "2:data:CONV:EL",
    "2:data:CONV:IOP-S",
    "2:data:CONV:NG-G",
    "2:data:DIST",
    "2:data:EFF",
    "2:data:EF_E:CH3OH-L",
    "2:data:EF_E:CH4-G",
    "2:data:EF_E:CO2-G",
    "2:data:EF_E:DIESEL-L",
    "2:data:EF_E:EL",
    "2:data:EF_E:HEAT",
    "2:data:EF_E:NG-G",
    "2:data:EF_E:NG-L",
    "2:data:EF_M:CH3OH-L",
    "2:data:EF_M:CH4-G",
    "2:data:EF_M:CO2-G",
    "2:data:EF_M:DIESEL-L",
    "2:data:EF_M:EL",
    "2:data:EF_M:HEAT",
    "2:data:EF_M:NG-G",
    "2:data:EF_M:NG-L",
    "2:data:FLH",
    "2:data:LIFETIME",
    "2:data:LOSS",
    "2:data:LOSS_FLOW:NG-G",
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
    "3:flows:flows:CO2-G",
    "3:flows:flows:DIESEL-L",
    "3:flows:flows:EL",
    "3:flows:flows:IOP-S",
    "3:flows:flows:NG-G",
    "3:flows:main_input",
    "3:flows:main_output",
    # "3:flows:process_code", # noqa
    # "3:flows:process_step", # noqa
    "4:costs:CAPEX",
    "4:costs:FLOW",
    "4:costs:OPEX",
]


def main(xlsx_filepath: str):
    # create one result for each chain
    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    chains = api.get_dimension("chain", tool_version_color="blue")
    results: dict[str, pd.DataFrame] = {}

    all_row_keys = set()

    for idx, (_, chain) in enumerate(chains.iterrows()):
        settings = {
            "chain": chain["chain"],
            "scenario": "2040 (medium)",
            "region": "Qatar",
            "country": "Germany",
            "transport": "Ship",
            "output_unit": "USD/t",  # worls for all
        }

        res = api.calculate(
            **settings,
            res_gen=None,
            ship_own_fuel=False,
            secproc_co2=None,
            secproc_water=None,
            tool_version_color="blue",
            optimize_flh=False,
        )

        # TODO: res.todo_data["secondary_process"]

        data_general = dict(flatten_dict(settings, "0:settings")) | dict(
            flatten_dict(res.todo_data["parameter"], "1:parameter")
        )
        all_row_keys = all_row_keys | set(data_general)
        pd_series = [pd.Series(data_general, name="")]

        data_steps = list_to_dict_by_step(
            res.todo_data["main_export_process_chain"]
            + res.todo_data["transport_process_chain"]
            + res.todo_data["main_import_process_chain"]
        )
        results_flows_steps = list_to_dict_by_step(res.todo_results_flows)

        for step in STEPS:
            d_data = dict(flatten_dict(data_steps.get(step, {}), "2:data"))
            d_flows = dict(flatten_dict(results_flows_steps.get(step, {}), "3:flows"))

            process_code = chain[step]
            if process_code:
                d_data["0:process:process_code"] = process_code
                d_data["0:process:main_flow_code_in"] = api.get_dimension(
                    "process"
                ).loc[process_code, "main_flow_code_in"]
                d_data["0:process:main_flow_code_out"] = api.get_dimension(
                    "process"
                ).loc[process_code, "main_flow_code_out"]

            d_costs = dict(
                flatten_dict(
                    dict(
                        res.costs.loc[res.costs["process_subtype"] == process_code]
                        .groupby(["cost_type"])
                        .sum(["values"])["values"]
                        .items()
                    ),
                    "4:costs",
                )
            )

            pd_series.append(pd.Series(d_data | d_flows, name=step))

            all_row_keys = all_row_keys | set(d_data)
            all_row_keys = all_row_keys | set(d_flows)
            all_row_keys = all_row_keys | set(d_costs)

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
