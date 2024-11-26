"""Primary class for converting experiment-specific cell registration output."""

from neuroconv.basedatainterface import BaseDataInterface
from neuroconv.utils import DeepDict
from typing import Optional
from pathlib import Path
from pynwb import NWBFile
from hdmf.common.table import DynamicTable, VectorData

import pandas as pd


class Zaki2024CellRegistrationInterface(BaseDataInterface):
    """Adds a table to store the output of CellReg."""

    keywords = ["cross sessions cell registration"]

    def __init__(self, file_paths: list[Path], verbose: bool = False):

        self.verbose = verbose
        self.file_paths = file_paths
        super().__init__(file_paths=file_paths)

    def get_metadata(self) -> DeepDict:
        # Automatically retrieve as much metadata as possible from the source files available
        metadata = super().get_metadata()

        return metadata

    def add_to_nwbfile(
        self,
        nwbfile: NWBFile,
        subject_id: str,
        stub_test: bool = False,
        metadata: Optional[dict] = None,
    ):
        processing_module = nwbfile.create_processing_module(
            name="cell_registration",
            description="Processing module for cross session cell registration. "
            "Cells recorded across sessions were cross-registered using a previously published open-source "
            "cross-registration algorithm, CellReg, using the spatial correlations of nearby cells to "
            "determine whether highly correlated footprints close in space are likely to be the same cell across sessions."
            "Each offline recording was cross-registered with all the encoding and recall sessions, "
            "but not with the other offline sessions because cross-registering between all sessions would lead to too many conflicts and, "
            "therefore, to no cells cross-registered across all sessions."
            "Each table represents the output of the cross-registration between one offline sessions and all the encoding and recall sessions. "
            "A table maps the global ROI ids (row of the table) to the ROI ids in each of cross-registered session's plane segmentation.",
        )

        for file_path in self.file_paths:
            offline_session_name = Path(file_path).stem.split(f"{subject_id}_")[-1]
            name = offline_session_name + "vsConditioningSessions"
            data = pd.read_csv(file_path)

            columns = [
                VectorData(
                    name=col,
                    description=f"ROI indexes of plane segmentation of session {col}",
                    data=data[col].tolist()[:100] if stub_test else data[col].tolist(),
                )
                for col in data.columns
            ]

            dynamic_table = DynamicTable(
                name=name,
                description="Table maps the global ROI ids (row of the table) to the ROI ids in each of cross-registered session's plane segmentation."
                "The column names refer to the cross-registered session's ids"
                "The values -9999 indicates no correspondence. ",
                columns=columns,
            )

            processing_module.add(dynamic_table)
