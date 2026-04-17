from dataclasses import dataclass
from typing import Any, Literal, Optional, Protocol

import pandas as pd

from ptxboa.static import (
    ChainType,
    DataQueryParameterType,
    EmissionType,
    FlowCodeType,
    ParameterCodeType,
    ProcessCodeResType,
    ProcessCodeType,
    ProcessStepType,
    ResultClassType,
    ResultCostType,
    ResultEmissionType,
    ResultGasType,
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
    df_results_emissions_e_g_co2e: pd.DataFrame
    df_results_emissions_m_g_co2e: pd.DataFrame
    _internal_process_data: Optional[list] = None
    _internal_data: Optional[dict] = None


@dataclass(slots=True, frozen=True)
class ApiCalculateResult:
    metadata: dict
    costs: pd.DataFrame
    emissions_t_co2e: pd.DataFrame
    emission_mass_t_co2e: pd.DataFrame
    _internal_process_data: Optional[list] = None
    _internal_data: Optional[dict] = None


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


ProcessStep = tuple[ProcessCodeType, ProcessStepType | str | None]


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
    process_type: ResultClassType
    process_subtype: ProcessCodeType | FlowCodeType
    cost_type: ResultCostType
    values: float


@dataclass(slots=True, frozen=True)
class ProcessEmissionType_E_M:
    co2_captured: float = 0  # used for CSS
    co2_bound_in_product: float = 0  # used for next process and final bound in product
    co2_bound_in_product_per_output: float | None = (
        None  # used for next process (partial flow)
    )
    co2_direct: float = 0  # used for output
    co2_indirect_scope2: float = 0  # used for output
    ch4_direct_co2e: float = 0  # used for output


ProcessEmissionType = dict[EmissionType, ProcessEmissionType_E_M]


@dataclass(slots=True, frozen=True)
class ProcessResultEmissionType:
    process_type: ResultClassType | str
    process_subtype: ProcessCodeType | FlowCodeType | str
    emission_type: ResultEmissionType
    gas_type: ResultGasType
    values: float
