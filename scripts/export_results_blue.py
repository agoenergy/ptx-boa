"""export some results for new blue chain for evaluation.

- creates one result for each blue chain
- combine intermediate results for flows, emissions, costs
- save in excel: one sheet per result, one column per process



"""

from typing import Any, Iterable

import pandas as pd

from ptxboa.api import PtxboaAPI
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler


def flatten_dict(v: Any, key_prefix: None | str = None) -> Iterable[tuple[str, Any]]:
    if isinstance(v, list):
        raise NotImplementedError(v)
    elif isinstance(v, dict):
        for k2, v2 in v.items():
            yield from flatten_dict(
                v2, key_prefix=k2 if key_prefix is None else f"{key_prefix}:{k2}"
            )
    elif isinstance(v, (float, str, int, type(None))):
        if not key_prefix:
            raise NotImplementedError(v)
        yield (key_prefix, v)
    else:
        raise TypeError(type(v))


def list_to_dict_by_step(d: list) -> dict:
    return {s.get("step"): s for s in d}


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
    "SECONDARY:CO2-G",
    "SECONDARY:CO2-C",
    "SECONDARY:EL",
    "SECONDARY:HEAT",
    "SECONDARY:H2O-L",
    "SECONDARY:IMPORT:CO2-C",
]

expected_rows = [
    "0:settings:chain",
    "0:settings:country",
    "0:settings:output_unit",
    "0:settings:region",
    "0:settings:scenario",
    "0:settings:secproc_co2",
    "0:settings:secproc_water",
    "0:settings:transport",
    "1:parameter:process_code",
    "1:parameter:main_flow_code_out",
    "1:parameter:CAPEX",
    "1:parameter:CBOUND:B-DRI-S",
    "1:parameter:CBOUND:CO2-DAC",
    "1:parameter:CBOUND:CO2-G",
    "1:parameter:CBOUND:CO2-INDF",
    "1:parameter:CBOUND:CO2-INDS",
    "1:parameter:CBOUND:NG-G",
    "1:parameter:CH4SHARE:NG-G",
    "1:parameter:CH4SHARE:NG-L",
    "1:parameter:CO2CPT-R:CH4-G",
    "1:parameter:CO2CPT-R:NG-G",
    "1:parameter:CO2CPT-S:CH4-G",
    "1:parameter:CO2CPT-S:NG-G",
    "1:parameter:CONV-OT:BFUEL-L",
    "1:parameter:CONV-OT:NG-L",
    "1:parameter:CONV:BFUEL-L",
    "1:parameter:CONV:CO2-G",
    "1:parameter:CONV:DIESEL-L",
    "1:parameter:CONV:EL",
    "1:parameter:CONV:HEAT",
    "1:parameter:CONV:IOF-S",
    "1:parameter:CONV:IOP-S",
    "1:parameter:CONV:NG-G",
    "1:parameter:DIST",
    "1:parameter:DST-S-D",
    "1:parameter:DST-S-DP",
    "1:parameter:EF_E:CH3OH-L",
    "1:parameter:EF_E:CH4-G",
    "1:parameter:EF_E:CO2-C",
    "1:parameter:EF_E:CO2-G",
    "1:parameter:EF_E:BFUEL-L",
    "1:parameter:EF_E:CO2-INDF",
    "1:parameter:EF_E:DIESEL-L",
    "1:parameter:EF_E:EL",
    "1:parameter:EF_E:HEAT",
    "1:parameter:EF_E:NG-G",
    "1:parameter:EF_E:NG-L",
    "1:parameter:EF_M:BFUEL-L",
    "1:parameter:EF_M:CH3OH-L",
    "1:parameter:EF_M:CH4-G",
    "1:parameter:EF_M:CO2-C",
    "1:parameter:EF_M:CO2-DAC",
    "1:parameter:EF_M:CO2-G",
    "1:parameter:EF_M:CO2-INDF",
    "1:parameter:EF_M:CO2-INDS",
    "1:parameter:EF_M:DIESEL-L",
    "1:parameter:EF_M:EL",
    "1:parameter:EF_M:HEAT",
    "1:parameter:EF_M:NG-G",
    "1:parameter:EF_M:NG-L",
    "1:parameter:EFF",
    "1:parameter:FLH",
    "1:parameter:LIFETIME",
    "1:parameter:LOSS-T",
    "1:parameter:LOSS:NH3-L",
    "1:parameter:LOSS:NG-L",
    "1:parameter:LOSS:H2-L",
    "1:parameter:LOSS:CH3OH-L",
    "1:parameter:LOSS:NG-G",
    "1:parameter:OPEX-F",
    "1:parameter:OPEX-O",
    "1:parameter:OPEX-T",
    "1:parameter:SEASHARE",
    "1:parameter:SPECCOST:BFUEL-L",
    "1:parameter:SPECCOST:DIESEL-L",
    "1:parameter:SPECCOST:EL",
    "1:parameter:SPECCOST:IOF-S",
    "1:parameter:SPECCOST:IOP-S",
    "1:parameter:SPECCOST:NG-G",
    "1:parameter:WACC",
    "2:flows:main_flow_in",
    "2:flows:main_flow_out",
    "2:flows:secondary_flows_in:BFUEL-L",
    "2:flows:secondary_flows_in:CO2-C",
    "2:flows:secondary_flows_in:CO2-G",
    "2:flows:secondary_flows_in:DIESEL-L",
    "2:flows:secondary_flows_in:EL",
    "2:flows:secondary_flows_in:HEAT",
    "2:flows:secondary_flows_in:IOF-S",
    "2:flows:secondary_flows_in:IOP-S",
    "2:flows:secondary_flows_in:NG-G",
    "3:costs:CAPEX",
    "3:costs:FLOW",
    "3:costs:OPEX",
    "4:emissions:emission:ch4_direct_co2e",
    "4:emissions:emission:co2_bound_in_product",
    "4:emissions:emission:co2_captured",
    "4:emissions:emission:co2_direct",
    "4:emissions:emission:co2_indirect_scope2",
    "4:emissions:mass:ch4_direct_co2e",
    "4:emissions:mass:co2_bound_in_product",
    "4:emissions:mass:co2_captured",
    "4:emissions:mass:co2_direct",
    "4:emissions:mass:co2_indirect_scope2",
    # "4:emissions:emission:co2_bound_in_product_per_output", # noqa
    # "4:emissions:mass:co2_bound_in_product_per_output", # noqa
]


df_proc = DataHandler.get_dimension("process")

sec_proc = {
    "EL": df_proc.loc["CCGT-CC#B"],
    "CO2-C": df_proc.loc["CO2-T+S#B"],
    "CO2-G": df_proc.loc["DAC#B"],
    "H2O-L": df_proc.loc["DESAL"],
    "HEAT": df_proc.loc["HEATPUMP#B"],
}


def get_secproc_process(secproc_step: str) -> str:
    proc_cls = secproc_step.split(":")[-1]
    return sec_proc[proc_cls]["process_code"]


def main(xlsx_filepath: str):
    # create one result for each chain
    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    chains = api.get_dimension("chain", tool_version_color="blue")
    results: dict[str, pd.DataFrame] = {}

    all_row_keys = set()

    for idx, (_, chain) in enumerate(chains.iterrows()):
        output_unit = "USD/t"  # works always

        dacs = [
            "Direct Air Capture (blue)",  # DAC#B
            "CO2 from other industrial sources",  # CO2-INDF#B
            "CO2 from hard-to-abate or sustainable sources",  # CO2-INDS#B
        ]
        settings = {
            "chain": chain["chain"],
            "scenario": "2040 (medium)",
            "region": "Algeria",
            "country": "Germany",
            "transport": "Ship",
            "secproc_co2": dacs[0],
            "secproc_water": "Sea Water desalination",
        }

        res = api.calculate(
            **settings,
            res_gen=None,
            ship_own_fuel=False,
            tool_version_color="blue",
            output_unit=output_unit,
            optimize_flh=False,
        )._internal_process_data

        data_general = dict(flatten_dict(settings, "0:settings")) | {
            "0:settings:output_unit": output_unit,
        }
        all_row_keys = all_row_keys | set(data_general)

        pd_series = [pd.Series(data_general, name="")]

        steps = set()
        for proc_data in res:  # type: ignore
            proc_or_flow_code = proc_data["process_code"]

            step = proc_data["process_step"]
            assert step, f"not process_step in {proc_or_flow_code}"
            if step in steps:
                # duplicate market
                steps_ = {x for x in steps if x.startswith(step + "/")}
                nmax = max(int(x.split("/")[-1]) for x in steps_) if steps_ else 1
                step = step + f"/{nmax + 1}"
                assert step not in steps

            steps.add(step)

            proc_data_dict = {
                "1:parameter:main_flow_code_out": (
                    df_proc.at[proc_or_flow_code, "main_flow_code_out"]
                    if proc_or_flow_code in df_proc.index
                    else proc_or_flow_code
                )
            }
            for i, k in enumerate(["parameter", "flows", "costs", "emissions"]):
                proc_data_dict = proc_data_dict | dict(
                    flatten_dict(proc_data[k], key_prefix=f"{i + 1}:{k}")
                )

            s_all = pd.Series(proc_data_dict, name=step)
            # drop 0/empty
            s_all = s_all.loc[
                (~s_all.isna())
                & (~(s_all == 0))
                & (~(s_all == None))  # noqa
                & (~(s_all == ""))
            ]
            pd_series.append(s_all)
            all_row_keys = all_row_keys | set(s_all.index)

        df = pd.concat(pd_series, axis=1)
        df = df.reindex(expected_rows)

        sheet_name = f"{idx}_" + chain["chain_name"][:28].replace("*", "")
        results[sheet_name] = df

    all_row_keys = all_row_keys - {
        "1:parameter:step",
        "4:emissions:emission:co2_bound_in_product_per_output",
        "4:emissions:mass:co2_bound_in_product_per_output",
    }

    assert all_row_keys < set(expected_rows), (
        "Keys (new/missing)",
        (all_row_keys - set(expected_rows)),
        (set(expected_rows) - all_row_keys),
    )

    with pd.ExcelWriter(xlsx_filepath) as xlsx:
        for sheet_name, df in results.items():
            df.to_excel(xlsx, sheet_name=sheet_name)


if __name__ == "__main__":
    main("test_blue.xlsx")
