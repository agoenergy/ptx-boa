# -*- coding: utf-8 -*-
"""API interface for FLH optimizer."""
from _types import OptInputDataType, OptOutputDataType


def optimize(input_data: OptInputDataType) -> OptOutputDataType:
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
    result_data = {  # OptOutputDataType
        "RES": [{"SHARE_FACTOR": 0.519, "FLH": 0.907, "PROCESS_CODE": "PV-FIX"}],
        "ELY": {"FLH": 0.548},
        "EL_STR": {"CAP_F": 0.112},
        "H2_STR": {"CAP_F": 0.698},
    }
    return result_data
