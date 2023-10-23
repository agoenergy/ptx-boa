# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import pandas as pd


class Chain:
    def __init__(self, get_parameter_value, process_codes, subprocesses):
        self.processes = [
            GenericProcess.create_process(
                code,
                get_parameter_value=get_parameter_value,
                subprocesses=subprocesses,
            )
            for code in process_codes
        ]
        # TODO:optionally: check that chain is valid (flows)
        # assert self.processes[0].main_flow_in is None # noqa
        # for i in range(1, len(self.processes)): # noqa
        #    assert self.processes[i].main_flow_in == self.processes[i + 1].main_flow_out # noqa

    def __call__(self, input_value=1) -> pd.DataFrame:
        """Calculate chain.

        Parameters
        ----------
        input_value: float
            usually we start the (normalized) chain with 1.0 and rescale at the end

        """
        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process
        value = input_value
        results = []
        for p in self.processes:
            value, results_ = p(value)
            results += results_

        # convert results in Dataframe (maybe aggregate some?)
        results = pd.DataFrame(
            results, columns=["process_type", "process_subtype", "cost_type", "values"]
        )

        # aggregate over all key columns
        results = (
            results.groupby(["process_type", "process_subtype", "cost_type"])
            .sum()
            .reset_index()
        )
        # TODO: rescale results correctly (using `value`)
        return results

    def __str__(self):
        return "->".join(str(p) for p in self.processes)


class ProcessMeta(type):
    """Register all subclasses by process codes using metaclass."""

    _classes = {}

    def __init__(cls, name, bases, attrs):
        super().__init__(name, bases, attrs)
        for code in cls.codes:
            assert code not in cls._classes  # no duplicates
            # print(f"register {code} -> {cls.__name__}") # noqa
            cls._classes[code] = cls

    @classmethod
    def create_process(cls, code: str, *args, **kwargs):
        """Get process instance by code.

        Parameters
        ----------
        code: str

        Returns
        -------
        Process class instance
        """
        class_ = cls._classes[code]
        return class_(code, *args, **kwargs)


class GenericProcess(metaclass=ProcessMeta):
    codes = ()
    flows = ()
    parameters = ()
    main_flow_in = None
    main_flow_out = None
    process_type = None
    process_subtype = None

    def __init__(self, code, get_parameter_value, subprocesses):
        self.code = code
        self.flow_procs = {}
        self.param_values = {}

        for p in self.parameters:
            self.param_values[p] = get_parameter_value(
                process_code=self.code, parameter_code=p
            )

        for flow in self.flows:
            if flow in subprocesses:
                self.flow_procs[flow] = ProcessSecondary.create_process(
                    self, subprocesses[flow], get_parameter_value
                )
                # TODO: check that flow matches
                # assert self.flow_procs[flow].main_flow_out == flow # noqa
            else:
                self.flow_procs[flow] = ProcessSecondaryMarket(
                    self, flow, get_parameter_value
                )

    def _calculate_output_value(self, input_value) -> float:
        return input_value

    def _calculate_results(self, output_value) -> list:
        return []

    def __call__(self, input_value):
        """Calculate results.

        Parameter
        ---------
        input_value: float
        """
        output_value = self._calculate_output_value(input_value)

        # adding tuple (process_type, process_subtype, cost_type, values)
        results = self._calculate_results(output_value)

        for fp in self.flow_procs.values():
            _, results_ = fp(output_value)
            results += results_

        return output_value, results

    def __str__(self):
        return self.code


class ProcessMain(GenericProcess):
    """Process in main chain."""

    parameters = ("EFF",)

    def _calculate_results(self, output_value) -> list:
        results = super()._calculate_results(output_value)
        # DUMMY
        results += [
            (self.process_type, self.process_subtype, "CAPEX", output_value * 0.1),
            (self.process_type, self.process_subtype, "OPEX", output_value * 0.1),
        ]
        return results


class ProcessSecondary(GenericProcess):
    """Secondary process to generate required flows."""

    parameters = ("CONV",)

    def __init__(self, parent_process, code, get_parameter_value):
        super().__init__(code, get_parameter_value, subprocesse={})
        self.parent_process = parent_process


class ProcessSecondaryMarket(ProcessSecondary):
    """Dummy process to buy required flows at market cost."""

    def __init__(self, parent_process, flow: str, get_parameter_value):
        self.code = ""
        self.process_type = "TODO"
        self.process_subtype = "TODO"
        self.flow_procs = {}
        self.parent_process = parent_process
        self.main_flow_out = flow
        self.param_values = {
            "SPECCOST": get_parameter_value(flow=flow, parameter="SPECCOST")
        }

    def _calculate_results(self, output_value) -> list:
        results = super()._calculate_results(output_value)
        results += [
            (
                self.process_type,
                self.process_subtype,
                "FLOW",
                output_value * self.param_values["SPECCOST"],
            ),
        ]
        return results


class ProcessReGen(ProcessMain):
    codes = ("PV-FIX", "PV-TRK", "RES-HYBR", "WIND-OFF", "WIND-ON")
    main_flow_out = "EL"
    process_type = "Electricity generation"
    process_subtype = "res"

    def _calculate_output_value(self, input_value) -> float:
        return input_value * self.param_values["EFF"]


class ProcessELEC(ProcessMain):
    codes = ("AEL-EL", "PEM-EL", "SOEC-EL")
    main_flow_in = "EL"
    main_flow_out = "H2-G"
    process_type = "Electrolysis"
    process_subtype = "ely"
    flows = ("CO2-G",)


if __name__ == "__main__":
    # Dummy implementation

    def get_parameter_value(*args, **kwargs):
        """Get the parameter value."""
        return 1

    # setup chain
    chain = Chain(get_parameter_value, ["WIND-ON", "AEL-EL"], {"H2O-L": "DESAL"})

    print(chain)

    # calculate chain
    print(chain())
