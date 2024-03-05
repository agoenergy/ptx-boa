# -*- coding: utf-8 -*-
"""Data interface for optimized data of FLH."""

import hashlib
import json
import logging
import os
import pickle  # noqa S403
import time

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

    def get_data(self, input_data: dict):
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
