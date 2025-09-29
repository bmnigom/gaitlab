# File: gaitlab/plotting.py
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, Any

class PngPlotter:
    """Generates static PNG plots for gait analysis data."""
    def __init__(self, layout: Dict[str, Any], output_dir: Path):
        self.layout = layout
        self.output_dir = output_dir / "figures"
        self.units = layout.get('units', {})
        self.output_dir.mkdir(exist_ok=True)

    def plot_all_panels(self, master_df: pd.DataFrame, normative_df: pd.DataFrame):
        """Generates all plot panels defined in the layout."""
        logging.info("Generating all PNG plot panels...")
        for panel_config in self.layout.get('panels', []):
            self._plot_panel(panel_config, master_df, normative_df)

    def _plot_panel(self, panel_config: dict, master_df: pd.DataFrame, normative_df: pd.DataFrame):
        """Generates a single panel with multiple subplots."""
        name = panel_config['name']
        logging.info(f"Generating PNG panel: {name}...")
        rows, cols = panel_config['grid']['rows'], panel_config['grid']['cols']
        fig, axes = plt.subplots(rows, cols, figsize=(cols * 5, rows * 4), squeeze=False)
        fig.suptitle(name, fontsize=16, fontweight='bold')
        axes = axes.flatten()

        time_points = np.linspace(0, 100, 51)
        colors = {'left': '#D95319', 'right': '#0072BD'} # Orange/Blue

        for i, entry in enumerate(panel_config['entries']):
            ax = axes[i]
            self._plot_single_trace(ax, entry, master_df, normative_df, time_points, colors)

        for i in range(len(panel_config['entries']), len(axes)):
            axes[i].set_visible(False)

        fig.tight_layout(rect=[0, 0.03, 1, 0.95])
        filename = self.output_dir / f"{name.lower().replace(' ', '_')}.png"
        fig.savefig(filename, dpi=120)
        plt.close(fig)
        logging.info(f"Saved PNG panel to {filename}")

    def _plot_single_trace(self, ax, entry, master_df, normative_df, time_points, colors):
        """Plots data for a single subplot."""
        ax.set_title(entry['label'], fontsize=10)
        part_name, part_base = entry.get('part', ''), entry.get('part', '')

        sides = []
        if part_name.endswith('_l'):
            sides, part_base = ['left'], part_name.replace('_l', '')
        elif part_name.endswith('_r'):
            sides, part_base = ['right'], part_name.replace('_r', '')
        elif entry.get('lateral'):
            sides = ['left', 'right']

        for side in sides:
            can_name = f"{entry['family']}.{part_base}.{entry['axis']}.{side}"

            # Plot individual curves
            curves = master_df[master_df['canonical_variable'] == can_name]
            if not curves.empty:
                ax.plot(time_points, curves[list(range(51))].T, color=colors[side], lw=0.5, alpha=0.15)

            # Plot normative band
            norm_data = normative_df[normative_df['canonical_variable'] == can_name]
            if not norm_data.empty:
                mean = norm_data[[f'mean_{i}' for i in range(51)]].values.flatten()
                std = norm_data[[f'std_{i}' for i in range(51)]].values.flatten()
                ax.plot(time_points, mean, color=colors[side], lw=2.5, label=f"{side.capitalize()} (n={len(curves)})")
                ax.fill_between(time_points, mean - std, mean + std, color=colors[side], alpha=0.2)

        ax.set_xlabel("Gait Cycle (%)", fontsize=8)
        ax.set_ylabel(self.units.get(entry['family'], ''), fontsize=8)
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.axhline(0, color='black', lw=0.8)
        ax.set_xlim(0, 100)
        if sides: ax.legend(fontsize=8)


class HtmlPlotter:
    """Generates interactive HTML plots for gait analysis data."""
    def __init__(self, layout: Dict[str, Any], output_dir: Path):
        self.layout = layout
        self.output_dir = output_dir / "html"
        self.units = layout.get('units', {})
        self.output_dir.mkdir(exist_ok=True)

    def plot_all_panels(self, master_df: pd.DataFrame, normative_df: pd.DataFrame):
        logging.info("Generating all HTML plot panels...")
        for panel_config in self.layout.get('panels', []):
            self._plot_panel(panel_config, master_df, normative_df)

    def _plot_panel(self, panel_config: dict, master_df: pd.DataFrame, normative_df: pd.DataFrame):
        name = panel_config['name']
        logging.info(f"Generating HTML panel: {name}...")
        rows, cols = panel_config['grid']['rows'], panel_config['grid']['cols']

        fig = make_subplots(
            rows=rows, cols=cols,
            subplot_titles=[e['label'] for e in panel_config['entries']]
        )
        time_points = np.linspace(0, 100, 51)
        colors = {'left': '#D95319', 'right': '#0072BD'} # Orange/Blue

        for i, entry in enumerate(panel_config['entries']):
            r, c = i // cols + 1, i % cols + 1
            part_name, part_base = entry.get('part', ''), entry.get('part', '')

            sides = []
            if part_name.endswith('_l'):
                sides, part_base = ['left'], part_name.replace('_l', '')
            elif part_name.endswith('_r'):
                sides, part_base = ['right'], part_name.replace('_r', '')
            elif entry.get('lateral'):
                sides = ['left', 'right']

            for side in sides:
                can_name = f"{entry['family']}.{part_base}.{entry['axis']}.{side}"

                # Individual curves
                curves = master_df[master_df['canonical_variable'] == can_name]
                for _, row in curves.iterrows():
                    fig.add_trace(go.Scatter(
                        x=time_points, y=row[list(range(51))], mode='lines',
                        line={'color': colors[side], 'width': 0.7}, opacity=0.3,
                        name=row['subject_id'], hoverinfo='none', showlegend=False
                    ), row=r, col=c)

                # Normative band
                norm_data = normative_df[normative_df['canonical_variable'] == can_name]
                if not norm_data.empty:
                    mean = norm_data[[f'mean_{i}' for i in range(51)]].values.flatten()
                    std = norm_data[[f'std_{i}' for i in range(51)]].values.flatten()

                    fig.add_trace(go.Scatter(
                        x=np.concatenate([time_points, time_points[::-1]]),
                        y=np.concatenate([mean + std, (mean - std)[::-1]]),
                        fill='toself', fillcolor=colors[side], opacity=0.2,
                        line={'color': 'rgba(255,255,255,0)'}, showlegend=False
                    ), row=r, col=c)

                    fig.add_trace(go.Scatter(
                        x=time_points, y=mean, mode='lines', name=f"Mean {side.capitalize()}",
                        line={'color': colors[side], 'width': 3}
                    ), row=r, col=c)

            fig.update_xaxes(title_text="Gait Cycle (%)", row=r, col=c)
            fig.update_yaxes(title_text=self.units.get(entry['family'], ''), row=r, col=c)

        fig.update_layout(title_text=f"<b>{name}</b>", height=rows * 350)
        filename = self.output_dir / f"{name.lower().replace(' ', '_')}.html"
        fig.write_html(filename)
        logging.info(f"Saved HTML panel to {filename}")