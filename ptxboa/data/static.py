# -*- coding: utf-8 -*-
"""DO NOT EDIT (created by _update_static.py)."""

from typing import Literal

YearCode = Literal["2030", "2040"]

ParameterRangeCode = Literal["high", "low", "medium"]

SourceRegionCode = Literal[
    "ARE",
    "ARG",
    "ARG-BA",
    "ARG-CAT",
    "ARG-CBA",
    "ARG-CHA",
    "ARG-CHU",
    "ARG-COR",
    "ARG-CRB",
    "ARG-CRU",
    "ARG-EST",
    "ARG-FOR",
    "ARG-FUE",
    "ARG-JUJ",
    "ARG-LAR",
    "ARG-MEN",
    "ARG-MIS",
    "ARG-NEG",
    "ARG-NEU",
    "ARG-PAM",
    "ARG-RIO",
    "ARG-SAF",
    "ARG-SAJ",
    "ARG-SAL",
    "ARG-SAT",
    "ARG-TUC",
    "AUS",
    "BRA",
    "CHL",
    "CHN",
    "COL",
    "CRI",
    "DNK",
    "DZA",
    "EGY",
    "ESP",
    "IDN",
    "IND",
    "JOR",
    "KAZ",
    "KEN",
    "MAR",
    "MAR-BEN",
    "MAR-CAS",
    "MAR-DAK",
    "MAR-DRA",
    "MAR-FES",
    "MAR-GUE",
    "MAR-LAA",
    "MAR-LOR",
    "MAR-MAR",
    "MAR-RAB",
    "MAR-SOU",
    "MAR-TAN",
    "MEX",
    "MRT",
    "NAM",
    "NOR",
    "PER",
    "PRT",
    "RUS",
    "SAU",
    "SWE",
    "THA",
    "TUN",
    "UKR",
    "URY",
    "USA",
    "VNM",
    "ZAF",
    "ZAF-EC",
    "ZAF-FRS",
    "ZAF-GAU",
    "ZAF-KWA",
    "ZAF-LIM",
    "ZAF-MPU",
    "ZAF-NC",
    "ZAF-NW",
    "ZAF-WC",
]

TargetCountryCode = Literal[
    "CHN", "DEU", "ESP", "FRA", "IND", "JPN", "KOR", "NLD", "USA"
]

ProcessCode = Literal[
    "AEL-EL",
    "ATR",
    "CH3OHREC",
    "CH3OH-S",
    "CH3OH-SB",
    "CH3OHSYN",
    "CH4-COMP",
    "CH4-LIQ",
    "CH4-P-L",
    "CH4-P-LR",
    "CH4-P-S",
    "CH4-P-SR",
    "CH4-RGAS",
    "CH4-S",
    "CH4-SB",
    "CH4SYN",
    "DAC",
    "DESAL",
    "DRI",
    "DRI-S",
    "DRI-SB",
    "EFUELSYN",
    "EL-STR",
    "EL-TRANS",
    "H2-COMP",
    "H2-LIQ",
    "H2-P-L",
    "H2-P-LR",
    "H2-P-S",
    "H2-P-SR",
    "H2-RGAS",
    "H2-S",
    "H2-SB",
    "H2-STR",
    "LOHC-CON",
    "LOHC-REC",
    "LOHC-S",
    "LOHC-SB",
    "NH3-REC",
    "NH3-S",
    "NH3-SB",
    "NH3SYN",
    "PEM-EL",
    "PV-FIX",
    "PV-TRK",
    "REGASATR",
    "RES-HYBR",
    "SOEC-EL",
    "SYN-S",
    "SYN-SB",
    "WIND-OFF",
    "WIND-ON",
]

FlowCode = Literal[
    "BFUEL-L",
    "CH3OH-L",
    "CH4-G",
    "CH4-L",
    "CHX-L",
    "CO2-G",
    "C-S",
    "DRI-S",
    "EL",
    "H2-G",
    "H2-L",
    "H2O-L",
    "HEAT",
    "LOHC-L",
    "N2-G",
    "NH3-L",
]

ParameterCode = Literal[
    "CALOR",
    "CAPEX",
    "CAP-T",
    "CONV",
    "DST-S-D",
    "DST-S-DP",
    "EFF",
    "FLH",
    "LIFETIME",
    "LOSS-T",
    "OPEX-F",
    "OPEX-O",
    "OPEX-T",
    "RE-POT",
    "SEASHARE",
    "SPECCOST",
    "STR-CF",
    "WACC",
]

ScenarioCode = Literal[
    "2030 (high)",
    "2030 (low)",
    "2030 (medium)",
    "2040 (high)",
    "2040 (low)",
    "2040 (medium)",
]

ResultProcessTypes = Literal[
    "Carbon",
    "Derivate production",
    "Electricity and H2 storage",
    "Electricity generation",
    "Electrolysis",
    "HEAT",
    "Transportation (Pipeline)",
    "Transportation (Ship)",
    "Water",
]
