"""Primary class for converting experiment-specific behavior."""

from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import VideoInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from typing import Optional


class FreezingBehaviorInterface(BaseDataInterface):
    """Adds intervals of freezing behavior interface."""

    keywords = ["behavior"]

    def __init__(self, file_path: FilePath, video_sampling_frequency: float, verbose: bool = False):
        # This should load the data lazily and prepare variables you need

        self.file_path = file_path
        self.verbose = verbose
        self.video_sampling_frequency = video_sampling_frequency

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: Optional[dict] = None):

        import pandas as pd
        from ndx_events import Events

        freezing_behavior_df = pd.read_csv(self.file_path)

        # Extract parameters, those values are unique per run
        file = freezing_behavior_df["File"].unique()[0]
        motion_cutoff = freezing_behavior_df["MotionCutoff"].unique()[0]
        freeze_threshold = freezing_behavior_df["FreezeThresh"].unique()[0]
        min_freeze_duration = freezing_behavior_df["MinFreezeDuration"].unique()[0]

        # Extract timestamps of the freezing events
        # From the discussion wih the author, the freezing events are the frames where the freezing behavior is 100
        freezing_frames = freezing_behavior_df[freezing_behavior_df["Freezing"] == 100]["Frame"].values
        timestamps = freezing_frames / self.video_sampling_frequency

        events_description = (
            f"Freezing Events Calculated with EzTrack software for file {file} "
            f"with motion cutoff {motion_cutoff}, freeze threshold {freeze_threshold} "
            f"and min freeze duration {min_freeze_duration}"
        )

        events = Events(
            name="FreezingEvents",
            description=events_description,
            timestamps=timestamps,
        )
        
        if "behavior" not in nwbfile.processing:
            behavior_module = nwbfile.create_processing_module(
                name="behavior", description="Contains behavior data"
            )
        else:
            behavior_module = nwbfile.processing["behavior"]

        behavior_module.add(events)
