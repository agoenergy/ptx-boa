# -*- coding: utf-8 -*-
"""Data interface for optimized data of FLH."""

import hashlib
import json
import logging
import os
import pickle  # noqa S403
import time

import streamlit as st

from flh_opt._types import OptInputDataType, OptOutputDataType
from flh_opt.api_opt import optimize
from ptxboa.static._types import CalculateDataType

DEFAULT_CACHE_DIR = os.path.dirname(__file__) + "/data/cache"
IS_TEST = "PYTEST_CURRENT_TEST" in os.environ
logger = logging.getLogger()


def wait_for_file_to_disappear(
    filepath: str, timeout_s: float = 10, poll_interv_s: float = 0.2
):
    t_waited = 0
    while True:
        if not os.path.exists(filepath):
            return True
        time.sleep(poll_interv_s)
        t_waited += poll_interv_s
        if timeout_s > 0 and t_waited >= timeout_s:
            logger.warning("Timeout")
            return False


def get_data_hash_md5(key: object) -> str:
    """Create md5 hash of data.

    Parameters
    ----------
    key : object
        any json serializable object

    Returns
    -------
    str
        md5 hash of a standardized byte representation of the input data
    """
    # serialize to str, make sure to sort keys
    sdata = json.dumps(key, sort_keys=True, ensure_ascii=False, indent=0)
    # to bytes (only bytes can be hashed)
    bdata = sdata.encode()
    # create hash
    hash_md5 = hashlib.md5(bdata).hexdigest()  # noqa: S324 (md5 is fine)
    return hash_md5


class PtxOpt:

    def __init__(self, cache_dir: str = DEFAULT_CACHE_DIR):
        self.cache_dir = cache_dir
        self.profiles_path = "flh_opt/renewable_profiles"

    def _save(self, filepath: str, data: object, raise_on_overwrite=False) -> None:
        if raise_on_overwrite and os.path.exists(filepath):
            raise FileExistsError("file already exists: %s", filepath)
        with open(filepath, "wb") as file:
            pickle.dump(data, file)

    def _load(self, filepath: str) -> object:
        with open(filepath, "rb") as file:
            data = pickle.load(file)  # noqa S301
        return data

    def _get_cache_filepath(self, name, suffix=".pickle"):
        # group twice by first two chars (256 combinations)
        dirpath = self.cache_dir + f"/{name[0:2]}/{name[2:4]}"
        os.makedirs(dirpath, exist_ok=True)
        filepath = f"{dirpath}/{name}{suffix}"
        return filepath

    def _get_data(self, input_data: dict):
        """Calculate or load hashed optimized data.

        Parameters
        ----------
        input_data : dict
            hashable input data

        Returns
        -------
        dict
            result data
        """
        # try to load
        key_hash_md5 = get_data_hash_md5(input_data)
        filepath = self._get_cache_filepath(key_hash_md5)
        filepath_lock = filepath + ".lock"

        # someone else already started this, so we wait for it to finish (with timeout)
        logger.info(f"START get_data: {key_hash_md5}")

        wait_for_file_to_disappear(filepath_lock)

        if not os.path.exists(filepath):
            # create lockfile
            logger.info(f"LOCK  get_data: {key_hash_md5}")
            open(filepath_lock, "wb").close()
            logger.info(f"CALC  get_data: {key_hash_md5}")
            data = self._calculate_data(input_data)
            self._save(filepath, data)
            # remove lock
            os.remove(filepath_lock)
            logger.info(f"SAVE  get_data: {key_hash_md5}")

        logger.info(f"STOP get_data: {key_hash_md5}")
        return self._load(filepath)

    def _calculate_data(self, input_data: dict):
        # dummy: run optimization

        wait_seconds = 0 if IS_TEST else 3
        time.sleep(wait_seconds)

        return input_data

    @staticmethod
    def _prepare_data(input_data: CalculateDataType) -> OptInputDataType:

        src_reg = input_data["context"]["source_region_code"]

        result = {
            "SOURCE_REGION_CODE": src_reg,
            "RES": [],
            "ELY": None,
            "DERIV": None,
            "SPECCOST": {"H2O-L": input_data["parameter"]["SPECCOST"]["H2O-L"]},
        }

        for step in input_data["main_process_chain"]:
            if step["step"] == "RES":
                if step["process_code"] == "RES-HYBR":
                    for pc in ["PV-FIX", "WIND-ON"]:
                        proc_data = input_data["flh_opt_process"][pc]
                        result["RES"].append(
                            {
                                "CAPEX_A": proc_data["CAPEX"],
                                "OPEX_F": proc_data["OPEX-F"],
                                "OPEX_O": proc_data["OPEX-O"],
                                "PROCESS_CODE": pc,
                            }
                        )
                else:
                    result["RES"].append(
                        {
                            "CAPEX_A": step["CAPEX"],  # TODO why CAPEX_A?
                            "OPEX_F": step["OPEX-F"],
                            "OPEX_O": step["OPEX-O"],
                            "PROCESS_CODE": step["process_code"],
                        }
                    )

            elif step["step"] == "ELY":
                result["ELY"] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": step["CAPEX"],
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                    "CONV": step["CONV"],
                }
            elif step["step"] == "DERIV":
                result["DERIV"] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": step["CAPEX"],
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                    "PROCESS_CODE": step["process_code"],
                    "CONV": step["CONV"],
                }
            elif step["step"] in ("EL_STR", "H2_STR"):
                result[step["step"]] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": step["CAPEX"],
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                }

        return result

    @staticmethod
    def _merge_data(input_data: CalculateDataType, opt_output_data: OptOutputDataType):
        flh_opt_process = input_data["flh_opt_process"]

        # only overwrite  flh if optimization was successful:
        if opt_output_data["model_status"][1] == "optimal":
            for step in input_data["main_process_chain"]:
                if step["step"] == "RES":
                    output_res = opt_output_data["RES"]
                    if step["process_code"] == "RES-HYBR":
                        assert len(output_res) == 2
                        step["FLH"] = sum(
                            x["FLH"] * x["SHARE_FACTOR"] for x in output_res
                        )
                        # Merge technologies with SHARE_FACTOR for each PROCESS_CODE
                        for k in ["LIFETIME", "CAPEX", "OPEX-F", "OPEX-O"]:
                            step[k] = sum(
                                flh_opt_process[x["PROCESS_CODE"]][k]
                                * x["SHARE_FACTOR"]
                                for x in output_res
                            )
                    else:
                        assert len(output_res) == 1
                        flh = output_res[0]["FLH"]
                        step["FLH"] = flh

                    step["FLH"] = step["FLH"] * 8760  # NOTE: output is fraction

                elif step["step"] == "ELY":
                    step["FLH"] = opt_output_data["ELY"]["FLH"] * 8760
                elif step["step"] == "DERIV":
                    step["FLH"] = opt_output_data["DERIV"]["FLH"] * 8760
        else:
            logging.warning("Optimization not successful.")
            logging.warning(f"Solver status:{opt_output_data['model_status'][0]}")
            logging.warning(f"Model status:{opt_output_data['model_status'][1]}")

            # TODO: Storage: "CAP_F"

    def get_data(self, data: CalculateDataType) -> CalculateDataType:
        """Get calculation data including optimized FLH.

        Parameters
        ----------
        data : CalculateDataType
            input data

        Returns
        -------
        CalculateDataType
            same data, but replaced FLH (and some other data points)
            with results from optimization
        """
        opt_input_data = self._prepare_data(data)
        opt_output_data, _network = optimize(
            opt_input_data, profiles_path=self.profiles_path
        )
        # todo: for debugging, temporarily pass network to session state:
        st.session_state["network"] = _network
        st.session_state["model_status"] = opt_output_data["model_status"][1]

        self._merge_data(data, opt_output_data)
        return data
