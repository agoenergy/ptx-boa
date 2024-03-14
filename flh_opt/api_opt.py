# -*- coding: utf-8 -*-
"""API interface for FLH optimizer."""
import math
from typing import List, Optional

import pandas as pd
from pypsa import Network

from flh_opt._types import OptInputDataType, OptOutputDataType


def get_profiles_and_weights(
    source_region_code: str,
    re_location: str,
    path: str = "tests/test_profiles",
    selection: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Get RES profiles from CSV file."""
    filestem = f"{source_region_code}_{re_location}_aggregated"
    data = pd.read_csv(f"{path}/{filestem}.csv", index_col=["period_id", "TimeStep"])
    weights = pd.read_csv(
        f"{path}/{filestem}.weights.csv", index_col=["period_id", "TimeStep"]
    )

    if selection:
        data = data.iloc[selection]
        weights = weights.iloc[selection]

    return data, weights


def optimize(input_data: OptInputDataType) -> tuple[OptOutputDataType, Network]:
    """Run flh optimization.

    Parameters
    ----------
    input_data : OptInputDataType
        Example:
        {
            "SOURCE_REGION_CODE": "GYE",
            "RES": [
                {
                "CAPEX_A": 0.826,
                "OPEX_F": 0.209,
                "OPEX_O": 0.025,
                "PROCESS_CODE": "PV-FIX"
                }
            ],
            "ELY": {
                "EFF": 0.834,
                "CAPEX_A": 0.52,
                "OPEX_F": 0.131,
                "OPEX_O": 0.2
            },
            "EL_STR": {
                "EFF": 0.544,
                "CAPEX_A": 0.385,
                "OPEX_F": 0.835,
                "OPEX_O": 0.501
            },
            "H2_STR": {
                "EFF": 0.478,
                "CAPEX_A": 0.342,
                "OPEX_F": 0.764,
                "OPEX_O": 0.167
            },
            "SPECCOST": {
                "H2O": 0.658
            }
        }

    Returns
    -------
    OptOutputDataType
        Example:
        {
            "RES": [
                {
                "SHARE_FACTOR": 0.519,
                "FLH": 0.907,
                "PROCESS_CODE": "PV-FIX"
                }
            ],
            "ELY": {
                "FLH": 0.548
            },
            "EL_STR": {
                "CAP_F": 0.112
            },
            "H2_STR": {
                "CAP_F": 0.698
            }
        }
    """
    # initialize network object:
    n = Network()

    # add buses:
    n.add("Bus", "ELEC")
    n.add("Bus", "H2")

    # add carriers:
    n.add("Carrier", "Electricity")
    n.add("Carrier", "H2")
    n.add("Carrier", "H2O")

    # add generators:
    for g in input_data["RES"]:
        n.add("Carrier", name=g["PROCESS_CODE"])
        n.add(
            "Generator",
            name=g["PROCESS_CODE"],
            bus="ELEC",
            carrier=g["PROCESS_CODE"],
            capital_cost=g["CAPEX_A"] + g["OPEX_F"],
            marginal_cost=g["OPEX_O"],
            p_nom_extendable=True,
        )

    # add links:
    # TODO: account for water demand
    n.add(
        "Link",
        name="ELY",
        bus0="ELEC",
        bus1="H2",
        carrier="H2",
        efficiency=input_data["ELY"]["EFF"],
        capital_cost=input_data["ELY"]["CAPEX_A"] + input_data["ELY"]["OPEX_F"],
        marginal_cost=input_data["ELY"]["OPEX_O"],
        p_nom_extendable=True,
    )

    # add loads:
    n.add("Load", name="H2_demand", bus="H2", p_set=1)

    # add storage:
    # TODO: for H2 storage: invest in cap and store/dispatch cap. individually?
    def add_storage(n: Network, input_data: dict, name: str, bus: str) -> None:
        n.add(
            "StorageUnit",
            name=name,
            bus=bus,
            capital_cost=input_data[name]["CAPEX_A"] + input_data[name]["OPEX_F"],
            efficiency_store=input_data[name]["EFF"],
            max_hours=24,  # TODO: move this parameter out of the code.
            cyclic_state_of_charge=True,
            marginal_cost=input_data[name]["OPEX_O"],
            p_nom_extendable=True,
        )

    add_storage(n, input_data, "EL_STR", "ELEC")
    add_storage(n, input_data, "H2_STR", "H2")

    # add RE profiles:
    for g in input_data["RES"]:
        process_code = g["PROCESS_CODE"]
        if len(input_data["RES"]) > 1:
            re_location = "RES_HYBR"
        else:
            re_location = process_code
        res_profiles, weights = get_profiles_and_weights(
            source_region_code=input_data["SOURCE_REGION_CODE"],
            re_location=re_location,
            selection=range(0, 48),  # TODO: make this a function parameter?
        )

    # define snapshots:
    n.snapshots = res_profiles.index

    # define snapshot weightings:
    if not not math.isclose(weights.sum(), 8760):
        weights = weights * 8760 / weights.sum()

    n.snapshot_weightings["generators"] = weights
    n.snapshot_weightings["objective"] = weights
    n.snapshot_weightings["stores"] = 1

    # import profiles to network:
    n.import_series_from_dataframe(res_profiles, "Generator", "p_max_pu")

    # solve optimization problem:
    n.optimize(solver_name="highs")

    # calculate results:

    def get_flh(n: Network, g: str, component_type: str) -> float:
        if component_type == "Generator":
            flh = n.generators_t["p"][g].mean() / n.generators.at[g, "p_nom_opt"]
        if component_type == "Link":
            flh = n.links_t["p0"][g].mean() / n.links.at[g, "p_nom_opt"]
        return flh

    result_data = {}
    result_data["RES"] = []

    # Calculate total RES capacity:
    list_res = [item["PROCESS_CODE"] for item in input_data["RES"]]
    cap_total = n.generators.loc[list_res, "p_nom_opt"].sum()

    # Add results for each RES type:
    for g in input_data["RES"]:
        d = {}
        d["PROCESS_CODE"] = g["PROCESS_CODE"]
        d["FLH"] = get_flh(n, g["PROCESS_CODE"], "Generator")
        d["SHARE_FACTOR"] = n.generators.at[g["PROCESS_CODE"], "p_nom_opt"] / cap_total
        result_data["RES"].append(d)

    # Calculate FLH for electrolyzer:
    result_data["ELY"] = {}
    result_data["ELY"]["FLH"] = get_flh(n, "ELY", "Link")

    # calculate capacity factor for storage units:
    # TODO: we use storage capacity per output, is this correct?
    # TODO: or rather use p_nom per output?
    result_data["EL_STR"] = {}
    result_data["EL_STR"]["CAP_F"] = (
        n.storage_units.at["EL_STR", "p_nom_opt"]
        * n.storage_units.at["EL_STR", "max_hours"]
    )
    result_data["H2_STR"] = {}
    result_data["H2_STR"]["CAP_F"] = (
        n.storage_units.at["H2_STR", "p_nom_opt"]
        * n.storage_units.at["H2_STR", "max_hours"]
    )
    return result_data, n
