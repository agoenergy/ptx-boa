# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""
import logging

import pandas as pd


def get_from_dict(dct, key, msg=None):
    """Raise detailed KeyError."""
    try:
        return dct[key]
    except KeyError:
        msg = f"{msg}: " if msg else ""
        raise KeyError(f"{msg}'{key}' not in {list(dct)}.")


def get_from_df(df, key, msg=None):
    """Raise detailed KeyError."""
    try:
        return df.loc[key]
    except KeyError:
        msg = f"{msg}: " if msg else ""
        raise KeyError(f"{msg}'{key}' not in {list(df.index)}.")


# TODO: too complicated: just create a mapping of codes to classes
class ProcessMeta(type):
    """Register all subclasses by process codes using metaclass."""

    _classes = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        assert name not in cls._classes  # no duplicates
        cls._classes[name] = cls

    @classmethod
    def create_process(cls, class_name: str, **kwargs):
        """Get process instance by code.

        Parameters
        ----------
        code: str

        Returns
        -------
        Process class instance
        """
        process_class = get_from_dict(cls._classes, class_name, "process class_name")
        return process_class(**kwargs)


class GenericProcess(metaclass=ProcessMeta):
    flows = ()  # Tuple[str]: flows required by a process of this class
    parameters = ()  # Tuple[str]: parameters required by this process

    def __init__(
        self,
        process_code,
        data_handler,
        result_process_type,
        flow_code_to_result_process_type=None,
        secondary_processes=None,
        source_region_code="",
        target_country_code="",
        process_code_res="",
        process_code_ely="",
        process_code_deriv="",
        flow_code="",
        use_ship=True,
        ship_own_fuel=None,
        # main_flow_out=None, # TODO?
    ):
        secondary_processes = secondary_processes or {}
        flow_code_to_result_process_type = flow_code_to_result_process_type or {}

        self.data_handler = data_handler
        self.result_process_type = result_process_type
        self.process_code = process_code
        self.flow_procs = {}
        self.param_values = {}

        # TODO: not nice
        if isinstance(self, ProcessTransport):
            self.use_ship = use_ship
            self.ship_own_fuel = ship_own_fuel

        for parameter_code in self.parameters:
            value = self._get_parameter_value(
                parameter_code=parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                source_region_code=source_region_code,
                target_country_code=target_country_code,
                process_code_res=process_code_res,
                process_code_ely=process_code_ely,
                process_code_deriv=process_code_deriv,
            )
            self.param_values[parameter_code] = value
            logging.debug("%s.%s = %s", self, parameter_code, value)

        process_dim = self.data_handler.get_dimension("process")  # TODO: better lookup

        for flow_code in self.flows:
            if flow_code in secondary_processes:
                flow_proc_code = secondary_processes[flow_code]
                # TODO: better lookup
                proc_attrs = get_from_df(process_dim, flow_proc_code, "process")
                self.flow_procs[flow_code] = ProcessSecondary.create_process(
                    class_name=proc_attrs["class_name"],
                    result_process_type=proc_attrs["result_process_type"],
                    process_code=flow_proc_code,
                    flow_code=flow_code,
                    data_handler=data_handler,
                    source_region_code=source_region_code,
                )
                # TODO: check that flow matches
                # assert self.flow_procs[flow].main_flow_out == flow # noqa
            else:
                # result_process_type can also come from flow,
                # otherwise: parent process result_process_type

                result_process_type = (
                    flow_code_to_result_process_type.get(flow_code)
                    or self.result_process_type
                )

                self.flow_procs[flow_code] = ProcessMarketFlow(
                    process_code=process_code,
                    result_process_type=result_process_type,
                    flow_code=flow_code,
                    data_handler=data_handler,
                    source_region_code=source_region_code,
                )

    def _get_parameter_value(self, **kwargs):
        """Temporarily ignore data errors."""
        try:
            return self.data_handler.get_parameter_value(**kwargs)
        except ValueError:
            # TODO: mayve add in data?: some CONV are missing == 0
            # or maybe: parameter defaults?
            return 0

    def _calculate_output_value(self, input_value) -> float:
        raise NotImplementedError()

    def _calculate_results(self, output_value) -> list:
        return []

    def _create_result_row(self, cost_type, value) -> list:
        res = (self.result_process_type, self.__class__.__name__, cost_type, value)
        return res

    def __call__(self, input_value):
        """Calculate results.

        Parameter
        ---------
        input_value: float

        Returns
        -------
        : tuple[float, tuple]
            (output_value, list of result tuples)


        """
        output_value = self._calculate_output_value(input_value)

        # adding tuple (result_process_type, process_subtype, cost_type, values)
        results = self._calculate_results(output_value)

        for fp in self.flow_procs.values():
            _, results_from_sec_processes = fp(output_value)
            results += results_from_sec_processes

        return output_value, results

    def __str__(self):
        return f"{self.__class__.__name__}({self.process_code})"


def pmt(r, n, v):
    if r == 0:
        return v / n
    else:
        return v * r / (1 - (1 / (1 + r) ** n))


class ProcessMain(GenericProcess):
    """Process in main chain."""

    parameters = ("EFF", "WACC", "FLH", "LIFETIME", "CAPEX", "OPEX-F", "OPEX-O")

    def _calculate_output_value(self, input_value) -> float:
        return input_value * self.param_values["EFF"]

    def _calculate_results(self, main_output_value) -> list:
        results = super()._calculate_results(main_output_value)

        # installed capacity
        capacity = main_output_value / self.param_values["FLH"]
        capex = capacity * self.param_values["CAPEX"]
        capex_ann = pmt(self.param_values["WACC"], self.param_values["LIFETIME"], capex)
        opex = (
            self.param_values["OPEX-F"] * capacity
            + self.param_values["OPEX-O"] * main_output_value
        )

        results.append(self._create_result_row("CAPEX", capex_ann))
        results.append(self._create_result_row("OPEX", opex))
        return results


class ProcessPassthrough(GenericProcess):
    """Process that does not do anything."""

    def _calculate_output_value(self, input_value) -> float:
        return input_value


class ProcessTransportPrePost(ProcessPassthrough):
    """Process that does not do anything."""


class ProcessTransport(GenericProcess):
    def _calculate_output_value(self, input_value) -> float:
        dist = self._get_distance()
        eff = 1 - self.param_values["LOSS-T"] * dist
        return input_value * eff

    def _get_distance(self):
        raise NotImplementedError()


class ProcessTransportPipeline(ProcessTransport):
    parameters = ("LOSS-T", "DST-S-DP", "SEASHARE", "CAP-T")

    def _get_distance(self):
        # TODO: user can override to use ship insetad
        if self.use_ship:
            return 0

        # if existing pipeline: only retrofit (if not, only new)
        if bool(self.param_values["CAP-T"]) != self._is_retrofit():
            return 0

        dist = self.param_values["DST-S-DP"]
        share = self.param_values["SEASHARE"]
        if self._is_land():
            share = 1 - share

        dist = share * dist
        return dist

    def _is_land(self):
        code = self.process_code.split("-")[-1]
        assert code in {"S", "L", "SR", "LR"}, self.process_code
        return code in {"L", "LR"}

    def _is_retrofit(self):
        code = self.process_code.split("-")[-1]
        assert code in {"S", "L", "SR", "LR"}, self.process_code
        return code in {"SR", "LR"}


class ProcessTransportShip(ProcessTransport):
    parameters = (
        "DST-S-D",
        "DST-S-DP",
        "LOSS-T",
    )
    flows = ("BFUEL-L",)

    def _get_distance(self):
        # if possible pipeline: use that instead of ship
        if self.param_values["DST-S-DP"] and not self.use_ship:
            return 0

        if self.ship_own_fuel != self._use_own_fuel():
            return 0

        dist = self.param_values["DST-S-D"]
        return dist

    def _use_own_fuel(self):
        code = self.process_code.split("-")[-1]
        assert code in {"S", "SB"}, self.process_code
        return code in {"SB"}

        return self.process_code.split("-")[-1] == "OWN"


class ProcessSecondary(GenericProcess):
    """Secondary process to generate required flows."""

    parameters = ("CONV",)
    flows = ("HEAT", "EL")

    def _calculate_output_value(self, main_output_value) -> float:
        # NOTE: when calledwe pass the main_output_value, (not input_value)
        return main_output_value * self.param_values["CONV"]


class ProcessMarketFlow(ProcessSecondary):
    """Dummy process to buy required flows at market cost."""

    flows = ()  # Important: no further flows

    parameters = (
        "CONV",
        "SPECCOST",
    )

    def _calculate_results(self, output_value) -> list:
        # no need for super()
        results = [
            self._create_result_row(
                "FLOW", output_value * self.param_values["SPECCOST"]
            )
        ]
        return results


class ProcessRenewableGeneration(ProcessMain):
    def _calculate_output_value(self, input_value) -> float:
        return input_value


class ProcessElectrolysis(ProcessMain):
    flows = ("H2O-L", "EL")


class ProcessDerivate(ProcessMain):
    flows = ("H2O-L", "CO2-G", "EL", "HEAT", "N2-G")


class PtxCalc:
    def __init__(
        self,
        data_handler,
    ):
        self.data_handler = data_handler

    def calculate(
        self,
        secproc_co2_code,
        secproc_water_code,
        chain,
        process_code_res,
        region_code,
        country_code,
        use_ship,
        ship_own_fuel,
        output_unit,
    ):
        """Calculate results."""
        # get process codes for selected chain
        chain_dim = self.data_handler.get_dimension("chain")
        process_dim = self.data_handler.get_dimension("process")
        chain_attrs = get_from_df(chain_dim, chain, "chains")
        process_codes = [process_code_res]
        process_code_ely = chain_attrs["ELY"]
        process_code_deriv = chain_attrs["DERIV"]

        # some flows are grouped into their own output category (but not all)
        # so we load the mapping from the data
        flow_dim = self.data_handler.get_dimension("flow")
        flow_code_to_result_process_type = dict(
            flow_dim.loc[flow_dim["result_process_type"] != "", "result_process_type"]
        )

        for c in [
            "ELY",
            "DERIV",
            "PRE_SHP",
            "PRE_PPL",
            "POST_SHP",
            "POST_PPL",
            "SHP",
            "SHP-OWN",
            "PPLS",
            "PPL",
            "PPLX",
            "PPLR",
        ]:
            process_code = chain_attrs[c]
            if not process_code:
                continue
            process_codes.append(process_code)
        secondary_processes = {}
        if secproc_water_code:
            secondary_processes["H2O-L"] = secproc_water_code
        if secproc_co2_code:
            secondary_processes["CO2-G"] = secproc_co2_code

        processes = []
        for process_code in process_codes:
            proc_attrs = get_from_df(
                process_dim, process_code, "process"
            )  # TODO: better lookup
            process = GenericProcess.create_process(
                class_name=proc_attrs["class_name"],
                result_process_type=proc_attrs["result_process_type"],
                flow_code_to_result_process_type=flow_code_to_result_process_type,
                process_code=process_code,
                data_handler=self.data_handler,
                secondary_processes=secondary_processes,
                source_region_code=region_code,
                target_country_code=country_code,
                use_ship=use_ship,
                ship_own_fuel=ship_own_fuel,
                process_code_ely=process_code_ely,
                process_code_deriv=process_code_deriv,
                process_code_res=process_code_res,
            )
            processes.append(process)

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        value = 1  # start with normalized value of 1

        results = []
        for process in processes:
            value, results_from_process = process(value)
            results += results_from_process

        # TODO: fist one should be renamed to result_process_type
        dim_columns = ["process_type", "process_subtype", "cost_type"]
        # convert results in Dataframe (maybe aggregate some?)
        results = pd.DataFrame(
            results,
            columns=dim_columns + ["values"],
        )

        # TODO: maybe not required: aggregate over all key columns
        # in case some processes create data with the same categories

        # remove negatives
        results = results.loc[results["values"] > 0]

        results = results.groupby(dim_columns).sum().reset_index()

        # TODO: apply output_unit conversion on
        # simple sacling (TODO: EL, UNIT)
        results["values"] = results["values"] / value * 1000  # kwh => MWh

        return results
