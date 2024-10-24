"""Primary script to run to convert an entire session for of data using the NWBConverter."""
from pathlib import Path
from typing import Union
import datetime
from zoneinfo import ZoneInfo

from neuroconv.utils import load_dict_from_file, dict_deep_update

from zaki_2024_nwbconverter import Zaki2024NWBConverter

def session_to_nwb(data_dir_path: Union[str, Path], output_dir_path: Union[str, Path], subject_id: str, session_id: str,  stub_test: bool = False):

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{session_id}.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add Segmentation
    minian_folder_path = data_dir_path / "Ca_EEG_Calcium" / subject_id / session_id / "minian"
    source_data.update(dict(MinianSegmentation=dict(folder_path=minian_folder_path)))
    conversion_options.update(dict(MinianSegmentation=dict(stub_test=stub_test)))

    converter = Zaki2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()
    datetime.datetime(
        year=2020, month=1, day=1, tzinfo=ZoneInfo("US/Eastern")
    )
    date = datetime.datetime.today()  # TO-DO: Get this from author
    metadata["NWBFile"]["session_start_time"] = date

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "zaki_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.run_conversion(metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options, overwrite=True)


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("D:/")
    subject_id = "Ca_EEG3-4"
    task = "NeutralExposure"
    session_id = subject_id + "_" + task
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    stub_test = False

    session_to_nwb(data_dir_path=data_dir_path,
                    output_dir_path=output_dir_path,
                    stub_test=stub_test,
                   subject_id=subject_id,
                   session_id=session_id
                    )
