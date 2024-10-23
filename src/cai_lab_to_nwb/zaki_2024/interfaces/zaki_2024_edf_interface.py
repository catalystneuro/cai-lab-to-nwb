from pydantic import FilePath
from pathlib import Path

from neuroconv.basedatainterface import BaseDataInterface
from pynwb import NWBFile, TimeSeries
from pynwb.device import Device

class Zaki2024EDFInterface(BaseDataInterface):
    
    def __init__(self, file_path: FilePath, verbose: bool = False):
        
        self.file_path = Path(file_path)
        self.verbose = verbose
        super().__init__(file_path=file_path)

    def add_to_nwbfile(self, nwbfile: NWBFile, **conversion_options) -> NWBFile:
        
        from mne.io import read_raw_edf

        edf_reader = read_raw_edf(input_fname=self.file_path, verbose=self.verbose)
                
        channels_of_interest = ["Temp", "EEG", "EMG", "Activity"]
        data, times = edf_reader.get_data(picks=channels_of_interest, return_times=True)
        data = data.astype("float32")
        
        # Add temperature data to NWBFile
        temperature = data[0]
        temperature_time_series = TimeSeries(name="TimeSeriesTemperature", data=temperature, unit="Celsius", timestamps=times)
        
        nwbfile.add_acquisition(temperature_time_series)
        
        EEG = data[1]
        EMG = data[2]
        
        # Add EEG and EMG data to NWBFile
        eeg_time_series = TimeSeries(name="TimeSeriesSeriesEEG", data=EEG, unit="V", timestamps=times)
        emg_time_series = TimeSeries(name="TimeSeriesSeriesEMG", data=EMG, unit="V", timestamps=times)
        
        nwbfile.add_acquisition(eeg_time_series)
        nwbfile.add_acquisition(emg_time_series)
        
        # Add Activity
        
        activity = data[3]
        
        # TODO: Figure out if the units of activity are correct, the raw format marks Volts
        # TODO: My own reading of the header indicates that the physical units is counts
        activity_time_series = TimeSeries(name="TimeSeriesActivity", data=activity, unit="n.a.", timestamps=times)
        
        nwbfile.add_acquisition(activity_time_series)
        
        # Add device
        description = "Wireless telemetry probe used to record EEG, EMG, temperature, and activity data"
        name = "HD-X02, Data Science International"
        device = Device(name=name, description=description)
        nwbfile.add_device(device)
        
        return nwbfile
        

