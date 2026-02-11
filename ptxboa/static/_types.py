from typing import Any, Dict, Literal

CalculateDataType = Dict[
    Literal[
        "flh_opt_process",
        "main_export_process_chain",
        "transport_process_chain",
        "main_import_process_chain",
        "secondary_process",
        "parameter",
        "context",
        "flh_opt_hash",
    ],
    Any,
]
