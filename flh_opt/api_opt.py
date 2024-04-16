# -*- coding: utf-8 -*-
"""API interface for FLH optimizer."""
import math
import os
from typing import List, Optional

import pandas as pd
from pypsa import Network

from flh_opt._types import OptInputDataType, OptOutputDataType

solver_options = {
    "output_flag": os.environ.get(
        "HIGHS_OUTPUT_FLAG", "true"
    )  # set environment variable HIGHS_OUTPUT_FLAG=false to reduce HIGHS solver print
}


def get_profiles_and_weights(
    source_region_code: str,
    re_location: str,
    profiles_path: str = "flh_opt/renewable_profiles",
    selection: Optional[List[int]] = None,
) -> pd.DataFrame:
    """Get RES profiles from CSV file."""
    filestem = f"{source_region_code}_{re_location}_aggregated"
    data = pd.read_csv(
        f"{profiles_path}/{filestem}.csv", index_col=["period_id", "TimeStep"]
    )
    data.index = data.index.map(lambda x: f"{x[0]}_{x[1]}")
    weights_and_period_ids = pd.read_csv(
        f"{profiles_path}/{filestem}.weights.csv", index_col="TimeStep"
    )
    weights_and_period_ids.index = data.index

    if selection:
        data = data.iloc[selection]
        weights_and_period_ids = weights_and_period_ids.iloc[selection]
    return data, weights_and_period_ids


def optimize(
    input_data: OptInputDataType, profiles_path: str = "flh_opt/renewable_profiles"
) -> tuple[OptOutputDataType, Network]:
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
                "OPEX_O": 0.2,
                "CONV": {
                    "H2O-L": 0.677
                }
            },
            "DERIV": {
                "EFF": 0.717,
                "CAPEX_A": 0.367,
                "OPEX_F": 0.082,
                "OPEX_O": 0.132,
                "PROCESS_CODE": "CH4SYN",
                "CONV": {
                    "CO2-G": 0.2,
                    "HEAT": -0.2,
                    "H2O-L": -0.15
                }
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
                "H2O-L": 0.658,
                "CO2-G": 1.0
            }
        }

    profiles_path: str: path for for profiles data

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
            "DERIV": {
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

    # add buses and carriers:
    carriers = ["EL", "H2"]
    for c in carriers:
        n.add("Bus", name=c, carrier=c)
        n.add("Carrier", name=c)

    # create list of secondary carriers:
    if "DERIV" in input_data.keys():
        if input_data["DERIV"] is not None:
            carriers_sec = list(input_data["DERIV"]["CONV"].keys())
        else:
            carriers_sec = []

    # we need H2O in any case because it is required by the electrolyzer:
    if "H2O-L" not in carriers_sec:
        carriers_sec.append("H2O-L")

    if input_data.get("DERIV"):
        n.add("Bus", "final_product", carrier="final_product")
        n.add("Carrier", "final_product")

    # add RE generators:
    for g in input_data["RES"]:
        n.add("Carrier", name=g["PROCESS_CODE"])
        n.add(
            "Generator",
            name=g["PROCESS_CODE"],
            bus="EL",
            carrier=g["PROCESS_CODE"],
            capital_cost=g["CAPEX_A"] + g["OPEX_F"],
            marginal_cost=g["OPEX_O"],
            p_nom_extendable=True,
        )

    # add supply for secondary inputs:
    for c in carriers_sec:
        if c not in carriers:
            n.add("Bus", name=c, carrier=c)
            n.add("Carrier", name=c)
            n.add(
                "Generator",
                name=f"{c}_supply",
                bus=c,
                carrier=c,
                marginal_cost=input_data["SPECCOST"][c],
                p_nom=100,
            )
            n.add(
                "Generator",
                name=f"{c}_sink",
                bus=c,
                carrier=c,
                p_max_pu=0,
                p_min_pu=-1,
                marginal_cost=0,
                p_nom=100,
            )

    # add links:
    # TODO: account for water demand
    n.add(
        "Link",
        name="ELY",
        bus0="EL",
        bus1="H2",
        bus2="H2O-L",
        carrier="H2",
        efficiency=input_data["ELY"]["EFF"],
        # input data is per main output,
        # pypsa link parameters are defined per main input
        efficiency2=-input_data["ELY"]["CONV"]["H2O-L"] / input_data["ELY"]["EFF"],
        capital_cost=(input_data["ELY"]["CAPEX_A"] + input_data["ELY"]["OPEX_F"])
        / input_data["ELY"]["EFF"],
        marginal_cost=input_data["ELY"]["OPEX_O"] / input_data["ELY"]["EFF"],
        p_nom_extendable=True,
    )

    if input_data.get("DERIV"):
        n.add(
            "Link",
            name="DERIV",
            bus0="H2",
            bus1="final_product",
            carrier="final_product",
            efficiency=input_data["DERIV"]["EFF"],
            # input data is per main output,
            # pypsa link parameters are defined per main input
            capital_cost=(
                input_data["DERIV"]["CAPEX_A"] + input_data["DERIV"]["OPEX_F"]
            )
            / input_data["DERIV"]["EFF"],
            marginal_cost=input_data["DERIV"]["OPEX_O"] / input_data["DERIV"]["EFF"],
            p_nom_extendable=True,
        )
        # add conversion efficiencies and buses for secondary input / output
        for i, c in enumerate(input_data["DERIV"]["CONV"].keys()):
            n.links.at["DERIV", f"bus{i+2}"] = c
            # input data is per main output,
            # pypsa link parameters are defined per main input
            n.links.at["DERIV", f"efficiency{i+2}"] = (
                -input_data["DERIV"]["CONV"][c] / input_data["DERIV"]["EFF"]
            )

    # add loads:
    if input_data.get("DERIV"):
        n.add(
            "Load", name="demand", bus="final_product", carrier="final_product", p_set=1
        )
    else:
        n.add("Load", name="demand", bus="H2", carrier="H2", p_set=1)

    # add storage:
    def add_storage(n: Network, input_data: dict, name: str, bus: str) -> None:
        n.add(
            "StorageUnit",
            name=name,
            bus=bus,
            carrier=n.buses.at[bus, "carrier"],
            capital_cost=input_data[name]["CAPEX_A"] + input_data[name]["OPEX_F"],
            efficiency_store=input_data[name]["EFF"],
            max_hours=4,  # TODO: move this parameter out of the code.
            cyclic_state_of_charge=True,
            marginal_cost=input_data[name]["OPEX_O"],
            p_nom_extendable=True,
        )

    add_storage(n, input_data, "EL_STR", "EL")
    if input_data.get("DERIV"):
        n.add("Bus", name="H2_STR_bus", carrier="H2")
        n.add(
            "Link",
            name="H2_STR_in",
            bus0="H2",
            bus1="H2_STR_bus",
            carrier="H2",
            p_nom_extendable=True,
            capital_cost=input_data["H2_STR"]["CAPEX_A"]
            + input_data["H2_STR"]["OPEX_F"],
            efficiency=input_data["H2_STR"]["EFF"],
            marginal_cost=input_data["H2_STR"]["OPEX_O"],
        )
        n.add(
            "Link",
            name="H2_STR_out",
            bus0="H2_STR_bus",
            bus1="H2",
            carrier="H2",
            p_nom=100,
        )
        n.add("Store", name="H2_STR_store", bus="H2_STR_bus", carrier="H2", e_nom=1e5)
        bus = "final_product"
        carrier = "final_product"
    else:
        bus = "H2"
        carrier = "H2"

    # add final product storage (for flexible demand):
    n.add(
        "StorageUnit",
        name="final_product_storage",
        bus=bus,
        carrier=carrier,
        p_nom=100,
        max_hours=8760,
    )

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
            profiles_path=profiles_path,
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
    model_status = n.optimize(solver_name="highs", solver_options=solver_options)

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

    # store model status:
    result_data["model_status"] = model_status

    # only store results if optimization was successful:
    if model_status[1] == "optimal":
        result_data["RES"] = []

        # Calculate total RES capacity:
        list_res = [item["PROCESS_CODE"] for item in input_data["RES"]]
        cap_total = n.generators.loc[list_res, "p_nom_opt"].sum()

        # Add results for each RES type:
        for g in input_data["RES"]:
            d = {}
            d["PROCESS_CODE"] = g["PROCESS_CODE"]
            d["FLH"] = get_flh(n, g["PROCESS_CODE"], "Generator")
            d["SHARE_FACTOR"] = (
                n.generators.at[g["PROCESS_CODE"], "p_nom_opt"] / cap_total
            )
            result_data["RES"].append(d)

        # Calculate FLH for electrolyzer:
        result_data["ELY"] = {}
        result_data["ELY"]["FLH"] = get_flh(n, "ELY", "Link")

        # calculate capacity factor for storage units:
        # we use charging capacity (p_nom) per final product demand
        result_data["EL_STR"] = {}
        result_data["EL_STR"]["CAP_F"] = n.storage_units.at["EL_STR", "p_nom_opt"]
        if input_data.get("DERIV"):
            result_data["H2_STR"] = {}
            result_data["H2_STR"]["CAP_F"] = n.links.at["H2_STR_in", "p_nom_opt"]
            result_data["DERIV"] = {}
            result_data["DERIV"]["FLH"] = get_flh(n, "DERIV", "Link")

    return result_data, n
