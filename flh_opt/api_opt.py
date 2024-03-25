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
    data.index = data.index.map(lambda x: f"{x[0]}_{x[1]}")
    weights_and_period_ids = pd.read_csv(
        f"{path}/{filestem}.weights.csv", index_col="TimeStep"
    )
    weights_and_period_ids.index = data.index

    if selection:
        data = data.iloc[selection]
        weights_and_period_ids = weights_and_period_ids.iloc[selection]
    return data, weights_and_period_ids


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
            "DERIV":{
                "CAPEX_A": 0.826,
                "OPEX_F": 0.209,
                "OPEX_O": 0.025,
                "PROCESS_CODE": "CH4SYN",
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
    n.add("Bus", "ELEC", carrier="Electricity")
    n.add("Bus", "H2", carrier="H2")
    if "DERIV" in input_data.keys():
        n.add("Bus", "final_product", carrier="final_product")

    # add carriers:
    n.add("Carrier", "Electricity")
    n.add("Carrier", "H2")
    n.add("Carrier", "H2O")
    if "DERIV" in input_data.keys():
        n.add("Carrier", "final_product")

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

    if "DERIV" in input_data.keys():
        n.add(
            "Link",
            name="DERIV",
            bus0="H2",
            bus1="final_product",
            carrier="final_product",
            efficiency=input_data["DERIV"]["EFF"],
            capital_cost=input_data["DERIV"]["CAPEX_A"] + input_data["DERIV"]["OPEX_F"],
            marginal_cost=input_data["DERIV"]["OPEX_O"],
            p_nom_extendable=True,
        )

    # add loads:
    if "DERIV" in input_data.keys():
        n.add(
            "Load", name="demand", bus="final_product", carrier="final_product", p_set=1
        )
    else:
        n.add("Load", name="demand", bus="H2", carrier="H2", p_set=1)

    # add storage:
    # TODO: for H2 storage: invest in cap and store/dispatch cap. individually?
    def add_storage(n: Network, input_data: dict, name: str, bus: str) -> None:
        n.add(
            "StorageUnit",
            name=name,
            bus=bus,
            carrier=n.buses.at[bus, "carrier"],
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
        res_profiles, weights_and_period_ids = get_profiles_and_weights(
            source_region_code=input_data["SOURCE_REGION_CODE"],
            re_location=re_location,
        )

    # define snapshots:
    n.snapshots = res_profiles.index

    # define snapshot weightings:
    weights = weights_and_period_ids["weight"]
    if not math.isclose(weights.sum(), 8760):
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
            gen = n.generators_t["p"][g].mean()
            p_nom = n.generators.at[g, "p_nom_opt"]
        if component_type == "Link":
            gen = n.links_t["p0"][g].mean()
            p_nom = n.links.at[g, "p_nom_opt"]
        if gen == 0:
            flh = 0
        else:
            flh = gen / p_nom
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
