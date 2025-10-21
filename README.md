# cai-lab-to-nwb
NWB conversion scripts for Cai lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation

To use this conversion package, you'll need to install it directly from GitHub. This approach allows you to access the latest features and modify the source code if needed to adapt to your specific experimental requirements.

### Prerequisites

Before installation, ensure you have the following tools installed:
- `git` ([installation instructions](https://github.com/git-guides/install-git))
- `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) - recommended for managing dependencies

### Installation Steps

From a terminal (note that conda should install one in your system) you can do the following:

```bash
git clone https://github.com/catalystneuro/cai-lab-to-nwb
cd cai-lab-to-nwb
conda env create --file make_env.yml
conda activate cai_lab_to_nwb_env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries. We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

If you fork this repository and are running code from that fork, instead use:

```bash
git clone https://github.com/your_github_username/cai-lab-to-nwb
```

Alternatively, if you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```bash
git clone https://github.com/catalystneuro/cai-lab-to-nwb
cd cai-lab-to-nwb
pip install --editable .
```

Note: both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs). The dependencies for this environment are stored in the dependencies section of the `pyproject.toml` file.

## Repository structure
Each conversion is organized in a directory of its own in the `src` directory:

```
cai-lab-to-nwb/
├── LICENSE
├── make_env.yml
├── pyproject.toml
├── README.md
├── dandi_upload.md
├── requirements.txt
├── setup.py
└── src
    └── cai_lab_to_nwb
        ├── another_conversion
        └── zaki_2024
            ├── interfaces
            │   ├── __init__.py
            │   ├── eztrack_interface.py
            │   ├── minian_interface.py
            │   ├── miniscope_imaging_interface.py
            │   ├── zaki_2024_cell_registration_interface.py
            │   ├── zaki_2024_edf_interface.py
            │   ├── zaki_2024_shock_stimuli_interface.py
            │   └── zaki_2024_sleep_classification_interface.py
            ├── notes
            │   ├── zaki_2024_notes.md
            │   └── ... .png
            ├── tutorials
            │   ├── zaki_2024_tutorial.md
            │   └── ... .png
            ├── utils
            │   ├── __init__.py
            │   ├── conversion_parameters.yaml
            │   ├── define_conversion_parameters.py
            │   ├── edf_slicing.py
            │   ├── generate_session_description.py
            │   └── source_data_path_resolver.py
            ├── __init__.py
            ├── zaki_2024_convert_all_sessions.py
            ├── zaki_2024_convert_session.py
            ├── zaki_2024_convert_week_session.py
            ├── zaki_2024_metadata.yaml
            └── zaki_2024_run_conversion.ipynb
```

 For example, for the conversion `zaki_2024` you can find a directory located in `src/cai-lab-to-nwb/zaki_2024`. Inside each conversion directory you can find the following files:

* `zaki_2024_convert_session.py`: this script defines the function to convert one full session of the conversion.
* `zaki_2024_convert_week_session.py`: this script defines the function to convert a week-long experimental session into an NWB file.
* `zaki_2024_convert_all_sessions.py`: this script defines the function to perform a batch conversion of a set of sessions. The conversion parameters of each session needs to be defined in `utils/conversion_parameters.yaml`
* `zaki_2024_nwbconverter.py`: the place where the `NWBConverter` class is defined.
* `zaki_2024_metadata.yaml`: YAML file containing experimental metadata for the session.
* `zaki_2024_run_conversion.ipynb`: notebook with tutorial on how to run the conversion.
* `notes/zaki_2024_notes.md`: notes and comments concerning this specific conversion.
* `interfaces/`: directory containing the interface classes for this specific conversion.
* `tutorials/`: directory containing tutorials for this specific conversion.
* `utils/`: directory containing utility functions for this specific conversion.


### Notes on the conversion

The conversion notes is located in `src/cai_lab_to_nwb/zaki_2024/notes/zaki_2024_notes.md`.
This file contains information about the expected file structure and the conversion process.

### Running a NWB conversion for zaki_2024 dataset

For detailed documentation on how to run NWB conversion for zaki_2024 dataset see
[`zaki_2024_run_conversion.ipynb`](src/cai_lab_to_nwb/zaki_2024/zaki_2024_run_conversion.ipynb)


## NWB tutorials

The `tutorials` directory contains Jupyter notebooks that demonstrate how to read the NWB files generated by the conversion scripts.
The notebooks are located in the `src/cai_lab_to_nwb/zaki_2024/tutorials` directory.

You might need to install `jupyter` before running the notebooks:

```
pip install jupyter
cd src/cai_lab_to_nwb/zaki_2024/tutorials
jupyter lab
```

## Upload to the DANDI Archive

Detailed instructions on how to upload the data to the DANDI archive can be found [here](dandi_upload.md).

## Customizing for New Datasets

To create a new conversion or adapt this one for different experimental paradigms:

### 1. Create a New Dataset Directory

Follow the naming convention and create a new directory under `src/cai_lab_to_nwb/`:

```bash
mkdir src/cai_lab_to_nwb/new_experiment_2025
```

### 2. Implement Dataset-Specific Interfaces

Create custom interfaces inheriting from existing ones:

```python
from neuroconv.datainterfaces import BaseDataInterface

class CustomInterface(BaseDataInterface):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_to_nwbfile(self, nwbfile, metadata, **kwargs):
        # Custom processing logic
        super().add_to_nwbfile(nwbfile, metadata, **kwargs)
```

### 3. Create an NWBConverter Class

Combine all interfaces for your dataset:

```python
from neuroconv import NWBConverter

class NewExperimentNWBConverter(NWBConverter):
    data_interface_classes = dict(
        Behavior=CustomInterface,
        Video=ExternalVideoInterface,
        # Add other interfaces as needed
    )
```

### 4. Write Conversion Scripts

Create scripts for single sessions and batch processing following the established patterns.

### 5. Create Metadata Files

Develop YAML metadata files with dataset-specific experimental parameters:

```yaml
NWBFile:
  experiment_description: "Description of your new experiment"
  institution: "Your Institution"
  lab: "Your Lab"

Subject:
  species: "Mus musculus"
  # Add subject-specific metadata

# Add other experimental metadata
```

Each conversion should be self-contained within its directory and follow the established patterns for consistency and maintainability.

## Troubleshooting

### Performance Optimization

- Use `stub_test=True` for initial testing with small data subsets
- Process sessions in parallel for large datasets
- Consider using SSD storage for faster I/O operations
- Monitor memory usage for large video files

### Getting Help

For issues specific to this conversion:
1. Check the `notes.md` file in the conversion directory
2. Review the metadata YAML files for parameter examples
3. Examine the conversion scripts for usage patterns

For general neuroconv issues:
- Visit the [neuroconv documentation](https://neuroconv.readthedocs.io/)
- Check the [neuroconv GitHub repository](https://github.com/catalystneuro/neuroconv)

## Citation

If you use this conversion in your research, please cite:

- The original experimental work (add appropriate citation)
- [NeuroConv](https://github.com/catalystneuro/neuroconv)
- [NWB](https://www.nwb.org/)

## License

This project is licensed under the terms specified in the LICENSE file.