"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time
from natsort import natsorted
from pathlib import Path
from typing import Union
import re
from datetime import datetime
from mne.io import read_raw_edf

from neuroconv.utils import load_dict_from_file, dict_deep_update
from neuroconv.tools.nwb_helpers import configure_and_write_nwbfile

from cai_lab_to_nwb.zaki_2024.utils import (
    get_session_slicing_time_range,
    get_session_run_time,
    get_session_times_df,
    get_imaging_folder_path,
    get_experiment_dir_path,
    get_date_str_from_experiment_dir_path,
)
from cai_lab_to_nwb.zaki_2024.interfaces.miniscope_imaging_interface import get_miniscope_folder_path
from cai_lab_to_nwb.zaki_2024.zaki_2024_nwbconverter import Zaki2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    stub_test: bool = False,
    verbose: bool = True,
):
    """
    Convert a week-long experimental session into an NWB file using the NWBConverter.

    This function processes multiple data streams, including EEG/EMG signals and
    cross-session cell registration, and generates a single NWB file representing
    the entire week-long session for a given subject.

    Parameters
    ----------
    data_dir_path : Union[str, Path]
        Path to the root directory containing all session data for the subject.
    output_dir_path : Union[str, Path]
        Path to the directory where the resulting NWB file will be saved.
    subject_id : str
        Identifier for the subject whose data is being converted.
    stub_test : bool, optional
        If True, perform a quick test conversion using a subset of the data. Default is False.
    verbose : bool, optional
        If True, print detailed progress information. Default is True.

    Data Streams
    ------------
    1. MultiEDFSignals
       - EEG, EMG, temperature, and activity signals are extracted from `.edf` files
         located in the `Ca_EEG_EDF/<subject_id>_EDF` folder.
       - All `.edf` files in the directory are included.

    2. CellRegistration
       - Cross-session cell registration results are extracted from `.csv` files
         located in subdirectories of `Ca_EEG_Calcium/<subject_id>/SpatialFootprints`.
       - Folder and file names are matched using the regex pattern
         `CellRegResults_OfflineDay(\d+)Session(\d+)`.

    3. Other sessions within the week
        - Epochs are added to the NWB file to define time intervals corresponding to
          conditioning and offline sessions. If imaging data is available, session start
          and stop times are determined from the Miniscope metadata and timestamps.
          Otherwise, they are calculated using session notes and provided time/dates.

    Output
    ------
    - An NWB file named `sub-<subject_id>_ses-Week.nwb` is saved in the `output_dir_path`.

    Examples
    --------
    Convert a session with the following parameters:

    ```python
    from pathlib import Path
    session_to_nwb(
        data_dir_path=Path("/path/to/data"),
        output_dir_path=Path("/path/to/output"),
        subject_id="Subject123",
        stub_test=True,
        verbose=True,
    )
    ```

    Notes
    -----
    - The function adds metadata to the NWB file, including subject details and
      session description.
    - If any required data files are missing, the function raises an assertion error
      with a descriptive message.
    """

    if verbose:
        print(f"Converting week-long session")
        start = time.time()

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-Week.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add EEG, EMG, Temperature and Activity signals
    edf_folder_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF")
    edf_file_paths = natsorted(edf_folder_path.glob("*.edf"))
    assert edf_file_paths, f"No .edf files found in {edf_folder_path}"

    source_data.update(
        dict(
            MultiEDFSignals=dict(
                file_paths=edf_file_paths,
            )
        )
    )
    conversion_options.update(dict(MultiEDFSignals=dict(stub_test=stub_test)))

    # Add Cross session cell registration
    main_folder = data_dir_path / f"Ca_EEG_Calcium/{subject_id}/SpatialFootprints"
    pattern = re.compile(r"^CellRegResults_OfflineDay(\d+)Session(\d+)$")

    file_paths = []
    for folder in main_folder.iterdir():
        match = pattern.match(folder.name)
        if folder.is_dir() and match:
            offline_day, session_number = match.groups()
            filename = f"CellRegResults_{subject_id}_OfflineDay{offline_day}Session{session_number}.csv"
            csv_file = folder / filename
            assert csv_file.is_file(), f"Expected file not found: {csv_file}"
            file_paths.append(csv_file)

    source_data.update(dict(CellRegistration=dict(file_paths=file_paths)))
    conversion_options.update(dict(CellRegistration=dict(stub_test=stub_test, subject_id=subject_id)))

    converter = Zaki2024NWBConverter(source_data=source_data)
    # Add datetime to conversion
    metadata = converter.get_metadata()
    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "zaki_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = subject_id
    metadata["NWBFile"]["session_id"] = "Week"

    edf_reader = read_raw_edf(input_fname=edf_file_paths[0], verbose=verbose)
    session_start_time = edf_reader.info["meas_date"]

    metadata["NWBFile"]["session_start_time"] = session_start_time

    session_description = (
        "Week long of continuous recording with HD-X02 wireless telemetry probe of EEG, EMG, Temperature and Activity signals. "
        "Conditioning and Offline sessions, as described in the experiment_description, were performed during the week. "
        "The output of cell registration across conditioning and offline sessions are reported in this nwb file. "
    )
    metadata["NWBFile"]["session_description"] = session_description

    nwbfile = converter.create_nwbfile(metadata=metadata, conversion_options=conversion_options)

    # Add epochs table to store time range of conditioning and offline sessions
    session_times_df = get_session_times_df(subject_id=subject_id, data_dir_path=data_dir_path)

    # Add columns to TimeIntervals
    nwbfile.add_epoch_column(name="session_ids", description="ID of the session")

    for session_id, date_str, time_str in zip(
        session_times_df["Session"], session_times_df["Date"], session_times_df["Time"]
    ):
        experiment_dir_path = get_experiment_dir_path(
            subject_id=subject_id, session_id=session_id, data_dir_path=data_dir_path
        )
        if date_str is None:
            date_str = get_date_str_from_experiment_dir_path(experiment_dir_path=experiment_dir_path)
        try:
            folder_path = get_imaging_folder_path(
                subject_id=subject_id,
                session_id=session_id,
                data_dir_path=data_dir_path,
                time_str=time_str,
                date_str=date_str,
            )
            miniscope_folder_path = get_miniscope_folder_path(folder_path)
            miniscope_metadata_json = folder_path / "metaData.json"
            assert miniscope_metadata_json.exists(), f"General metadata json not found in {folder_path}"
            timestamps_file_path = miniscope_folder_path / "timeStamps.csv"
            assert timestamps_file_path.exists(), f"Miniscope timestamps file not found in {miniscope_folder_path}"

            start_datetime_timestamp, stop_datetime_timestamp = get_session_slicing_time_range(
                miniscope_metadata_json=miniscope_metadata_json, timestamps_file_path=timestamps_file_path
            )

            start_time = (start_datetime_timestamp - session_start_time.replace(tzinfo=None)).total_seconds()
            stop_time = (stop_datetime_timestamp - session_start_time.replace(tzinfo=None)).total_seconds()

        # Some sessions may not have imaging data, so we extract the run time from the session notes (.txt file)
        # and use the data string and time string to retrieve the start datetime of the session
        except:
            datetime_str = date_str + " " + time_str
            start_datetime_timestamp = datetime.strptime(datetime_str, "%Y_%m_%d %H_%M_%S")

            txt_file_path = experiment_dir_path / f"{subject_id}_{session_id}.txt"
            session_run_time = get_session_run_time(txt_file_path=txt_file_path)

            start_time = (start_datetime_timestamp - session_start_time.replace(tzinfo=None)).total_seconds()
            stop_time = start_time + session_run_time

        nwbfile.add_epoch(start_time=start_time, stop_time=stop_time, session_ids=session_id)

    # Run conversion
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
    data_dir_path = Path("D:/Cai-CN-data-share/")
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    subject_id = "Ca_EEG3-4"
    stub_test = False
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        subject_id=subject_id,
    )
