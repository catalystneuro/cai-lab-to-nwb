"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time
import pytz
from pathlib import Path
from typing import Union
from datetime import datetime, timedelta

from neuroconv.utils import load_dict_from_file, dict_deep_update

from cai_lab_to_nwb.zaki_2024.zaki_2024_nwbconverter import Zaki2024NWBConverter
from cai_lab_to_nwb.zaki_2024.utils import get_session_slicing_time_range, get_session_run_time
from cai_lab_to_nwb.zaki_2024.interfaces.miniscope_imaging_interface import get_miniscope_folder_path


def session_to_nwb(
    output_dir_path: Union[str, Path],
    subject_id: str,
    session_id: str,
    date_str: str,
    time_str: str,
    session_description: str,
    stub_test: bool = False,
    overwrite: bool = False,
    verbose: bool = False,
    experiment_dir_path: Union[str, Path] = None,
    imaging_folder_path: Union[str, Path] = None,
    minian_folder_path: Union[str, Path] = None,
    video_file_path: Union[str, Path] = None,
    freezing_output_file_path: Union[str, Path] = None,
    edf_file_path: Union[str, Path] = None,
    sleep_classification_file_path: Union[str, Path] = None,
    shock_stimulus: dict = None,
):
    """
    Converts data from an experimental session into NWB (Neurodata Without Borders) format using the `Zaki2024NWBConverter`.

    This function aggregates data from various sources, such as imaging, segmentation, behavioral videos, EEG signals, and other experimental data,
    to create a single NWB file for a session. It supports customization via options such as stub testing, metadata updates, and file overwrite policies.

    Parameters
    ----------
    output_dir_path : Union[str, Path]
        Directory where the output NWB file will be saved.
    subject_id : str
        Unique identifier for the subject.
    session_id : str
        Unique identifier for the session.
    date_str : str
        Date of the session in the format 'YYYY_MM_DD'.
    time_str : str
        Time of the session in the format 'HH_MM_SS'.
    session_description : str
        Description of the session.
    stub_test : bool, optional
        If True, generates a smaller, test-friendly NWB file. Default is False.
    overwrite : bool, optional
        If True, overwrites existing NWB files in the output directory. Default is False.
    verbose : bool, optional
        If True, prints detailed logging information during the conversion process. Default is False.
    experiment_dir_path : Union[str, Path], optional
        Path to the directory containing experimental data.
    imaging_folder_path : Union[str, Path], optional
        Path to the folder containing imaging data. If None, imaging data will not be included.
    minian_folder_path : Union[str, Path], optional
        Path to the folder containing Miniscope segmentation data. If None, segmentation data will not be included.
    video_file_path : Union[str, Path], optional
        Path to a behavioral video file. If None, video data will not be included.
    freezing_output_file_path : Union[str, Path], optional
        Path to a file containing freezing behavior analysis output. If None, freezing behavior data will not be included.
    edf_file_path : Union[str, Path], optional
        Path to an EDF file containing EEG, EMG, temperature, or activity signals. If None, EEG/EMG data will not be included.
    sleep_classification_file_path : Union[str, Path], optional
        Path to a file containing sleep classification data. If None, sleep classification data will not be included.
    shock_stimulus : dict, optional
        Dictionary specifying shock stimulus times for fear conditioning sessions. If None, shock stimulus data will not be included.

    Raises
    ------
    AssertionError
        If any specified file or folder does not exist.
    ValueError
        If required metadata or parameters are missing or invalid.

    Notes
    -----
    - Uses `Zaki2024NWBConverter` for the conversion process.
    - Session start time is automatically localized to the "US/Eastern" timezone.
    - Supports integrating multiple data modalities, each with its own conversion options.
    - If a specific data source is not provided (set to None), it will be excluded from the conversion.
    - Logs the total time taken for the conversion process if `verbose` is True.

    Examples
    --------
    Convert a session for a specific subject:
    >>> session_to_nwb(
    >>>     output_dir_path="D:/cai_lab_conversion_nwb",
    >>>     subject_id="Ca_EEG2-1",
    >>>     session_id="FC",
    >>>     time_str="10_11_24",
    >>>     session_description="Behavioral testing session",
    >>>     stub_test=False,
    >>>     verbose=True,
    >>>     overwrite=True,
    >>>     experiment_dir_path="D:/Ca_EEG_Experiment/Ca_EEG2-1/Ca_EEG2-1_Sessions/Ca_EEG2-1_FC",
    >>>     imaging_folder_path=" D:/Ca_EEG_Experiment/Ca_EEG2-1/Ca_EEG2-1_Sessions/Ca_EEG2-1_FC/10_11_24",
    >>>     minian_folder_path="D:/Ca_EEG_Calcium/Ca_EEG2-1/Ca_EEG2-1_FC/minian",
    >>>     video_file_path="D:/Ca_EEG_Experiment/Ca_EEG2-1/Ca_EEG2-1_Sessions/Ca_EEG2-1_FC/Ca_EEG2-1_FC.wmv",
    >>>     freezing_output_file_path="D:/Ca_EEG_Experiment/Ca_EEG2-1/Ca_EEG2-1_Sessions/Ca_EEG2-1_FC/Ca_EEG2-1_FC_FreezingOutput.csv",
    >>>     shock_stimulus={"shock_times":[120.0, 180.0, 240.0],"shock_amplitude": 1.5, "shock_duration": 2.0}
    """

    if verbose:
        print(f"Converting session {session_id} for subject {subject_id}")
        start = time.time()

    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"sub-{subject_id}_ses-{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Miniscope data
    miniscope_folder_path = None
    if imaging_folder_path:
        imaging_folder_path = Path(imaging_folder_path)
        miniscope_folder_path = get_miniscope_folder_path(imaging_folder_path)
        assert miniscope_folder_path.is_dir(), f"{miniscope_folder_path} does not exist"

        source_data.update(dict(MiniscopeImaging=dict(folder_path=miniscope_folder_path)))
        conversion_options.update(dict(MiniscopeImaging=dict(stub_test=stub_test)))

    # Add Segmentation and Motion Correction
    if minian_folder_path:
        minian_folder_path = Path(minian_folder_path)
        assert minian_folder_path.is_dir(), f"{minian_folder_path} does not exist"
        source_data.update(dict(MinianSegmentation=dict(folder_path=minian_folder_path)))
        conversion_options.update(dict(MinianSegmentation=dict(stub_test=stub_test)))

        # motion_corrected_video = minian_folder_path / "minian_mc.mp4"
        # if motion_corrected_video.is_file():
        #     source_data.update(
        #         dict(
        #             MinianMotionCorrection=dict(folder_path=minian_folder_path, video_file_path=motion_corrected_video)
        #         )
        #     )
        #     conversion_options.update(dict(MinianMotionCorrection=dict(stub_test=stub_test)))
        # elif verbose and not motion_corrected_video.is_file():
        #     print(f"No motion corrected data found at {motion_corrected_video}")

    # Add Behavioral Video
    if video_file_path:
        video_file_path = Path(video_file_path)
        assert video_file_path.is_file(), f"{video_file_path} does not exist"
        source_data.update(dict(Video=dict(file_paths=[video_file_path])))
        conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    # Add Freezing Analysis output
    if freezing_output_file_path:
        freezing_output_file_path = Path(freezing_output_file_path)
        assert freezing_output_file_path.is_file(), f"{freezing_output_file_path} does not exist"
        source_data.update(
            dict(FreezingBehavior=dict(file_path=freezing_output_file_path, video_sampling_frequency=30.0))
        )
        conversion_options.update(dict(FreezingBehavior=dict(stub_test=stub_test)))

    # Add EEG, EMG, Temperature and Activity signals
    if edf_file_path:
        edf_file_path = Path(edf_file_path)
        assert edf_file_path.is_file(), f"{edf_file_path} does not exist"
        if imaging_folder_path.is_dir() and miniscope_folder_path.is_dir():
            miniscope_metadata_json = imaging_folder_path / "metaData.json"
            assert miniscope_metadata_json.exists(), f"General metadata json not found in {imaging_folder_path}"
            timestamps_file_path = miniscope_folder_path / "timeStamps.csv"
            assert timestamps_file_path.exists(), f"Miniscope timestamps file not found in {miniscope_folder_path}"
            start_datetime_timestamp, stop_datetime_timestamp = get_session_slicing_time_range(
                miniscope_metadata_json=miniscope_metadata_json, timestamps_file_path=timestamps_file_path
            )
        else:
            datetime_str = date_str + " " + time_str
            start_datetime_timestamp = datetime.strptime(datetime_str, "%Y_%m_%d %H_%M_%S")

            txt_file_path = experiment_dir_path / f"{subject_id}_{session_id}.txt"
            assert txt_file_path.is_file(), f"{txt_file_path} does not exist"

            session_run_time = get_session_run_time(txt_file_path=txt_file_path)
            stop_datetime_timestamp = start_datetime_timestamp + timedelta(seconds=session_run_time)

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

    # Add Sleep Classification output
    if sleep_classification_file_path:
        sleep_classification_file_path = Path(sleep_classification_file_path)
        assert sleep_classification_file_path.is_file(), f"{sleep_classification_file_path} does not exist"
        source_data.update(
            dict(SleepClassification=dict(file_path=sleep_classification_file_path, sampling_frequency=15.0))
        )

    # Add Shock Stimuli times for FC sessions
    if shock_stimulus is not None:

        source_data.update(ShockStimuli=dict())
        conversion_options.update(
            ShockStimuli=shock_stimulus,
        )

    converter = Zaki2024NWBConverter(source_data=source_data, verbose=verbose)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    # if session_start_time has been already set from other interfaces do not override
    if not metadata["NWBFile"]["session_start_time"]:
        datetime_str = date_str + " " + time_str
        session_start_time = datetime.strptime(datetime_str, "%Y_%m_%d %H_%M_%S")
        metadata["NWBFile"]["session_start_time"] = session_start_time

    eastern = pytz.timezone("US/Eastern")
    metadata["NWBFile"]["session_start_time"] = eastern.localize(metadata["NWBFile"]["session_start_time"])

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "zaki_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = subject_id
    metadata["NWBFile"]["session_description"] = session_description
    metadata["NWBFile"]["session_id"] = session_id

    # Run conversion
    converter.run_conversion(
        metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options, overwrite=overwrite
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

    subject_id = "Ca_EEG3-4"
    session_id = "NeutralExposure"
    stub_test = True
    verbose = True
    overwrite = True
    yaml_file_path = Path(__file__).parent / "utils/conversion_parameters.yaml"
    conversion_parameter_dict = load_dict_from_file(yaml_file_path)
    session_to_nwb_kwargs_per_session = conversion_parameter_dict[subject_id][session_id]
    session_to_nwb(**session_to_nwb_kwargs_per_session, stub_test=stub_test, verbose=verbose, overwrite=overwrite)
