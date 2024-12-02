from typing import Union
from pathlib import Path
import pandas as pd
from datetime import datetime
import re
import yaml

# TODO: invece di mandare errori per file mancanti, manda warnings e lascia vuoto
# TODO: testare su codice di conversione
# TODO: implementare per secondo soggetto


def get_session_times_file_path(subject_id: str, data_dir_path: Union[str, Path]):
    if "Ca_EEG3-" in subject_id:
        session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_SessionTimes.csv")
        assert session_times_file_path.is_file(), f"{session_times_file_path} does not exist"
    elif "Ca_EEG2-" in subject_id:
        session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / "Session_Timestamps.csv"
        assert session_times_file_path.is_file(), f"{session_times_file_path} does not exist"
    elif "Ca_EEG_Pilot" in subject_id:
        print("Not implemented yet ")
        session_times_file_path = None
    else:
        print(f"Invalid subject_id: {subject_id}")
    return session_times_file_path


def get_experiment_dir_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    if "Offline" in session_id:
        offline_day = session_id.split("Session")[0]
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Offline") / offline_day
    else:
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Sessions") / session_id
    assert experiment_dir_path.is_dir(), f"{experiment_dir_path} does not exist"
    return experiment_dir_path


def get_edf_file_path(subject_id: str, date_str: str, data_dir_path: Union[str, Path]):
    # TODO check date_str is in the "%Y_%m_%d" format
    datetime_obj = datetime.strptime(date_str, "%Y_%m_%d")
    reformatted_date_str = datetime_obj.strftime("_%m%d%y")
    edf_file_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF") / (subject_id + reformatted_date_str + ".edf")
    assert edf_file_path.is_file(), f"{edf_file_path} does not exist"
    return edf_file_path


def get_sleep_classification_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    sleep_classification_file_path = (
        data_dir_path / "Ca_EEG_Sleep" / subject_id / "AlignedSleep" / (session_id + "_AlignedSleep.csv")
    )
    assert sleep_classification_file_path.is_file(), f"{sleep_classification_file_path} does not exist"
    return sleep_classification_file_path


def get_video_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    video_file_path = experiment_dir_path / (session_id + ".wmv")
    assert video_file_path.is_file(), f"{video_file_path} does not exist"
    return video_file_path


def get_freezing_output_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    freezing_output_file_path = experiment_dir_path / (session_id + "_FreezingOutput.csv")
    assert freezing_output_file_path.is_file(), f"{freezing_output_file_path} does not exist"
    return freezing_output_file_path


def get_imaging_folder_path(
    subject_id: str, session_id: str, data_dir_path: Union[str, Path], time_str: str, date_str: str = None
):
    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    if date_str is not None:
        imaging_folder_path = experiment_dir_path / date_str / time_str
    else:
        imaging_folder_path = experiment_dir_path / time_str
    assert imaging_folder_path.is_dir(), f"{imaging_folder_path} does not exist"
    return imaging_folder_path


def get_miniscope_folder_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]):
    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    assert minian_folder_path.is_dir(), f"{minian_folder_path} does not exist"
    return minian_folder_path


def update_session_to_nwb_kwargs_yaml(
    subject_id: str,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    experiment_design_file_path: Union[str, Path],
    session_id: str = None,
):
    yaml_file_path = Path(__file__).parent / "session_to_nwb_kwargs.yaml"
    subjects_df = pd.read_excel(experiment_design_file_path)
    if session_id is None:
        # Update yaml for all session listed in {subject_id}_SessionTimes.csv or Session_Timestamps.csv
        if "Ca_EEG3-" in subject_id:
            session_times_file_path = get_session_times_file_path(subject_id, data_dir_path)
            session_times_df = pd.read_csv(session_times_file_path)
            for task in session_times_df["Session"]:
                session_id = subject_id + "_" + task
                session_row = session_times_df[session_times_df["Session"] == task].iloc[0]
                date_str = session_row["Date"]
                time_str = session_row["Time"]
                experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
                edf_file_path = (
                    get_edf_file_path(subject_id, date_str, data_dir_path) if "Offline" in session_id else None
                )
                sleep_classification_file_path = (
                    get_sleep_classification_file_path(subject_id, session_id, data_dir_path)
                    if "Offline" in session_id
                    else None
                )
                video_file_path = (
                    None if "Offline" in session_id else get_video_file_path(subject_id, session_id, data_dir_path)
                )
                freezing_output_file_path = (
                    None
                    if "Offline" in session_id
                    else get_freezing_output_file_path(subject_id, session_id, data_dir_path)
                )
                if task == "FC":
                    shock_amplitude = subjects_df["Amplitude"][subjects_df["Mouse"] == subject_id].to_numpy()[0]
                    shock_amplitude = float(re.findall(r"[-+]?\d*\.\d+|\d+", shock_amplitude)[0])
                    shock_stimulus = dict(
                        shock_times=[120.0, 180.0, 240.0], shock_amplitude=shock_amplitude, shock_duration=2.0
                    )
                else:
                    shock_stimulus = None
                imaging_folder_path = get_imaging_folder_path(subject_id, session_id, data_dir_path, time_str, date_str)
                minian_folder_path = get_miniscope_folder_path(subject_id, session_id, data_dir_path)

                session_to_nwb_kwargs_per_session = {
                    session_id: {
                        "output_dir_path": str(output_dir_path),
                        "subject_id": subject_id,
                        "session_id": session_id,
                        "date_str": date_str,
                        "time_str": time_str,
                        "stub_test": False,
                        "verbose": True,
                        "experiment_dir_path": str(experiment_dir_path),
                        "imaging_folder_path": str(imaging_folder_path),
                        "minian_folder_path": str(minian_folder_path),
                        "video_file_path": str(video_file_path),
                        "freezing_output_file_path": str(freezing_output_file_path),
                        "edf_file_path": str(edf_file_path),
                        "sleep_classification_file_path": str(sleep_classification_file_path),
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

    #     if "Ca_EEG2-" in subject_id:
    #         session_times_file_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / "Session_Timestamps.csv"
    #     if "Ca_EEG_Pilot" in subject_id:
    #         warning("Not implemented yet")
    # else:
    #     # Update yaml only for session_id

    return


def update_session_metadata_yaml(experiment_design_file_path: Union[str, Path]):
    metadata_path = Path(__file__).parent / "../zaki_2024_metadata.yaml"

    return None


if __name__ == "__main__":
    update_session_to_nwb_kwargs_yaml(
        subject_id="Ca_EEG3-4",
        data_dir_path=Path("D:/"),
        output_dir_path=Path("D:/cai_lab_conversion_nwb/"),
        experiment_design_file_path=Path("D:/Ca_EEG_Design.xlsx"),
    )
