# -*- coding: utf-8 -*-
"""
@Project ：Midea-DR-Project-main 
@File    ：Plot_fig.py
@Time: 02/13/2023 22:47
@Author: Mingchen Li
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

for name in ['pic_ML_train_result.xlsx', 'pic_ML_test_result.xlsx', 'pic_train_result_CVRMSE.xlsx', 'pic_test_result_CVRMSE.xlsx',
             'pic_ML_feature_result.xlsx']:
# for name in ['pic_ML_feature_result.xlsx']:
    df = pd.read_excel(name)
    # df.drop(columns=['Li_2009'], inplace=True)
    if 'ML' not in name:
        df.drop(columns=['Li_2009'], inplace=False)
    # Plot the box plot

    sns.set(font_scale=1.5)
    # sns.set_style("white")

    plt.figure(figsize=(10, 5))
    color_palette = ['lightgray' if 'SVM' in col or 'Xgb' in col or 'ANN' in col else 'darkgray' for col in df.columns]

    # Create horizontal notched boxplot of the values without outliers and whiskers
    if "feature" not in name:
        ax = sns.boxplot(data=df, orient="h", showfliers=False, width=0.6)
        ax.set(xlabel='CV-RMSE(%)')
    else:
        if "Compressor frequency 1" in df.columns:
            df.rename(columns={'Compressor frequency 1': 'Compressor frequency'}, inplace=True)
        if "Mean(Indoor temperature)" in df.columns:
            df.rename(columns={'Mean(Indoor temperature)': 'Indoor dry bulb temperature'}, inplace=True)

        mean_df = df.mean().sort_values(ascending=False)
        df = df[mean_df.index]
        ax = sns.barplot(data=df, orient="h", palette="Set2")
        ax.set(xlabel='Total Gain')
    # ax = sns.boxplot(data=df, orient="h", palette=color_palette, showfliers=False, notch=True, whis=0, width=0.6, showcaps=False)

    # Add median values to the plot
    for i in range(df.shape[1]):
        median = df.iloc[:,i].median()

        # 手动计算whisker
        q1, q3 = np.percentile(df.iloc[:,i], [25, 75])
        iqr = q3 - q1
        lower_whisker = q1 - 1.5 * iqr
        upper_whisker = q3 + 1.5 * iqr

        ax.text(q3, i, f"{median:.2f}", ha="left", va="bottom", color="black", fontsize=16)


    ax.spines['bottom'].set(linewidth=2, color='darkgray')
    # Plot the two green lines from train to test for each pair
    # for i in range(0, df.shape[1], 2):
    #     column1 = df.columns[i]
    #     column2 = df.columns[i + 1]
    #     median1 = df[column1].median()
    #     median2 = df[column2].median()
        # plt.plot([median1, median1], [column1, column2], color='green', linewidth=1.5)
        # plt.plot([median2, median2], [column1, column2], color='green', linewidth=1.5)
        # plt.fill_betweenx([column1, column2], median1, median2, color='green', alpha=0.3)

    # plt.xlim(0,1)
    plt.tick_params(top=False,bottom=True,left=True,right=False, length=10, color='darkgray', width=3)
    sns.despine(left=True)
    plt.tight_layout()

    new_filename = name.replace('.xlsx', '.jpg')
    plt.savefig(new_filename, dpi=200)


    plt.show()