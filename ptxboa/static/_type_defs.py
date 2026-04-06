from dataclasses import dataclass
from typing import Any, Literal, Optional, Protocol

import pandas as pd

from ptxboa.static import (
    ChainType,
    DataQueryParameterType,
    FlowCodeType,
    ParameterCodeType,
    ProcessCodeResType,
    ProcessCodeType,
    ProcessStepType,
    ResultClassType,
    ResultCostType,
    SourceRegionCodeType,
    TargetCountryCodeType,
    TransportType,
)

CalculateDataType = dict[
    Literal[
        "flh_opt_process",  # "PV-FIX"/"WIND-ON" => ProcessDataType
        "main_export_process_chain",  # list[ProcessDataType]
        "main_transport_process_chain",  # list[ProcessDataType]
        "main_import_process_chain",  # list[ProcessDataType]
        "secondary_process",  # dict[FlowType,ProcessDataType]
        "secondary_process_import",  # dict[FlowType,ProcessDataType] # TODO new
        "parameter",  # WACC and SPECCOST on export side
        "parameter_import",  # global params and speccost on import side
        "context",  # {source/target}
        "flh_opt_hash",  # optional,addedby optimizer
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


@dataclass(slots=True, frozen=True)
class ChainDefStatic:
    """Without region/country."""

    chain_name: ChainType
    process_res: ProcessCodeResType | None
    secondary_processes: dict[FlowCodeType, ProcessCodeType]
    transport: TransportType
    ship_own_fuel: bool

    @property
    def unique_key(self):
        """Hashable id."""
        return (
            self.chain_name,
            self.process_res,
            frozenset(self.secondary_processes.values()),  # set of ProcessCodeType
            self.transport,
            self.ship_own_fuel,
        )


@dataclass(slots=True, frozen=True)
class ChainDef(ChainDefStatic):
    source_region_code: SourceRegionCodeType
    target_country_code: TargetCountryCodeType


ProcessStep = tuple[ProcessCodeType, ProcessStepType | None]


class ParameterGetter(Protocol):
    def __call__(
        self,
        process_code: ProcessCodeType | None = None,
        flow_code: FlowCodeType | None = None,
        **kwargs: str | None,
    ) -> float | None:
        """Get parameter value."""
        ...


ParameterGetters = dict[ParameterCodeType | str, ParameterGetter]

DataQueryDicType = dict[DataQueryParameterType, str | None]


@dataclass(slots=True, frozen=True)
class ProcessResultFlowsType:
    main_flow_out: float
    main_flow_in: float | None
    secondary_flows_in: dict[FlowCodeType, float]


@dataclass(slots=True, frozen=True)
class ProcessResultCostsType:
    process_type: ResultClassType | None = None
    process_subtype: ProcessCodeType | FlowCodeType | None = None
    cost_type: ResultCostType | None = None
    values: float = 0
    value_rel_per_flow: float = 0
    # capex: float = 0 # noqa
    # opex: float = 0 # noqa
    # specccost: float = 0 # noqa
    # lc: float | None = None  # TODO # noqa


@dataclass(slots=True, frozen=True)
class ProcessResultEmissionType:
    value: float = 0
