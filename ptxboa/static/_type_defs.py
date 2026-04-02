from dataclasses import dataclass
from typing import Any, Dict, Literal, Optional

import pandas as pd

from ptxboa.static import (
    ChainType,
    FlowCodeType,
    ParameterCodeType,
    ProcessCodeResType,
    ProcessCodeType,
    SourceRegionCodeType,
    TargetCountryCodeType,
)

CalculateDataType = Dict[
    Literal[
        "flh_opt_process",
        "main_export_process_chain",
        "transport_process_chain",
        "main_import_process_chain",
        "secondary_process",
        "parameter",
        "parameter_i",
        "context",
        "flh_opt_hash",
    ],
    Any,
]

ProcessDataType = dict[
    ParameterCodeType | str, None | float | dict[FlowCodeType | str, None | float]
]


@dataclass(slots=True)
class PtxCalcResult:
    df_results_cost: pd.DataFrame
    df_results_emissions_e_g_co2e: Optional[pd.DataFrame]
    df_results_emissions_m_g_co2e: Optional[pd.DataFrame]
    results_flows_chain: Optional[list]
    results_flows_secondary: Optional[list]


@dataclass(slots=True)
class ChainDef:
    secondary_processes: Dict[FlowCodeType, ProcessCodeType]
    chain_name: ChainType
    process_code_res: ProcessCodeResType
    source_region_code: SourceRegionCodeType
    target_country_code: TargetCountryCodeType
    use_ship: bool
    ship_own_fuel: bool
