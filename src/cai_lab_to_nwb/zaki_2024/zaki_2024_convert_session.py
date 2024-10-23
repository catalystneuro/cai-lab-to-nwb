"""Primary script to run to convert an entire session for of data using the NWBConverter."""

from pathlib import Path
from typing import Union
from datetime import datetime
import pandas as pd

from neuroconv.utils import load_dict_from_file, dict_deep_update

from zaki_2024_nwbconverter import Zaki2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    session_id: str,
    date_str: str,
    time_str: str,
    stub_test: bool = False,
):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    raw_data_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id

    # Add Imaging
    miniscope_folder_path = (
        raw_data_dir_path / (subject_id + "_Sessions") / session_id / date_str / time_str / "miniscope"
    )
    source_data.update(dict(MiniscopeImaging=dict(folder_path=miniscope_folder_path)))
    conversion_options.update(dict(MiniscopeImaging=dict(stub_test=stub_test)))

    # Add Segmentation
    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    source_data.update(dict(MinianSegmentation=dict(folder_path=minian_folder_path)))
    # conversion_options.update(dict(MinianSegmentation=dict(stub_test=stub_test)))

    # Add Behavioral Video
    video_file_paths = [raw_data_dir_path / (subject_id + "_Sessions") / session_id / (session_id + ".wmv")]
    source_data.update(dict(Video=dict(file_paths=video_file_paths)))
    conversion_options.update(dict(Video=dict(stub_test=stub_test)))

    # Add Freezing Analysis output
    csv_file_path = raw_data_dir_path / (subject_id + "_Sessions") / session_id / (session_id + "_FreezingOutput.csv")
    source_data.update(dict(FreezingBehavior=dict(file_path=csv_file_path, video_sampling_frequency=30.0)))
    # conversion_options.update(dict(FreezingBehavior=dict(stub_test=stub_test)))

    # Add EEG, EMG, Temperature and Activity signals
    # TODO discuss how to slice this data
    datetime_obj = datetime.strptime(date_str, "%Y_%m_%d")
    reformatted_date_str = datetime_obj.strftime("_%m%d%y")
    edf_file_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF") / (subject_id + reformatted_date_str + ".edf")
    source_data.update(dict(EDFSignals=dict(file_path=edf_file_path)))

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
