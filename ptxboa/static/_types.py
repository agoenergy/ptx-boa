# -*- coding: utf-8 -*-
from typing import Any, Dict, Literal

CalculateDataType = Dict[
    Literal[
        "flh_opt_process",
        "main_process_chain",
        "transport_process_chain",
        "secondary_process",
        "parameter",
        "context",
        "flh_opt_hash",
    ],
    Any,
]
