from __future__ import annotations  # otherwise nx.DiGraph[Process] does not work

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable, cast

import networkx as nx

from ptxboa.static import (
    SourceRegionCodeType,
    TargetCountryCodeType,
)
from ptxboa.static._type_defs import (
    CalculateDataType,
    ChainDef,
    DataQueryDicType,
    ParameterGetters,
    ProcessDataType,
    ProcessResultCostsType,
    ProcessResultEmissionType,
    ProcessResultFlowsType,
    PtxCalcResult,
)

if TYPE_CHECKING:
    from ptxboa.api_data import DataHandler


@dataclass(slots=True, frozen=True)
class Flow:
    pass


@dataclass(slots=True, frozen=True)
class Process:
    chain: "Chain"

    def get_parameter_data(
        self,
        parameter_getters: "ParameterGetters",
        parameter_values: DataQueryDicType,
    ) -> ProcessDataType: ...

    def calculate_flows(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> ProcessResultFlowsType: ...

    def calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, ProcessResultCostsType],
    ) -> ProcessResultCostsType: ...

    def calculate_emissions(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_emissions: dict[Process, ProcessResultEmissionType],
    ) -> ProcessResultEmissionType: ...

    @property
    def is_in_import_region(self) -> bool:
        return False


class Chain:
    _instances: dict[object, "Chain"] = {}

    def __init__(self, _graph: nx.DiGraph[Process]):
        self._graph = _graph

    @property
    def all_processes_ordered_forwards(self) -> Iterable[Process]: ...

    @property
    def all_processes_ordered_backwards(self) -> Iterable[Process]: ...

    @classmethod
    def _create_process_graph(cls, chain_def: ChainDef) -> nx.DiGraph[Process]: ...

    @classmethod
    def get_or_create(cls, chain_def: ChainDef) -> "Chain":
        key = chain_def.unique_key
        if key not in cls._instances:
            cls._instances[key] = Chain(
                _graph=cls._create_process_graph(chain_def=chain_def)
            )
        return cls._instances[key]

    def _get_default_parameter_values(self) -> DataQueryDicType: ...
    def _get_parameter_getters(
        self,
        data_handler: "DataHandler",
        use_user_data: bool = True,
    ) -> ParameterGetters: ...

    def _get_parameter_data_from_processes(
        self,
        data_handler: "DataHandler",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
    ) -> dict[Process, ProcessDataType]:
        result: dict[Process, ProcessDataType] = {}

        parameter_getters = self._get_parameter_getters(
            data_handler=data_handler, use_user_data=use_user_data
        )
        parameter_getters_default = self._get_default_parameter_values()

        for process in self.all_processes_ordered_forwards:
            parameter_values = parameter_getters_default | cast(
                DataQueryDicType,
                (
                    {
                        "source_region_code": target_country_code,
                        "target_country_code": target_country_code,
                    }  # NOTE: source_region_code
                    if process.is_in_import_region
                    else {
                        "source_region_code": source_region_code,
                        "target_country_code": target_country_code,
                    }
                ),
            )

            result[process] = process.get_parameter_data(
                parameter_getters=parameter_getters, parameter_values=parameter_values
            )
        return result

    def _calculate_flows(
        self, parameter_data: dict[Process, ProcessDataType]
    ) -> dict[Process, ProcessResultFlowsType]:
        results_flows: dict[Process, ProcessResultFlowsType] = {}
        for process in self.all_processes_ordered_backwards:
            results_flows[process] = process.calculate_flows(
                parameter_data=parameter_data, results_flows=results_flows
            )
        return results_flows

    def _calculate_costs(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> dict[Process, ProcessResultCostsType]:
        results_costs: dict[Process, ProcessResultCostsType] = {}
        for process in self.all_processes_ordered_forwards:
            results_costs[process] = process.calculate_costs(
                parameter_data=parameter_data,
                results_flows=results_flows,
                results_costs=results_costs,
            )
        return results_costs

    def _calculate_emissions(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
    ) -> dict[Process, ProcessResultEmissionType]:
        results_emissions: dict[Process, ProcessResultEmissionType] = {}
        for process in self.all_processes_ordered_forwards:
            results_emissions[process] = process.calculate_emissions(
                parameter_data=parameter_data,
                results_flows=results_flows,
                results_emissions=results_emissions,
            )
        return results_emissions

    def get_calculation_data(
        self,
        data_handler: "DataHandler",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
    ) -> CalculateDataType:
        parameter_data = self._get_parameter_data_from_processes(
            data_handler=data_handler,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            use_user_data=use_user_data,
        )
        return self._merge_parameter_data(parameter_data=parameter_data)

    def calculate(self, data: CalculateDataType) -> PtxCalcResult:
        parameter_data = self._split_parameter_data(data=data)
        results_flows = self._calculate_flows(parameter_data=parameter_data)
        results_costs = self._calculate_costs(
            parameter_data=parameter_data, results_flows=results_flows
        )
        results_emissions = self._calculate_emissions(
            parameter_data=parameter_data, results_flows=results_flows
        )
        return self._merge_calculation_results(
            parameter_data=parameter_data,
            results_flows=results_flows,
            results_costs=results_costs,
            results_emissions=results_emissions,
        )

    def plot(self, file_basename: str, results_flows: dict):
        pass

    def _merge_calculation_results(
        self,
        parameter_data: dict[Process, ProcessDataType],
        results_flows: dict[Process, ProcessResultFlowsType],
        results_costs: dict[Process, ProcessResultCostsType],
        results_emissions: dict[Process, ProcessResultEmissionType],
    ) -> PtxCalcResult: ...

    def _merge_parameter_data(
        self,
        parameter_data: dict[Process, ProcessDataType],
    ) -> CalculateDataType: ...

    def _split_parameter_data(
        self,
        data: CalculateDataType,
    ) -> dict[Process, ProcessDataType]: ...
