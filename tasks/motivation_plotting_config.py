#!/usr/bin/env python3
"""
Centralized configuration for all plotting scripts.
Import this in your plotting scripts to ensure consistent styling and dimensions.

Usage:
    from motivation_plotting_config import *
"""

import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import subprocess

# ============================
# Standard Figure Dimensions
# ============================
# Standard axis dimensions - these are the most important parameters
AX_WIDTH = 1.85  # Width of plotting area in inches
AX_HEIGHT = 1.15  # Height of plotting area in inches
AX_LEFT_MARGIN = 0.4  # Left margin for y-axis labels
AX_RIGHT_MARGIN = 0.05  # Right margin
AX_TOP_MARGIN = 0.65  # Top margin for title
AX_BOTTOM_MARGIN = 0.5  # Bottom margin for x-axis labels

# Dimensions for broken-axis plots
BROKEN_AXIS_GAP = 0.02  # Gap between broken axes in inches
BROKEN_AXIS_TOP_RATIO = 0.5  # Proportion of total height for top axis
BROKEN_AXIS_BOTTOM_RATIO = 0.5  # Proportion of total height for bottom axis

# ============================
# Font Sizes and Text Settings
# ============================
TITLE_FONTSIZE = 6  # Plot title font size
AXIS_LABEL_FONTSIZE = 6  # Axis labels font size
TICKS_FONTSIZE = 5  # Tick labels font size
LEGEND_FONTSIZE = 6  # Legend font size
ANNOTATION_SIZE = 4  # Annotation text size

# ============================
# Colors and Styles
# ============================
# Color palettes
PALETTE_REGULAR = sns.color_palette("deep")  # Regular color palette
PALETTE_PASTEL = sns.color_palette("pastel")  # Pastel color palette

# Hatching patterns for bar plots
HATCHES = ["", "//", "xx", "\\\\", "..", "*", "o", "-"]

# Line styles
LINE_WIDTH = 1.0  # Default line width
MARKER_SIZE = 2.0  # Default marker size
ERROR_BAR_CAP_SIZE = 1.0  # Error bar cap size
ERROR_BAR_LINE_WIDTH = 0.4  # Error bar line width
GRID_LINE_WIDTH = 0.5  # Grid line width
GRID_ALPHA = 0.7  # Grid line opacity
BORDER_LINE_WIDTH = 0.6  # Axis border line width

# ============================
# Label Templates
# ============================
LOWER_BETTER_TITLE = "Lower is better ↓"  # Template for metrics where lower is better
HIGHER_BETTER_TITLE = (
    "Higher is better ↑"  # Template for metrics where higher is better
)


# ============================
# General Matplotlib Settings
# ============================
# Apply matplotlib settings
def apply_mpl_settings():
    """Apply standard matplotlib settings."""
    mpl.use("Agg")
    mpl.rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"
    mpl.rcParams["pdf.fonttype"] = 42
    mpl.rcParams["ps.fonttype"] = 42
    mpl.rcParams["font.family"] = "libertine"

    # Seaborn style settings
    sns.set_style("whitegrid")
    sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
    sns.set_context(
        "paper", rc={"font.size": 5, "axes.titlesize": 5, "axes.labelsize": 8}
    )


# ============================
# Helper Functions
# ============================
def create_standardized_plot(
    ax_width=AX_WIDTH,
    ax_height=AX_HEIGHT,
    left_margin=AX_LEFT_MARGIN,
    right_margin=AX_RIGHT_MARGIN,
    top_margin=AX_TOP_MARGIN,
    bottom_margin=AX_BOTTOM_MARGIN,
):
    """
    Create a figure with standardized axis dimensions.

    Parameters:
    -----------
    ax_width : float
        Width of the plotting area in inches
    ax_height : float
        Height of the plotting area in inches
    left_margin : float
        Left margin in inches (for labels)
    right_margin : float
        Right margin in inches
    top_margin : float
        Top margin in inches
    bottom_margin : float
        Bottom margin in inches (for labels)

    Returns:
    --------
    fig : matplotlib Figure
    ax : matplotlib Axis
    """
    # Calculate total figure size from axis dimensions and margins
    fig_width = ax_width + left_margin + right_margin
    fig_height = ax_height + top_margin + bottom_margin

    # Create figure
    fig = plt.figure(figsize=(fig_width, fig_height))

    # Calculate position of the axes as a fraction of figure dimensions
    left = left_margin / fig_width
    bottom = bottom_margin / fig_height
    width = ax_width / fig_width
    height = ax_height / fig_height

    # Create axes with specified dimensions
    ax = fig.add_axes([left, bottom, width, height])

    return fig, ax


def create_standardized_subplots(
    nrows=1,
    ncols=2,
    ax_width=AX_WIDTH,
    ax_height=AX_HEIGHT,
    left_margin=AX_LEFT_MARGIN,
    right_margin=AX_RIGHT_MARGIN,
    top_margin=AX_TOP_MARGIN,
    bottom_margin=AX_BOTTOM_MARGIN,
    wspace=0.4,
    hspace=0.3,
):
    """
    Create a figure with standardized subplots.

    Parameters:
    -----------
    nrows : int
        Number of subplot rows
    ncols : int
        Number of subplot columns
    ax_width : float
        Width of each subplot axis in inches
    ax_height : float
        Height of each subplot axis in inches
    left_margin : float
        Left margin in inches (for labels)
    right_margin : float
        Right margin in inches
    top_margin : float
        Top margin in inches
    bottom_margin : float
        Bottom margin in inches (for labels)
    wspace : float
        Width spacing between subplots as a fraction of subplot width
    hspace : float
        Height spacing between subplots as a fraction of subplot height

    Returns:
    --------
    fig : matplotlib Figure
    axes : matplotlib Axes array (can be 1D or 2D depending on nrows and ncols)
    """
    # Calculate total figure size from axis dimensions, margins, and spacing
    fig_width = (
        left_margin
        + (ax_width * ncols)
        + (wspace * ax_width * (ncols - 1))
        + right_margin
    )
    fig_height = (
        bottom_margin
        + (ax_height * nrows)
        + (hspace * ax_height * (nrows - 1))
        + top_margin
    )

    # Create figure
    fig = plt.figure(figsize=(fig_width, fig_height))

    # Calculate subplot params as fractions of figure dimensions
    left = left_margin / fig_width
    bottom = bottom_margin / fig_height
    right = 1 - (right_margin / fig_width)
    top = 1 - (top_margin / fig_height)

    # Set up the subplot layout parameters
    plt.subplots_adjust(
        left=left, bottom=bottom, right=right, top=top, wspace=wspace, hspace=hspace
    )

    # Create and return the subplot axes
    axes = []
    for i in range(1, nrows * ncols + 1):
        ax = fig.add_subplot(nrows, ncols, i)
        axes.append(ax)

    # Reshape the axes array for 2D access if needed
    if nrows > 1 and ncols > 1:
        axes = np.array(axes).reshape(nrows, ncols)

    # Apply consistent styling to each axis
    for ax in np.array(axes).flatten():
        # Configure ticks
        ax.tick_params(
            axis="both",
            which="major",
            labelsize=TICKS_FONTSIZE,
            pad=3,
            length=2.5,
            width=BORDER_LINE_WIDTH,
            direction="in",
        )
        ax.tick_params(
            axis="both", which="minor", length=1.5, width=0.4, direction="in"
        )

        # Grid settings
        ax.grid(True, linestyle="--", alpha=GRID_ALPHA, linewidth=GRID_LINE_WIDTH)

        # Spine settings
        for spine in ax.spines.values():
            spine.set_linewidth(BORDER_LINE_WIDTH)

    return fig, axes


def create_standardized_cutoff_plot(
    ax_width=AX_WIDTH,
    ax_height=AX_HEIGHT,
    top_ratio=BROKEN_AXIS_TOP_RATIO,
    bottom_ratio=BROKEN_AXIS_BOTTOM_RATIO,
    gap=BROKEN_AXIS_GAP,
    left_margin=AX_LEFT_MARGIN,
    right_margin=AX_RIGHT_MARGIN,
    top_margin=AX_TOP_MARGIN,
    bottom_margin=AX_BOTTOM_MARGIN,
):
    """
    Create a figure with broken/cutoff y-axis with standardized dimensions.

    Parameters:
    -----------
    ax_width : float
        Width of each axis in inches
    ax_height : float
        Total height of both plotting areas combined in inches
    top_ratio : float
        Proportion of ax_height allocated to top axis
    bottom_ratio : float
        Proportion of ax_height allocated to bottom axis
    gap : float
        Gap between axes in inches
    left_margin : float
        Left margin in inches (for labels)
    right_margin : float
        Right margin in inches
    top_margin : float
        Top margin in inches
    bottom_margin : float
        Bottom margin in inches (for labels)

    Returns:
    --------
    fig : matplotlib Figure
    (ax1, ax2) : tuple of matplotlib Axes (top, bottom)
    """
    # Calculate axis heights based on proportions
    ax_height_top = ax_height * top_ratio
    ax_height_bottom = ax_height * bottom_ratio

    # Calculate total figure dimensions
    fig_width = ax_width + left_margin + right_margin
    fig_height = ax_height_top + ax_height_bottom + gap + top_margin + bottom_margin

    # Create main figure
    fig = plt.figure(figsize=(fig_width, fig_height))

    # Create the two axes with precise positioning
    # Top axis (ax1)
    top_bottom = (bottom_margin + ax_height_bottom + gap) / fig_height
    top_height = ax_height_top / fig_height
    ax1 = fig.add_axes(
        [left_margin / fig_width, top_bottom, ax_width / fig_width, top_height]
    )

    # Bottom axis (ax2)
    bottom_bottom = bottom_margin / fig_height
    bottom_height = ax_height_bottom / fig_height
    ax2 = fig.add_axes(
        [left_margin / fig_width, bottom_bottom, ax_width / fig_width, bottom_height]
    )

    # Setup for broken y-axis
    ax1.spines.bottom.set_visible(False)
    ax2.spines.top.set_visible(False)
    ax1.xaxis.set_visible(False)

    return fig, (ax1, ax2)


def apply_broken_axis_style(ax1, ax2):
    """
    Apply the diagonal break marks and style to a broken axis plot.

    Parameters:
    -----------
    ax1 : matplotlib Axis (top)
    ax2 : matplotlib Axis (bottom)
    """
    # Add break marks
    d = 0.5  # proportion of vertical to horizontal extent of the slanted line
    kwargs = dict(
        marker=[(-1, -d), (1, d)],
        markersize=TICKS_FONTSIZE,
        linestyle="none",
        color="k",
        mec="k",
        mew=1,
        clip_on=False,
    )
    ax1.plot([0, 1], [0, 0], transform=ax1.transAxes, **kwargs)
    ax2.plot([0, 1], [1, 1], transform=ax2.transAxes, **kwargs)


def create_standardized_multi_cutoff_plot(
    n_sections=2,
    ax_width=AX_WIDTH,
    ax_height=AX_HEIGHT,
    section_ratios=None,
    gaps=None,
    left_margin=AX_LEFT_MARGIN,
    right_margin=AX_RIGHT_MARGIN,
    top_margin=AX_TOP_MARGIN,
    bottom_margin=AX_BOTTOM_MARGIN,
    sharex=True,
):
    """
    Create a figure with multiple broken/cutoff y-axes with standardized dimensions.

    Parameters:
    -----------
    n_sections : int
        Number of vertical sections (axes) with cutoffs between them
    ax_width : float
        Width of each axis in inches
    ax_height : float
        Total height of all plotting areas combined in inches
    section_ratios : list of float, optional
        Proportion of ax_height allocated to each section. If None, sections are equal.
        Must sum to 1.0
    gaps : list of float, optional
        Gaps between axes in inches. If None, uses BROKEN_AXIS_GAP for all.
        Should have (n_sections-1) elements.
    left_margin : float
        Left margin in inches (for labels)
    right_margin : float
        Right margin in inches
    top_margin : float
        Top margin in inches
    bottom_margin : float
        Bottom margin in inches (for labels)
    sharex : bool
        Whether all axes should share the x-axis

    Returns:
    --------
    fig : matplotlib Figure
    axes : list of matplotlib Axes (from top to bottom)
    """
    # Default section ratios if not provided
    if section_ratios is None:
        section_ratios = [1.0 / n_sections] * n_sections

    # Check that section ratios sum to 1
    if abs(sum(section_ratios) - 1.0) > 1e-6:
        raise ValueError(f"Section ratios must sum to 1.0, got {sum(section_ratios)}")

    # Default gaps if not provided
    if gaps is None:
        gaps = [BROKEN_AXIS_GAP] * (n_sections - 1)

    # Check correct number of gaps
    if len(gaps) != n_sections - 1:
        raise ValueError(f"Expected {n_sections-1} gaps, got {len(gaps)}")

    # Calculate individual axis heights based on proportions
    ax_heights = [ax_height * ratio for ratio in section_ratios]

    # Calculate total figure dimensions
    fig_width = ax_width + left_margin + right_margin
    fig_height = sum(ax_heights) + sum(gaps) + top_margin + bottom_margin

    # Create main figure
    fig = plt.figure(figsize=(fig_width, fig_height))

    # Create the subplots directly for better positioning control
    fig, axes = plt.subplots(
        n_sections,
        1,
        figsize=(fig_width, fig_height),
        gridspec_kw={"height_ratios": section_ratios},
        sharex=sharex,
    )

    # Ensure axes is a list even with a single section
    if n_sections == 1:
        axes = [axes]

    # Adjust the figure to have proper spacing
    plt.subplots_adjust(
        left=left_margin / fig_width,
        right=1 - right_margin / fig_width,
        top=1 - top_margin / fig_height,
        bottom=bottom_margin / fig_height,
        hspace=0.1,  # Small spacing between subplots
    )

    # Set up broken axis appearance
    for i in range(n_sections - 1):
        # Top axis has no bottom spines
        axes[i].spines.bottom.set_visible(False)
        # Bottom axis has no top spines
        axes[i + 1].spines.top.set_visible(False)

        # Hide x-axis for all but the bottom subplot if sharex is True
        if sharex and i < n_sections - 1:
            axes[i].tick_params(labelbottom=False)

    # Add break marks
    for i in range(n_sections - 1):
        d = 0.5  # proportion of vertical to horizontal extent of the slanted line
        kwargs = dict(
            marker=[(-1, -d), (1, d)],
            markersize=TICKS_FONTSIZE,
            linestyle="none",
            color="k",
            mec="k",
            mew=1,
            clip_on=False,
        )
        axes[i].plot([0, 1], [0, 0], transform=axes[i].transAxes, **kwargs)
        axes[i + 1].plot([0, 1], [1, 1], transform=axes[i + 1].transAxes, **kwargs)

    return fig, axes


def apply_consistent_style(
    ax, title=None, xlabel=None, ylabel=None, grid=True, labelpad=None
):
    """
    Apply consistent styling to a matplotlib axis.

    Parameters:
    -----------
    ax : matplotlib Axis
        The axis to style
    title : str, optional
        Plot title
    xlabel : str, optional
        X-axis label
    ylabel : str, optional
        Y-axis label
    grid : bool, optional
        Whether to show grid lines
    """
    # Set title and labels if provided
    if title:
        ax.set_title(title, fontsize=TITLE_FONTSIZE, pad=3, color="navy")
    if xlabel:
        ax.set_xlabel(xlabel, fontsize=AXIS_LABEL_FONTSIZE, labelpad=labelpad)
    else:
        ax.set_xlabel("", fontsize=AXIS_LABEL_FONTSIZE)
    if ylabel:
        ax.set_ylabel(ylabel, fontsize=AXIS_LABEL_FONTSIZE)

    # Configure ticks
    ax.tick_params(
        axis="both",
        which="major",
        #labelsize=TICKS_FONTSIZE,
        labelsize=AXIS_LABEL_FONTSIZE,
        pad=3,
        length=2.5,
        width=BORDER_LINE_WIDTH,
        direction="in",
    )
    ax.tick_params(axis="both", which="minor", length=1.5, width=0.4, direction="in")

    # Grid settings
    if grid:
        ax.grid(True, linestyle="--", alpha=GRID_ALPHA, linewidth=GRID_LINE_WIDTH)

    # Spine settings
    for spine in ax.spines.values():
        spine.set_linewidth(BORDER_LINE_WIDTH)


def create_annotation_y_label(ax, label, position=None):
    """
    Create a rotated y-axis label positioned precisely for consistent appearance.

    Parameters:
    -----------
    ax : matplotlib Axis
        The axis to add label to
    label : str
        The label text
    position : tuple, optional
        Custom (x, y) position for the label, if None, uses default positioning
    """
    if position is None:
        position = (-0.28, 0.5)

    ax.annotate(
        label,
        xy=position,
        xytext=(-45, 0),
        textcoords="offset points",
        rotation=90,
        va="center",
        fontsize=AXIS_LABEL_FONTSIZE,
    )


# Utility functions
def format_bytes(value):
    """Format byte sizes into human readable format"""
    for unit in ["B", "KB", "MB"]:
        if value < 1024:
            return f"{value:.0f}{unit}"
        value /= 1024
    return f"{value:.0f}MB"


def crop_pdf(input_path):
    """Use pdfcrop to crop the PDF file."""
    try:
        subprocess.run(["pdfcrop", input_path, input_path], check=True)
        print(f"Successfully cropped {input_path}")
    except subprocess.CalledProcessError as e:
        print(f"Error cropping PDF {input_path}: {e}")
    except FileNotFoundError:
        print("pdfcrop command not found. Please install texlive-extra-utils package.")


# Predefined label mappings used in plots
LABEL_MAPPINGS_SYSTEM = {
    "Native": "Native",
    "Gramine": "LibOS (Gramine)",
    "VM": "VM (KVM-Linux)",
    "Kata Containers": "Containers (Kata)",
    "CVM": "CVM (SEV-SNP)",
    "Wallet": "Wallet",
}

LABEL_MAPPINGS_VM = {
    "vm": "VM (KVM-Linux)",
    "kata": "Containers (Kata)",
    "cvm": "CVM (SEV-SNP)",
    "wallet": "Wallet",
}

LABEL_MAPPINGS_SIMULATIONS_MOTIVATION = {
    "VM": "VM (KVM-Linux)",
    "KATA": "Containers (Kata)",
    "CVM": "CVM (SEV-SNP)",
    "WALLET": "Wallet",
}

LABEL_MAPPINGS_SIMULATIONS_EVALUATION = {
    "VM": "VM",
    "KATA": "Containers",
    "CVM": "CVM",
    "WALLET": "Wallet",
}


# Apply settings on import
apply_mpl_settings()
