"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time

from pathlib import Path
from typing import Union
from datetime import datetime, timedelta
import pandas as pd
import json
from neuroconv.utils import load_dict_from_file, dict_deep_update

from zaki_2024_nwbconverter import Zaki2024NWBConverter

# TODO:
# 1. aggiungere sessions start time da edf.info["meas_date"]
# 2. creare un interfaccia per multi edf files


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    stub_test: bool = False,
    verbose: bool = True,
    include_eeg_emg_signals: bool = True,
):
    print(f"Converting session {session_id}")
    if verbose:
        start = time.time()

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{subject_id}_week_session.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add EEG, EMG, Temperature and Activity signals
    datetime_obj = datetime.strptime(date_str, "%Y_%m_%d")
    reformatted_date_str = datetime_obj.strftime("_%m%d%y")
    edf_file_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF") / (subject_id + reformatted_date_str + ".edf")

    if edf_file_path.is_file() and include_eeg_emg_signals:

        source_data.update(
            dict(
                EDFSignals=dict(
                    file_path=edf_file_path,
                )
            )
        )
        conversion_options.update(dict(EDFSignals=dict(stub_test=stub_test)))
    elif verbose and not include_eeg_emg_signals:
        print(f"The EEG, EMG, Temperature and Activity signals will not be included for session {session_id}")
    elif verbose and not edf_file_path.is_file():
        print(f"No .edf file found at {edf_file_path}")

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
    task = "OfflineDay1Session1"
    session_id = subject_id + "_" + task
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    stub_test = False
    session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_SessionTimes.csv")
    df = pd.read_csv(session_times_file_path)
    session_row = df[df["Session"] == task].iloc[0]
    date_str = session_row["Date"]
    time_str = session_row["Time"]
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        subject_id=subject_id,
        session_id=session_id,
        date_str=date_str,
        time_str=time_str,
    )
