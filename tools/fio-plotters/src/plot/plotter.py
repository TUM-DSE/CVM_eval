from dataclasses import dataclass

from plot.json_parser import MT_BW, MT_ALAT, MT_IOPS
from plot.repr import IotGroup

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

import time

# sns settings
sns.set_style("whitegrid")
sns.set_style("ticks", {"xtick.major.size": 8, "ytick.major.size": 8})
sns.set_context("paper", rc={"font.size": 5, "axes.titlesize": 5, "axes.labelsize": 8})

FIRST_COL_LABEL = 'io type'
SCND_COL_LABEL = 'io stack'
THIRD_COL_LABEL = 'mt res'

READ_IOT_TYPE_ID = 'read'
WRITE_IOT_TYPE_ID = 'write'

PALETTE = sns.color_palette("pastel")
WIDTH   = 7 # \textwidth is 7 inch
HEIGHT  = 1.8

HATCHES = ['//', '\\\\', '|']


def legend_without_duplicate_labels(ax):
    handles, labels = ax.get_legend_handles_labels()
    unique = [(h, l) for i, (h, l) in enumerate(zip(handles, labels)) if l not in labels[:i]]
    ax.legend(*zip(*unique))

def add_values_on_bars(ax):
    for container in ax.containers:
        ax.bar_label(container, fmt='%.1f')


# https://stackoverflow.com/questions/67416696/how-to-add-the-repeated-hatches-to-each-bar-in-seaborn-barplot
def apply_hatches(ax):
    for bars, hatch in zip(ax.containers, HATCHES):
        # Set a different hatch for each group of bars
        for bar in bars:
            bar.set_hatch(hatch)
    # create the legend again to show the new hatching
    ax.legend(title='Class')

# mt : iot (grouped), (unique triplet) env, device, mt_res
# NOTE: this code is a mess, some refactoring wouldn't hurt
def plot(mt_data_dict, output_dir):

    for mt, iot_group_dict in mt_data_dict.items():

        # df = pd.DataFrame(data=iot_group_dict)
        # print(df)

        print(f'{mt}\n')
        for iot, iot_group in iot_group_dict.items():
            iot_group_collection = {FIRST_COL_LABEL: [], SCND_COL_LABEL: [], THIRD_COL_LABEL: []}
            for iot_group_member in iot_group:
                iot_group_collection[FIRST_COL_LABEL].append(iot)
                iot_group_collection[SCND_COL_LABEL].append(iot_group_member[0])
                iot_group_collection[THIRD_COL_LABEL].append(iot_group_member[1])

            df = pd.DataFrame(data=iot_group_collection)\
                .drop_duplicates(subset=[FIRST_COL_LABEL, SCND_COL_LABEL])\
                .sort_values(by=[SCND_COL_LABEL])\
                .reset_index(drop=True)

            plot = sns.barplot(x=FIRST_COL_LABEL, y=THIRD_COL_LABEL, hue=SCND_COL_LABEL,
                data=df, palette=PALETTE, edgecolor = 'w')
            legend_without_duplicate_labels(plot)
            add_values_on_bars(plot)
            apply_hatches(plot)
            fig = plot.get_figure()
            fig.savefig(f'{output_dir}/{mt}-{iot}-out.png')
            print(f'{output_dir}/{mt}-{iot}-out.png')
            plt.clf()

