from pathlib import Path
from typing import Union
from datetime import timedelta

from src.cai_lab_to_nwb.zaki_2024.interfaces.miniscope_imaging_interface import (
    get_miniscope_timestamps,
    get_recording_start_time,
)


def get_session_slicing_time_range(miniscope_metadata_json: Union[str, Path], timestamps_file_path: Union[str, Path]):
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


def get_session_run_time(txt_file_path: Union[str, Path]):
    import re

    try:
        with open(txt_file_path, "r") as file:
            text = file.read()
    except FileNotFoundError:
        print(f"File not found at {txt_file_path}")
        exit()
    # Extract the Run Time line
    run_time_line = re.search(r"Run Time\s*:\s*([\d:.]+)", text)
    if run_time_line:
        run_time_str = run_time_line.group(1)

        # Convert Run Time to seconds
        h, m, s = map(float, run_time_str.split(":"))
        duration = h * 3600 + m * 60 + s
        return duration
    else:
        print("Run Time information not found.")
