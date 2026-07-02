# File: gaitlab/core.py
import pandas as pd
import numpy as np
from pathlib import Path
import yaml
import logging
from typing import Dict, List, Any

class Trial:
    """
    Represents and processes all data for a single gait trial subject.
    """
    def __init__(self, subject_id: str, trial_files: List[Path], config: Dict[str, Any]):
        self.subject_id = subject_id
        self.files = {p.name: p for p in trial_files}
        self.config = config
        self.is_valid = False
        self.cycle_times = {}
        self.stance_times = {}
        self.kinetic_valid = {'left': True, 'right': True}
        self.spatiotemporal_params = []

        self._load_and_validate_events()
        if self.is_valid:
            self._assess_kinetic_validity()
            self._calculate_spatiotemporals()

    def _load_and_validate_events(self):
        """Loads gaitEvents.yaml and determines valid gait cycles."""
        events_filename = next((fname for fname in self.files if fname.endswith("gaitEvents.yaml")), None)
        if not events_filename:
            return

        try:
            with open(self.files[events_filename], "r", encoding='utf-8') as f:
                gait_events_raw = yaml.safe_load(f)
        except Exception:
            return

        gait_events = []
        for key, times in gait_events_raw.items():
            side_char, _, name_raw = key.partition('_')
            side = 'left' if side_char == 'l' else 'right'
            for t in times:
                gait_events.append({'context': side, 'name': name_raw.replace('_', ' '), 'time': float(t)})

        for side in ['left', 'right']:
            strikes = sorted([e for e in gait_events if 'strike' in e['name'] and e['context'] == side], key=lambda x: x['time'])
            offs = sorted([e for e in gait_events if 'off' in e['name'] and e['context'] == side], key=lambda x: x['time'])

            if len(strikes) < 2: continue
            for i in range(len(strikes) - 1):
                hs1, hs2 = strikes[i]['time'], strikes[i+1]['time']
                to = [t for t in offs if hs1 < t['time'] < hs2]
                if len(to) == 1:
                    self.cycle_times[side] = (hs1, hs2)
                    self.stance_times[side] = (hs1, to[0]['time'])
                    break

        if 'left' in self.cycle_times and 'right' in self.cycle_times:
            self.is_valid = True

    def _assess_kinetic_validity(self):
        """Flags sides with implausible kinetic signal (e.g. no force-plate contact).

        Some trials have missing or near-zero force-plate data for a side (foot never
        landed on a plate), which biases inverse-dynamics outputs (moments/forces/powers/
        platform GRF) without making them exactly zero. This is detected via the peak
        absolute ankle force during stance, since the joint-forces file is present for
        every trial (unlike platform GRF, which can be entirely missing).
        """
        qc_config = self.config.get('quality_control', {}).get('kinetic_validity', {})
        check_canonical = qc_config.get('check_canonical', 'forces.ankle.z')
        min_peak_abs = qc_config.get('min_peak_abs', 5.0)

        family, part, axis = check_canonical.split('.')
        dataset_props = self.config.get('datasets', {}).get(family)
        if not dataset_props:
            return

        pattern = self.config['files'][dataset_props['source_file']]['pattern']
        file_path = next((p for p in self.files.values() if p.match(pattern)), None)
        if not file_path:
            logging.warning(f"{self.subject_id}: could not assess kinetic validity (no {family} file found)")
            return

        try:
            df = pd.read_csv(file_path, low_memory=False).set_index("time")
        except Exception:
            logging.warning(f"{self.subject_id}: could not assess kinetic validity (failed to read {family} file)")
            return

        for side in ['left', 'right']:
            can_name = f"{family}.{part}.{axis}.{side}"
            headers = dataset_props.get('canonical_to_headers', {}).get(can_name, [])
            header = next((h for h in headers if h in df.columns), None)
            if not header or side not in self.stance_times:
                continue

            start, end = self.stance_times[side]
            peak = df.loc[start:end, header].abs().max()
            if pd.isna(peak) or peak < min_peak_abs:
                self.kinetic_valid[side] = False
                logging.warning(
                    f"{self.subject_id}: kinetic data flagged invalid on {side} "
                    f"(peak |{can_name}|={peak} < threshold={min_peak_abs})"
                )

    def _calculate_spatiotemporals(self):
        """Calculates spatiotemporal parameters using trajectory data."""
        traj_config = self.config.get('internal_datasets', {}).get('trajectories')
        if not traj_config: return

        pattern = self.config['files'][traj_config['source_file']]['pattern']
        traj_path = next((p for p in self.files.values() if p.match(pattern)), None)
        if not traj_path: return

        try:
            df_traj = pd.read_csv(traj_path).set_index("time")
        except Exception:
            return

        def get_pos(side, axis, time):
            header = traj_config['canonical_to_headers'].get(f'trajectories.ankle.{axis}.{side}', [None])[0]
            if not header or header not in df_traj.columns: return None
            return np.interp(time, df_traj.index, df_traj[header])

        for side in ['left', 'right']:
            other_side = 'right' if side == 'left' else 'left'
            hs1, hs2 = self.cycle_times[side]
            stance_start, stance_end = self.stance_times[side]

            pos_hs1_self = np.array([get_pos(side, axis, hs1) for axis in 'xyz'])
            pos_hs1_other = np.array([get_pos(other_side, axis, hs1) for axis in 'xyz'])
            pos_hs2_self = np.array([get_pos(side, axis, hs2) for axis in 'xyz'])

            if any(p is None for p in np.concatenate([pos_hs1_self, pos_hs1_other, pos_hs2_self])): continue

            stride_time = hs2 - hs1
            stride_length = np.linalg.norm(pos_hs2_self - pos_hs1_self) / 1000.0

            self.spatiotemporal_params.append({
                'subject_id': self.subject_id, 'side': side,
                'walking_speed_m_s': stride_length / stride_time if stride_time > 0 else 0,
                'cadence_steps_min': (1 / (stride_time / 2)) * 60 if stride_time > 0 else 0,
                'stride_length_m': stride_length,
                'step_length_m': np.linalg.norm(pos_hs1_self - pos_hs1_other) / 1000.0,
                'stance_time_s': stance_end - stance_start,
                'swing_time_s': stride_time - (stance_end - stance_start),
                'stance_pct': ((stance_end - stance_start) / stride_time) * 100 if stride_time > 0 else 0
            })

    def process_time_series(self) -> pd.DataFrame | None:
        """Processes and normalizes all time-series data (angles, moments, etc.)."""
        if not self.is_valid:
            return None

        all_headers = {h for d in self.config['datasets'].values() for c in d['canonical_to_headers'].values() for h in c}
        all_headers.add("time")

        normalized_data = []
        for props in self.config['datasets'].values():
            pattern = self.config['files'][props['source_file']]['pattern']
            file_path = next((p for p in self.files.values() if p.match(pattern)), None)
            if not file_path: continue

            try:
                df = pd.read_csv(file_path, usecols=lambda c: c in all_headers, low_memory=False).set_index("time")
            except (ValueError, FileNotFoundError):
                continue

            for can_name, headers in props.get('canonical_to_headers', {}).items():
                header = next((h for h in headers if h in df.columns), None)
                if not header: continue

                side = can_name.split('.')[-1]
                proc_type = props.get('processing_type', 'kinematic')
                start, end = self.stance_times.get(side) if proc_type == 'kinetic' else self.cycle_times.get(side)

                if start is None: continue

                cycle_data = df.loc[start:end, header].dropna() * props.get('scale_factor', 1.0)
                if len(cycle_data) < 2: continue

                norm_times = np.linspace(0, 100, 51)
                interp_values = np.interp(norm_times, np.linspace(0, 100, len(cycle_data)), cycle_data.values)

                row = {'subject_id': self.subject_id, 'canonical_variable': can_name, 'side': side}
                if proc_type == 'kinetic':
                    row['kinetic_valid'] = self.kinetic_valid.get(side, True)
                row.update({i: val for i, val in enumerate(interp_values)})
                normalized_data.append(row)

        return pd.DataFrame(normalized_data) if normalized_data else None