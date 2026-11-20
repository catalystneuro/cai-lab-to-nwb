"""Tests of the timestamps of the Miniscope imaging data, on a small made-up Miniscope recording."""

import json
from datetime import datetime, timedelta, timezone

import cv2
import numpy as np
import pandas as pd
import pytest
from numpy.testing import assert_allclose, assert_array_equal
from pynwb import NWBFile

from cai_lab_to_nwb.zaki_2024.interfaces import MiniscopeImagingInterface
from cai_lab_to_nwb.zaki_2024.zaki_2024_nwbconverter import Zaki2024NWBConverter

NUM_VIDEOS = 2
FRAMES_PER_VIDEO = 6
NUM_FRAMES = NUM_VIDEOS * FRAMES_PER_VIDEO
AVI_HEADER_FRAME_RATE = 60.0  # the header of the .avi files does not hold the acquisition frame rate
RECORDING_START_TIME = datetime(2021, 10, 12, 10, 44, 18, 744000)

# Measured timestamps in milliseconds of a recording at about 30 frames per second, with one dropped frame.
INTERVALS_MS = np.array([35, 32, 34, 33, 33, 67, 33, 34, 32, 34, 33])
TIMESTAMPS_MS_FROM_ZERO = np.concatenate([[0], np.cumsum(INTERVALS_MS)])


def make_miniscope_folder(session_folder_path, timestamps_ms=None):
    """Write a Miniscope recording (.avi files, metaData.json and timeStamps.csv) and return the Miniscope folder."""
    miniscope_folder_path = session_folder_path / "Miniscope"
    miniscope_folder_path.mkdir(parents=True)

    session_metadata = dict(
        miniscopes=["Miniscope"],
        recordingStartTime=dict(
            year=RECORDING_START_TIME.year,
            month=RECORDING_START_TIME.month,
            day=RECORDING_START_TIME.day,
            hour=RECORDING_START_TIME.hour,
            minute=RECORDING_START_TIME.minute,
            second=RECORDING_START_TIME.second,
            msec=RECORDING_START_TIME.microsecond // 1000,
        ),
    )
    with open(session_folder_path / "metaData.json", "w") as f:
        json.dump(session_metadata, f)

    miniscope_metadata = dict(
        deviceName="Miniscope",
        deviceType="Miniscope_V4_BNO",
        compression="FFV1",
        ewl=0,
        frameRate="30FPS",
        framesPerFile=FRAMES_PER_VIDEO,
        gain="High",
        led0=10,
    )
    with open(miniscope_folder_path / "metaData.json", "w") as f:
        json.dump(miniscope_metadata, f)

    width, height = 16, 12
    for video_index in range(NUM_VIDEOS):
        writer = cv2.VideoWriter(
            str(miniscope_folder_path / f"{video_index}.avi"),
            cv2.VideoWriter_fourcc(*"MJPG"),
            AVI_HEADER_FRAME_RATE,
            (width, height),
        )
        assert writer.isOpened()
        for frame_index in range(FRAMES_PER_VIDEO):
            writer.write(np.full((height, width, 3), 10 * (video_index * FRAMES_PER_VIDEO + frame_index), "uint8"))
        writer.release()

    if timestamps_ms is not None:
        timestamps_table = pd.DataFrame(
            {
                "Frame Number": np.arange(len(timestamps_ms)),
                "Time Stamp (ms)": timestamps_ms,
                "Buffer Index": np.zeros(len(timestamps_ms), dtype=int),
            }
        )
        timestamps_table.to_csv(miniscope_folder_path / "timeStamps.csv", index=False)

    return miniscope_folder_path


def get_written_timestamps(interface: MiniscopeImagingInterface) -> np.ndarray:
    """Add the imaging data to a new NWBFile and return the timestamps of the OnePhotonSeries."""
    nwbfile = NWBFile(
        session_description="test",
        identifier="test",
        session_start_time=RECORDING_START_TIME.replace(tzinfo=timezone.utc),
    )
    interface.add_to_nwbfile(nwbfile=nwbfile, metadata=interface.get_metadata())
    one_photon_series = nwbfile.acquisition["OnePhotonSeries"]
    assert one_photon_series.rate is None
    return np.asarray(one_photon_series.timestamps)


@pytest.mark.parametrize("first_timestamp_ms", [0, 12])
def test_measured_timestamps_are_used_when_the_first_timestamp_is_not_negative(tmp_path, first_timestamp_ms):
    timestamps_ms = TIMESTAMPS_MS_FROM_ZERO + first_timestamp_ms
    miniscope_folder_path = make_miniscope_folder(tmp_path / "session", timestamps_ms=timestamps_ms)
    interface = MiniscopeImagingInterface(folder_path=miniscope_folder_path)
    assert interface.imaging_extractor.get_num_samples() == NUM_FRAMES
    assert interface.imaging_extractor.get_sampling_frequency() == AVI_HEADER_FRAME_RATE

    expected_timestamps = timestamps_ms / 1000.0
    assert_array_equal(interface.get_timestamps(), expected_timestamps)
    assert_array_equal(get_written_timestamps(interface), expected_timestamps)


def test_converter_keeps_measured_timestamps_when_the_first_timestamp_is_not_negative(tmp_path):
    miniscope_folder_path = make_miniscope_folder(tmp_path / "session", timestamps_ms=TIMESTAMPS_MS_FROM_ZERO)
    converter = Zaki2024NWBConverter(source_data=dict(MiniscopeImaging=dict(folder_path=str(miniscope_folder_path))))

    metadata = converter.get_metadata()
    converter.temporally_align_data_interfaces()

    assert metadata["NWBFile"]["session_start_time"] == RECORDING_START_TIME
    interface = converter.data_interface_objects["MiniscopeImaging"]
    assert_array_equal(get_written_timestamps(interface), TIMESTAMPS_MS_FROM_ZERO / 1000.0)


def test_converter_shifts_the_session_start_time_when_the_first_timestamp_is_negative(tmp_path):
    """The session start time moves back and the timestamps move forward, so that no timestamp is negative."""
    first_timestamp_ms = -12
    timestamps_ms = TIMESTAMPS_MS_FROM_ZERO + first_timestamp_ms
    miniscope_folder_path = make_miniscope_folder(tmp_path / "session", timestamps_ms=timestamps_ms)
    converter = Zaki2024NWBConverter(source_data=dict(MiniscopeImaging=dict(folder_path=str(miniscope_folder_path))))

    metadata = converter.get_metadata()
    converter.temporally_align_data_interfaces()

    expected_session_start_time = RECORDING_START_TIME - timedelta(milliseconds=abs(first_timestamp_ms))
    assert metadata["NWBFile"]["session_start_time"] == expected_session_start_time
    interface = converter.data_interface_objects["MiniscopeImaging"]
    written_timestamps = get_written_timestamps(interface)
    assert written_timestamps[0] == 0.0
    assert_allclose(written_timestamps, TIMESTAMPS_MS_FROM_ZERO / 1000.0, rtol=0, atol=1e-12)


@pytest.mark.parametrize("num_timestamps", [NUM_FRAMES - 1, NUM_FRAMES + 1])
def test_number_of_timestamps_different_from_number_of_frames_raises(tmp_path, num_timestamps):
    timestamps_ms = np.arange(num_timestamps) * 33
    miniscope_folder_path = make_miniscope_folder(tmp_path / "session", timestamps_ms=timestamps_ms)
    interface = MiniscopeImagingInterface(folder_path=miniscope_folder_path)

    with pytest.raises(ValueError, match=f"has {num_timestamps} timestamps, but the .avi files have {NUM_FRAMES}"):
        interface.get_timestamps()
    with pytest.raises(ValueError, match=f"has {num_timestamps} timestamps, but the .avi files have {NUM_FRAMES}"):
        get_written_timestamps(interface)


def test_missing_timestamps_file_raises(tmp_path):
    miniscope_folder_path = make_miniscope_folder(tmp_path / "session", timestamps_ms=None)
    interface = MiniscopeImagingInterface(folder_path=miniscope_folder_path)

    with pytest.raises(AssertionError, match="Miniscope timestamps file not found"):
        get_written_timestamps(interface)
