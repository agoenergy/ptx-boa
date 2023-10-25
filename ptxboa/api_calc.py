# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import logging

import pandas as pd


def get_from_dict(dct, key, dct_name="data"):
    """Raise detailed KeyError."""
    try:
        return dct[key]
    except KeyError:
        raise KeyError(f"`{key}` not in {dct_name}. Must be one of {list(dct)}")


def get_from_df(df, key, df_name="data"):
    """Raise detailed KeyError."""
    try:
        return df.loc[key]
    except KeyError:
        raise KeyError(f"`{key}` not in {df_name}. Must be one of {list(df.index)}")


# TODO: too complicated: just create a mapping of codes to classes
class ProcessMeta(type):
    """Register all subclasses by process codes using metaclass."""

    _classes = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        assert name not in cls._classes  # no duplicates
        # print(f"register {code} -> {cls.__name__}") # noqa
        cls._classes[name] = cls

    @classmethod
    def create_process(cls, class_name: str, *args, **kwargs):
        """Get process instance by code.

        Parameters
        ----------
        code: str

        Returns
        -------
        Process class instance
        """
        process_class = get_from_dict(cls._classes, class_name, "process classes")
        return process_class(class_name, *args, **kwargs)


class GenericProcess(metaclass=ProcessMeta):
    flows = ()  # Tuple[str]: flows required by a process of this class
    parameters = ()  # Tuple[str]: parameters required by this process
    main_flow_in = None  # str
    main_flow_out = None  # str

    def __init__(
        self,
        process_code,
        data_handler,
        secondary_processes=None,
        region_code="",
        country_code="",
        process_code_res="",
        process_code_ely="",
        process_code_deriv="",
        flow_code="",
    ):
        secondary_processes = secondary_processes or {}
        self.process_code = process_code
        self.flow_procs = {}
        self.param_values = {}

        for parameter_code in self.parameters:
            if parameter_code != "FLH":
                value = self._get_parameter_value(
                    parameter_code=parameter_code,
                    process_code=process_code,
                    flow_code=flow_code,
                    source_region_code=region_code,
                    target_country_code=country_code,
                )
            else:
                value = self._get_parameter_value(
                    parameter_code=parameter_code,
                    process_code=process_code,
                    source_region_code=region_code,
                    process_code_res=process_code_res,
                    process_code_ely=process_code_ely,
                    process_code_deriv=process_code_deriv,
                )
            self.param_values[parameter_code] = value

        for flow_code in self.flows:
            if flow_code in secondary_processes:
                flow_proc_code = secondary_processes[flow_code]
                self.flow_procs[flow_code] = ProcessSecondary.create_process(
                    process_code=flow_proc_code,
                    data_handler=data_handler,
                    source_region_code=region_code,
                )
                # TODO: check that flow matches
                # assert self.flow_procs[flow].main_flow_out == flow # noqa
            else:
                self.flow_procs[flow_code] = ProcessMarketFlow(
                    flow_code=flow_code,
                    data_handler=data_handler,
                    source_region_code=region_code,
                )

    def _get_parameter_value(self, *args, **kwargs):
        """Temporarily ignore data errors."""
        try:
            return self.data_handler.get_parameter_value(*args, **kwargs)
        except ValueError as err:
            logging.error(err)
            return 1.0

    def _calculate_output_value(self, input_value) -> float:
        raise NotImplementedError()

    def _calculate_results(self, output_value) -> list:
        return []

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

        # adding tuple (process_type, process_subtype, cost_type, values)
        results = self._calculate_results(output_value)

        for fp in self.flow_procs.values():
            _, results_from_sec_processes = fp(main_output_value=output_value)
            results += results_from_sec_processes

        return output_value, results

    def __str__(self):
        return self.process_code


class ProcessMain(GenericProcess):
    """Process in main chain."""

    parameters = ("EFF",)

    def _calculate_output_value(self, input_value) -> float:
        return input_value * self.param_values["EFF"]

    def _calculate_results(self, main_output_value) -> list:
        results = super()._calculate_results(main_output_value)
        subprocess_type = self.__class__.__name__
        # DUMMY factors
        results += [
            (self.process_type, subprocess_type, "CAPEX", main_output_value * 0.1),
            (self.process_type, subprocess_type, "OPEX", main_output_value * 0.1),
        ]
        return results


class ProcessPassthrough(GenericProcess):
    """Process that does not do anything."""

    def _calculate_output_value(self, input_value) -> float:
        return input_value


class ProcessSecondary(GenericProcess):
    """Secondary process to generate required flows."""

    parameters = ("CONV",)

    def _calculate_output_value(self, main_output_value) -> float:
        # NOTE: when calledwe pass the main_output_value, (not input_value)
        return main_output_value / self.param_values["CONV"]


class ProcessMarketFlow(ProcessSecondary):
    """Dummy process to buy required flows at market cost."""

    parameters = ("SPECCOST",)

    def __init__(self, parent_process_type, **kwargs):
        super().__init__(**kwargs)
        self.process_type = parent_process_type

    def _calculate_results(self, output_value) -> list:
        results = []  # no need for super
        subprocess_type = self.__class__.__name__
        results += [
            (
                self.process_type,
                subprocess_type,
                "FLOW",
                output_value * self.param_values["SPECCOST"],
            ),
        ]
        return results


class ProcessReGen(ProcessMain):
    main_flow_out = "EL"
    process_type = "Electricity generation"
    parameters = ()

    def _calculate_output_value(self, input_value) -> float:
        return input_value


class ProcessElectrolysis(ProcessMain):
    main_flow_in = "EL"
    main_flow_out = "H2-G"
    process_type = "Electrolysis"
    flows = ("HEAT",)


class ProcessDerivateNH3(ProcessMain):
    main_flow_in = "H2-G"
    main_flow_out = "NH3-L"
    process_type = "Derivate production"
    flows = ("CO2-G", "HEAT")


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
        transport,
        ship_own_fuel,
        output_unit,
    ):
        """Calculate results."""
        # get process codes for selected chain
        chain_dim = self.data_handler.get_dimension("chain")
        chain_attrs = get_from_df(chain_dim, chain, "chains")
        main_flow_out = chain_attrs["FLOW_OUT"]
        can_pipeline = chain_attrs["CAN_PIPELINE"]
        process_codes = [process_code_res]
        process_code_ely = chain_attrs["ELY"]
        process_code_deriv = chain_attrs["DERIV"]

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
            process_codes.append(process_code)
        secondary_processes = {}
        if secproc_water_code:
            secondary_processes["H20-L"] = secproc_water_code
        elif secproc_co2_code:
            secondary_processes["CO2-G"] = secproc_co2_code

        processes = [
            GenericProcess.create_process(
                process_code=process_code,
                data_handler=self.data_handler,
                secondary_processes=secondary_processes,
                region_code=region_code,
                country_code=country_code,
                transport=transport,
                main_flow_out=main_flow_out,
                can_pipeline=can_pipeline,
                ship_own_fuel=ship_own_fuel,
                process_code_ely=process_code_ely,
                process_code_deriv=process_code_deriv,
                process_code_res=process_code_res,
            )
            for process_code in process_codes
        ]
        # TODO:optionally: check that chain is valid (flows)
        # assert self.processes[0].main_flow_in is None # noqa
        # for i in range(1, len(self.processes)): # noqa
        #    assert self.processes[i].main_flow_in == self.processes[i + 1].main_flow_out # noqa

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        value = 1  # start with normalized value of 1

        results = []
        for process in processes:
            value, results_from_process = process(value)
            results += results_from_process

        # convert results in Dataframe (maybe aggregate some?)
        results = pd.DataFrame(
            results, columns=["process_type", "process_subtype", "cost_type", "values"]
        )

        # TODO: maybe not required: aggregate over all key columns
        # in case some processes create data with the same categories
        results = (
            results.groupby(["process_type", "process_subtype", "cost_type"])
            .sum()
            .reset_index()
        )

        # TODO: apply output_unit conversion on

        return results
