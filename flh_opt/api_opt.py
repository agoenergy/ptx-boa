# -*- coding: utf-8 -*-
"""API interface for FLH optimizer."""
from pypsa import Network

from flh_opt._types import OptInputDataType, OptOutputDataType


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
    n.add(
        "Link",
        name="ELY",
        bus0="ELEC",
        bus1="H2",
        efficiency=input_data["ELY"]["EFF"],
        capital_cost=input_data["ELY"]["CAPEX_A"] + input_data["ELY"]["OPEX_F"],
        marginal_cost=input_data["ELY"]["OPEX_O"],
        p_nom_extendable=True,
    )

    # add loads:
    n.add("Load", name="H2_demand", bus="H2", p_set=1)

    # add storage:
    # TODO

    # add RE profiles:
    # TODO

    # solve optimization problem:
    n.optimize(solver_name="highs")

    # calculate results:
    # TODO

    result_data = {  # OptOutputDataType
        "RES": [{"SHARE_FACTOR": 0.519, "FLH": 0.907, "PROCESS_CODE": "PV-FIX"}],
        "ELY": {"FLH": 0.548},
        "EL_STR": {"CAP_F": 0.112},
        "H2_STR": {"CAP_F": 0.698},
    }

    def _get_flh(n: Network, g: str) -> float:
        flh = n.generators.at[g, "p_nom_opt"] / n.generators_t["p"][g].sum()
        return flh

    result_data = {}
    result_data["RES"] = []
    for g in input_data["RES"]:
        d = {}
        d["FLH"] = _get_flh(n, g["PROCESS_CODE"])
        result_data["RES"].append(d)

    return result_data, n
