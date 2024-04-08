# -*- coding: utf-8 -*-
from typing import Any, Dict, Literal

CalculateDataType = Dict[
    Literal[
        "main_process_chain",
        "transport_process_chain",
        "secondary_process",
        "parameter",
        "context",
    ],
    Any,
]
