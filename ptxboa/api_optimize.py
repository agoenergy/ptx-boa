# -*- coding: utf-8 -*-
"""Data interface for optimized data of FLH."""

import datetime
import hashlib
import json
import os
import pickle  # noqa S403
import time
from pathlib import Path

import streamlit as st
from pypsa import Network

from flh_opt._types import OptInputDataType, OptOutputDataType
from flh_opt.api_opt import optimize
from ptxboa import logger
from ptxboa.static._types import CalculateDataType
from ptxboa.utils import annuity


# TODO unused
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


class TempFile:
    def __init__(self, filepath, raise_on_overwrite=False):
        self.filepath = filepath
        self.filepath_tmp = str(self.filepath) + ".tmp"
        self.raise_on_overwrite = raise_on_overwrite

    def __enter__(self):
        # check existing files
        for path in [self.filepath, self.filepath_tmp]:
            if os.path.exists(path):
                message = f"file should not exist - overwriting: {path}"
                if self.raise_on_overwrite:
                    raise FileExistsError(message)
                logger.warning(message)
                os.remove(path)
        return self.filepath_tmp

    def __exit__(self, exc_type, exc_val, exc_tb):
        # move to filepath_tmp => filepath
        if not os.path.exists(self.filepath_tmp):
            # file should have been written
            logger.warning(f"file does not exist: {self.filepath_tmp}")
            return
        if os.path.exists(self.filepath):
            # file was created in the meantime?
            logger.warning(f"file should not exist - overwriting: {self.filepath}")
            os.remove(self.filepath)
        if exc_type:
            # there was an error: remove temporary file
            os.remove(self.filepath_tmp)
            logger.warning(exc_val)  # or raise Error
        else:
            # move file to target
            os.rename(self.filepath_tmp, self.filepath)
            logger.info(f"saved file {self.filepath}")


class PtxOpt:

    def __init__(self, profiles_path: Path, cache_dir: Path):
        self.cache_dir = cache_dir
        self.profiles_path = profiles_path

    def _save(
        self,
        filepath: str,
        data: object,
        network: Network,
        metadata: dict,
        raise_on_overwrite=False,
    ) -> None:
        with TempFile(filepath, raise_on_overwrite=raise_on_overwrite) as filepath_tmp:
            with open(filepath_tmp, "wb") as file:
                pickle.dump(data, file)

        # also save network
        filepath_nw = str(filepath) + ".network.nc"
        with TempFile(filepath_nw, raise_on_overwrite=False) as filepath_tmp:
            network.export_to_netcdf(filepath_tmp)

        # also save metadata
        filepath_metadata = str(filepath) + ".metadata.json"
        with open(filepath_metadata, "w", encoding="utf-8") as file:
            json.dump(metadata, file, indent=2, ensure_ascii=False)

    def _load(self, filepath: str) -> object:
        with open(filepath, "rb") as file:
            data = pickle.load(file)  # noqa S301
        return data

    def _get_cache_filepath(self, hashsum: str, suffix=".pickle"):
        # group twice by first two chars (256 combinations)
        dirpath = self.cache_dir / hashsum[0:2] / hashsum[2:4]
        os.makedirs(dirpath, exist_ok=True)
        filepath = dirpath / f"{hashsum}{suffix}"
        return filepath

    @staticmethod
    def _prepare_data(input_data: CalculateDataType) -> OptInputDataType:

        src_reg = input_data["context"]["source_region_code"]

        result = {
            "SOURCE_REGION_CODE": src_reg,
            "RES": [],
            "ELY": None,
            "DERIV": None,
            "SPECCOST": {
                "H2O-L": input_data["parameter"]["SPECCOST"]["H2O-L"],
                "CO2-G": input_data["parameter"]["SPECCOST"]["CO2-G"],
                "N2-G": input_data["parameter"]["SPECCOST"]["N2-G"],
                "HEAT": input_data["parameter"]["SPECCOST"]["HEAT"],
            },
        }

        for step in input_data["main_process_chain"]:
            if step["step"] == "RES":
                if step["process_code"] == "RES-HYBR":
                    for pc in ["PV-FIX", "WIND-ON"]:
                        proc_data = input_data["flh_opt_process"][pc]
                        result["RES"].append(
                            {
                                "CAPEX_A": annuity(
                                    periods=proc_data["LIFETIME"],
                                    rate=input_data["parameter"]["WACC"],
                                    value=proc_data["CAPEX"],
                                ),
                                "OPEX_F": proc_data["OPEX-F"],
                                "OPEX_O": proc_data["OPEX-O"],
                                "PROCESS_CODE": pc,
                            }
                        )
                else:
                    result["RES"].append(
                        {
                            "CAPEX_A": annuity(
                                periods=step["LIFETIME"],
                                rate=input_data["parameter"]["WACC"],
                                value=step["CAPEX"],
                            ),
                            "OPEX_F": step["OPEX-F"],
                            "OPEX_O": step["OPEX-O"],
                            "PROCESS_CODE": step["process_code"],
                        }
                    )

            elif step["step"] == "ELY":
                result["ELY"] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": annuity(
                        periods=step["LIFETIME"],
                        rate=input_data["parameter"]["WACC"],
                        value=step["CAPEX"],
                    ),
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                    "CONV": step["CONV"],
                }
            elif step["step"] == "DERIV":
                result["DERIV"] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": annuity(
                        periods=step["LIFETIME"],
                        rate=input_data["parameter"]["WACC"],
                        value=step["CAPEX"],
                    ),
                    "OPEX_F": step["OPEX-F"],
                    "OPEX_O": step["OPEX-O"],
                    "PROCESS_CODE": step["process_code"],
                    "CONV": step["CONV"],
                }
            elif step["step"] in ("EL_STR", "H2_STR"):
                result[step["step"]] = {
                    "EFF": step["EFF"],
                    "CAPEX_A": annuity(
                        periods=step["LIFETIME"],
                        rate=input_data["parameter"]["WACC"],
                        value=step["CAPEX"],
                    ),
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
            logger.warning("Optimization not successful.")
            logger.warning(f"Solver status:{opt_output_data['model_status'][0]}")
            logger.warning(f"Model status:{opt_output_data['model_status'][1]}")

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

        if self.cache_dir:
            hashsum = get_data_hash_md5(opt_input_data)
            filepath = self._get_cache_filepath(hashsum)

            if os.path.exists(filepath):
                logger.info(f"load opt flh data from cache: {hashsum}")
                data = self._load(filepath)
                return data

        opt_output_data, network = optimize(
            opt_input_data, profiles_path=self.profiles_path
        )
        # todo: for debugging, temporarily pass network to session state:
        st.session_state["network"] = network
        st.session_state["model_status"] = opt_output_data["model_status"][1]

        self._merge_data(data, opt_output_data)

        if self.cache_dir:
            metadata = {
                "opt_input_data": opt_input_data,
                "model_status": opt_output_data["model_status"],
                "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._save(filepath, data, network, metadata)
            data = self._load(filepath)

        return data
