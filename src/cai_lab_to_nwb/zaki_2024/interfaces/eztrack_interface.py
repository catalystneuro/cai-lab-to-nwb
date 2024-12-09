"""Primary class for converting experiment-specific behavior."""

import numpy as np
import pandas as pd

from pynwb import TimeSeries
from pynwb.epoch import TimeIntervals
from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from typing import Optional, List


class EzTrackFreezingBehaviorInterface(BaseDataInterface):
    """Adds intervals of freezing behavior and motion series."""

    keywords = ["behavior", "freezing", "motion"]

    def __init__(self, file_path: FilePath, video_sampling_frequency: float, verbose: bool = False):
        # This should load the data lazily and prepare variables you need

        self.file_path = file_path
        self.verbose = verbose
        self.video_sampling_frequency = video_sampling_frequency
        self._start_times = None
        self._stop_times = None
        self._starting_time = None

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def get_interval_times(self):
        # Extract start and stop times of the freezing events
        # From the discussion wih the author, the freezing events are the frames where the freezing behavior is 100
        freezing_behavior_df = pd.read_csv(self.file_path)
        freezing_values = freezing_behavior_df["Freezing"].values
        changes_in_freezing = np.diff(freezing_values)
        freezing_start = np.where(changes_in_freezing == 100)[0] + 1
        freezing_stop = np.where(changes_in_freezing == -100)[0] + 1

        start_frames = freezing_behavior_df["Frame"].values[freezing_start]
        stop_frames = freezing_behavior_df["Frame"].values[freezing_stop]

        start_times = (
            self._start_times if self._start_times is not None else start_frames / self.video_sampling_frequency
        )
        stop_times = self._stop_times if self._stop_times is not None else stop_frames / self.video_sampling_frequency
        return start_times, stop_times

    def get_starting_time(self) -> float:
        freezing_behavior_df = pd.read_csv(self.file_path)
        return freezing_behavior_df["Frame"].values[0] / self.video_sampling_frequency

    def set_aligned_interval_times(self, start_times: List[float], stop_times: List[float]) -> None:
        self._start_times = start_times
        self._stop_times = stop_times

    def set_aligned_starting_time(self, aligned_start_time) -> None:
        self._starting_time = aligned_start_time

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: Optional[dict] = None, stub_test: bool = False):

        freezing_behavior_df = pd.read_csv(self.file_path)

        start_times, stop_times = self.get_interval_times()

        # Extract motion data
        motion_data = freezing_behavior_df["Motion"].values
        starting_time = self._starting_time if self._starting_time is not None else self.get_starting_time()

        motion_series = TimeSeries(
            name="MotionSeries",
            description="ezTrack measures the motion of the animal by assessing the number of pixels of the behavioral "
            "video whose grayscale change exceeds a particular threshold from one frame to the next.",
            data=motion_data[:100] if stub_test else motion_data,
            unit="n.a",
            starting_time=starting_time,
            rate=self.video_sampling_frequency,
        )

        # Extract parameters, those values are unique per run
        file = freezing_behavior_df["File"].unique()[0]
        motion_cutoff = freezing_behavior_df["MotionCutoff"].unique()[0]
        freeze_threshold = freezing_behavior_df["FreezeThresh"].unique()[0]
        min_freeze_duration = freezing_behavior_df["MinFreezeDuration"].unique()[0]

        description = f"""
            Freezing behavior intervals generated using EzTrack software for file {file}. 
            Parameters used include a motion cutoff of {motion_cutoff}, freeze threshold of {freeze_threshold}, 
            and a minimum freeze duration of {min_freeze_duration}.
            
            - Freeze threshold: The maximum amount of motion the animal can display while still being classified as freezing.
            - Minimum freeze duration: The shortest time period the animal must remain below the freeze threshold to qualify as freezing.
            - Motion cutoff: The level of pixel intensity change required to register as motion.
        """

        freeze_intervals = TimeIntervals(name="FreezingIntervals", description=description)
        for start_time, stop_time in zip(start_times, stop_times):
            freeze_intervals.add_interval(start_time=start_time, stop_time=stop_time, timeseries=[motion_series])

        if "behavior" not in nwbfile.processing:
            behavior_module = nwbfile.create_processing_module(name="behavior", description="Contains behavior data")
        else:
            behavior_module = nwbfile.processing["behavior"]

        behavior_module.add(motion_series)
        behavior_module.add(freeze_intervals)
