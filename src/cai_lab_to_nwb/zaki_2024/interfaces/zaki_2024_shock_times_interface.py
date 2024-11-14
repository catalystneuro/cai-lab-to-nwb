"""Primary class for converting experiment-specific behavior."""

from pynwb.file import NWBFile

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from typing import Optional, List
from pynwb.epoch import TimeIntervals


class Zaki2024ShockTimesInterface(BaseDataInterface):
    """Adds annotated events of shock times."""

    keywords = ["behavior", "sleep stages"]

    def __init__(self, verbose: bool = False):

        self.verbose = verbose
        super().__init__()

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        shock_amplitude: float,
        shock_times: List = [120, 180, 240],
        shock_duration: float = 2.0,
        metadata: Optional[dict] = None,
    ):

        description = (
            "During aversive encoding, after a baseline period of 2 min, mice received three 2 s foot shocks "
            "of either amplitude 0.25 mA (low-shock) or 1.5 mA (high-shock), with an intershock interval of 1 min. "
            "All testing was done in Med Associates chambers. "
        )

        shock_stimuli = TimeIntervals(name="ShockStimuli", description=description)
        column_description = "Shock amplitude in mA"
        shock_stimuli.add_column(name="shock_amplitude", description=column_description)
        for start_time in shock_times:
            shock_stimuli.add_interval(
                start_time=start_time, stop_time=start_time + shock_duration, shock_amplitude=shock_amplitude
            )

        nwbfile.add_time_intervals(shock_stimuli)
