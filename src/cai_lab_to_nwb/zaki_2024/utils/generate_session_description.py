from pathlib import Path
from typing import Union
import pandas as pd
import re


def generate_session_description(experiment_design_file_path: Union[Path, str], subject_id: str, session_id: str):
    subjects_df = pd.read_excel(experiment_design_file_path)
    subject_df = subjects_df[subjects_df["Mouse"] == subject_id]
    shock_amplitude = subject_df["Amplitude"].to_numpy()[0]
    shock_amplitude = float(re.findall(r"[-+]?\d*\.\d+|\d+", shock_amplitude)[0])

    Contexts = {
        "A": "overhead external light, external fan off, box fan on, smooth floor, white curve insert, simple green 5pct scent",
        "B": "overhead external light, external fan off, box fan on, bath mat floor, A frame insert, ethanol 70pct scent",
        "S": "overhead external light, external fan at medium level, box fan on, even grid floor, acetic acid 1pct scent",
    }

    session_descriptions = {
        "NeutralExposure": f"Neutral Exposure session: mouse was exposed to a neutral context for 10 min to explore. Context: {Contexts["A"]}",
        "FC": f"Fear Conditioning session: after a baseline period of 2 min, mouse received three 2s foot shocks of {shock_amplitude}, with an intershock interval of 1 min. Then, 30 s after the final shock, the mice were removed and returned to the vivarium. Context: {Contexts["S"]}",
        "Recall1": f"First Recall session: mouse was placed in shock context for 5 min. Context: {Contexts['S']}",
        "Recall2": f"Second Recall session: mouse was placed in {subject_df["Test_2"].to_numpy()[0]} context for 5 min. Context: {Contexts[subject_df["Test_2_ctx"].to_numpy()[0]]}",
        "Recall3": f"Third Recall session: mouse was placed in {subject_df["Test_3"].to_numpy()[0]} context for 5 min. Context: {Contexts[subject_df["Test_3_ctx"].to_numpy()[0]]}",
        "Offline": f"After Neutral Exposure and Fear Conditioning sessions, mice were taken out of the testing chambers and immediately placed in their homecage (scope was not removed).The homecage was placed in a dark grey storage bin with a webcam on top of the bin, taped to a wooden plank, looking down into the homecage. Mouse behavior and calcium were recorded for an hour.",
    }
    if "Offline" in session_id:
        session_id = "Offline"

    return session_descriptions[session_id]


if __name__ == "__main__":
    experiment_design_file_path = Path("D:/Ca_EEG_Design.xlsx")
    subject_id = "Ca_EEG3-4"
    session_id = "NeutralExposure"
    session_description = generate_session_description(
        experiment_design_file_path=experiment_design_file_path, subject_id=subject_id, session_id=session_id
    )
    print(session_description)
