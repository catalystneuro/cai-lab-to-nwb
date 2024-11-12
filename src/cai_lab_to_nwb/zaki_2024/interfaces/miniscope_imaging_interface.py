from roiextractors.imagingextractor import ImagingExtractor
from roiextractors.multiimagingextractor import MultiImagingExtractor
from roiextractors.extraction_tools import PathType, DtypeType, get_package

import json
import datetime

from copy import deepcopy
from typing import Union
from pathlib import Path
from typing import Literal, Optional

import numpy as np
from pydantic import DirectoryPath, validate_call
from pynwb import NWBFile

from neuroconv.datainterfaces.ophys.baseimagingextractorinterface import BaseImagingExtractorInterface
from neuroconv.utils import DeepDict, dict_deep_update


def get_session_start_time(folder_path: Union[str, Path]):
    """
    Retrieve the session start time from metadata in the specified folder.

    Parameters:
    -----------
    folder_path : Union[str, Path]
        Path to the main session folder, expected to contain a "metaData.json" file with recording start time details.

    Returns:
    --------
    datetime.datetime
        A datetime object representing the session start time, based on the metadata's year, month, day, hour, minute,
        second, and millisecond fields.

    Raises:
    -------
    AssertionError
        If the "metaData.json" file is not found in the specified folder path.
    KeyError
        If any of the required time fields ("year", "month", "day", "hour", "minute", "second", "msec") are missing
        from the metadata.

    Notes:
    ------
    - The function expects a "recordingStartTime" key in the metadata JSON, which contains start time details.
      If not present, the top-level JSON object is assumed to contain the time information.
    - The "msec" field in the metadata is converted from milliseconds to microseconds for compatibility with the datetime
      microsecond field.
    """
    general_metadata_json = folder_path / "metaData.json"
    assert general_metadata_json.exists(), f"General metadata json not found in {folder_path}"
    ## Read metadata
    with open(general_metadata_json) as f:
        general_metadata = json.load(f)

    if "recordingStartTime" in general_metadata:
        start_time_info = general_metadata["recordingStartTime"]
    else:
        start_time_info = general_metadata

    required_keys = ["year", "month", "day", "hour", "minute", "second", "msec"]
    for key in required_keys:
        if key not in start_time_info:
            raise KeyError(f"Missing required key '{key}' in the metadata")

    session_start_time = datetime.datetime(
        year=start_time_info["year"],
        month=start_time_info["month"],
        day=start_time_info["day"],
        hour=start_time_info["hour"],
        minute=start_time_info["minute"],
        second=start_time_info["second"],
        microsecond=start_time_info["msec"] * 1000,  # Convert milliseconds to microseconds
    )

    return session_start_time


def get_miniscope_timestamps(miniscope_folder_path: Union[str, Path]):
    """
    Retrieve the Miniscope timestamps from a CSV file and convert them to seconds.

    Parameters:
    -----------
    miniscope_folder_path : Union[str, Path]
        Path to the folder containing the Miniscope "timeStamps.csv" file, which includes timestamps in milliseconds.

    Returns:
    --------
    np.ndarray
        A NumPy array containing the Miniscope timestamps in seconds, converted from the original milliseconds.

    Raises:
    -------
    AssertionError
        If the "timeStamps.csv" file is not found in the specified Miniscope folder path.

    Notes:
    ------
    - This function expects the timestamps CSV file to have a column named "Time Stamp (ms)" with values in milliseconds.
    - The timestamps are converted from milliseconds to seconds for compatibility with other functions that expect time
      values in seconds.
    """
    timestamps_file_path = miniscope_folder_path / "timeStamps.csv"
    assert timestamps_file_path.exists(), f"Miniscope timestamps file not found in {miniscope_folder_path}"
    import pandas as pd

    timetsamps_df = pd.read_csv(timestamps_file_path)
    timestamps_milliseconds = timetsamps_df["Time Stamp (ms)"].values.astype(float)
    timestamps_seconds = timestamps_milliseconds / 1000.0

    return np.asarray(timestamps_seconds)


class MiniscopeImagingExtractor(MultiImagingExtractor):

    def __init__(self, folder_path: DirectoryPath):

        self.miniscope_videos_folder_path = Path(folder_path)
        assert self.miniscope_videos_folder_path.exists(), f"Miniscope videos folder not found in {Path(folder_path)}"

        self._miniscope_avi_file_paths = [p for p in self.miniscope_videos_folder_path.iterdir() if p.suffix == ".avi"]
        assert len(self._miniscope_avi_file_paths) > 0, f"No .avi files found in {self.miniscope_videos_folder_path}"
        import natsort

        self._miniscope_avi_file_paths = natsort.natsorted(self._miniscope_avi_file_paths)

        imaging_extractors = []
        for file_path in self._miniscope_avi_file_paths:
            extractor = _MiniscopeSingleVideoExtractor(file_path=file_path)
            imaging_extractors.append(extractor)

        super().__init__(imaging_extractors=imaging_extractors)

        self._sampling_frequency = self._imaging_extractors[0].get_sampling_frequency()
        self._image_size = self._imaging_extractors[0].get_image_size()
        self._dtype = self._imaging_extractors[0].get_dtype()

    def get_num_frames(self) -> int:
        return self._num_frames

    def get_num_channels(self) -> int:
        return 1

    def get_image_size(self) -> tuple[int, int]:
        return self._image_size

    def get_sampling_frequency(self):
        return self._sampling_frequency

    def get_dtype(self) -> DtypeType:
        return self._dtype

    def get_channel_names(self) -> list[str]:
        return ["OpticalChannel"]


class _MiniscopeSingleVideoExtractor(ImagingExtractor):
    """An auxiliar extractor to get data from a single Miniscope video (.avi) file.

    This format consists of a single video (.avi)
    Multiple _MiniscopeSingleVideoExtractor are combined into the MiniscopeImagingExtractor for public access.
    """

    extractor_name = "_MiniscopeSingleVideo"

    def __init__(self, file_path: PathType):
        """Create a _MiniscopeSingleVideoExtractor instance from a file path.

        Parameters
        ----------
        file_path: PathType
           The file path to the Miniscope video (.avi) file.
        """
        from neuroconv.datainterfaces.behavior.video.video_utils import VideoCaptureContext

        self._video_capture = VideoCaptureContext
        self._cv2 = get_package(package_name="cv2", installation_instructions="pip install opencv-python-headless")
        self.file_path = file_path
        super().__init__()

        cap = self._cv2.VideoCapture(str(self.file_path))

        self._num_frames = int(cap.get(self._cv2.CAP_PROP_FRAME_COUNT))

        # Get the frames per second (fps)
        self._sampling_frequency = cap.get(self._cv2.CAP_PROP_FPS)
        self.frame_width = int(cap.get(self._cv2.CAP_PROP_FRAME_WIDTH))
        self.frame_height = int(cap.get(self._cv2.CAP_PROP_FRAME_HEIGHT))

        _, frame = cap.read()
        self._dtype = frame.dtype

        # Release the video capture object
        cap.release()

    def get_num_frames(self) -> int:
        return self._num_frames

    def get_num_channels(self) -> int:
        return 1

    def get_image_size(self) -> tuple[int, int]:
        return (self.frame_height, self.frame_width)

    def get_sampling_frequency(self):
        return self._sampling_frequency

    def get_dtype(self) -> DtypeType:
        return self._dtype

    def get_channel_names(self) -> list[str]:
        return ["OpticalChannel"]

    def get_video(
        self, start_frame: Optional[int] = None, end_frame: Optional[int] = None, channel: int = 0
    ) -> np.ndarray:
        """Get the video frames.

        Parameters
        ----------
        start_frame: int, optional
            Start frame index (inclusive).
        end_frame: int, optional
            End frame index (exclusive).
        channel: int, optional
            Channel index.

        Returns
        -------
        video: numpy.ndarray
            The video frames.

        Notes
        -----
        The grayscale conversion is based on minian
        https://github.com/denisecailab/minian/blob/f64c456ca027200e19cf40a80f0596106918fd09/minian/utilities.py#LL272C12-L272C12
        """
        if channel != 0:
            raise NotImplementedError(
                f"The {self.extractor_name}Extractor does not currently support multiple color channels."
            )

        end_frame = end_frame or self.get_num_frames()
        start_frame = start_frame or 0

        video = np.empty(shape=(end_frame - start_frame, *self.get_image_size()), dtype=self.get_dtype())
        with self._video_capture(file_path=str(self.file_path)) as video_obj:
            # Set the starting frame position
            video_obj.current_frame = start_frame
            for frame_number in range(end_frame - start_frame):
                frame = next(video_obj)
                video[frame_number] = self._cv2.cvtColor(frame, self._cv2.COLOR_RGB2GRAY)

        return video


class MiniscopeImagingInterface(BaseImagingExtractorInterface):
    """Data Interface for MiniscopeImagingExtractor."""

    Extractor = MiniscopeImagingExtractor
    display_name = "Miniscope Imaging"
    associated_suffixes = (".avi", ".csv", ".json")
    info = "Interface for Miniscope imaging data."

    @classmethod
    def get_source_schema(cls) -> dict:
        source_schema = super().get_source_schema()
        source_schema["properties"]["folder_path"][
            "description"
        ] = "The folder where the Miniscope videos are contained"

        return source_schema

    @validate_call
    def __init__(self, folder_path: DirectoryPath):
        """
        Initialize reading the Miniscope imaging data.

        Parameters
        ----------
        folder_path : DirectoryPath
            The folder where the Miniscope videos are contained. The video files are expected to be in folder_path

        """
        from ndx_miniscope.utils import get_recording_start_times, read_miniscope_config

        super().__init__(folder_path=folder_path)

        self.miniscope_folder = Path(folder_path)
        # This contains the general metadata and might contain behavioral videos
        self.session_folder = self.miniscope_folder.parent

        self._miniscope_config = read_miniscope_config(folder_path=self.miniscope_folder)

        # use the frame rate of the json configuration to set the metadata
        frame_rate_string = self._miniscope_config["frameRate"]
        # frame_rate_string look like "30.0FPS", extract the float part
        self._metadata_frame_rate = float(frame_rate_string.split("FPS")[0])

        self.photon_series_type = "OnePhotonSeries"

    def get_metadata(self) -> DeepDict:
        from neuroconv.tools.roiextractors import get_nwb_imaging_metadata

        metadata = super().get_metadata()
        default_metadata = get_nwb_imaging_metadata(self.imaging_extractor, photon_series_type=self.photon_series_type)
        metadata = dict_deep_update(metadata, default_metadata)
        metadata["Ophys"].pop("TwoPhotonSeries", None)

        session_start_time = get_session_start_time(folder_path=self.session_folder)

        metadata["NWBFile"].update(session_start_time=session_start_time)

        device_metadata = metadata["Ophys"]["Device"][0]
        miniscope_config = deepcopy(self._miniscope_config)
        miniscope_config.pop("name")
        description = (
            "The Miniscope is the head-mounted miniature microscope part of the UCLA Miniscope imaging platform."
        )
        device_metadata.update(description=description, **miniscope_config)
        # Add link to Device for ImagingPlane
        imaging_plane_metadata = metadata["Ophys"]["ImagingPlane"][0]
        imaging_plane_metadata.update(imaging_rate=self._metadata_frame_rate)
        one_photon_series_metadata = metadata["Ophys"]["OnePhotonSeries"][0]
        one_photon_series_metadata.update(unit="px")

        return metadata

    def get_metadata_schema(self) -> dict:
        metadata_schema = super().get_metadata_schema()
        metadata_schema["properties"]["Ophys"]["definitions"]["Device"]["additionalProperties"] = True
        return metadata_schema

    def get_original_timestamps(self) -> np.ndarray:
        timestamps_seconds = get_miniscope_timestamps(miniscope_folder_path=self.miniscope_folder)
        # Shift when the first timestamp is negative
        # TODO: Figure why, I copied from Miniscope. Need to shift also session_start_time
        if timestamps_seconds[0] < 0.0:
            timestamps_seconds += abs(timestamps_seconds[0])

        return timestamps_seconds

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        photon_series_type: Literal["TwoPhotonSeries", "OnePhotonSeries"] = "OnePhotonSeries",
        photon_series_index: int = 0,
        stub_test: bool = False,
        stub_frames: int = 100,
    ):
        from ndx_miniscope.utils import add_miniscope_device

        from neuroconv.tools.roiextractors import add_photon_series_to_nwbfile

        miniscope_timestamps = self.get_original_timestamps()
        imaging_extractor = self.imaging_extractor

        if stub_test:
            stub_frames = min([stub_frames, self.imaging_extractor.get_num_frames()])
            imaging_extractor = self.imaging_extractor.frame_slice(start_frame=0, end_frame=stub_frames)
            miniscope_timestamps = miniscope_timestamps[:stub_frames]

        imaging_extractor.set_times(times=miniscope_timestamps)

        device_metadata = metadata["Ophys"]["Device"][0]
        # Cast to string because Miniscope extension requires so
        device_metadata["gain"] = str(device_metadata["gain"])
        device_metadata.pop("ewl")
        add_miniscope_device(nwbfile=nwbfile, device_metadata=device_metadata)

        add_photon_series_to_nwbfile(
            imaging=imaging_extractor,
            nwbfile=nwbfile,
            metadata=metadata,
            photon_series_type=photon_series_type,
            photon_series_index=photon_series_index,
        )
