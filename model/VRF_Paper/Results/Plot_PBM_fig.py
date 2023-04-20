# -*- coding: utf-8 -*-
"""
@Project ：Midea-DR-Project-main 
@File    ：Plot_PBM_fig.py
@Time: 02/22/2023 2:20
@Author: Mingchen Li
"""

import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# 生成数据
np.random.seed(2023)
data = np.random.randn(50)

# 设定基准中位数
baseline = 0

# 计算每个数据点与基准中位数的差值
medians = np.median(data)
diffs = medians - baseline

# 将数据点与差值打包，并按照差值排序
data_diffs = list(zip(data, diffs))
data_sorted = sorted(data_diffs, key=lambda x: x[1])

# 将排序后的数据点和差值分开
data_sorted, sorted_diffs = zip(*data_sorted)

# 绘制箱型图
sns.boxplot(y=data_sorted, orient='horizontal', color='gray')

# 绘制基准中位数虚线
plt.axvline(x=baseline, linestyle='--', color='green')

# 为箱型图着色
for i, diff in enumerate(sorted_diffs):
    if diff < 0:
        color = 'gray'
    elif diff == 0:
        color = 'green'
    else:
        color = 'blue'
    plt.getp(plt.gca().artists[i], facecolor=color)
