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
            name="cell_registration", description="Processing module for cross session cell registration."
        )

        for file_path in self.file_paths:
            offline_session_name = Path(file_path).stem.split(f"{subject_id}_")[-1]
            name = offline_session_name + "vsConditioningSessions"
            data = pd.read_csv(file_path)

            columns = [
                VectorData(
                    name=col,
                    description=f"ROI indexes from segmentation of session {col} imaging data",
                    data=data[col].tolist()[:100] if stub_test else data[col].tolist(),
                )
                for col in data.columns
            ]

            dynamic_table = DynamicTable(
                name=name,
                description=f"Table storing data from cross sessions cell registration: all conditioning sessions are registered with respect to {offline_session_name} ",
                columns=columns,
            )

            processing_module.add(dynamic_table)
