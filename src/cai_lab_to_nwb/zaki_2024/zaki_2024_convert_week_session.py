"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time
import uuid
from copy import deepcopy
from natsort import natsorted
from pathlib import Path
from typing import Union
import os
import pandas as pd

from pynwb import NWBFile
from pynwb.epoch import TimeIntervals
from neuroconv.utils import load_dict_from_file, dict_deep_update
from neuroconv.tools.nwb_helpers import configure_and_write_nwbfile

from utils import get_session_slicing_time_range
from interfaces.miniscope_imaging_interface import get_miniscope_folder_path
from zaki_2024_nwbconverter import Zaki2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    stub_test: bool = False,
    verbose: bool = True,
):
    print(f"Converting week-long session")
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
    edf_folder_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF")
    edf_file_paths = natsorted(edf_folder_path.glob("*.edf"))
    if len(edf_file_paths) > 0:
        source_data.update(
            dict(
                MultiEDFSignals=dict(
                    file_paths=edf_file_paths,
                )
            )
        )
        conversion_options.update(dict(MultiEDFSignals=dict(stub_test=stub_test)))
    else:
        print(f"No .edf file found in {edf_folder_path}")

        # Add Cross session cell registration
    main_folder = data_dir_path / f"/Ca_EEG_Calcium/{subject_id}/SpatialFootprints"
    file_paths = []
    for folder in os.listdir(main_folder):
        folder_path = os.path.join(main_folder, folder)
        if os.path.isdir(folder_path):  # Ensure it's a directory
            filename = folder.split("_")[0] + f"_{subject_id}_" + folder.split("_")[-1]
            csv_file = os.path.join(folder_path, f"{filename}.csv")
            if os.path.isfile(csv_file):  # Check if the file exists
                file_paths.append(csv_file)
    source_data.update(dict(CellRegistration=dict(file_paths=file_paths)))
    conversion_options.update(dict(CellRegistration=dict(stub_test=stub_test, subject_id=subject_id)))

    from mne.io import read_raw_edf

    edf_reader = read_raw_edf(input_fname=edf_file_paths[0], verbose=verbose)
    session_start_time = edf_reader.info["meas_date"]

    editable_metadata_path = Path(__file__).parent / "zaki_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    nwbfile_kwargs = deepcopy(editable_metadata["NWBFile"])

    nwbfile_kwargs.update(
        dict(
            session_id=f"{subject_id}_week_session",
            identifier=str(uuid.uuid4()),
            session_start_time=session_start_time,
        )
    )

    nwbfile = NWBFile(**nwbfile_kwargs)

    # Add epochs table to store time range of conditioning and offline sessions
    sessions_summary_file = data_dir_path / f"Ca_EEG_Experiment/{subject_id}/{subject_id}_SessionTimes.csv"
    sessions_summary_df = pd.read_csv(sessions_summary_file)

    # Add columns to TimeIntervals
    nwbfile.add_epoch_column(name="session_ids", description="ID of the session")

    for task, date_str, time_str in zip(
        sessions_summary_df["Session"], sessions_summary_df["Date"], sessions_summary_df["Time"]
    ):
        session_id = subject_id + "_" + task
        if "Offline" in session_id:
            offline_day = session_id.split("Session")[0]
            experiment_dir_path = (
                data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Offline") / offline_day
            )
        else:
            experiment_dir_path = (
                data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Sessions") / session_id
            )
        folder_path = experiment_dir_path / date_str / time_str
        miniscope_folder_path = get_miniscope_folder_path(folder_path)
        miniscope_metadata_json = folder_path / "metaData.json"
        assert miniscope_metadata_json.exists(), f"General metadata json not found in {folder_path}"
        timestamps_file_path = miniscope_folder_path / "timeStamps.csv"
        assert timestamps_file_path.exists(), f"Miniscope timestamps file not found in {miniscope_folder_path}"
        start_datetime_timestamp, stop_datetime_timestamp = get_session_slicing_time_range(
            miniscope_metadata_json=miniscope_metadata_json, timestamps_file_path=timestamps_file_path
        )
        start_time = start_datetime_timestamp - session_start_time.replace(tzinfo=None)
        stop_time = stop_datetime_timestamp - session_start_time.replace(tzinfo=None)
        nwbfile.add_epoch(
            start_time=start_time.total_seconds(), stop_time=stop_time.total_seconds(), session_ids=session_id
        )

    converter = Zaki2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.add_to_nwbfile(metadata=metadata, nwbfile=nwbfile, conversion_options=conversion_options)
    configure_and_write_nwbfile(nwbfile=nwbfile, backend="hdf5", output_filepath=nwbfile_path)

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
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    subject_id = "Ca_EEG3-4"
    stub_test = False
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        subject_id=subject_id,
    )
