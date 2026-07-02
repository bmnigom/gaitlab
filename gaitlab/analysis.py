# File: gaitlab/analysis.py
import pandas as pd
from pathlib import Path
from typing import List, Tuple
import logging

try:
    display  # provided automatically by Jupyter/IPython
except NameError:
    def display(x):
        """Fallback for running this module outside Jupyter (e.g. via main.py)."""
        print(x)

def generate_coverage_report(master_df: pd.DataFrame, output_dir: Path):
    """Calculates and saves the variable coverage report."""
    logging.info("Calculating variable coverage...")
    coverage = master_df.groupby('canonical_variable')['subject_id'].nunique().reset_index()
    coverage.rename(columns={'subject_id': 'subject_count'}, inplace=True)
    total_subjects = master_df['subject_id'].nunique()
    coverage['coverage_pct'] = (coverage['subject_count'] / total_subjects) * 100

    coverage_path = output_dir / "tables" / "coverage_by_variable.csv"
    coverage.sort_values('coverage_pct', ascending=False).to_csv(coverage_path, index=False)
    logging.info(f"Coverage report saved to {coverage_path}")

    print("\n" + "="*50)
    print("      Top 15 Variables with HIGHEST Coverage")
    print("="*50)
    display(coverage.sort_values('subject_count', ascending=False).head(15))

    print("\n" + "="*50)
    print("      Top 15 Variables with LOWEST Coverage")
    print("="*50)
    display(coverage.sort_values('subject_count', ascending=True).head(15))

def calculate_normative_stats(master_df: pd.DataFrame, output_dir: Path) -> pd.DataFrame:
    """Calculates and saves normative statistics (mean, std) for time-series data."""
    logging.info("Calculating normative statistics...")
    time_cols = list(range(51)) # 51 time points from 0 to 100

    # Ensure time columns are numeric
    for col in time_cols:
        master_df[col] = pd.to_numeric(master_df[col], errors='coerce')

    normative_stats = master_df.groupby('canonical_variable')[time_cols].agg(['mean', 'std']).reset_index()
    normative_stats.columns = [f'{col[1]}_{col[0]}' if col[1] else col[0] for col in normative_stats.columns]

    normative_path = output_dir / "tables" / "normative_stats.parquet"
    normative_stats.to_parquet(normative_path)
    logging.info(f"Normative statistics saved to {normative_path}")

    print("\n" + "="*50)
    print("      Normative Statistics Preview")
    print("="*50)
    display(normative_stats.head())
    return normative_stats

def calculate_spatiotemporal_stats(spatiotemporal_df: pd.DataFrame, output_dir: Path):
    """Calculates and saves descriptive statistics for spatiotemporal parameters."""
    if spatiotemporal_df.empty:
        logging.warning("Spatiotemporal DataFrame is empty. Skipping statistics calculation.")
        return

    logging.info("Calculating normative statistics for spatiotemporal parameters...")
    stats = spatiotemporal_df.drop(columns=['subject_id', 'side']).describe(
        percentiles=[.05, .25, .5, .75, .95]
    ).round(3)

    spt_path = output_dir / "tables" / "spatiotemporal_normative_stats.csv"
    stats.to_csv(spt_path)

    print("\n" + "="*60)
    print("      Normative Spatiotemporal Parameters Table")
    print("="*60)
    display(stats)
    logging.info(f"Spatiotemporal normative statistics saved to {spt_path}")

def generate_kinetic_qc_report(records: List[Tuple[str, str, bool]], output_dir: Path):
    """Saves an auditable list of subjects/sides flagged for unreliable kinetic data
    (e.g. no valid force-plate contact). Data for these subjects/sides is NOT removed
    from master_df -- this report exists so researchers can filter downstream if desired.
    """
    if not records:
        logging.warning("No kinetic QC records to report. Skipping.")
        return

    qc_df = pd.DataFrame(records, columns=['subject_id', 'side', 'kinetic_valid'])
    qc_path = output_dir / "tables" / "kinetic_qc_flags.csv"
    qc_df.sort_values(['subject_id', 'side']).to_csv(qc_path, index=False)

    n_flagged = (~qc_df['kinetic_valid']).sum()
    logging.info(f"Kinetic QC report saved to {qc_path} ({n_flagged}/{len(qc_df)} subject-sides flagged invalid)")

    print("\n" + "="*50)
    print("      Subjects Flagged for Invalid Kinetic Data")
    print("="*50)
    display(qc_df[~qc_df['kinetic_valid']])