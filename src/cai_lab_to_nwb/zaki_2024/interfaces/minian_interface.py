import zarr
import warnings
import numpy as np
import pandas as pd
from neuroconv import BaseDataInterface
from neuroconv.tools import get_module

from roiextractors.extraction_tools import PathType, DtypeType, get_package
from neuroconv.datainterfaces.ophys.basesegmentationextractorinterface import BaseSegmentationExtractorInterface
from roiextractors.segmentationextractor import SegmentationExtractor
from roiextractors.imagingextractor import ImagingExtractor

from typing import Optional
from pynwb import NWBFile, TimeSeries
from pynwb.ophys import MotionCorrection, CorrectedImageStack, OnePhotonSeries


class MinianSegmentationExtractor(SegmentationExtractor):
    """A SegmentationExtractor for Minian.

    This class inherits from the SegmentationExtractor class, having all
    its functionality specifically applied to the dataset output from
    the 'Minian' ROI segmentation method.

    Users can extract key information such as ROI traces, image masks,
    and timestamps from the output of the Minian pipeline.

    Key features:
    - Extracts fluorescence traces (denoised, baseline, neuropil, deconvolved) for each ROI.
    - Retrieves ROI masks and background components.
    - Provides access to timestamps corresponding to calcium traces.
    - Retrieves maximum projection image.

    Parameters
    ----------
    folder_path: str
        Path to the folder containing Minian .zarr output files.

    """

    extractor_name = "MinianSegmentation"
    is_writable = True
    mode = "file"

    def __init__(self, folder_path: PathType):
        """Initialize a MinianSegmentationExtractor instance.

        Parameters
        ----------
        folder_path: str
            The location of the folder containing minian .zarr output.
        """
        SegmentationExtractor.__init__(self)
        self.folder_path = folder_path
        self._roi_response_denoised = self._read_trace_from_zarr_field(field="C")
        self._roi_response_baseline = self._read_trace_from_zarr_field(field="b0")
        self._roi_response_neuropil = self._read_trace_from_zarr_field(field="f")
        self._roi_response_deconvolved = self._read_trace_from_zarr_field(field="S")
        self._image_maximum_projection = np.array(self._read_zarr_group("/max_proj.zarr/max_proj"))
        self._image_masks = self._read_roi_image_mask_from_zarr_field()
        self._background_image_masks = self._read_background_image_mask_from_zarr_field()
        self._times = self._read_timestamps_from_csv()

    def _read_zarr_group(self, zarr_group=""):
        """Read the zarr.

        Returns
        -------
        zarr.open
            The zarr object specified by self.folder_path.
        """
        if zarr_group not in zarr.open(str(self.folder_path)):
            warnings.warn(f"Group '{zarr_group}' not found in the Zarr store.", UserWarning)
            return None
        else:
            return zarr.open(str(self.folder_path) + f"/{zarr_group}", "r")

    def _read_roi_image_mask_from_zarr_field(self):
        """Read the image masks from the zarr output.

        Returns
        -------
        image_masks: numpy.ndarray
            The image masks for each ROI.
        """
        dataset = self._read_zarr_group("/A.zarr")
        if dataset is None or "A" not in dataset:
            return None
        else:
            return np.transpose(dataset["A"], (1, 2, 0))

    def _read_background_image_mask_from_zarr_field(self):
        """Read the image masks from the zarr output.

        Returns
        -------
        image_masks: numpy.ndarray
            The image masks for each background components.
        """
        dataset = self._read_zarr_group("/b.zarr")
        if dataset is None or "b" not in dataset:
            return None
        else:
            return np.expand_dims(dataset["b"], axis=2)

    def _read_trace_from_zarr_field(self, field):
        """Read the traces specified by the field from the zarr object.

        Parameters
        ----------
        field: str
            The field to read from the zarr object.

        Returns
        -------
        trace: numpy.ndarray
            The traces specified by the field.
        """
        dataset = self._read_zarr_group(f"/{field}.zarr")

        if dataset is None or field not in dataset:
            return None
        elif dataset[field].ndim == 2:
            return np.transpose(dataset[field])
        elif dataset[field].ndim == 1:
            return np.expand_dims(dataset[field], axis=1)

    def _read_timestamps_from_csv(self):
        """Extract timestamps corresponding to frame numbers of the stored denoised trace

        Returns
        -------
        np.ndarray
            The timestamps of the denoised trace.
        """
        csv_file = self.folder_path / "timeStamps.csv"
        df = pd.read_csv(csv_file)
        frame_numbers = self._read_zarr_group("/C.zarr/frame")
        filtered_df = df[df["Frame Number"].isin(frame_numbers)] * 1e-3

        return filtered_df["Time Stamp (ms)"].to_numpy()

    def get_image_size(self):
        dataset = self._read_zarr_group("/A.zarr")
        height = dataset["height"].shape[0]
        width = dataset["width"].shape[0]
        return (height, width)

    def get_accepted_list(self) -> list:
        """Get a list of accepted ROI ids.

        Returns
        -------
        accepted_list: list
            List of accepted ROI ids.
        """
        return self.get_roi_ids()

    def get_rejected_list(self) -> list:
        """Get a list of rejected ROI ids.

        Returns
        -------
        rejected_list: list
            List of rejected ROI ids.
        """
        return list()

    def get_roi_ids(self) -> list:
        dataset = self._read_zarr_group("/A.zarr")
        return list(dataset["unit_id"])

    def get_traces_dict(self) -> dict:
        """Get traces as a dictionary with key as the name of the ROiResponseSeries.

        Returns
        -------
        _roi_response_dict: dict
            dictionary with key, values representing different types of RoiResponseSeries:
                Raw Fluorescence, DeltaFOverF, Denoised, Neuropil, Deconvolved, Background, etc.
        """
        return dict(
            denoised=self._roi_response_denoised,
            baseline=self._roi_response_baseline,
            neuropil=self._roi_response_neuropil,
            deconvolved=self._roi_response_deconvolved,
        )

    def get_images_dict(self) -> dict:
        """Get images as a dictionary with key as the name of the ROIResponseSeries.

        Returns
        -------
        _roi_image_dict: dict
            dictionary with key, values representing different types of Images used in segmentation:
                Mean, Correlation image
        """
        return dict(
            mean=self._image_mean,
            correlation=self._image_correlation,
            maximum_projection=self._image_maximum_projection,
        )


class MinianSegmentationInterface(BaseSegmentationExtractorInterface):
    """Data interface for MinianSegmentationExtractor."""

    Extractor = MinianSegmentationExtractor
    display_name = "Minian Segmentation"
    associated_suffixes = (".zarr",)
    info = "Interface for Minian segmentation data."

    @classmethod
    def get_source_schema(cls) -> dict:
        source_metadata = super().get_source_schema()
        source_metadata["properties"]["folder_path"]["description"] = "Path to .zarr output."
        return source_metadata

    def __init__(self, folder_path: PathType, verbose: bool = True):
        """

        Parameters
        ----------
        folder_path : PathType
            Path to .zarr path.
        verbose : bool, default True
            Whether to print progress
        """
        super().__init__(folder_path=folder_path)
        self.verbose = verbose

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: Optional[dict] = None,
        stub_test: bool = False,
        stub_frames: int = 100,
        include_background_segmentation: bool = True,
        include_roi_centroids: bool = True,
        include_roi_acceptance: bool = False,
        mask_type: Optional[str] = "image",  # Literal["image", "pixel", "voxel"]
        plane_segmentation_name: Optional[str] = None,
        iterator_options: Optional[dict] = None,
    ):
        super().add_to_nwbfile(
            nwbfile=nwbfile,
            metadata=metadata,
            stub_test=stub_test,
            stub_frames=stub_frames,
            include_background_segmentation=include_background_segmentation,
            include_roi_centroids=include_roi_centroids,
            include_roi_acceptance=include_roi_acceptance,
            mask_type=mask_type,
            plane_segmentation_name=plane_segmentation_name,
            iterator_options=iterator_options,
        )


class _MinianMotionCorrectedVideoExtractor(ImagingExtractor):
    """An auxiliar extractor to get data from a single Minian motion corrected video (.mp4) file.

    This format consists of a single video (.mp4)
    """

    extractor_name = "_MinianMotionCorrectedVideo"

    def __init__(self, file_path: PathType):
        """Create a _MinianMotionCorrectedVideoExtractor instance from a file path.

        Parameters
        ----------
        file_path: PathType
           The file path to the Minian motion corrected video (.mp4) file.
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
        self.frame_width = int(cap.get(self._cv2.CAP_PROP_FRAME_WIDTH) / 2)
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
        return None

    def get_dtype(self) -> DtypeType:
        return self._dtype

    def get_channel_names(self) -> list[str]:
        return ["OpticalChannel"]

    def get_original_timestamps(self, stub_test: bool = False) -> list[np.ndarray]:
        """
        Retrieve the original unaltered timestamps for the data in this interface.

        This function should retrieve the data on-demand by re-initializing the IO.

        Returns
        -------
        timestamps : numpy.ndarray
            The timestamps for the data stream.
        stub_test : bool, default: False
            This method scans through each video; a process which can take some time to complete.

            To limit that scan to a small number of frames, set `stub_test=True`.
        """
        max_frames = 100 if stub_test else None
        with self._video_capture(file_path=str(self.file_path)) as video:
            # fps = video.get_video_fps()  # There is some debate about whether the OpenCV timestamp
            # method is simply returning range(length) / fps 100% of the time for any given format
            timestamps = video.get_video_timestamps(max_frames=max_frames)
        return timestamps

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

                # motion corrected video in minian are saved side by side (right side) with non-corrected video
                # thus we need to extract only the right side of the frames
                video[frame_number] = self._cv2.cvtColor(frame[:, self.frame_width :], self._cv2.COLOR_RGB2GRAY)

        return video


class MinianMotionCorrectionInterface(BaseDataInterface):
    """Data interface for adding the motion corrected image data produced by Minian software."""

    display_name = "MinianMotionCorrection"
    associated_suffixes = (".mp4", ".zarr")
    info = "Interface for motion corrected imaging data produced by Minian software."

    def __init__(self, folder_path: PathType, video_file_path: PathType, verbose: bool = True):
        """
        Interface for motion corrected imaging data produced by Minian software.

        Parameters
        ----------
        folder_path : PathType
            Path to .zarr store (Minian output).
        video_file_path : PathType
            Path to .mp4 video of motion corrected images.
        verbose : bool, default True
            Whether to print progress
        """
        super().__init__(folder_path=folder_path, video_file_path=video_file_path, verbose=verbose)
        self.folder_path = folder_path
        self.video_file_path = video_file_path

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        metadata: dict,
        corrected_image_stack_name: str = "CorrectedImageStack",
        stub_test: bool = False,
    ) -> None:

        # extract xy_shift
        assert "/motion.zarr" in zarr.open(self.folder_path), f"Group '/motion.zarr' not found in the Zarr store."
        dataset = zarr.open(str(self.folder_path) + "/motion.zarr")
        # from zarr field motion.zarr/shift_dim we can verify that the two column refer respectively to
        # ['height','width'] --> ['y','x']. Following best practice we swap the two columns
        xy_shifts = dataset["motion"][:, [1, 0]]

        csv_file = self.folder_path / "timeStamps.csv"
        df = pd.read_csv(csv_file)
        frame_numbers = dataset["frame"]
        filtered_df = df[df["Frame Number"].isin(frame_numbers)] * 1e-3
        timestamps = filtered_df["Time Stamp (ms)"].to_numpy()

        # extract corrected image stack
        extractor = _MinianMotionCorrectedVideoExtractor(file_path=str(self.video_file_path))
        end_frame = 100 if stub_test else None
        motion_corrected_data = extractor.get_video(end_frame=end_frame)

        # add motion correction
        name_suffix = corrected_image_stack_name.replace("CorrectedImageStack", "")
        original_one_photon_series_name = f"OnePhotonSeries{name_suffix}"
        assert (
            original_one_photon_series_name in nwbfile.acquisition
        ), f"The one photon series '{original_one_photon_series_name}' does not exist in the NWBFile."

        original_one_photon_series = nwbfile.acquisition[original_one_photon_series_name]

        xy_translation = TimeSeries(
            name="xy_translation",  # name must be 'xy_translation'
            data=xy_shifts[:end_frame, :],
            description=f"The x, y shifts for the {original_one_photon_series_name} imaging data.",
            unit="px",
            timestamps=timestamps[:end_frame],
        )

        corrected_one_photon_series = OnePhotonSeries(
            name="corrected",  # name must be 'corrected'
            data=motion_corrected_data,
            imaging_plane=original_one_photon_series.imaging_plane,
            timestamps=timestamps[:end_frame],
            unit="n.a.",
        )

        corrected_image_stack = CorrectedImageStack(
            name=corrected_image_stack_name,
            corrected=corrected_one_photon_series,
            original=original_one_photon_series,
            xy_translation=xy_translation,
        )

        ophys = get_module(nwbfile, name="ophys", description="Data processed with MiniAn software")
        if "MotionCorrection" not in ophys.data_interfaces:
            motion_correction = MotionCorrection(name="MotionCorrection")
            ophys.add(motion_correction)
        else:
            motion_correction = ophys.data_interfaces["MotionCorrection"]

        motion_correction.add_corrected_image_stack(corrected_image_stack)
