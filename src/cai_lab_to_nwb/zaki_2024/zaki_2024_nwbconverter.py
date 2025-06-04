"""Primary NWBConverter class for this dataset."""

from datetime import timedelta

from neuroconv import NWBConverter
from neuroconv.datainterfaces import VideoInterface
from neuroconv.utils.dict import DeepDict

from cai_lab_to_nwb.zaki_2024.interfaces import (
    MinianSegmentationInterface,
    Zaki2024EDFInterface,
    Zaki2024MultiEDFInterface,
    EzTrackFreezingBehaviorInterface,
    Zaki2024SleepClassificationInterface,
    MiniscopeImagingInterface,
    MinianMotionCorrectionInterface,
    Zaki2024ShockStimuliInterface,
    Zaki2024CellRegistrationInterface,
)


class Zaki2024NWBConverter(NWBConverter):
    """Primary conversion class Cai Lab dataset."""

    data_interface_classes = dict(
        MiniscopeImaging=MiniscopeImagingInterface,
        MinianSegmentation=MinianSegmentationInterface,
        MinianMotionCorrection=MinianMotionCorrectionInterface,
        SleepClassification=Zaki2024SleepClassificationInterface,
        EDFSignals=Zaki2024EDFInterface,
        MultiEDFSignals=Zaki2024MultiEDFInterface,
        FreezingBehavior=EzTrackFreezingBehaviorInterface,
        Video=VideoInterface,
        ShockStimuli=Zaki2024ShockStimuliInterface,
        CellRegistration=Zaki2024CellRegistrationInterface,
    )

    def get_metadata(self) -> DeepDict:
        metadata = super().get_metadata()

        if "MiniscopeImaging" in self.data_interface_objects:
            imaging_interface = self.data_interface_objects["MiniscopeImaging"]
            imaging_timestamps = imaging_interface.get_original_timestamps()
            # If the first timestamp in the imaging data is negative, adjust the session start time
            # to ensure all timestamps are positive. This is done by shifting the session start time
            # backward by the absolute value of the negative timestamp.
            if imaging_timestamps[0] < 0.0:
                time_shift = timedelta(seconds=abs(imaging_timestamps[0]))
                session_start_time = imaging_interface.get_metadata()["NWBFile"]["session_start_time"]
                metadata["NWBFile"].update(session_start_time=session_start_time - time_shift)
        return metadata

    def temporally_align_data_interfaces(self, metadata: dict | None = None, conversion_options: dict | None = None):
        if "MiniscopeImaging" in self.data_interface_objects:
            imaging_interface = self.data_interface_objects["MiniscopeImaging"]
            imaging_timestamps = imaging_interface.get_original_timestamps()
            # Align the starting times of all data interfaces when the imaging data's first timestamp is negative.
            # This is done by calculating a time shift based on the absolute value of the first negative timestamp.
            # The time shift is applied to all relevant data interfaces to ensure temporal alignment.
            if imaging_timestamps[0] < 0.0:
                time_shift = abs(imaging_timestamps[0])
                imaging_interface.set_aligned_timestamps(imaging_timestamps + time_shift)
                if "MinianSegmentation" in self.data_interface_objects:
                    segmentation_interface = self.data_interface_objects["MinianSegmentation"]
                    segmentation_timestamps = segmentation_interface.get_original_timestamps()
                    segmentation_interface.set_aligned_timestamps(segmentation_timestamps + time_shift)

                # if "MinianMotionCorrection" in self.data_interface_objects:
                #     motion_correction_interface = self.data_interface_objects["MinianMotionCorrection"]
                #     motion_correction_timestamps = motion_correction_interface.get_original_timestamps()
                #     motion_correction_interface.set_aligned_timestamps(motion_correction_timestamps + time_shift)

                if "SleepClassification" in self.data_interface_objects:
                    sleep_classification_interface = self.data_interface_objects["SleepClassification"]
                    start_times, stop_times, sleep_states = sleep_classification_interface.get_sleep_states_times()
                    start_times += time_shift
                    stop_times += time_shift
                    sleep_classification_interface.set_aligned_interval_times(
                        start_times=start_times, stop_times=stop_times
                    )
                if "EDFSignals" in self.data_interface_objects:
                    edf_signals_interface = self.data_interface_objects["EDFSignals"]
                    edf_signals_interface.set_aligned_starting_time(time_shift)

                if "FreezingBehavior" in self.data_interface_objects:
                    freezing_behavior_interface = self.data_interface_objects["FreezingBehavior"]
                    start_times, stop_times = freezing_behavior_interface.get_interval_times()
                    start_times += time_shift
                    stop_times += time_shift
                    freezing_behavior_interface.set_aligned_interval_times(
                        start_times=start_times, stop_times=stop_times
                    )
                    starting_time = freezing_behavior_interface.get_starting_time()
                    freezing_behavior_interface.set_aligned_starting_time(starting_time + time_shift)

                if "Video" in self.data_interface_objects:
                    video_interface = self.data_interface_objects["Video"]
                    video_timestamps = video_interface.get_original_timestamps()
                    aligned_video_timestamps = video_timestamps + time_shift
                    video_interface.set_aligned_timestamps(aligned_video_timestamps)
