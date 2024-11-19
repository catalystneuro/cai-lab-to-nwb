"""Primary NWBConverter class for this dataset."""

from neuroconv import NWBConverter
from pynwb import NWBFile
from neuroconv.datainterfaces import VideoInterface
from typing import Optional
from pathlib import Path

from interfaces import (
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
