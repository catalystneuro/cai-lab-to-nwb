"""Primary script to run to convert an entire session for of data using the NWBConverter."""

import time
from natsort import natsorted
from pathlib import Path
from typing import Union
from neuroconv.utils import load_dict_from_file, dict_deep_update

from zaki_2024_nwbconverter import Zaki2024NWBConverter


def session_to_nwb(
    data_dir_path: Union[str, Path],
    output_dir_path: Union[str, Path],
    subject_id: str,
    stub_test: bool = False,
    verbose: bool = True,
):

    if verbose:
        print(f"Converting week-long session")
        start = time.time()

    data_dir_path = Path(data_dir_path)
    output_dir_path = Path(output_dir_path)
    if stub_test:
        output_dir_path = output_dir_path / "nwb_stub"
    output_dir_path.mkdir(parents=True, exist_ok=True)

    nwbfile_path = output_dir_path / f"{subject_id}_week_session.nwb"

    source_data = dict()
    conversion_options = dict()

    # Add EEG, EMG, Temperature and Activity signals
    edf_folder_path = data_dir_path / "Ca_EEG_EDF" / (subject_id + "_EDF")
    edf_file_paths = natsorted(edf_folder_path.glob("*.edf"))
    assert edf_file_paths, f"No .edf files found in {edf_folder_path}"

    source_data.update(
        dict(
            MultiEDFSignals=dict(
                file_paths=edf_file_paths,
            )
        )
    )
    conversion_options.update(dict(MultiEDFSignals=dict(stub_test=stub_test)))

    # Add Cross session cell registration
    main_folder = data_dir_path / f"Ca_EEG_Calcium/{subject_id}/SpatialFootprints"
    file_paths = []

    for folder in main_folder.iterdir():
        if folder.is_dir():  # Ensure it's a directory
            filename = folder.name.split("_")[0] + f"_{subject_id}_" + folder.name.split("_")[-1]
            csv_file = folder / f"{filename}.csv"
            if csv_file.is_file():  # Check if the file exists
                file_paths.append(csv_file)

    source_data.update(dict(CellRegistration=dict(file_paths=file_paths)))
    conversion_options.update(dict(CellRegistration=dict(stub_test=stub_test, subject_id=subject_id)))

    converter = Zaki2024NWBConverter(source_data=source_data)

    # Add datetime to conversion
    metadata = converter.get_metadata()

    from mne.io import read_raw_edf

    edf_reader = read_raw_edf(input_fname=edf_file_paths[0], verbose=verbose)
    session_start_time = edf_reader.info["meas_date"]
    metadata["NWBFile"]["session_start_time"] = session_start_time

    # Update default metadata with the editable in the corresponding yaml file
    editable_metadata_path = Path(__file__).parent / "zaki_2024_metadata.yaml"
    editable_metadata = load_dict_from_file(editable_metadata_path)
    metadata = dict_deep_update(metadata, editable_metadata)

    metadata["Subject"]["subject_id"] = subject_id

    # Run conversion
    converter.run_conversion(
        metadata=metadata, nwbfile_path=nwbfile_path, conversion_options=conversion_options, overwrite=True
    )

    if verbose:
        stop_time = time.time()
        conversion_time_seconds = stop_time - start
        if conversion_time_seconds <= 60 * 3:
            print(f"Conversion took {conversion_time_seconds:.2f} seconds")
        elif conversion_time_seconds <= 60 * 60:
            print(f"Conversion took {conversion_time_seconds / 60:.2f} minutes")
        else:
            print(f"Conversion took {conversion_time_seconds / 60 / 60:.2f} hours")


if __name__ == "__main__":

    # Parameters for conversion
    data_dir_path = Path("D:/")
    output_dir_path = Path("D:/cai_lab_conversion_nwb/")
    subject_id = "Ca_EEG3-4"
    stub_test = False
    session_to_nwb(
        data_dir_path=data_dir_path,
        output_dir_path=output_dir_path,
        stub_test=stub_test,
        subject_id=subject_id,
    )
