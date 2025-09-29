# File: README.md

# Gait Analysis Processing Pipeline

## 📖 Overview

This project provides a robust and modular pipeline for processing biomechanical gait analysis data. It is designed to handle raw data from C3D files (exported as CSVs), normalize gait cycles, calculate key spatiotemporal parameters, generate normative datasets, and produce publication-quality visualizations.

The entire workflow is configurable through YAML files, allowing for easy adaptation to different data formats and plotting requirements without changing the source code.

## ✨ Features

- **Modular & Reusable Code**: The logic is organized into a Python package (`gaitlab`) for clarity and maintainability.
- **Configurable Pipeline**: Easily map variable names (`variables_map.yaml`) and define plot layouts (`plot_layout.yaml`).
- **Time Normalization**: Normalizes kinematic and kinetic data to a 51-point gait cycle (0-100%).
- **Spatiotemporal Analysis**: Automatically calculates parameters like walking speed, cadence, stride/step length, and stance/swing times.
- **Comprehensive Analysis**: Generates data coverage reports and normative statistics (mean, std).
- **Dual Visualization Output**:
    - **Static Plots**: Generates high-quality PNG figures for direct inclusion in papers.
    - **Interactive Reports**: Creates HTML plots using Plotly for interactive data exploration.
- **Reproducible Environment**: Includes a `requirements.txt` file for easy dependency management.

## 📂 Project Structure

The project is organized into the following directories and key files:

```
gaitlab/
│
├── config/                  # Configuration files
│   ├── variables_map.yaml   # Maps canonical variable names to CSV headers
│   └── plot_layout.yaml     # Defines the layout for all plots and panels
│
├── gaitlab/                 # The core Python source code package
│   ├── analysis.py          # Functions for statistical analysis
│   ├── core.py              # Main `Trial` class and data processing logic
│   ├── plotting.py          # Classes for generating PNG and HTML plots
│   └── utils.py             # Helper functions (e.g., file discovery)
│
├── output/                  # Default directory for all generated files (ignored by Git)
│
├── .gitignore               # Specifies files and folders for Git to ignore
├── main.py                  # A command-line script to run the full pipeline
├── README.md                # This documentation file
├── requirements.txt         # Python dependencies
└── process_gait_data.ipynb  # A clean Jupyter Notebook for interactive execution
```

## 🚀 Getting Started

### 1. Installation

Clone the repository and install the required Python packages using `pip`.

```bash
git clone <your-repository-url>
cd gait-analysis-pipeline
pip install -r requirements.txt
```

### 2. Configuration

1.  **Place Your Data**: Add your subject data folders to a main directory (e.g., `C:/.../VICON`). Update the `BASE_DIR` path in `main.py` or `process_gait_data.ipynb` to point to this location.
2.  **Verify Configuration**:
    * `config/variables_map.yaml`: Ensure the `pattern` for each file type matches your CSV filenames and that the `canonical_to_headers` mappings are correct.
    * `config/plot_layout.yaml`: Adjust the panels, grids, and plot entries as needed for your analysis.

### 3. Usage

You can run the pipeline in two ways:

#### A) From the Command Line (Recommended for full runs)

Execute the `main.py` script from your terminal. This will process all subjects and generate all outputs automatically.

```bash
python main.py
```

#### B) Interactively in Jupyter Notebook

Open and run the cells in `process_gait_data.ipynb`. This is ideal for step-by-step execution, debugging, and data exploration.

## 📦 Outputs

All results are saved in the `output/` directory:

-   `output/tables/`: Contains CSV files with coverage reports, normative statistics, and spatiotemporal parameters.
-   `output/figures/`: Contains all static PNG plots.
-   `output/html/`: Contains all interactive HTML plot files.
-   `output/logs/`: Contains detailed log files of the pipeline execution.

## 🎓 How to Cite

If you use this pipeline in your research, please cite it as follows:

*(You can add your preferred citation format here once your paper is published or the code is archived in a service like Zenodo).*