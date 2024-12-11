import re
import yaml

from src.cai_lab_to_nwb.zaki_2024.utils.source_data_path_resolver import *
from src.cai_lab_to_nwb.zaki_2024.utils.generate_session_description import generate_session_description


def update_conversion_parameters_yaml(
    subject_id: str,
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    experiment_design_file_path: Union[str, Path],
    session_ids: list = (),
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
    session_ids : list, optional
        List of session types to process. Defaults to an empty list.

    Returns:
    --------
    None
    """
    yaml_file_path = Path(__file__).parent / "conversion_parameters.yaml"
    subjects_df = pd.read_excel(experiment_design_file_path)
    session_times_df = get_session_times_df(subject_id=subject_id, data_dir_path=data_dir_path, session_ids=session_ids)
    for session_id in session_times_df["Session"]:
        session_row = session_times_df[session_times_df["Session"] == session_id].iloc[0]
        date_str = session_row["Date"]
        time_str = session_row["Time"]
        experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
        if "Offline" in session_id:
            if date_str is None:
                date_str = get_date_str_from_experiment_dir_path(experiment_dir_path=experiment_dir_path)
            edf_file_path = get_edf_file_path(subject_id, date_str, data_dir_path)
            sleep_classification_file_path = get_sleep_classification_file_path(subject_id, session_id, data_dir_path)
            video_file_path = None
            freezing_output_file_path = None
            shock_stimulus = None
        else:
            edf_file_path = None
            sleep_classification_file_path = None
            video_file_path = get_video_file_path(subject_id, session_id, data_dir_path)
            freezing_output_file_path = get_freezing_output_file_path(subject_id, session_id, data_dir_path)
            if session_id == "FC":
                shock_amplitude = subjects_df["Amplitude"][subjects_df["Mouse"] == subject_id].to_numpy()[0]
                shock_amplitude = float(re.findall(r"[-+]?\d*\.\d+|\d+", shock_amplitude)[0])
                shock_stimulus = dict(
                    shock_times=[120.0, 180.0, 240.0], shock_amplitude=shock_amplitude, shock_duration=2.0
                )
            else:
                shock_stimulus = None
        imaging_folder_path = get_imaging_folder_path(subject_id, session_id, data_dir_path, time_str, date_str)
        minian_folder_path = get_miniscope_folder_path(subject_id, session_id, data_dir_path)

        session_description = generate_session_description(
            experiment_design_file_path=experiment_design_file_path, subject_id=subject_id, session_id=session_id
        )
        session_to_nwb_kwargs_per_session = {
            session_id: {
                "output_dir_path": str(output_dir_path),
                "subject_id": subject_id,
                "session_id": session_id,
                "date_str": date_str,
                "time_str": time_str,
                "session_description": session_description,
                "experiment_dir_path": str(experiment_dir_path),
                "imaging_folder_path": str(imaging_folder_path) if imaging_folder_path else None,
                "minian_folder_path": str(minian_folder_path) if minian_folder_path else None,
                "video_file_path": str(video_file_path) if video_file_path else None,
                "freezing_output_file_path": str(freezing_output_file_path) if freezing_output_file_path else None,
                "edf_file_path": str(edf_file_path) if edf_file_path else None,
                "sleep_classification_file_path": (
                    str(sleep_classification_file_path) if sleep_classification_file_path else None
                ),
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
    session_ids = [
        "NeutralExposure",
        "FC",
        "OfflineDay1Session1",
        "OfflineDay2Session1",
        "Recall1",
        "Recall2",
        "Recall3",
    ]
    update_conversion_parameters_yaml(
        subject_id="Ca_EEG2-1",
        data_dir_path=Path("D:/"),
        output_dir_path=Path("D:/cai_lab_conversion_nwb/"),
        experiment_design_file_path=Path("D:/Ca_EEG_Design.xlsx"),
        session_ids=session_ids,
    )
