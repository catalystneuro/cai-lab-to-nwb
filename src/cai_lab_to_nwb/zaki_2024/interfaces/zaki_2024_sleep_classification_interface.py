"""Primary class for converting experiment-specific behavior."""

import pandas as pd
from pydantic import FilePath
from typing import Optional, List

from pynwb.file import NWBFile
from pynwb.epoch import TimeIntervals
from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict


class Zaki2024SleepClassificationInterface(BaseDataInterface):
    """Adds intervals of sleeping behavior."""

    keywords = ["behavior", "sleep stages"]

    def __init__(self, file_path: FilePath, sampling_frequency: float, verbose: bool = False):
        # This should load the data lazily and prepare variables you need

        self.file_path = file_path
        self.verbose = verbose
        self.sampling_frequency = sampling_frequency
        self._start_times = None
        self._stop_times = None

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def get_sleep_states_times(self):
        sleep_behavior_df = pd.read_csv(self.file_path)

        import numpy as np

        # Note this will have the first row as None
        shifted_sleep_state = sleep_behavior_df["SleepState"].shift()
        start_indices = np.where(sleep_behavior_df["SleepState"] != shifted_sleep_state)[0]
        stop_indices = [i - 1 for i in start_indices[1:]]
        stop_indices.append(len(sleep_behavior_df) - 1)
        stop_indices = np.array(stop_indices)

        start_frames = sleep_behavior_df["Frame"][start_indices].values
        start_times = self._start_times if self._start_times is not None else start_frames / self.sampling_frequency
        stop_frames = sleep_behavior_df["Frame"][stop_indices].values
        stop_times = self._stop_times if self._stop_times is not None else stop_frames / self.sampling_frequency

        sleep_state = sleep_behavior_df["SleepState"][start_indices].values

        return start_times, stop_times, sleep_state

    def set_aligned_interval_times(self, start_times: List[float], stop_times: List[float]) -> None:
        self._start_times = start_times
        self._stop_times = stop_times

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: Optional[dict] = None):

        start_times, stop_times, sleep_state = self.get_sleep_states_times()

        description = (
            "Sleep states classified with custom algorithm using the data "
            "from the HD-X02 sensor (EEG, EMG, temperature, etc.)."
        )

        sleep_intervals = TimeIntervals(name="SleepIntervals", description=description)
        column_description = """
            Sleep State Classification, it can be one of the following: 
            - 'quiet wake': The animal is awake and alert but at rest, without engaging in any voluntary movement or significant cognitive activity
            - 'rem': Sleep stage characterized by Rapid Eye Movements (REM) beneath closed eyelids.
            - 'sws':  Slow-Wave Sleep (SWS) is a stage of non-REM (NREM) sleep characterized by slow, high-amplitude brain waves
            - 'wake': State of full consciousness when the animal is alert, responsive to the environment, and capable of voluntary movement
        """
        sleep_intervals.add_column(name="sleep_state", description=column_description)

        for start_time, stop_time, state in zip(start_times, stop_times, sleep_state):
            sleep_intervals.add_interval(start_time=start_time, stop_time=stop_time, sleep_state=state)

        if "sleep" not in nwbfile.processing:
            sleep_module = nwbfile.create_processing_module(name="sleep", description="Sleep data")
        else:
            sleep_module = nwbfile.processing["sleep"]

        sleep_module.add(sleep_intervals)
