"""A SegmentationExtractor for Minian.

Classes
-------
MinianSegmentationExtractor
    A class for extracting segmentation from Minian output.
"""

from pathlib import Path

import zarr
import warnings
import numpy as np
import pandas as pd

from roiextractors.extraction_tools import PathType
from neuroconv.datainterfaces.ophys.basesegmentationextractorinterface import BaseSegmentationExtractorInterface
from roiextractors.segmentationextractor import SegmentationExtractor

from typing import Optional

from pynwb import NWBFile

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
        self._roi_response_denoised = self._read_trace_from_zarr_filed(field="C")
        self._roi_response_baseline = self._read_trace_from_zarr_filed(field="b0")
        self._roi_response_neuropil = self._read_trace_from_zarr_filed(field="f")
        self._roi_response_deconvolved = self._read_trace_from_zarr_filed(field="S")
        self._image_maximum_projection = np.array(self._read_zarr_group("/max_proj.zarr/max_proj"))
        self._image_masks = self._read_roi_image_mask_from_zarr_filed()
        self._background_image_masks = self._read_background_image_mask_from_zarr_filed()
        self._times = self._read_timestamps_from_csv()

    def _read_zarr_group(self, zarr_group=""):
        """Read the zarr.

        Returns
        -------
        zarr.open
            The zarr object specified by self.folder_path.
        """
        if zarr_group not in zarr.open(self.folder_path, mode="r"):
            warnings.warn(f"Group '{zarr_group}' not found in the Zarr store.", UserWarning)
            return None
        else:
            return zarr.open(str(self.folder_path) + f"/{zarr_group}", "r")

    def _read_roi_image_mask_from_zarr_filed(self):
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

    def _read_background_image_mask_from_zarr_filed(self):
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

    def _read_trace_from_zarr_filed(self, field):
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
        return list(range(self.get_num_rois()))

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



