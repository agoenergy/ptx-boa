from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Literal, Optional, Protocol

import pandas as pd

from ptxboa.static import (
    ChainType,
    FlowCodeType,
    ParameterCodeType,
    ProcessCodeResType,
    ProcessCodeType,
    ProcessStepType,
    SourceRegionCodeType,
    TargetCountryCodeType,
    TransportType,
)

if TYPE_CHECKING:
    from ptxboa.process_classes import Process

CalculateDataType = dict[
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


@dataclass(slots=True, frozen=True)
class ChainDefStatic:
    """Without region/country."""

    chain_name: ChainType
    process_code_res: ProcessCodeResType
    secondary_processes: dict[FlowCodeType, ProcessCodeType]
    transport: TransportType
    ship_own_fuel: bool

    @property
    def unique_key(self):
        """Hashable id."""
        return (
            self.chain_name,
            self.process_code_res,
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
        **kwargs: str,
    ) -> float | None:
        """Get parameter value."""
        ...


ParameterGetters = dict[ParameterCodeType | str, ParameterGetter]
AggregateProcessDataType = tuple[ProcessDataType, dict[Process, ProcessDataType]]
