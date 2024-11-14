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
        verbose: bool = False,
    ):
        self.file_path = Path(file_path)
        self.verbose = verbose
        super().__init__(file_path=file_path)

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        stub_test: bool = False,
        stub_frames: int = 100,
        start_datetime_timestamp: datetime = None,
        stop_datetime_timestamp: datetime = None,
        **conversion_options,
    ) -> NWBFile:
        """
        Adds data from EEG, EMG, temperature, and activity channels to an NWBFile.

        Parameters
        ----------
        nwbfile : NWBFile
            The NWBFile object to which data will be added.
        stub_test : bool, optional
            If True, loads only a subset of frames (controlled by `stub_frames` parameter)
            to facilitate testing and faster execution. Default is False.
        stub_frames : int, optional
            The number of frames to load if `stub_test` is True. Default is 100.
        start_datetime_timestamp : datetime, optional
            The starting timestamp for slicing the data. If specified, data will be included
            only from this time onward. Default is None, which includes data from the start.
        stop_datetime_timestamp : datetime, optional
            The ending timestamp for slicing the data. If specified, data will be included
            only up to this time. Default is None, which includes data until the end.
        **conversion_options
            Additional options for data conversion (not currently used directly in this function).

        Returns
        -------
        NWBFile
            The NWBFile object with added data and metadata from the specified channels.
        """
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
        if start_datetime_timestamp is not None:
            # Get edf start_time in datetime format
            edf_start_time = edf_reader.info["meas_date"]
            # Convert relative edf timestamps to datetime timestamps
            edf_start_time = edf_start_time.replace(tzinfo=None)
            edf_datetime_timestamps = [edf_start_time + timedelta(seconds=t) for t in times]
            # Find the indices of the timestamps within the time range
            start_idx = np.searchsorted(edf_datetime_timestamps, start_datetime_timestamp, side="left")
            end_idx = np.searchsorted(edf_datetime_timestamps, stop_datetime_timestamp, side="right")
            starting_time = edf_datetime_timestamps[start_idx] - start_datetime_timestamp
            starting_time = starting_time.total_seconds()
        else:
            start_idx = 0
            end_idx = -1
            starting_time = times[start_idx]

        # Slice the data and timestamps within the time range
        if stub_test:
            data = data[:, start_idx : start_idx + stub_frames]
        else:
            data = data[:, start_idx:end_idx]

        for channel_index, channel_name in enumerate(channels_dict.keys()):
            time_series_kwargs = channels_dict[channel_name].copy()
            time_series_kwargs.update(
                data=data[channel_index], starting_time=starting_time, rate=edf_reader.info["sfreq"]
            )
            time_series = TimeSeries(**time_series_kwargs)
            nwbfile.add_acquisition(time_series)

        # Add device
        description = "Wireless telemetry probe used to record EEG, EMG, temperature, and activity data"
        name = "HD-X02, Data Science International"
        device = Device(name=name, description=description)
        nwbfile.add_device(device)

        return nwbfile
