"""Class based calculation."""

import argparse
import logging
import re
from dataclasses import dataclass
from typing import Iterable, Literal, Protocol, Union, cast

import coloredlogs
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from ptxboa.static import (
    ChainType,
    FlowCodeType,
    OutputUnitType,
    ParameterCodeType,
    ParameterCodeValues,
    ProcessCodeType,
    ProcessStepType,
    ProcessStepValues,
    ResGenType,
    ScenarioType,
    SecProcCO2Type,
    SecProcH2OType,
    SourceRegionCodeType,
    SourceRegionNameType,
    TargetCountryCodeType,
    TargetCountryNameType,
    ToolVersionColorType,
    TransportType,
)

logger = logging.getLogger("main")

DataQueryParameterType = Literal[
    "parameter_code",
    "process_code",
    "flow_code",
    "source_region_code",
    "target_country_code",
    "default",
    "use_user_data",
    "region",
    "process_res",
    "process_ely",
    "process_deriv",
    "process_flh",
]

ProcessStepValuesSorted = ProcessStepValues
assert tuple(ProcessStepValuesSorted) == (
    "EL_STR",
    "ELY",
    "H2_STR",
    "DERIV",
    "DERIV2",
    "PRE_SHP",
    "SHP",
    "SHP_OWN",
    "POST_SHP",
    "PRE_PPL",
    "PPLS",
    "PPL",
    "PPLX",
    "PPLR",
    "POST_PPL",
    "ELY_I",
    "DERIV_I",
    "DERIV_I2",
)


df_process_by_code = DataHandler.get_dimension("process")
df_process_by_name = df_process_by_code.set_index("process_name", drop=False)
df_chain = DataHandler.get_dimension("chain")
df_parameter_by_code = DataHandler.get_dimension("parameter")
df_region_by_name = DataHandler.get_dimension("region")
df_region_by_code = df_region_by_name.set_index("region_code", drop=False)

# get_dimensions_parameter_code


class ProcessType:
    def __init__(
        self,
        process_code: ProcessCodeType,
        is_transport: bool,
        is_secondary: bool,
        is_re_generation: bool,
        is_transformation: bool,
        is_storage: bool,
        is_pipeline: bool,
        is_pipeline_retrofitted: bool,
        is_pipeline_sea: bool,
        is_shipping: bool,
        is_shipping_own_fuel: bool,
        main_flow_code_out: FlowCodeType,
        main_flow_code_in: FlowCodeType | None,
        secondary_flows: Iterable[FlowCodeType] | None,
        **_kwargs,
    ):
        self.process_code: ProcessCodeType = process_code
        self.is_transport: bool = is_transport  # includes pre/post transformation
        self.is_secondary: bool = is_secondary
        self.is_transformation: bool = is_transformation
        self.is_storage: bool = is_storage
        self.is_re_generation: bool = is_re_generation
        self.is_pipeline: bool = is_pipeline
        self.is_pipeline_retrofitted: bool = is_pipeline_retrofitted
        self.is_pipeline_sea: bool = is_pipeline_sea
        self.is_shipping: bool = is_shipping
        self.is_shipping_own_fuel: bool = is_shipping_own_fuel
        self.main_flow_code_out: FlowCodeType = main_flow_code_out
        self.main_flow_code_in: FlowCodeType | None = main_flow_code_in
        self.secondary_flow_types: set[FlowCodeType] = (
            set(secondary_flows) if secondary_flows else set()
        )

        # checks
        if self.main_flow_code_in in self.secondary_flow_types:
            logger.error(
                f"{self.process_code}: main_flow_code_in {self.main_flow_code_in} "
                "in secondary_flow_types"
            )
        if self.main_flow_code_out in self.secondary_flow_types:
            logger.error(
                f"{self.process_code}: main_flow_code_out {self.main_flow_code_out} "
                "in secondary_flow_types"
            )
        if self.is_secondary and self.main_flow_code_in:
            logger.warning(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )
        if self.is_initial and self.main_flow_code_in:
            logger.error(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return self.is_re_generation or self.process_code == "NG-PROD#B"

    @property
    def process_class(self) -> type["Process"]:
        """Process class.

        So we can dynamically use subclasses.
        """
        if self.is_initial:
            return InitialProcess
        elif self.is_secondary:
            return SecondaryProcess
        elif self.is_transport and not self.is_transformation:
            return TransportProcess
        else:
            return Process

    @property
    def allow_in_export(self) -> bool:
        """Is process allowed in export."""
        return not self.allow_in_transport or self.is_secondary

    @property
    def allow_in_transport(self) -> bool:
        """Is process allowed in transport."""
        return (
            self.is_transport  # includes pre/post transformation
            and not self.is_transformation  # we want pre/post shipping in export/import
            and not self.is_secondary
            and not self.is_storage
        )

    @property
    def allow_in_import(self) -> bool:
        """Is process allowed in import."""
        # secondary: only allow CCS
        return self.allow_in_export and (
            # CSS is onlyallowed secondary(?) # TODO:generalize?
            not self.is_secondary
            or self.process_code == "CO2-T+S#B"
        )


ProcessTypes: dict[ProcessCodeType, ProcessType] = {
    p["process_code"]: ProcessType(**cast(dict, p))
    for p in df_process_by_code.to_dict(orient="records")
}


class AbstractProcess:
    _parameter_codes_process: list[ParameterCodeType] = []
    _parameter_codes_process_flow: list[ParameterCodeType] = []

    def __init__(
        self,
        process_step: ProcessStepType | str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        self._main_flow_out: float | None = None  # will be set in calculate()
        self._main_flow_in: float | None = None  # will be set in calculate()
        self._secondary_flows_in: dict[FlowCodeType, float] | None = None
        self.parent_process = parent_process

        self._parameters: (
            dict[
                ParameterCodeType | str,
                float | None | dict[FlowCodeType | str, float | None],
            ]
            | None
        ) = None  # will be set in initialize_parameters()
        self.process_step: ProcessStepType | str | None = process_step

    def get_main_flow_out(self) -> float:
        """Value of main out flow."""
        if self._main_flow_out is None:
            raise Exception("Not calculated yet")
        return self._main_flow_out

    def get_main_flow_in(self) -> float:
        """Value of calculated main in flow."""
        if self._main_flow_in is None:
            raise Exception("Not calculated yet, or main_flow_in does not exist")
        return self._main_flow_in

    def get_secondary_flow_in(self, flow_code: FlowCodeType) -> float:
        """Value of calculated secondary in flow for given flow type."""
        if self._secondary_flows_in is None:
            raise Exception(f"Not calculated yet: {self}")
        return self._secondary_flows_in[flow_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return None

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        raise NotImplementedError

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return None

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return set()

    @property
    def _parameter_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return self.secondary_flow_types

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return False

    @property
    def is_transport(self) -> bool:
        """Is this a transport process."""
        return False

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return False

    def initialize_parameters(
        self, parameter_getters: "ParameterGetters", data_lookup_defaults: dict
    ):
        """Initialize parameetr data for this process."""
        self._parameters = {}
        for p in self._parameter_codes_process:
            self._parameters[p] = parameter_getters[p](
                process_code=self.process_code, **data_lookup_defaults
            )
        {
            p: parameter_getters[p](
                process_code=self.process_code, **data_lookup_defaults
            )
            for p in self._parameter_codes_process
        }

        for p in self._parameter_codes_process_flow:
            self._parameters[p] = {
                f: parameter_getters[p](
                    process_code=self.process_code, flow_code=f, **data_lookup_defaults
                )
                for f in self._parameter_flow_types
            }

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        self._main_flow_out = main_flow_out

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        step = f"{self.process_step}=" if self.process_step else ""
        return f"{self.__class__.__name__}({step}{self.process_code}{s_val})"

    def get_parameters_incl_parents(self) -> dict:
        params = self._parameters or {}
        if self.parent_process:
            params = self.parent_process.get_parameters_incl_parents() | params
        return params


class Process(AbstractProcess):
    color = "lightblue"
    _parameter_codes_process = ["LIFETIME", "EFF", "FLH", "CAPEX", "OPEX-F", "OPEX-O"]
    _parameter_codes_process_flow = [
        "CH4SHARE",
        "EF_E",
        "EF_M",
        "CBOUND",
        "CONV-OT",
        "CO2CPT-R",
        "CO2CPT-S",
        "CONV",
        "LOSS",
    ]

    def __init__(
        self,
        process_code: ProcessCodeType,
        process_step: ProcessStepType | str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
        self._process_type: ProcessType = ProcessTypes[process_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return self._process_type.process_code

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._process_type.main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self._process_type.main_flow_code_in

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return self._process_type.secondary_flow_types

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return self._process_type.is_initial

    @property
    def is_transport(self) -> bool:
        """Is this a transport process."""
        return self._process_type.is_transport

    @property
    def is_re_generation(self) -> bool:
        """Is this re generation process."""
        return self._process_type.is_re_generation

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)
        eff: float = self._parameters.get("EFF")  # type: ignore
        if not eff:
            logging.warning("EFF = 0")
            eff = 1

        self._main_flow_in = main_flow_out / eff
        self._secondary_flows_in = {}
        convs = self._parameters.get("CONV", {})  # type: ignore
        for fc in self.secondary_flow_types:
            conv: float = convs.get(fc, 0)  # type: ignore
            value = main_flow_out * conv
            if value < 0:  # ignore (e.g. exothermal heat)
                value = 0
            self._secondary_flows_in[fc] = value


class TransportProcess(Process):
    _parameter_codes_process = ["OPEX-T", "LOSS-T"]
    color = "teal"


class SecondaryProcess(Process):
    color = "lightgreen"

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return True


class InitialProcess(SecondaryProcess):
    color = "skyblue"


class MarketProcess(AbstractProcess):
    color = "lightgray"
    _parameter_codes_process_flow: list[ParameterCodeType] = ["SPECCOST"]

    def __init__(
        self,
        main_flow_code_out: FlowCodeType,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(parent_process=parent_process)
        self._main_flow_code_out: FlowCodeType = main_flow_code_out

    @property
    def _parameter_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return {self.main_flow_code_out}

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)
        # TODO

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._main_flow_code_out

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return self.main_flow_code_out  # type: ignore


def get_chain_sections(
    main_process_codes_steps: list["ProcessStep"],
) -> list[tuple[type["ChainSectionProcess"], int, int]]:
    # split and check into export, transport, import
    is_transport = [
        ProcessTypes[p].allow_in_transport for p, _s in main_process_codes_steps
    ]
    # first and last index
    idx_transport_start = is_transport.index(True)
    try:
        idx_transport_end = is_transport.index(False, idx_transport_start)
    except ValueError:  # no import steps
        idx_transport_end = len(is_transport)

    if not (0 < idx_transport_start < idx_transport_end):
        raise Exception("Transport")
    return [  # export,transport,import
        (ChainExportProcess, 0, idx_transport_start),
        (ChainTransportProcess, idx_transport_start, idx_transport_end),
        (ChainImportProcess, idx_transport_end, len(main_process_codes_steps)),
    ]


class AggregateProcess(AbstractProcess):
    def __init__(
        self,
        process_graph: "ProcessGraph",
        process_step: str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
        self.process_graph: "ProcessGraph" = process_graph

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self.process_graph.main_processes[-1].main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self.process_graph.main_processes[0].main_flow_code_in

    @property
    def full_main_chain(self) -> list[AbstractProcess]:
        """List of the entire main chain (including nested aggregated processes)."""
        result: list[AbstractProcess] = []
        for proc in self.process_graph.main_processes:
            if isinstance(proc, AggregateProcess):
                result += proc.full_main_chain
            else:
                result.append(proc)

        return result

    def initialize_parameters(
        self, parameter_getters: "ParameterGetters", data_lookup_defaults: dict
    ):
        """Initialize parameetr data for this process."""

        super().initialize_parameters(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,
        )

        for process in self.process_graph.calculate_order:
            process.initialize_parameters(
                parameter_getters=parameter_getters,
                data_lookup_defaults=data_lookup_defaults,
            )

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)

        # in first in reverse order, we use the given main_flow_out
        # for all following, we combine the required flows from all links.
        # if graph iscorrect,these must have been already calculated
        for process in self.process_graph.calculate_order:
            if process == self.process_graph.main_processes[-1]:
                # is last in main chain
                main_flow_out_current = main_flow_out
            else:
                main_flow_out_current = 0  # calculate
                flow_code = process.main_flow_code_out

                for proc_target, in_main in self.process_graph.links_out.get(
                    process, []
                ):
                    logger.info(f"{process}: Serve {flow_code} to {proc_target}")
                    main_flow_out_current += (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow_code=flow_code)
                    )

                # check
                if not main_flow_out_current:
                    if main_flow_out_current is None:
                        raise ValueError(f"{process}: main_flow_out is None")
                    else:
                        logger.warning(f"{process}: main_flow_out is 0")
            logger.info(f"Calculate: {process} for {main_flow_out_current}")
            process.calculate(main_flow_out=main_flow_out_current)

            if process == self.process_graph.main_processes[0]:
                self._main_flow_in = process.get_main_flow_in()

    def get_subprocesses_by_class(
        self, class_or_classes: type | tuple[type]
    ) -> list[AbstractProcess]:
        return [
            p
            for p in self.process_graph.calculate_order
            if isinstance(p, class_or_classes)
        ]


class ChainProcess(AggregateProcess):
    _parameter_codes_process = ["CALOR"]  # conversion kg / kwh

    def __init__(
        self,
        transport: TransportType,
        ship_own_fuel: bool,
        chain: str,
        first_process_code: ProcessCodeType,
        secondary_process_codes: set[ProcessCodeType],
        **_kwargs,
    ):
        """Create aggregated process for entire chain."""

        chain_data = DataHandler.get_dimension("chain").loc[chain].to_dict()

        main_process_codes_steps: list["ProcessStep"] = [
            (cast(ProcessCodeType, chain_data[step]), cast(ProcessStepType, step))
            for step in ProcessStepValuesSorted
            if chain_data[step]
        ]

        main_process_codes_steps_filtered = filter_transport_process_codes(
            main_process_codes_steps,
            transport=transport,
            ship_own_fuel=ship_own_fuel,
        )
        # add initial step
        chain_start_with_res = ProcessTypes[first_process_code].is_re_generation
        initial_step = cast(
            ProcessStepType,
            # TODO: maybe from green/blue?
            ("RES" if chain_start_with_res else "NG_PROD"),
        )
        main_process_codes_steps_filtered.insert(0, (first_process_code, initial_step))

        # for FLH lookup we need these process codes
        self._data_lookup_defaults_static: dict[str, ProcessCodeType | None] = {
            "process_res": (first_process_code if chain_start_with_res else None),
            "process_ely": chain_data["ELY"],
            "process_deriv": chain_data["DERIV"],
        }
        self._data_lookup_defaults: dict | None = None  # will be set in init params

        check_use_all_main_process_codes = []

        # FIXME: pre/post shipping processes, remove not required

        main_processes: list[AbstractProcess] = []

        for ChainSectionProcessClass, i, j in get_chain_sections(
            main_process_codes_steps=main_process_codes_steps_filtered
        ):
            main_process_codes_steps_part: list["ProcessStep"] = (
                main_process_codes_steps_filtered[i:j]
            )
            if not main_process_codes_steps_part:
                # no steps ==> skip this
                continue
            # check
            invalid_processes = [
                p
                for p, _s in main_process_codes_steps_part
                if not ChainSectionProcessClass.process_allowed(p)
            ]
            if invalid_processes:
                raise Exception(
                    f"Invalid {ChainSectionProcessClass} "
                    f"{main_process_codes_steps_part}: {invalid_processes}"
                )
            secondary_process_codes_part: set[ProcessCodeType] = {
                p
                for p in secondary_process_codes
                if ChainSectionProcessClass.process_allowed(p)
            }

            process = ChainSectionProcessClass(
                main_process_codes_steps=main_process_codes_steps_part,
                secondary_process_codes=secondary_process_codes_part,
                parent_process=self,
            )
            main_processes.append(process)

            check_use_all_main_process_codes = (
                check_use_all_main_process_codes + main_process_codes_steps_part
            )

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes, secondary_processes=[], parent_process=self
        )

        super().__init__(
            process_graph=process_graph,
            process_step="CHAIN",
        )

        # check (TODO: can be removed later)
        if not tuple(check_use_all_main_process_codes) == tuple(
            main_process_codes_steps_filtered
        ):
            raise Exception(
                f"{check_use_all_main_process_codes} != {main_process_codes_steps_filtered}"
            )
        # check (TODO: can be removed later)
        main_process_codes_ = tuple(p.process_code for p in self.full_main_chain)
        if (
            tuple(p for p, s_ in main_process_codes_steps_filtered)
            != main_process_codes_
        ):
            raise Exception(main_process_codes_)

    def initialize_parameters(
        self,
        parameter_getters: "ParameterGetters",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
    ):
        self._data_lookup_defaults = {
            "source_region_code": source_region_code,
            "target_country_code": target_country_code,
        }
        super().initialize_parameters(
            parameter_getters=parameter_getters,
            data_lookup_defaults=self._data_lookup_defaults_static
            | self._data_lookup_defaults,
        )


class ChainSectionProcess(AggregateProcess):
    _parameter_codes_process = ["WACC"]  # different in export / import

    def __init__(
        self,
        main_process_codes_steps: list["ProcessStep"],
        secondary_process_codes: set[ProcessCodeType],
        parent_process: Union["AbstractProcess", None] = None,
    ):

        main_processes: list[AbstractProcess] = [
            ProcessTypes[pt].process_class(
                process_code=pt, process_step=ps, parent_process=self
            )
            for pt, ps in main_process_codes_steps
        ]
        secondary_processes: list[Process] = [
            ProcessTypes[pt].process_class(process_code=pt, parent_process=self)
            for pt in secondary_process_codes
        ]

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes,
            secondary_processes=secondary_processes,
            parent_process=self,
        )
        super().__init__(
            process_graph=process_graph,
            parent_process=parent_process,
        )

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        return True


class ChainExportProcess(ChainSectionProcess):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        return ProcessTypes[process_code].allow_in_export


class ChainImportProcess(ChainSectionProcess):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        return ProcessTypes[process_code].allow_in_import

    def initialize_parameters(
        self, parameter_getters: "ParameterGetters", data_lookup_defaults: dict
    ):
        """Initialize parameetr data for this process."""
        # when getting data: switch region

        data_lookup_defaults = data_lookup_defaults | {
            "source_region_code": data_lookup_defaults["target_country_code"]
        }
        super().initialize_parameters(
            parameter_getters=parameter_getters,
            data_lookup_defaults=data_lookup_defaults,
        )


class ChainTransportProcess(ChainSectionProcess):
    _parameter_codes_process = [
        "CAP-T",
        "DST-S-D",
        "DST-S-DP",
        "SEASHARE",
    ]

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        return ProcessTypes[process_code].allow_in_transport


def group_by_flow_type_out(
    process_codes: Iterable[ProcessCodeType],
) -> dict[FlowCodeType, ProcessCodeType]:
    result = {}
    for process_code in process_codes:
        flow_code = ProcessTypes[process_code].main_flow_code_out
        if flow_code in result:
            raise KeyError(f"Multiple items for {flow_code}")
        result[flow_code] = process_code
    return result


@dataclass
class Settings:
    scenario: ScenarioType
    secproc_co2: SecProcCO2Type | None
    secproc_water: SecProcH2OType | None
    chain: ChainType
    res_gen: ResGenType | None
    region: SourceRegionNameType
    country: TargetCountryNameType
    transport: TransportType
    ship_own_fuel: bool
    user_data: pd.DataFrame | None
    tool_version_color: ToolVersionColorType


def create_permutations(scenario: ScenarioType) -> Iterable[Settings]:

    # secproc_co2: SecProcCO2Type | None # noqa
    # secproc_water: SecProcH2OType | None # noqa
    # chain: ChainNameType # noqa
    res_gen: ResGenType | None = df_process_by_code.loc["RES-HYBR", "process_name"]  # type: ignore
    region: SourceRegionNameType = df_region_by_code.loc["DZA", "region_name"]  # type: ignore
    country: TargetCountryNameType = df_region_by_code.loc["DEU", "region_name"]  # type: ignore
    # transport: TransportType # noqa
    # ship_own_fuel: bool # noqa
    transports: list[tuple[TransportType, bool]] = [
        ("Pipeline", False),
        ("Ship", False),
        ("Ship", True),
    ]

    for chain_spec in df_chain.to_dict(orient="records"):
        chain = chain_spec["chain"]
        tool_version_color: ToolVersionColorType = (
            "green" if chain_spec["is_green"] else "blue"
        )
        secproc_co2: SecProcCO2Type | None = (
            "Direct Air Capture (blue)"
            if tool_version_color == "blue"
            else "Direct Air Capture"
        )
        secproc_water: SecProcH2OType | None = "Sea Water desalination"

        for transport, ship_own_fuel in transports:
            if transport == "Pipeline" and not chain_spec["can_pipeline"]:
                continue
            if transport == "Ship" and ship_own_fuel and not chain_spec["SHP_OWN"]:
                continue
            yield Settings(
                scenario=scenario,
                country=country,
                region=region,
                chain=chain,
                ship_own_fuel=ship_own_fuel,
                transport=transport,
                res_gen=res_gen,
                user_data=None,
                tool_version_color=tool_version_color,
                secproc_co2=secproc_co2,
                secproc_water=secproc_water,
            )


class ProcessGraph:
    _KEY_MAIN = "(MAIN)"  # nust not be a flow code

    def __init__(
        self,
        main_processes: list[AbstractProcess],
        secondary_processes: list[Process],
        parent_process: AbstractProcess | None = None,
    ):
        self.main_processes: list[AbstractProcess] = main_processes

        # calculate_order: includes main, secondary, tertiary(market) processes
        self.calculate_order: Iterable[AbstractProcess] = []
        self.links_out: dict[AbstractProcess, list[tuple[AbstractProcess, bool]]] = {}

        G = nx.DiGraph()
        G.add_nodes_from(main_processes)
        G.add_nodes_from(secondary_processes)

        def add_link_out(
            proc_provider: AbstractProcess,
            proc_recipient: AbstractProcess,
            in_main: bool,
        ):
            # check
            flow_codes_in = (
                {proc_recipient.main_flow_code_in}
                if in_main
                else proc_recipient.secondary_flow_types
            )
            if proc_provider.main_flow_code_out not in flow_codes_in:
                raise Exception(f"Cannot link {proc_provider} => {proc_recipient}")

            if proc_provider not in self.links_out:
                self.links_out[proc_provider] = []
            self.links_out[proc_provider].append((proc_recipient, in_main))
            G.add_edge(proc_provider, proc_recipient)
            logger.info(
                f"Create link {proc_provider}({proc_provider.main_flow_code_out}) "
                f"{'==>' if in_main else '-->'} {proc_recipient}"
            )

        market_processes: dict[FlowCodeType, MarketProcess] = {}

        def get_or_create_market_process(flow_type: FlowCodeType) -> MarketProcess:
            if flow_type not in market_processes:
                market_processes[flow_type] = MarketProcess(
                    main_flow_code_out=flow_type, parent_process=parent_process
                )
                G.add_node(market_processes[flow_type])
            return market_processes[flow_type]

        # collect all provider of secondary flows (can also come from initial (EL/NG))
        flow_provider_sec_or_initial: dict[FlowCodeType, AbstractProcess] = {}
        first_proc = self.main_processes[0]
        flow_from_initial_proc: FlowCodeType | None = None
        if first_proc.is_initial:
            flow_provider_sec_or_initial[first_proc.main_flow_code_out] = first_proc
            flow_from_initial_proc = first_proc.main_flow_code_out
        for sec_proc in secondary_processes:
            if sec_proc.main_flow_code_out in flow_provider_sec_or_initial:
                logger.warning(f"flow already proveided, skipping {sec_proc}")
                continue
            flow_provider_sec_or_initial[sec_proc.main_flow_code_out] = sec_proc

        # collect required flows
        required_flows_procs: dict[FlowCodeType, list[tuple[AbstractProcess, bool]]] = (
            {}
        )

        def add_required_flows_proc(
            proc: AbstractProcess, flow: FlowCodeType, in_main: bool
        ):
            if flow not in required_flows_procs:
                required_flows_procs[flow] = []
            required_flows_procs[flow].append((proc, in_main))

        for p in main_processes:
            for f in p.secondary_flow_types:
                add_required_flows_proc(p, f, in_main=False)
        for p in secondary_processes:
            for f in p.secondary_flow_types:
                add_required_flows_proc(p, f, in_main=False)
            if p.main_flow_code_in:
                # TODO: technically, secondary flows should not have main_flow_code_in
                # but some have them anyways?
                add_required_flows_proc(p, p.main_flow_code_in, in_main=True)

        # match required and provided flows in specific order without creating loops
        # specific order is important so we get a deterministic graph
        def sort_flows_b_priority(
            flow_codes: Iterable[FlowCodeType],
        ) -> Iterable[FlowCodeType]:
            flow_codes_todo = set(flow_codes)
            # FIXME: better way to set priority

            for f in [flow_from_initial_proc, "CO2-C", "EL", "HEAT"]:
                if f in flow_codes_todo:
                    yield f
                    flow_codes_todo.remove(f)

            yield from sorted(flow_codes_todo)

        # link main chain
        for i in range(len(main_processes) - 1):
            add_link_out(main_processes[i], main_processes[i + 1], in_main=True)

        for flow in sort_flows_b_priority(required_flows_procs):
            for proc_target, in_main in required_flows_procs[flow]:
                # try to get from secondary
                prov_sec = flow_provider_sec_or_initial.get(flow)
                if prov_sec:
                    # try to add without loop
                    if nx.has_path(G, proc_target, prov_sec):
                        logger.warning(
                            f"Could not add link {prov_sec} ={flow}=> {proc_target} "
                            "because it would create a loop. fall back on market"
                        )
                        prov_sec = None  # use market
                if not prov_sec:
                    prov_sec = get_or_create_market_process(flow)
                add_link_out(prov_sec, proc_target, in_main=in_main)

        # optional: subgraph to drop unused secondary

        procs_old = set(G.nodes)
        last_proc = self.main_processes[-1]
        G = cast(nx.DiGraph, G.subgraph(nx.ancestors(G, last_proc) | {last_proc}))
        procs_new = set(G.nodes)

        procs_dropped = procs_old - procs_new
        if procs_dropped:
            logger.warning("Dropping unused: %s", [str(x) for x in procs_dropped])
            # drop from links_out
            # TODO: maybe use Digraph? - this is very ugly
            for k, vs in self.links_out.items():
                self.links_out[k] = [(p, m) for p, m in vs if p not in procs_dropped]

        # calculate_order: includes main, secondary, tertiary(market) processes
        self.calculate_order = list(reversed(list(nx.topological_sort(G))))

        # check (TODO:can be removed later)
        missing_main = set(self.main_processes) - set(self.calculate_order)
        if missing_main:
            raise Exception(f"missing_main: {missing_main}")


def create_permutation_names(permutations: Iterable[Settings]) -> dict[str, Settings]:
    def create_name(settings: Settings) -> str:
        name = (
            f"{settings.chain}_{settings.transport}"
            f"{'_OWN' if settings.ship_own_fuel else ''}"
        )
        name = re.sub("[^A-Za-z0-9-%()]", "_", name)
        return name

    result: dict[str, Settings] = {}
    for settings in permutations:
        name = create_name(settings)
        if name in result:
            raise KeyError(name)
        result[name] = settings
    return result


def filter_transport_process_codes(
    main_process_codes_steps: list["ProcessStep"],
    transport: TransportType,
    ship_own_fuel: bool,
) -> list["ProcessStep"]:
    """If shipping: remove pipeline (and pre/post), and vice versa."""

    drop_steps: set[ProcessStepType | str]

    if transport == "Pipeline":
        drop_steps = {
            "PRE_SHP",
            "POST_SHP",
        }
    elif transport == "Ship":
        drop_steps = {
            "PRE_PPL",
            "PPLS",
            "PPL",
            "PPLX",
            "PPLR",
            "POST_PPL",
        }
        if ship_own_fuel:
            drop_steps = drop_steps | {"SHP"}
        else:
            drop_steps = drop_steps | {"SHP_OWN"}
    else:
        raise NotImplementedError(transport)

    return [(p, s) for p, s in main_process_codes_steps if s not in drop_steps]


ProcessStep = tuple[ProcessCodeType, ProcessStepType | None]


def plot_get_pos(
    chain_process: AggregateProcess,
) -> dict[AbstractProcess, tuple[float, float]]:

    node_pos = {}
    xs: list[float] = [0, 0, 0]
    proc_end_last = None

    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        xs[1] = max(xs[0] + 0.25, xs[0])  # stagger
        xs1_start = xs[1]
        xs[2] = max(xs[0], xs[2])

        for process in reversed(list(process_graph.calculate_order)):
            key = process

            # if is_main:
            if process in process_graph.main_processes:
                xs[0] = xs[0] + 1
                x = xs[0]
                y = 0
                if not proc_end_last and process == process_graph.main_processes[0]:
                    y = 0.05  # initial a little closer to secondary
            elif not isinstance(process, MarketProcess):
                #  is secondary
                xs[1] = xs[1] + 1
                x = xs[1]
                # non linear disntance for non overlapping arrows

                ampl = (x - xs1_start) * 0.01
                sgn = (x - xs1_start) % 2 - 1
                y = 0.1 + ampl * sgn
            else:
                # market
                xs[2] = xs[2] + 1
                x = xs[2]
                y = 0.2

            node_pos[key] = (x, y)

        proc_end_last = process_graph.main_processes[-1]

    return node_pos


def nested_round_drop_empty(x):
    if isinstance(x, list):
        return [nested_round_drop_empty(v) for v in x]
    elif isinstance(x, dict):
        result = {k: nested_round_drop_empty(v) for k, v in x.items()}
        result = {k: v for k, v in result.items() if v}
        return result
    elif isinstance(x, float):
        return round(x, 4)
    else:
        return x


def plot(chain_process: AggregateProcess, name: str):

    # Create a directed graph
    G = nx.DiGraph()
    node_labels = {}
    edge_labels = {}
    edge_widths = {}

    proc_end_last = None
    len_main_total = 0
    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        for process in reversed(list(process_graph.calculate_order)):
            label = str(process)

            G.add_node(process)
            node_labels[process] = (
                label.replace("=", "\n")
                .replace("(", "\n")
                .replace(")", "\n")
                .replace(" ", "\n")
                .strip()
            )

            for proc_target, in_main in process_graph.links_out.get(process, []):
                flow = process.main_flow_code_out
                e = (process, proc_target)
                G.add_edge(*e)
                try:
                    value = (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow)
                    )
                    value_str = f"\n{value:.4f}"
                except Exception:
                    value_str = ""
                edge_labels[e] = f"{flow}{value_str}"
                edge_widths[e] = 2 if in_main else 1

        if proc_end_last:
            # link from previous subpgraph
            proc_start = process_graph.main_processes[0]
            e = (proc_end_last, proc_start)
            G.add_edge(*e)
            edge_labels[e] = proc_end_last.main_flow_code_out
            try:
                edge_labels[e] += f"\n{proc_start.get_main_flow_in():.4f}"
            except Exception:  # not calculated yet, # noqa: S110
                pass
            edge_widths[e] = 2

        proc_end_last = process_graph.main_processes[-1]

        len_main_total += len(process_graph.main_processes)

    scale = 3

    # node_pos = nx.circular_layout(G) # noqa
    node_pos = plot_get_pos(chain_process=chain_process)

    plt.close()
    plt.clf()
    plt.figure(figsize=(len_main_total * scale, 2 * scale))

    # Draw nodes
    nx.draw(
        G,
        node_pos,
        with_labels=False,
        node_color=[cast(Process, k).color for k in G.nodes()],
        width=[edge_widths[k] for k in G.edges()],
        node_size=2000 * scale,
    )

    # Draw node labels
    nx.draw_networkx_labels(
        G, node_pos, labels=node_labels, font_size=6, font_color="black"
    )

    # Draw edge labels
    nx.draw_networkx_edge_labels(
        G,
        node_pos,
        edge_labels=edge_labels,
        font_size=6,
        font_color="black",
        label_pos=0.7,  # closer to beginning (1 ist start?)
    )

    # Save to PNG
    plt.savefig(f"chain_flowcharts/{name}.png", dpi=300)


class ParameterGetter(Protocol):
    def __call__(
        self,
        process_code: ProcessCodeType | None = None,
        flow_code: FlowCodeType | None = None,
        **kwargs,
    ) -> float: ...


class ParameterGetter_(Protocol):
    def __call__(
        self,
        process_code: ProcessCodeType | None = None,
        flow_code: FlowCodeType | None = None,
        **kwargs,
    ) -> tuple[str, float | None]: ...


ParameterGetters = dict[ParameterCodeType | str, ParameterGetter]


def create_parameter_getters(
    data_handler: DataHandler, use_user_data: bool
) -> ParameterGetters:

    def _get_df(
        parameter_code: ParameterCodeType, process_code: ProcessCodeType | None
    ):
        if (
            parameter_code == "FLH"
            and process_code
            and not ProcessTypes[process_code].is_re_generation
        ):
            # FLH not changed by user_data
            df = data_handler.flh
        else:
            if use_user_data:
                df = data_handler.scenario_data
            else:
                df = data_handler._scenario_data
        return df

    def _get_parameter_keys(
        parameter_code: ParameterCodeType, use_global_default: bool = False
    ) -> list[tuple[DataQueryParameterType, bool]]:
        if parameter_code == "FLH":
            return [
                (x, True)
                for x in [
                    "source_region_code",  # => region
                    "process_res",
                    "process_ely",
                    "process_deriv",
                    "process_code",  # => process_flh
                ]
            ]  # type: ignore
        else:
            dims = set(df_parameter_by_code.at[parameter_code, "dimensions"])  # type: ignore
            return [
                ("parameter_code", True),
                ("process_code", "process_code" in dims),
                ("flow_code", "flow_code" in dims),
                (
                    "source_region_code",
                    "source_region_code" in dims and not use_global_default,
                ),
                ("target_country_code", "target_country_code" in dims),
            ]

    def make_getter(
        parameter_code: ParameterCodeType, use_global_default: bool
    ) -> ParameterGetter_:
        keys = _get_parameter_keys(
            parameter_code, use_global_default=use_global_default
        )

        def _get_value(
            process_code: ProcessCodeType | None = None,
            flow_code: FlowCodeType | None = None,
            **data_lookup_defaults,
        ) -> tuple[str, float | None]:
            df = _get_df(parameter_code=parameter_code, process_code=process_code)
            # all available key values
            key_vals = data_lookup_defaults | {
                "parameter_code": parameter_code,
                "process_code": process_code,
                "process_flh": process_code,  # for FLH
                "flow_code": flow_code,
            }
            # join only required key_vals in correct order

            key = ",".join([(key_vals.get(k) or "") if use else "" for k, use in keys])

            # FIXME: remove later
            key_debug = ",".join(
                [k + "=" + ((key_vals.get(k) or "") if use else "") for k, use in keys]
            )
            if parameter_code == "FLH":
                key_debug = "parameter_code=FLH," + key_debug

            try:
                value = cast(float, df.at[key, "value"])
            except Exception:
                value = None

            logger.debug("data lookup: %s => %s", key_debug, value)

            return key_debug, value

        return _get_value

    def make_getter_2(
        parameter_code: ParameterCodeType,
    ) -> ParameterGetter:
        has_global_default = df_parameter_by_code.at[
            parameter_code, "has_global_default"
        ]

        default_value: float = (
            1 if parameter_code in {"EFF", "CALOR"} else 0
        )  # TODO: from  DB?

        _get_value_ = make_getter(
            parameter_code=parameter_code, use_global_default=False
        )
        _get_value_global_default = make_getter(
            parameter_code=parameter_code, use_global_default=True
        )

        def get_value(
            process_code: ProcessCodeType | None = None,
            flow_code: FlowCodeType | None = None,
            **kwargs,
        ) -> float:
            key, value = _get_value_(
                process_code=process_code, flow_code=flow_code, **kwargs
            )
            if value is None and has_global_default:
                key, value = _get_value_global_default(
                    process_code=process_code, flow_code=flow_code, **kwargs
                )
            if value is None:
                # TODO: get complete key
                logger.warning("No data for %s", key)
                value = default_value

            return value

        return get_value

    return {
        parameter_code: make_getter_2(parameter_code)  # type: ignore
        for parameter_code in ParameterCodeValues  # type: ignore
    }


def create_chain_process_api_wrapper(
    scenario: ScenarioType,
    secproc_co2: SecProcCO2Type | None,
    secproc_water: SecProcH2OType | None,
    chain: ChainType,
    res_gen: ResGenType | None,
    region: SourceRegionNameType,
    country: TargetCountryNameType,
    transport: TransportType,
    ship_own_fuel: bool,
    user_data: pd.DataFrame | None = None,
    tool_version_color: ToolVersionColorType = "green",
    _output_unit: OutputUnitType = "USD/MWh",
    _optimize_flh: bool = True,
    _use_user_data_for_optimize_flh: bool = False,
) -> ChainProcess:

    chain_color: ToolVersionColorType = (
        "green" if df_chain.at[chain, "is_green"] else "blue"
    )
    assert chain_color == tool_version_color

    secondary_process_codes: set[ProcessCodeType] = set()
    if secproc_co2:
        secondary_process_codes.add(
            df_process_by_name.at[secproc_co2, "process_code"]  # type: ignore
        )
    if secproc_water:
        secondary_process_codes.add(
            df_process_by_name.at[secproc_water, "process_code"]  # type: ignore
        )
    first_process_code: ProcessCodeType
    if chain_color == "blue":
        first_process_code = "NG-PROD#B"
        secondary_process_codes = secondary_process_codes | {
            "HEATPUMP#B",
            "CCGT-CC#B",
            "CO2-T+S#B",
        }  # type: ignore
    else:
        assert res_gen
        first_process_code = df_process_by_name.at[res_gen, "process_code"]  # type: ignore

    chain_process = ChainProcess(
        transport=transport,
        ship_own_fuel=ship_own_fuel,
        chain=chain,
        first_process_code=first_process_code,
        secondary_process_codes=secondary_process_codes,
    )

    data_handler = DataHandler(
        scenario=scenario, data_dir=DEFAULT_DATA_DIR, user_data=user_data
    )

    parameter_getters = create_parameter_getters(
        data_handler=data_handler, use_user_data=bool(user_data)
    )

    chain_process.initialize_parameters(
        parameter_getters,
        source_region_code=df_region_by_name.at[region, "region_code"],  # type: ignore
        target_country_code=df_region_by_name.at[country, "region_code"],  # type: ignore
    )

    chain_process.calculate(1)

    return chain_process


def main():
    scenario: ScenarioType = "2040 (medium)"
    permutations = create_permutation_names(create_permutations(scenario=scenario))

    for i, (name, settings) in enumerate(permutations.items()):
        # if name != "Methane_(SOEC)_Pipeline":
        if name != "STL-S__NG-DRI-C_EAF__prod_in_demand_Ship":
            continue

        logger.info(f"{i + 1}/{len(permutations)}: {settings}")

        chain_process = create_chain_process_api_wrapper(**settings.__dict__)

        plot(chain_process, name=name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--loglevel",
        "-l",
        choices=["debug", "info", "warning", "error"],
        default="warning",
    )
    # parse args
    kwargs = vars(ap.parse_args())
    # logging
    coloredlogs.install(
        logger=logger,
        level=getattr(logging, kwargs.pop("loglevel").upper()),
        fmt="[%(asctime)s %(levelname)7s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        field_styles={
            "asctime": {"color": "white"},
            "levelname": {"color": "white"},
        },
        level_styles={
            "debug": {"color": "blue"},
            "info": {"color": "green"},
            "warning": {"color": "yellow"},
            "error": {"color": "red"},
        },
    )

    main(**kwargs)


def _temp_data_adapter(chain_process: ChainProcess) -> dict:

    proc_export: AggregateProcess = chain_process.get_subprocesses_by_class(
        ChainExportProcess
    )[
        0
    ]  # type: ignore
    proc_transport: AggregateProcess = chain_process.get_subprocesses_by_class(
        ChainTransportProcess
    )[0]
    try:
        proc_import: AggregateProcess = chain_process.get_subprocesses_by_class(
            ChainImportProcess
        )[0]
    except Exception:
        proc_import = None

    context = chain_process._data_lookup_defaults

    parameter = proc_export.get_parameters_incl_parents()
    parameter["SPECCOST"] = {}
    # also aggregate all specccost
    for p in proc_export.get_subprocesses_by_class(MarketProcess):
        print(p)
        parameter["SPECCOST"] = (
            {
                "CO2-G": 0.044519,
                # "DIESEL-L": 0.042857,
                "EL": 0.08078,
                "H2O-L": 0.001374,
                "HEAT": 0.0577,
                "IOP-S": 0.267076,
                "N2-G": 0.01154,
            }
            | parameter["SPECCOST"]
            | p._parameters.get("SPECCOST", {})
        )

    if proc_import:
        parameter_i = proc_import.get_parameters_incl_parents()
        parameter_i["SPECCOST"] = {}
        # also aggregate all specccost
        for p in proc_import.get_subprocesses_by_class(MarketProcess):
            print(p)
            parameter_i["SPECCOST"] = (
                {
                    "CO2-G": 0.044519,
                    "DIESEL-L": 0.042857,
                    # "EL": 0.1,
                    "H2O-L": 0.001374,
                    "HEAT": 0.04,
                    # "IOP-S": 0.267076,
                    "N2-G": 0.01154,
                    # "NG-G": 0.030565,
                }
                | parameter_i["SPECCOST"]
                | p._parameters.get("SPECCOST", {})
            )
    else:
        parameter_i = {}

    main_import_process_chain = []
    transport_process_chain = []
    main_export_process_chain = []

    # NOTE: in old version, pre/post is part of transport

    export_wo_pre_transp = [
        x for x in proc_export.full_main_chain if not x.is_transport
    ]
    transport_w_pre_post = (
        [x for x in proc_export.full_main_chain if x.is_transport]
        + proc_transport.full_main_chain
        + [x for x in proc_import.full_main_chain if x.is_transport]
    )
    import_wo_post_transp = [
        x for x in proc_import.full_main_chain if not x.is_transport
    ]

    def get_proc_data(p: Process) -> dict:
        data = p._parameters | {"process_code": p.process_code, "step": p.process_step}
        return data

    return {
        "context": context,
        "parameter": parameter,
        "parameter_i": parameter_i,
        "main_export_process_chain": [get_proc_data(p) for p in export_wo_pre_transp],
        # "transport_process_chain": [get_proc_data(p) for p in transport_w_pre_post],
        # "main_import_process_chain": [get_proc_data(p) for p in import_wo_post_transp],
    }
