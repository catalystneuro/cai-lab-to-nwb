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
)


class Zaki2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        MiniscopeImaging=MiniscopeImagingInterface,
        MinianSegmentation=MinianSegmentationInterface,
        SleepClassification=Zaki2024SleepClassificationInterface,
        EDFSignals=Zaki2024EDFInterface,
        FreezingBehavior=EzTrackFreezingBehaviorInterface,
        Video=VideoInterface,
    )

    # TODO decide which datastream set the session start time
    # def get_metadata(self) -> DeepDict:
    #     if "" not in self.data_interface_objects:
    #         return super().get_metadata()
    #
    #     # Explicitly set session_start_time to ... start time
    #     metadata = super().get_metadata()
    #     session_start_time = self.data_interface_objects[""]
    #     metadata["NWBFile"]["session_start_time"] = session_start_time
    #
    #     return metadata

    def add_to_nwbfile(self, nwbfile: NWBFile, metadata, conversion_options: Optional[dict] = None) -> None:
        super().add_to_nwbfile(nwbfile=nwbfile, metadata=metadata, conversion_options=conversion_options)

        # Add motion correction
        if "MinianSegmentation" in self.data_interface_objects:
            minian_interface = self.data_interface_objects["MinianSegmentation"]
            minian_folder_path = minian_interface.source_data["folder_path"]
            interface_name = "MiniscopeImaging"
            one_photon_series_name = metadata["Ophys"]["OnePhotonSeries"][0]["name"]

            motion_correction = load_motion_correction_data(minian_folder_path)
            if interface_name in conversion_options:
                if "stub_test" in conversion_options[interface_name]:
                    if conversion_options[interface_name]["stub_test"]:
                        num_frames = 100
                        motion_correction = motion_correction[:num_frames, :]

            add_motion_correction(
                nwbfile=nwbfile,
                motion_correction_series=motion_correction,
                one_photon_series_name=one_photon_series_name,
            )

    # TODO discuss time alignment with author
    # def temporally_align_data_interfaces(self):
    #     aligned_starting_time = 0
    #     if "MiniscopeImaging" in self.data_interface_classes:
    #         miniscope_interface = self.data_interface_classes["MiniscopeImaging"]
    #         miniscope_interface.set_aligned_starting_time(aligned_starting_time=aligned_starting_time)
    #     if "MinianSegmentation" in self.data_interface_classes:
    #         minian_interface = self.data_interface_classes["MinianSegmentation"]
    #         minian_interface.set_aligned_starting_time(aligned_starting_time=aligned_starting_time)
