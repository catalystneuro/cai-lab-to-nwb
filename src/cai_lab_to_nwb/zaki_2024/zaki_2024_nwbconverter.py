"""Primary NWBConverter class for this dataset."""

from neuroconv import NWBConverter

from neuroconv.datainterfaces import VideoInterface

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
