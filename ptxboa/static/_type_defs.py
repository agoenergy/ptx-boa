from typing import Any, Dict, Literal

from ptxboa.static import FlowCodeType, ParameterCodeType

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
