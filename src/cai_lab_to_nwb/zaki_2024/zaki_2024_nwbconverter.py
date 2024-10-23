"""Primary NWBConverter class for this dataset."""
from neuroconv import NWBConverter
# from neuroconv.datainterfaces import MinianSegmentationInterface
from .interfaces import (MinianSegmentationInterface, Zaki2024EDFInterface, EzTrackFreezingBehaviorInterface,
                         Zaki2024SleepClassificationInterface)


class Zaki2024NWBConverter(NWBConverter):
    """Primary conversion class for my extracellular electrophysiology dataset."""

    data_interface_classes = dict(
        MinianSegmentation=MinianSegmentationInterface,
        SleepClassification = Zaki2024SleepClassificationInterface,
        EDFSignals = Zaki2024EDFInterface,
        FreezingBehavior = EzTrackFreezingBehaviorInterface,
    )
