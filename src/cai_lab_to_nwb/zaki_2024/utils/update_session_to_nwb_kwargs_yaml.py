import re
import yaml

from .source_data_path_resolver import *


def update_session_to_nwb_kwargs_yaml(
    subject_id: str,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    experiment_design_file_path: Union[str, Path],
    session_types: list = (),
):
    """
    Update a YAML file with parameters required for session-to-NWB conversion.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    data_dir_path : Union[str, Path]
        Path to the base data directory.
    output_dir_path : Union[str, Path]
        Path to the output directory for NWB files.
    experiment_design_file_path : Union[str, Path]
        Path to the experiment design file.
    session_types : list, optional
        List of session types to process. Defaults to an empty list.

    Returns:
    --------
    None
    """
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
