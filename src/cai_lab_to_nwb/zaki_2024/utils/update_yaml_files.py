from typing import Union
from pathlib import Path
import pandas as pd
from datetime import datetime
import re
import yaml
import warnings


def get_session_times_df(subject_id: str, data_dir_path: Union[str, Path], session_types: list = ()) -> pd.DataFrame:

    if "Ca_EEG3-" in subject_id:
        session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_SessionTimes.csv")
        assert session_times_file_path.is_file(), f"{session_times_file_path} does not exist"
        session_times_df = pd.read_csv(session_times_file_path)
        if session_types:
            session_times_df = session_times_df[session_times_df["Session"].isin(session_types)]
        return session_times_df

    elif "Ca_EEG2-" in subject_id:
        session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / "Session_Timestamps.csv"
        assert session_times_file_path.is_file(), f"{session_times_file_path} does not exist"
        session_times_df_original = pd.read_csv(session_times_file_path, header=None)
        session_names = session_times_df_original.iloc[0, 1:].tolist()  # Exclude first column
        session_times = session_times_df_original.iloc[1, 1:].tolist()  # Exclude first column
        # Create the DataFrame
        session_times_df = pd.DataFrame({"Session": session_names, "Time": session_times, "Date": None})
        if session_types:
            session_times_df = session_times_df[session_times_df["Session"].isin(session_types)]
        return session_times_df

    elif "Ca_EEG_Pilot" in subject_id:
        warnings.warn("Not implemented")

    else:
        print(f"Invalid subject_id: {subject_id}")


def get_experiment_dir_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    if "Offline" in session_id:
        offline_day = session_id.split("Session")[0]
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Offline") / offline_day
    else:
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Sessions") / session_id
    assert experiment_dir_path.is_dir(), f"{experiment_dir_path} does not exist"
    return experiment_dir_path


def get_date_str_from_experiment_dir_path(experiment_dir_path: Union[str, Path]):
    # get date_str as the name of the folder in experiment_dir_path
    for subdirectory in experiment_dir_path.iterdir():
        if subdirectory.is_dir():
            folder_name = subdirectory.name
            try:
                datetime.strptime(folder_name, "%Y_%m_%d")
                return folder_name
            except ValueError:
                print(f"The folder name '{folder_name}' is NOT in the correct date format: '%Y_%m_%d'.")


def get_edf_file_path(subject_id: str, date_str: str, data_dir_path: Union[str, Path]):
    try:
        datetime_obj = datetime.strptime(date_str, "%Y_%m_%d")
        reformatted_date_str = datetime_obj.strftime("_%m%d%y")
        edf_file_path = (
            data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF") / (subject_id + reformatted_date_str + ".edf")
        )
        if not edf_file_path.is_file():
            warnings.warn(f"{edf_file_path} not found. The EDF data stream will not be added.")
            return None
        return edf_file_path
    except ValueError:
        print(f"The date_str is not in the correct format: '{date_str}'")


def get_sleep_classification_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    sleep_classification_file_path = (
        data_dir_path / "Ca_EEG_Sleep" / subject_id / "AlignedSleep" / (session_id + "_AlignedSleep.csv")
    )
    if not sleep_classification_file_path.is_file():
        warnings.warn(
            f"{sleep_classification_file_path} not found. The sleep classification data stream will not be added."
        )
        return None
    return sleep_classification_file_path


def get_video_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    video_file_path = Path(experiment_dir_path) / (session_id + ".wmv")
    if not video_file_path.is_file():
        warnings.warn(f"{video_file_path} not found. The video data stream will not be added.")
        return None
    return video_file_path


def get_freezing_output_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    freezing_output_file_path = Path(experiment_dir_path) / (session_id + "_FreezingOutput.csv")
    if not freezing_output_file_path.is_file():
        warnings.warn(f"{freezing_output_file_path} not found. The freezing output data stream will not be added.")
        return None
    return freezing_output_file_path


def get_imaging_folder_path(
    subject_id: str, session_id: str, data_dir_path: Union[str, Path], time_str: str, date_str: str
):
    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    if date_str is not None:
        imaging_folder_path = Path(experiment_dir_path) / date_str / time_str
    else:
        imaging_folder_path = Path(experiment_dir_path) / time_str
    if not imaging_folder_path.is_dir():
        warnings.warn(f"{imaging_folder_path} not found. The freezing output data stream will not be added.")
        return None
    return imaging_folder_path


def get_miniscope_folder_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    if not minian_folder_path.is_dir():
        warnings.warn(f"{minian_folder_path} not found. The miniscope folder will not be added.")
        return None
    return minian_folder_path


def update_session_to_nwb_kwargs_yaml(
    subject_id: str,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    experiment_design_file_path: Union[str, Path],
    session_types: list = (),  # session_id without the subject_id
):

    yaml_file_path = Path(__file__).parent / "session_to_nwb_kwargs.yaml"
    subjects_df = pd.read_excel(experiment_design_file_path)
    session_times_df = get_session_times_df(
        subject_id=subject_id, data_dir_path=data_dir_path, session_types=session_types
    )
    for session_type in session_times_df["Session"]:
        session_id = subject_id + "_" + session_type
        session_row = session_times_df[session_times_df["Session"] == session_type].iloc[0]
        date_str = session_row["Date"]
        time_str = session_row["Time"]
        experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
        if "Offline" in session_id:
            if date_str is None:
                date_str = get_date_str_from_experiment_dir_path(experiment_dir_path=experiment_dir_path)
            edf_file_path = str(
                get_edf_file_path(subject_id, date_str, data_dir_path)
            )  # convert to str to save it correctly in the yaml
            sleep_classification_file_path = str(
                get_sleep_classification_file_path(subject_id, session_id, data_dir_path)
            )
            video_file_path = None
            freezing_output_file_path = None
            shock_stimulus = None
        else:
            edf_file_path = None
            sleep_classification_file_path = None
            video_file_path = str(get_video_file_path(subject_id, session_id, data_dir_path))
            freezing_output_file_path = str(get_freezing_output_file_path(subject_id, session_id, data_dir_path))
            if session_type == "FC":
                shock_amplitude = subjects_df["Amplitude"][subjects_df["Mouse"] == subject_id].to_numpy()[0]
                shock_amplitude = float(re.findall(r"[-+]?\d*\.\d+|\d+", shock_amplitude)[0])
                shock_stimulus = dict(
                    shock_times=[120.0, 180.0, 240.0], shock_amplitude=shock_amplitude, shock_duration=2.0
                )
            else:
                shock_stimulus = None
        imaging_folder_path = str(get_imaging_folder_path(subject_id, session_id, data_dir_path, time_str, date_str))
        minian_folder_path = str(get_miniscope_folder_path(subject_id, session_id, data_dir_path))
        session_to_nwb_kwargs_per_session = {
            session_id: {
                "output_dir_path": str(output_dir_path),
                "subject_id": subject_id,
                "session_id": session_id,
                "date_str": date_str,
                "time_str": time_str,
                "experiment_dir_path": str(experiment_dir_path),
                "imaging_folder_path": imaging_folder_path,
                "minian_folder_path": minian_folder_path,
                "video_file_path": video_file_path,
                "freezing_output_file_path": freezing_output_file_path,
                "edf_file_path": edf_file_path,
                "sleep_classification_file_path": sleep_classification_file_path,
                "shock_stimulus": shock_stimulus,
            }
        }

        try:
            with open(yaml_file_path, "r") as file:
                yaml_content = yaml.safe_load(file) or {}
        except FileNotFoundError:
            yaml_content = {}

        if subject_id not in yaml_content:
            yaml_content[subject_id] = {}

        yaml_content[subject_id].update(session_to_nwb_kwargs_per_session)

        with open(yaml_file_path, "w") as file:
            yaml.dump(yaml_content, file, default_flow_style=False)
    return


if __name__ == "__main__":
    update_session_to_nwb_kwargs_yaml(
        subject_id="Ca_EEG3-4",
        data_dir_path=Path("D:/"),
        output_dir_path=Path("D:/cai_lab_conversion_nwb/"),
        experiment_design_file_path=Path("D:/Ca_EEG_Design.xlsx"),
    )
