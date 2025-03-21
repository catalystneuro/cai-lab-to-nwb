# cai-lab-to-nwb
NWB conversion scripts for Cai lab data to the [Neurodata Without Borders](https://nwb-overview.readthedocs.io/) data format.

## Installation from Github
We recommend installing this package directly from Github. This option has the advantage that the source code can be modifed if you need to amend some of the code we originally provided to adapt to future experimental differences.
To install the conversion from GitHub you will need to use `git` ([installation instructions](https://github.com/git-guides/install-git)). We also recommend the installation of `conda` ([installation instructions](https://docs.conda.io/en/latest/miniconda.html)) as it contains
all the required machinery in a single and simple install.

From a terminal (note that conda should install one in your system) you can do the following:

```
git clone https://github.com/catalystneuro/cai-lab-to-nwb
cd cai-lab-to-nwb
conda env create --file make_env.yml
conda activate cai_lab_to_nwb_env
```

This creates a [conda environment](https://docs.conda.io/projects/conda/en/latest/user-guide/concepts/environments.html) which isolates the conversion code from your system libraries.  We recommend that you run all your conversion related tasks and analysis from the created environment in order to minimize issues related to package dependencies.

Alternatively, if you want to avoid conda altogether (for example if you use another virtual environment tool) you can install the repository with the following commands using only pip:

```
git clone https://github.com/catalystneuro/cai-lab-to-nwb
cd cai-lab-to-nwb
pip install -e .
```

Note:
both of the methods above install the repository in [editable mode](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs).

### Installing conversion specific dependencies

To install *all* the conversion specific dependencies you can run the following command:

```
pip install -r frozen_dependencies.txt
```

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
            ├── zaki_2024_nwbconverter.py
            ├── zaki_2024_requirements.txt
            └── zaki_2024_run_conversion.ipynb
```

 For example, for the conversion `zaki_2024` you can find a directory located in `src/cai-lab-to-nwb/zaki_2024`. Inside each conversion directory you can find the following files:

* `zaki_2024_convert_sesion.py`: this script defines the function to convert one full session of the conversion.
* `zaki_2024_requirements.txt`: dependencies specific to this conversion.
* `zaki_2024_nwbconverter.py`: the place where the `NWBConverter` class is defined.
* `notes/zaki_2024_notes.md`: notes and comments concerning this specific conversion.
* `interfaces/`: directory containing the interface classes for this specific conversion.
* `tutorials/`: directory containing tutorials for this specific conversion.
* `utils/`: directory containing utility functions for this specific conversion.

The directory might contain other files that are necessary for the conversion but those are the central ones.

### Notes on the conversion

The conversion notes is located in `src/cai_lab_to_nwb/zaki_2024/notes/zaki_2024_notes.md`.
This file contains information about the expected file structure and the conversion process.

### Running a specific conversion

Once you have installed the package with pip, you can run any of the conversion scripts in a notebook or a python file.

You can run a specific conversion with the following command:
```
python src/cai_lab_to_nwb/zaki_2024/zaki_2024_convert_session.py
```

## NWB tutorials

The `tutorials` directory contains Jupyter notebooks that demonstrate how to use the NWB files generated by the conversion scripts.
The notebooks are located in the `src/cai_lab_to_nwb/zaki_2024/tutorials` directory.

You might need to install `jupyter` before running the notebooks:

```
pip install jupyter
cd src/cai_lab_to_nwb/zaki_2024/tutorials
jupyter lab
```

## Upload to the DANDI Archive

Detailed instructions on how to upload the data to the DANDI archive can be found [here](dandi.md).