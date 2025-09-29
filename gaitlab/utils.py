# File: gaitlab/utils.py
import re
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

def discover_subjects(base_path: Path) -> Tuple[List[str], Dict[str, List[Path]]]:
    """
    Discovers subjects and groups all their corresponding files.

    Args:
        base_path: The root directory containing all subject data.

    Returns:
        A tuple containing a sorted list of subject IDs and a dictionary
        mapping each subject ID to a list of their file paths.
    """
    subject_regex = re.compile(r"^(subject_\d+)_cond_\d+_run_\d+")
    files_by_subject = defaultdict(list)

    # Use rglob to find all files recursively
    all_files = [p for p in base_path.rglob("*") if p.is_file()]

    for file_path in all_files:
        match = subject_regex.match(file_path.stem)
        if match:
            subject_id = match.group(1)
            files_by_subject[subject_id].append(file_path)

    sorted_subjects = sorted(files_by_subject.keys())

    if not sorted_subjects:
        print(f"Warning: No subjects found in {base_path}. Check the path and file naming.")

    return sorted_subjects, files_by_subject