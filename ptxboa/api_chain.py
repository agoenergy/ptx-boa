# -*- coding: utf-8 -*-
"""Classes for main process chain calculation."""

import pandas as pd


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
    def get_process_class_by_code(cls, code: str):
        """Get process class by code.

        Parameters
        ----------
        code: str

        Returns
        -------
        Process class
        """
        return cls._classes[code]

    @classmethod
    def get_process_by_code(cls, code: str, *args, **kwargs):
        """Get process instance by code.

        Parameters
        ----------
        code: str

        Returns
        -------
        Process class instance
        """
        class_ = cls.get_process_class_by_code(code)
        return class_(code, *args, **kwargs)


class Process(metaclass=ProcessMeta):
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
            self.param_values[p] = get_parameter_value(self.code, p)

        for flow in self.flows:
            if flow in subprocesses:
                self.flow_procs[flow] = Process.get_process_by_code(
                    subprocesses[flow], get_parameter_value, None
                )
                # TODO: check that flow matches
                # assert self.flow_procs[flow].main_flow_out == flow # noqa
            else:
                self.flow_procs[flow] = FlowMarketProcess(flow)

    def _calculate_output_value(self, input_value) -> float:
        return input_value * self.param_values["EFF"]

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


class FlowMarketProcess:
    """Dummy process to buy required flow at market cost."""

    def __init__(self, flow, get_parameter_value):
        self.main_flow_out = flow
        self.param_speccost = get_parameter_value()


class ProcessReGen(Process):
    codes = ("PV-FIX", "PV-TRK", "RES-HYBR", "WIND-OFF", "WIND-ON")
    flows = ()
    parameters = ("EFF",)
    main_flow_in = None
    main_flow_out = "EL"
    process_type = "Electricity generation"
    process_subtype = "res"

    def _calculate_results(self, output_value) -> list:
        # DUMMY
        return [
            (self.process_type, self.process_subtype, "CAPEX", output_value * 0.1),
            (self.process_type, self.process_subtype, "OPEX", output_value * 0.1),
        ]


class Chain:
    def __init__(self, get_parameter_value, process_codes, subprocesses):
        self.processes = [
            Process.get_process_by_code(
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


if __name__ == "__main__":
    # Dummy implementation

    def get_parameter_value(*args, **kwargs):
        """Get the parameter value."""
        return 1

    # setup chain
    chain = Chain(get_parameter_value, ["WIND-ON"], {"H2O-L": "DESAL"})

    print(chain)

    # calculate chain
    print(chain())
