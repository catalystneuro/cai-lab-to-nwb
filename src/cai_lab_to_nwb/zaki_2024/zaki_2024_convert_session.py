"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time

from pathlib import Path
from typing import Union
from datetime import datetime, timedelta
import pandas as pd
import json
from neuroconv.utils import load_dict_from_file, dict_deep_update

from zaki_2024_nwbconverter import Zaki2024NWBConverter
from interfaces.miniscope_imaging_interface import get_miniscope_timestamps, get_recording_start_time


def get_miniscope_folder_path(folder_path: Union[str, Path]):
    """
    Retrieve the path to the Miniscope folder within the given session folder based on metadata.

    Parameters:
    -----------
    folder_path : Union[str, Path]
        Path to the main session folder, which should contain a "metaData.json" file with information about the Miniscope.

    Returns:
    --------
    Optional[Path]
        Path to the Miniscope folder, formatted to replace any spaces in the Miniscope name with underscores. Returns `None` if the
        specified folder is not a directory or if the metadata JSON is missing or misconfigured.

    Raises:
    -------
    AssertionError
        If the "metaData.json" file is not found in the given folder path.
    """
    folder_path = Path(folder_path)
    if folder_path.is_dir():
        general_metadata_json = folder_path / "metaData.json"
        assert general_metadata_json.exists(), f"General metadata json not found in {folder_path}"
        with open(general_metadata_json) as f:
            general_metadata = json.load(f)
        miniscope_name = general_metadata["miniscopes"][0]
        return folder_path / miniscope_name.replace(" ", "_")
    else:
        print(f"No Miniscope data found at {folder_path}")
        return None


def get_edf_slicing_time_range(miniscope_metadata_json: Union[str, Path], timestamps_file_path: Union[str, Path]):
    """
    Calculate the time range for EDF slicing based on session start time and Miniscope timestamps.

    Parameters:
    -----------
    miniscope_metadata_json : Union[str, Path]
        Path to the metadata.json file produced by Miniscope output.

    timestamps_file_path : Union[str, Path]
        Path to the Miniscope timeStamps.csv file.

    Returns:
    --------
    Tuple[datetime, datetime]
        A tuple containing the start and stop timestamps (as datetime objects) for the EDF slicing period. The start timestamp
        corresponds to the session's start time adjusted by the first Miniscope timestamp, and the stop timestamp is the session's
        start time adjusted by the last Miniscope timestamp.

    """
    miniscope_metadata_json = Path(miniscope_metadata_json)
    timestamps_file_path = Path(timestamps_file_path)
    if miniscope_metadata_json.is_file() and timestamps_file_path.is_file():

        session_start_time = get_recording_start_time(file_path=miniscope_metadata_json)
        miniscope_timestamps = get_miniscope_timestamps(file_path=timestamps_file_path)

        start_datetime_timestamp = session_start_time + timedelta(seconds=miniscope_timestamps[0])
        stop_datetime_timestamp = session_start_time + timedelta(seconds=miniscope_timestamps[-1])

        return start_datetime_timestamp, stop_datetime_timestamp


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    session_id: str,
    date_str: str,
    time_str: str,
    stub_test: bool = False,
    verbose: bool = True,
    include_imaging: bool = True,
    include_freezing_behavior: bool = True,
    include_sleep_classification: bool = True,
    include_behavioral_video: bool = True,
    include_eeg_emg_signals: bool = True,
    shock_stimulus: dict = None,
):
    print(f"Converting session {session_id}")
    if verbose:
        start = time.time()

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    if "Offline" in session_id:
        offline_day = session_id.split("Session")[0]
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Offline") / offline_day
    else:
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Sessions") / session_id
        include_eeg_emg_signals = False
        include_sleep_classification = False

    # Add Imaging
    folder_path = experiment_dir_path / date_str / time_str
    miniscope_folder_path = get_miniscope_folder_path(folder_path)
    if miniscope_folder_path is not None and include_imaging:
        source_data.update(dict(MiniscopeImaging=dict(folder_path=miniscope_folder_path)))
        conversion_options.update(dict(MiniscopeImaging=dict(stub_test=stub_test)))
    elif verbose and not include_imaging:
        print(f"Miniscope data will not be included for session {session_id}")
    elif verbose and miniscope_folder_path is None:
        print(f"No Miniscope data found at {miniscope_folder_path}")

    # Add Segmentation
    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    if minian_folder_path.is_dir() and include_imaging:
        source_data.update(dict(MinianSegmentation=dict(folder_path=minian_folder_path)))
        conversion_options.update(dict(MinianSegmentation=dict(stub_test=stub_test)))
    elif verbose and not include_imaging:
        print(f"Minian data will not be included for session {session_id}")
    elif verbose and not minian_folder_path.is_dir():
        print(f"No Minian data found at {minian_folder_path}")

    # Add Motion Correction
    motion_corrected_video = minian_folder_path / "minian_mc.mp4"
    if motion_corrected_video.is_file() and include_imaging:
        source_data.update(
            dict(MinianMotionCorrection=dict(folder_path=minian_folder_path, video_file_path=motion_corrected_video))
        )
        conversion_options.update(dict(MinianMotionCorrection=dict(stub_test=stub_test)))
    elif verbose and not include_imaging:
        print(f"Minian Motion Correction data will not be included for session {session_id}")
    elif verbose and not motion_corrected_video.is_file():
        print(f"No motion corrected data found at {motion_corrected_video}")

    # Add Behavioral Video
    video_file_path = experiment_dir_path / (session_id + ".wmv")
    if video_file_path.is_file() and include_behavioral_video:
        source_data.update(dict(Video=dict(file_paths=[video_file_path])))
        conversion_options.update(dict(Video=dict(stub_test=stub_test)))
    elif verbose and not include_behavioral_video:
        print(f"The behavioral video will not be included for session {session_id}")
    elif verbose and not video_file_path.is_file():
        print(f"No behavioral video found at {video_file_path}")

    # Add Freezing Analysis output
    freezing_output_file_path = experiment_dir_path / (session_id + "_FreezingOutput.csv")
    if freezing_output_file_path.is_file() and include_freezing_behavior:
        source_data.update(
            dict(FreezingBehavior=dict(file_path=freezing_output_file_path, video_sampling_frequency=30.0))
        )
    elif verbose and not include_freezing_behavior:
        print(f"The Freezing Analysis output will not be included for session {session_id}")
    elif verbose and not freezing_output_file_path.is_file():
        print(f"No freezing output csv file found at {freezing_output_file_path}")

    # Add EEG, EMG, Temperature and Activity signals
    datetime_obj = datetime.strptime(date_str, "%Y_%m_%d")
    reformatted_date_str = datetime_obj.strftime("_%m%d%y")
    edf_file_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF") / (subject_id + reformatted_date_str + ".edf")

    if edf_file_path.is_file() and include_eeg_emg_signals:
        miniscope_metadata_json = folder_path / "metaData.json"
        assert miniscope_metadata_json.exists(), f"General metadata json not found in {folder_path}"
        timestamps_file_path = miniscope_folder_path / "timeStamps.csv"
        assert timestamps_file_path.exists(), f"Miniscope timestamps file not found in {miniscope_folder_path}"
        start_datetime_timestamp, stop_datetime_timestamp = get_edf_slicing_time_range(
            miniscope_metadata_json=miniscope_metadata_json, timestamps_file_path=timestamps_file_path
        )
        source_data.update(
            dict(
                EDFSignals=dict(
                    file_path=edf_file_path,
                )
            )
        )
        conversion_options.update(
            dict(
                EDFSignals=dict(
                    stub_test=stub_test,
                    start_datetime_timestamp=start_datetime_timestamp,
                    stop_datetime_timestamp=stop_datetime_timestamp,
                )
            )
        )
    elif verbose and not include_eeg_emg_signals:
        print(f"The EEG, EMG, Temperature and Activity signals will not be included for session {session_id}")
    elif verbose and not edf_file_path.is_file():
        print(f"No .edf file found at {edf_file_path}")

    # Add Sleep Classification output
    sleep_classification_file_path = (
        data_dir_path / "Ca_EEG_Sleep" / subject_id / "AlignedSleep" / (session_id + "_AlignedSleep.csv")
    )
    if sleep_classification_file_path.is_file() and include_sleep_classification:
        source_data.update(
            dict(SleepClassification=dict(file_path=sleep_classification_file_path, video_sampling_frequency=30.0))
        )
    elif verbose and not include_sleep_classification:
        print(f"The Sleep Classification output will not be included for session {session_id}")
    elif verbose and not sleep_classification_file_path.is_file():
        print(f"No sleep classification output csv file found at {sleep_classification_file_path}")

    # Add Shock Stimuli times for FC sessions
    if shock_stimulus is not None:

        source_data.update(ShockStimuli=dict())
        conversion_options.update(
            ShockStimuli=shock_stimulus,
        )

    converter = Zaki2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    # if session_start_time has been already set from other interfaces do not override
    if not metadata["NWBFile"]["session_start_time"]:
        datetime_str = date_str + " " + time_str
        session_start_time = datetime.strptime(datetime_str, "%Y_%m_%d %H_%M_%S")
        metadata["NWBFile"]["session_start_time"] = session_start_time

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "zaki_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.run_conversion(
        metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options, overwrite=True
    )

    if verbose:
        stop_time = time.time()
        conversion_time_seconds = stop_time - start
        if conversion_time_seconds <= 60 * 3:
            print(f"Conversion took {conversion_time_seconds:.2f} seconds")
        elif conversion_time_seconds <= 60 * 60:
            print(f"Conversion took {conversion_time_seconds / 60:.2f} minutes")
        else:
            print(f"Conversion took {conversion_time_seconds / 60 / 60:.2f} hours")


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("D:/")
    subject_id = "Ca_EEG3-4"
    task = "FC"
    session_id = subject_id + "_" + task
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    stub_test = False
    session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_SessionTimes.csv")
    df = pd.read_csv(session_times_file_path)
    session_row = df[df["Session"] == task].iloc[0]
    date_str = session_row["Date"]
    time_str = session_row["Time"]
    shock_stimulus = dict(shock_times=[120.0, 180.0, 240.0], shock_amplitude=0.25, shock_duration=2.0)
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        subject_id=subject_id,
        session_id=session_id,
        date_str=date_str,
        time_str=time_str,
        shock_stimulus=shock_stimulus,
    )
