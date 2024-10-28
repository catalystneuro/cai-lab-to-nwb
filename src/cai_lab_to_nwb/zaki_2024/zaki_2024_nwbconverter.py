"""Primary NWBConverter class for this dataset."""

from fontTools.misc.cython import returns
from pynwb import NWBFile
from typing import Optional

from neuroconv import NWBConverter

from neuroconv.datainterfaces import VideoInterface

from utils import add_motion_correction, load_motion_correction_data

from interfaces import (
    MinianSegmentationInterface,
    Zaki2024EDFInterface,
    EzTrackFreezingBehaviorInterface,
    Zaki2024SleepClassificationInterface,
    MiniscopeImagingInterface,
    MinianMotionCorrectionInterface,
)


class Zaki2024NWBConverter(NWBConverter):
    """Primary conversion class Cai Lab dataset."""

    data_interface_classes = dict(
        MiniscopeImaging=MiniscopeImagingInterface,
        MinianSegmentation=MinianSegmentationInterface,
        MinianMotionCorrection=MinianMotionCorrectionInterface,
        SleepClassification=Zaki2024SleepClassificationInterface,
        EDFSignals=Zaki2024EDFInterface,
        FreezingBehavior=EzTrackFreezingBehaviorInterface,
        Video=VideoInterface,
    )


"""
    # TODO decide which datastream set the session start time
    def get_metadata(self) -> DeepDict:
        if "" not in self.data_interface_objects:
            return super().get_metadata()

        # Explicitly set session_start_time to ... start time
        metadata = super().get_metadata()
        session_start_time = self.data_interface_objects[""]
        metadata["NWBFile"]["session_start_time"] = session_start_time

        return metadata
    
    # TODO Add cell global_ids
    def add_to_nwbfile(self, nwbfile: NWBFile, metadata, conversion_options: Optional[dict] = None) -> None:
        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, conversion_options=conversion_options)

        if "MinianSegmentation" in self.data_interface_objects:
            global_roi_ids = get_global_ids_from_csv()
            add_cell_registration(
                nwbfile=nwbfile,
                global_roi_ids=global_roi_ids,
                plane_segmentation_name="PlaneSegmentation",
            )

    # TODO discuss time alignment with author
    def temporally_align_data_interfaces(self):
        aligned_starting_time = 0
        if "MiniscopeImaging" in self.data_interface_classes:
            miniscope_interface = self.data_interface_classes["MiniscopeImaging"]
            miniscope_interface.set_aligned_starting_time(aligned_starting_time=aligned_starting_time)
        if "MinianSegmentation" in self.data_interface_classes:
            minian_interface = self.data_interface_classes["MinianSegmentation"]
            minian_interface.set_aligned_starting_time(aligned_starting_time=aligned_starting_time)
"""
