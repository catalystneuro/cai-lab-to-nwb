from pathlib import Path
from neuroconv.basedatainterface import BaseDataInterface
from pynwb import NWBFile, TimeSeries
from pynwb.device import Device
from mne.io import read_raw_edf
from datetime import datetime, timedelta
import numpy as np


class Zaki2024EDFInterface(BaseDataInterface):
    def __init__(
        self,
        file_path: Path,
        start_datetime_timestamp: datetime = None,
        stop_datetime_timestamp: datetime = None,
        verbose: bool = False,
    ):
        self.file_path = Path(file_path)
        self.start_datetime_timestamp = start_datetime_timestamp
        self.stop_datetime_timestamp = stop_datetime_timestamp
        self.verbose = verbose
        super().__init__(
            file_path=file_path,
            start_datetime_timestamp=start_datetime_timestamp,
            stop_datetime_timestamp=stop_datetime_timestamp,
        )

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
        if self.start_datetime_timestamp is not None:
            # Get edf start_time in datetime format
            edf_start_time = edf_reader.info["meas_date"]
            # Convert relative edf timestamps to datetime timestamps
            edf_start_time = edf_start_time.replace(tzinfo=None)
            edf_datetime_timestamps = [edf_start_time + timedelta(seconds=t) for t in times]
            # Find the indices of the timestamps within the time range
            start_idx = np.searchsorted(edf_datetime_timestamps, self.start_datetime_timestamp, side="left")
            end_idx = np.searchsorted(edf_datetime_timestamps, self.stop_datetime_timestamp, side="right")
        else:
            start_idx = 0
            end_idx = -1

        # Slice the data and timestamps within the time range
        if stub_test:
            data = data[:, start_idx : start_idx + stub_frames]
        else:
            data = data[:, start_idx:end_idx]

        for channel_index, channel_name in enumerate(channels_dict.keys()):
            time_series_kwargs = channels_dict[channel_name].copy()
            time_series_kwargs.update(data=data[channel_index], starting_time=0.0, rate=edf_reader.info["sfreq"])
            time_series = TimeSeries(**time_series_kwargs)
            nwbfile.add_acquisition(time_series)

        # Add device
        description = "Wireless telemetry probe used to record EEG, EMG, temperature, and activity data"
        name = "HD-X02, Data Science International"
        device = Device(name=name, description=description)
        nwbfile.add_device(device)

        return nwbfile
