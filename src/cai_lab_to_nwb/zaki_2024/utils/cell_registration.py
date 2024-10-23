from neuroconv.tools import get_module
from pynwb import NWBFile
import pandas as pd
from roiextractors.extraction_tools import PathType


def add_cell_registration(
    nwbfile: NWBFile,
    global_roi_ids: list,
    plane_segmentation_name: str,
) -> None:
    """Add cell registration data to the NWBFile.

    The global roi ids for the segmentation data (identified by 'plane_segmentation_name' are added to the NWBFile as
    an extra column of the PlaneSegmentation table).

    Parameters
    ----------
    nwbfile: NWBFile
        The NWBFile where the motion correction time series will be added to.
    global_roi_ids: list
        global roi ids for the segmentation data.
    plane_segmentation_name: str
        The name of the plane segmentation table in the NWBFile.
    """
    ophys = get_module(nwbfile, "ophys")
    assert (
        plane_segmentation_name in ophys["ImageSegmentation"].plane_segmentations.keys()
    ), f"The plane segmentation '{plane_segmentation_name}' does not exist in the NWBFile."

    plane_segmentation = ophys["ImageSegmentation"][plane_segmentation_name]
    plane_segmentation.add_column(
        name="global_ids",
        description="list of global ids of identified cells registered cross sessions",
        data=global_roi_ids,
    )


def get_global_ids_from_csv(
    file_path: PathType,
    session_id: str,
):
    df = pd.read_csv(file_path)
    # TODO discuss with Joe how to identify global ids
