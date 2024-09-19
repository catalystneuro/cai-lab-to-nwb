"""Primary class for converting experiment-specific behavior."""
from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.datainterfaces import VideoInterface
from neuroconv.utils import DeepDict
from pydantic import FilePath
from pynwb.epoch import TimeIntervals

class FreezingBehaviorInterface(BaseDataInterface):
    """Adds intervals of freezing behavior interface."""

    keywords = ["behavior"]
    
    def __init__(self, file_path: FilePath, verbose: bool = False):
        # This should load the data lazily and prepare variables you need
        
        self.file_path = file_path
        self.verbose = verbose
        
        

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()   

        return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata: dict):
        # All the custom code to add the data the nwbfile

        sampling_frequency = 30.0
        import pandas as pd 
        freezing_behavior_df = pd.read_csv(self.file_path, usecols=['Frame', 'Motion', 'Freezing'])
        
        start_time = freezing_behavior_df['Frame'][freezing_behavior_df['Freezing'] == 1].index.values/sampling_frequency
        
        TimeIntervals(name="Freezing", description="Intervals of freezing behavior", 
                      start_time=freezing_behavior_df['Frame'][freezing_behavior_df['Freezing'] == 1].index.values/sampling_frequency, 
                      stop_time=freezing_behavior_df['Frame'][freezing_behavior_df['Freezing'] == 0].index.values/sampling_frequency)
        
        
