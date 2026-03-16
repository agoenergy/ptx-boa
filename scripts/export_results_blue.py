"""export some results for new blue chain for evaluation.

- creates one result for each blue chain
- combine intermediate results for flows, emissions, costs
- save in excel: one sheet per result, one column per process

"""

import pandas as pd

from ptxboa.api import PtxboaAPI
from ptxboa.api_data import DEFAULT_DATA_DIR


def main(xlsx_filepath: str):
    # create one result for each chain
    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    chains = api.get_dimension("chain", tool_version_color="blue")
    results: dict[str, pd.DataFrame] = {}
    for idx, (_, chain) in enumerate(chains.iterrows()):
        settings = {
            "chain": chain["chain"],
            "scenario": "2040 (medium)",
            "region": "Qatar",
            "country": "Germany",
            "transport": "Ship",
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

        # convert all results into one series
        steps = [settings | {"chain": chain["chain_name"]}] + res.todo_results_flows
        df = pd.DataFrame()
        flow_codes = set()
        for step in steps:
            flow_codes = flow_codes | set(step.get("flows", {}))

        for step in steps:
            ps = step.get("process_step")
            pc = step.get("process_code")
            colname = f"{ps}={pc}" if ps and pc else ""
            step_data = {
                k: v
                for k, v in step.items()
                if k in set(settings) | {"main_input", "main_output"}
            }
            for k in flow_codes:
                step_data[f"FLOW:{k}"] = step.get("flows", {}).get(k)

            for k, v in step.get("emissions", {}).items():
                step_data["EMISSION:" + k] = v

            # costs
            for k, v in (
                res.costs.loc[res.costs["process_subtype"] == pc]
                .groupby(["cost_type"])
                .sum("values")["values"]
                .items()
            ):
                step_data["COST:" + k] = v

            df = pd.concat([df, pd.Series(step_data, name=colname)], axis=1)

        sheet_name = f"{idx}_" + chain["chain"][:28].replace("*", "")
        results[sheet_name] = df

    with pd.ExcelWriter(xlsx_filepath) as xlsx:
        for sheet_name, df in results.items():
            df.to_excel(xlsx, sheet_name=sheet_name)


if __name__ == "__main__":
    main("test_blue.xlsx")
