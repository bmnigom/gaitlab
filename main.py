# File: main.py
import pandas as pd
from pathlib import Path
import yaml
import logging
from gaitlab.utils import discover_subjects
from gaitlab.core import Trial
from gaitlab.analysis import (
    generate_coverage_report,
    calculate_normative_stats,
    calculate_spatiotemporal_stats,
    generate_kinetic_qc_report
)
from gaitlab.plotting import PngPlotter, HtmlPlotter

# --- 1. CONFIGURATION ---
# ⚠️ ACTION: Adjust these paths if needed.
BASE_DIR = Path(r"C:/Users/fx517/Documents/codigo/results/EUROBENCH_RESULTS/c3d_CES/VICON") # Example path
OUTPUT_DIR = Path("./output")
CONFIG_DIR = Path("./config")

def setup_environment():
    """Creates output directories and configures logging."""
    subfolders = ["figures", "tables", "logs", "html"]
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for sf in subfolders:
        (OUTPUT_DIR / sf).mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(OUTPUT_DIR / "logs" / "pipeline.log", mode='w', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main function to run the entire gait analysis pipeline."""
    setup_environment()

    # --- 2. LOAD CONFIGURATION ---
    logging.info("Loading configuration files...")
    with open(CONFIG_DIR / "variables_map.yaml", "r") as f:
        VARS_MAP = yaml.safe_load(f)
    with open(CONFIG_DIR / "plot_layout.yaml", "r") as f:
        LAYOUT_CONFIG = yaml.safe_load(f)

    # --- 3. DISCOVER AND PROCESS TRIALS ---
    logging.info(f"Discovering subjects in: {BASE_DIR}")
    subjects_list, files_by_subject = discover_subjects(BASE_DIR)
    if not subjects_list:
        logging.error("No subjects found. Exiting.")
        return

    logging.info(f"Found {len(subjects_list)} subjects. Starting processing...")

    all_timeseries = []
    all_spatiotemporal = []
    kinetic_qc_records = []

    for subject_id in subjects_list:
        try:
            trial = Trial(subject_id, files_by_subject[subject_id], VARS_MAP)
            if trial.is_valid:
                timeseries = trial.process_time_series()
                if timeseries is not None:
                    all_timeseries.append(timeseries)
                if trial.spatiotemporal_params:
                    all_spatiotemporal.extend(trial.spatiotemporal_params)
                for side, valid in trial.kinetic_valid.items():
                    kinetic_qc_records.append((subject_id, side, valid))
            else:
                logging.warning(f"Skipping {subject_id}: No valid gait cycles identified.")
        except Exception as e:
            logging.error(f"Failed to process {subject_id}: {e}", exc_info=True)

    if not all_timeseries:
        logging.error("Pipeline finished, but no time-series data was processed successfully.")
        return

    master_df = pd.concat(all_timeseries, ignore_index=True)
    spatiotemporal_df = pd.DataFrame(all_spatiotemporal)

    logging.info("--- ✅ Data Processing Complete ---")
    logging.info(f"Total normalized cycles: {len(master_df)}")
    logging.info(f"Total spatiotemporal entries: {len(spatiotemporal_df)}")

    # --- 4. ANALYSIS & REPORTING ---
    logging.info("--- Starting Analysis and Reporting ---")
    generate_coverage_report(master_df, OUTPUT_DIR)
    normative_stats = calculate_normative_stats(master_df, OUTPUT_DIR)
    calculate_spatiotemporal_stats(spatiotemporal_df, OUTPUT_DIR)
    generate_kinetic_qc_report(kinetic_qc_records, OUTPUT_DIR)

    # --- 5. VISUALIZATION ---
    logging.info("--- Starting Visualization ---")
    png_plotter = PngPlotter(LAYOUT_CONFIG, OUTPUT_DIR)
    png_plotter.plot_all_panels(master_df, normative_stats)

    html_plotter = HtmlPlotter(LAYOUT_CONFIG, OUTPUT_DIR)
    html_plotter.plot_all_panels(master_df, normative_stats)

    logging.info("--- ✅ Pipeline Finished Successfully! ---")


if __name__ == "__main__":
    main()