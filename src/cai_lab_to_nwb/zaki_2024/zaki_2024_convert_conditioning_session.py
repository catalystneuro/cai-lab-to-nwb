"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time

from pathlib import Path
from typing import Union
from datetime import datetime
import pandas as pd
import json
from neuroconv.utils import load_dict_from_file, dict_deep_update

from zaki_2024_nwbconverter import Zaki2024NWBConverter


def get_miniscope_folder_path(folder_path: Union[str, Path]):
    folder_path = Path(folder_path)
    if folder_path.is_dir():
        general_metadata_json = folder_path / "metaData.json"
        assert general_metadata_json.exists(), f"General metadata json not found in {folder_path}"
        with open(general_metadata_json) as f:
            general_metadata = json.load(f)
        miniscope_name = general_metadata["miniscopes"][0]
        return folder_path / miniscope_name.replace(" ", "_")
    else:
        print("No Miniscope data found at {}".format(folder_path))
        return None


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    session_id: str,
    date_str: str,
    time_str: str,
    stub_test: bool = False,
    verbose: bool = True,
):
    print("Converting session {}".format(session_id))
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

    experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Sessions")

    # Add Imaging
    folder_path = experiment_dir_path / session_id / date_str / time_str
    miniscope_folder_path = get_miniscope_folder_path(folder_path)
    if miniscope_folder_path is not None:
        source_data.update(dict(MiniscopeImaging=dict(folder_path=miniscope_folder_path)))
        conversion_options.update(dict(MiniscopeImaging=dict(stub_test=stub_test)))

    # Add Segmentation
    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    if minian_folder_path.is_dir():
        source_data.update(dict(MinianSegmentation=dict(folder_path=minian_folder_path)))
        conversion_options.update(dict(MinianSegmentation=dict(stub_test=stub_test)))
    else:
        print("No Minian data found at {}".format(minian_folder_path))

    # Add Motion Correction
    motion_corrected_video = minian_folder_path / "minian_mc.mp4"
    if motion_corrected_video.is_file():
        source_data.update(
            dict(MinianMotionCorrection=dict(folder_path=minian_folder_path, video_file_path=motion_corrected_video))
        )
        conversion_options.update(dict(MinianMotionCorrection=dict(stub_test=stub_test)))

    # Add Behavioral Video
    video_file_path = experiment_dir_path / session_id / (session_id + ".wmv")
    if video_file_path.is_file():
        source_data.update(dict(Video=dict(file_paths=[video_file_path])))
        conversion_options.update(dict(Video=dict(stub_test=stub_test)))
    else:
        print("No behavioral video found at {}".format(video_file_path))

    # Add Freezing Analysis output
    freezing_output_file_path = experiment_dir_path / session_id / (session_id + "_FreezingOutput.csv")
    if freezing_output_file_path.is_file():
        source_data.update(
            dict(FreezingBehavior=dict(file_path=freezing_output_file_path, video_sampling_frequency=30.0))
        )
    else:
        print("No freezing output csv file found at {}".format(freezing_output_file_path))

    # Add EEG, EMG, Temperature and Activity signals
    # TODO discuss how to slice this data
    datetime_obj = datetime.strptime(date_str, "%Y_%m_%d")
    reformatted_date_str = datetime_obj.strftime("_%m%d%y")
    edf_file_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF") / (subject_id + reformatted_date_str + ".edf")
    if edf_file_path.is_file():
        source_data.update(dict(EDFSignals=dict(file_path=edf_file_path)))
        conversion_options.update(dict(EDFSignals=dict(stub_test=stub_test)))
    else:
        print("No .edf file found at {}".format(edf_file_path))

    ophys_metadata_path = Path(__file__).parent / "zaki_2024_ophys_metadata.yaml"
    ophys_metadata = load_dict_from_file(ophys_metadata_path)

    converter = Zaki2024NWBConverter(source_data=source_data, ophys_metadata=ophys_metadata)

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
    task = "NeutralExposure"
    session_id = subject_id + "_" + task
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    stub_test = True
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
