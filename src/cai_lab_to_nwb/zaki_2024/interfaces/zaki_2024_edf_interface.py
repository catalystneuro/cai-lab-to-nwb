from pydantic import FilePath
from pathlib import Path

from neuroconv.basedatainterface import BaseDataInterface
from pynwb import NWBFile, TimeSeries
from pynwb.device import Device

from mne.io import read_raw_edf


class Zaki2024EDFInterface(BaseDataInterface):

    def __init__(self, file_path: FilePath, verbose: bool = False):

        self.file_path = Path(file_path)
        self.verbose = verbose
        super().__init__(file_path=file_path)

    def get_timestamps_reference_time(self):
        """
        Get datetime object of the first frame of the data in the .edf file.

        Returns
        ----------
        timestamps_reference_time : datetime.datetime
            datetime object of the first frame of the data in the .edf file.

        """
        edf_reader = read_raw_edf(input_fname=self.file_path, verbose=self.verbose)
        return edf_reader.info["meas_date"]

    def add_to_nwbfile(
        self, nwbfile: NWBFile, stub_test: bool = False, stub_frames: int = 100, **conversion_options
    ) -> NWBFile:

        channels_dict = {
            "Temp": {
                "name": "TemperatureSignal",
                "description": "Temperature signal recorder with HD-X02 wireless telemetry probe",
                "unit": "celsius",
            },
            "EEG": {
                "name": "EEGSignal",
                "description": "EEG signal recorder with HD-X02 wireless telemetry probe",
                "unit": "volts",
            },
            "EMG": {
                "name": "EMGSignal",
                "description": "EMG signal recorder with HD-X02 wireless telemetry probe",
                "unit": "volts",
            },
            # TODO: Figure out if the units of activity are correct, the raw format marks Volts
            # TODO: My own reading of the header indicates that the physical units is counts
            "Activity": {
                "name": "ActivitySignal",
                "description": "Activity signal recorder with HD-X02 wireless telemetry probe. It refers to the motion of the probe relative to the receiver and it can be used as a proxy for locomotion.",
                "unit": "n.a.",
            },
        }

        edf_reader = read_raw_edf(input_fname=self.file_path, verbose=self.verbose)
        data, times = edf_reader.get_data(picks=list(channels_dict.keys()), return_times=True)
        data = data.astype("float32")
        if stub_test:
            data = data[:, :stub_frames]
            times = times[:stub_frames]
        for channel_index, channel_name in enumerate(channels_dict.keys()):
            time_series_kwargs = channels_dict[channel_name].copy()
            time_series_kwargs.update(data=data[channel_index], timestamps=times)
            time_series = TimeSeries(**time_series_kwargs)
            nwbfile.add_acquisition(time_series)

        # Add device
        description = "Wireless telemetry probe used to record EEG, EMG, temperature, and activity data"
        name = "HD-X02, Data Science International"
        device = Device(name=name, description=description)
        nwbfile.add_device(device)

        return nwbfile
