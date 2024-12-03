from typing import Union
from pathlib import Path
import pandas as pd
from datetime import datetime
import warnings


def get_session_times_df(subject_id: str, data_dir_path: Union[str, Path], session_types: list = ()) -> pd.DataFrame:
    """
    Retrieve a DataFrame containing session times for a given subject.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    data_dir_path : Union[str, Path]
        Path to the base data directory.
    session_types : list, optional
        List of session types to filter. Defaults to an empty list.

    Returns:
    --------
    pd.DataFrame
        A DataFrame with session names, dates, times.

    Raises:
    -------
    AssertionError
        If the session times file does not exist.
    """

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


def get_experiment_dir_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]) -> Path:
    """
    Construct the path to the experiment directory for a given subject and session.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    session_id : str
        The ID of the session.
    data_dir_path : Union[str, Path]
        Path to the base data directory.

    Returns:
    --------
    Path
        The path to the experiment directory.

    Raises:
    -------
    AssertionError
        If the experiment directory does not exist.
    """

    if "Offline" in session_id:
        offline_day = session_id.split("Session")[0]
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Offline") / offline_day
    else:
        experiment_dir_path = data_dir_path / "Ca_EEG_Experiment" / subject_id / (subject_id + "_Sessions") / session_id
    assert experiment_dir_path.is_dir(), f"{experiment_dir_path} does not exist"
    return experiment_dir_path


def get_date_str_from_experiment_dir_path(experiment_dir_path: Union[str, Path]) -> Union[str, None]:
    """
    Extract the date string from the name of the subdirectory in the experiment directory.
    This is meant to work only for offline sessions

    Parameters:
    -----------
    experiment_dir_path : Union[str, Path]
        Path to the experiment directory.

    Returns:
    --------
    Union[str, None]
        The date string in the format "YYYY_MM_DD", or None if not found.
    """

    for subdirectory in experiment_dir_path.iterdir():
        if subdirectory.is_dir():
            folder_name = subdirectory.name
            try:
                datetime.strptime(folder_name, "%Y_%m_%d")
                return folder_name
            except ValueError:
                print(f"The folder name '{folder_name}' is NOT in the correct date format: '%Y_%m_%d'.")


def get_edf_file_path(subject_id: str, date_str: str, data_dir_path: Union[str, Path]) -> Union[Path, None]:
    """
    Retrieve the path to the EDF file for a given subject and date.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    date_str : str
        The date string in "YYYY_MM_DD" format.
    data_dir_path : Union[str, Path]
        Path to the base data directory.

    Returns:
    --------
    Union[Path, None]
        Path to the EDF file, or None if not found.
    """

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


def get_sleep_classification_file_path(
    subject_id: str, session_id: str, data_dir_path: Union[str, Path]
) -> Union[Path, None]:
    """
    Retrieve the path to the sleep classification file for a given subject and session.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    session_id : str
        The ID of the session.
    data_dir_path : Union[str, Path]
        Path to the base data directory.

    Returns:
    --------
    Union[Path, None]
        Path to the sleep classification file, or None if not found.
    """
    sleep_classification_file_path = (
        data_dir_path / "Ca_EEG_Sleep" / subject_id / "AlignedSleep" / (session_id + "_AlignedSleep.csv")
    )
    if not sleep_classification_file_path.is_file():
        warnings.warn(
            f"{sleep_classification_file_path} not found. The sleep classification data stream will not be added."
        )
        return None
    return sleep_classification_file_path


def get_video_file_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]) -> Union[Path, None]:
    """
    Retrieve the path to the behavioral video file for a given subject and session.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    session_id : str
        The ID of the session.
    data_dir_path : Union[str, Path]
        Path to the base data directory.

    Returns:
    --------
    Union[Path, None]
        Path to the video file, or None if not found.
    """

    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    video_file_path = Path(experiment_dir_path) / (session_id + ".wmv")
    if not video_file_path.is_file():
        warnings.warn(f"{video_file_path} not found. The video data stream will not be added.")
        return None
    return video_file_path


def get_freezing_output_file_path(
    subject_id: str, session_id: str, data_dir_path: Union[str, Path]
) -> Union[Path, None]:
    """
    Retrieve the path to the freezing output file for a given subject and session.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    session_id : str
        The ID of the session.
    data_dir_path : Union[str, Path]
        Path to the base data directory.

    Returns:
    --------
    Union[Path, None]
        Path to the freezing output file, or None if not found.
    """

    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    freezing_output_file_path = Path(experiment_dir_path) / (session_id + "_FreezingOutput.csv")
    if not freezing_output_file_path.is_file():
        warnings.warn(f"{freezing_output_file_path} not found. The freezing output data stream will not be added.")
        return None
    return freezing_output_file_path


def get_imaging_folder_path(
    subject_id: str, session_id: str, data_dir_path: Union[str, Path], time_str: str, date_str: str
) -> Union[Path, None]:
    """
    Retrieve the path to the imaging folder for a given session.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    session_id : str
        The ID of the session.
    data_dir_path : Union[str, Path]
        Path to the base data directory.
    time_str : str
        The session start time.
    date_str : str
        The session date.

    Returns:
    --------
    Union[Path, None]
        Path to the imaging folder, or None if not found.
    """

    experiment_dir_path = get_experiment_dir_path(subject_id, session_id, data_dir_path)
    if date_str is not None:
        imaging_folder_path = Path(experiment_dir_path) / date_str / time_str
    else:
        imaging_folder_path = Path(experiment_dir_path) / time_str
    if not imaging_folder_path.is_dir():
        warnings.warn(f"{imaging_folder_path} not found. The freezing output data stream will not be added.")
        return None
    return imaging_folder_path


def get_miniscope_folder_path(subject_id: str, session_id: str, data_dir_path: Union[str, Path]) -> Union[Path, None]:
    """
    Retrieve the path to the miniscope folder for a given subject and session.

    Parameters:
    -----------
    subject_id : str
        The ID of the subject.
    session_id : str
        The ID of the session.
    data_dir_path : Union[str, Path]
        Path to the base data directory.

    Returns:
    --------
    Union[Path, None]
        Path to the miniscope folder, or None if not found.
    """

    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    if not minian_folder_path.is_dir():
        warnings.warn(f"{minian_folder_path} not found. The miniscope folder will not be added.")
        return None
    return minian_folder_path
