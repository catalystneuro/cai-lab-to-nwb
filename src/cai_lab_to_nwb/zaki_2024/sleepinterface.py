"""Primary class for converting experiment-specific behavior."""

from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import VideoInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from typing import Optional


class SleepBehaviorInterface(BaseDataInterface):
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
        from ndx_events import LabeledEvents

        sleep_behavior_df = pd.read_csv(self.file_path)

        sleep_frames = sleep_behavior_df["Frame"].values
        timestamps = sleep_frames / self.video_sampling_frequency

        sleep_states = ['quiet wake', 'rem', 'sws', 'wake']
        # correspondin positionally to the sleep states
        labels = ["Quiet wake", "REM", "Slow Wave Sleep", "Wake"]
        state_to_index = {state: i for i, state in enumerate(sleep_states)}

        data = [state_to_index[sleep_state] for sleep_state in sleep_behavior_df.SleepState]


        description = (
            "Sleep states classified with custom algorithm using the data "
            "from the HD-X02 sensor (EEG, EMG, temperature, etc.)."
        )
        
        labeled_events = LabeledEvents(name="SleepEvents", description=description, labels=labels, data=data, timestamps=timestamps)

        if "sleep" not in nwbfile.processing:
            sleep_module = nwbfile.create_processing_module(name="sleep", description="Sleep data")
        else:
            sleep_module = nwbfile.processing["sleep"]
        
        sleep_module.add(labeled_events)

