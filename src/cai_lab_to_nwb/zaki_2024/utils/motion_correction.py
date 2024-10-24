from typing import List

import numpy as np
from neuroconv.tools import get_module
from pynwb import NWBFile, TimeSeries
from roiextractors.extraction_tools import DtypeType


def add_motion_correction(
    nwbfile: NWBFile,
    motion_correction_series: np.ndarray,
    one_photon_series_name: str,
) -> None:
    """Add motion correction data to the NWBFile.

    The x, y shifts for the imaging data (identified by 'one_photon_series_name' are added to the NWBFile as a TimeSeries.
    The series is added to the 'ophys' processing module.

    Parameters
    ----------
    nwbfile: NWBFile
        The NWBFile where the motion correction time series will be added to.
    motion_correction_series: numpy.ndarray
        The x, y shifts for the imaging data.
    one_photon_series_name: str
        The name of the one photon series in the NWBFile.
    """

    assert (
        one_photon_series_name in nwbfile.acquisition
    ), f"The one photon series '{one_photon_series_name}' does not exist in the NWBFile."
    name_suffix = one_photon_series_name.replace("OnePhotonSeries", "")
    motion_correction_time_series_name = "MotionCorrectionSeries" + name_suffix
    ophys = get_module(nwbfile, "ophys")
    if motion_correction_time_series_name in ophys.data_interfaces:
        raise ValueError(
            f"The motion correction time series '{motion_correction_time_series_name}' already exists in the NWBFile."
        )

    one_photon_series = nwbfile.acquisition[one_photon_series_name]
    num_frames = one_photon_series.data.maxshape[0]
    assert (
        num_frames == motion_correction_series.shape[0]
    ), f"The number of frames for motion correction ({motion_correction_series.shape[0]}) does not match the number of frames ({num_frames}) from the {one_photon_series_name} imaging data."
    xy_translation = TimeSeries(
        name="MotionCorrectionSeries" + name_suffix,
        description=f"The x, y shifts for the {one_photon_series_name} imaging data.",
        data=motion_correction_series.astype(dtype=convert_to_dtype, copy=False),
        unit="px",
        timestamps=one_photon_series.timestamps,
    )
    ophys.add(xy_translation)
