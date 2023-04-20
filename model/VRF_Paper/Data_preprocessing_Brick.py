# -*- coding: utf-8 -*-
"""
@Project ：Midea-DR-Project-main 
@File    ：Data_preprocessing_Brick.py
@Time: 01/16/2023 15:56
@Author: Mingchen Li
"""
import pandas as pd
from matplotlib import pyplot as plt
import seaborn as sns

def GetData_fromCSV(columns, filename='sys1_Qcool.csv',Q_coolname='Cooling capacity', resample='15T'):
    df = pd.read_csv('制冷量数据/'+filename)
    loc_list = columns
    new_df = df[loc_list]
    if 'Q_cool' in new_df.columns:
        new_df.loc[new_df['Q_cool'] < 0.0] = 0.0
        new_df['Q_cool'] = new_df['Q_cool']/1000
    new_df['time'] = pd.to_datetime(new_df['time'])
    new_df.set_index('time', inplace=True)
    bars = new_df.resample(resample).mean().dropna()
    bars.rename(columns={'Q_cool': Q_coolname}, inplace=True)
    return bars


def Plot_df(df, plot_nub=0, title="E_diff & Q_cool Day", y_label="P(Kw)"):
    df['time'] = range(df.shape[0])
    if plot_nub != 0:
        df = df.iloc[:plot_nub]
    # Change the style of plot
    plt.style.use('seaborn-darkgrid')

    # Create a color palette
    palette = plt.get_cmap('Set1')
    plt.figure(figsize=(8, 4), dpi=200)

    # Plot multiple lines
    num = 0
    for column in df.drop('time', axis=1):
        num += 1
        plt.plot(df['time'], df[column], marker='', color=palette(num), linewidth=1, alpha=0.9, label=column)

    # Add legend
    plt.legend(loc=2, ncol=2)

    # Add titles
    plt.title(title, loc='left', fontsize=12, fontweight=0, color='orange')
    plt.xlabel("Time")
    plt.ylabel(y_label)

    # Show the graph
    plt.show()
    plt.close()


def merge_plot(df_DB, df_CSV, shift_nub=0, diff=True, plot=True, plot_nub=150, resample_min=5):
    df = pd.concat([df_DB, df_CSV], axis=1)

    if 'Outdoor unit power' in df.columns and diff:
        df['delete'] = df['Outdoor unit power'].isnull()
        df = df.iloc[1:, :]
        # df['Outdoor unit power'] = df['Outdoor unit power'].fillna(df['Outdoor unit power'].interpolate())
        df['Outdoor unit power'] = df['Outdoor unit power'].diff()*60/resample_min
        # df = df.dropna(axis='index', how='any', subset=['Cooling capacity'])
        df = df.dropna(axis=0, how='all')
        df['Outdoor unit power'] = df['Outdoor unit power'].shift(-shift_nub)
        df['delete'] = df['delete'].shift(-shift_nub)
        for i in df_DB.columns:
            if i != 'Outdoor unit power':
                df[i] = df[i].shift(-shift_nub)
        df['delete1'] = True
        for i in range(0, len(df['delete']) - 1):
            if df['delete'][i]:
                df['delete1'][i+1] = True
            else:
                df['delete1'][i+1] = df['delete'][i+1]
        del df['delete']
        df.rename(columns={"Outdoor unit power": "diff(Outdoor unit power)"}, inplace=True)
        df = df.loc[df['delete1'] == False]
        # del df['delete1']
        df = df.loc[df['diff(Outdoor unit power)'] > 0.00001]
        df = df.loc[df['diff(Outdoor unit power)'] < 100]

    else:
        for i in df_DB.columns:
            df[i] = df[i].shift(-shift_nub)
        df['time'] = range(df.shape[0])
    if plot:
        Plot_df(df, plot_nub=plot_nub)

    return df


def Data2VRFData(data, plot=True, if_print=True):

    indoor_collist = []
    onoff_list = []
    for i in range(7):
        indoor_collist.append("Indoor temperature {}".format(i))
        onoff_list.append("Indoor unit cooling state {}".format(i))
    df = data
    df['COP'] = df['Cooling capacity']/(df['diff(Outdoor unit power)']+0.00001)
    real_df = df.loc[df['COP'] > 0]
    real_df = real_df.loc[100 > df['COP']]
    real_df = real_df.loc[df['delete1'] == False]
    del real_df['delete1']
    # 异常值
    iqr = real_df['COP'].quantile(0.75) - real_df['COP'].quantile(0.25)
    Boundary_L = real_df['COP'].quantile(0.25) - 1.5 * iqr
    Boundary_U = real_df['COP'].quantile(0.25) + 1.5 * iqr
    q_abnormal_L = real_df['COP'] < Boundary_L
    q_abnormal_U = real_df['COP'] > Boundary_U
    if if_print:
        print('COP' + '中有' + str(q_abnormal_L.sum() + q_abnormal_U.sum()) + '个异常值')
        print('COP边界值为[{:.3f}, {:.3f}]'.format(Boundary_L, Boundary_U))
    real_df = real_df.loc[real_df['COP'] > Boundary_L]
    real_df = real_df.loc[real_df['COP'] < Boundary_U]
    # 增补 删除小于1的COP
    real_df = real_df.loc[df['COP'] > 1]
    if if_print:
        print(real_df['COP'].min())
    if if_print:
        print(real_df.shape)
    if plot:
        plt.style.use('seaborn-darkgrid')
        sns.histplot(data=real_df, x="COP", color="skyblue", label="COP", kde=True)
        # plt.title("COP_8 hour", loc='left', fontsize=12, fontweight=0, color='orange')
        plt.legend()
        plt.show()
        plt.close()
    if "Indoor unit cooling state 0" in real_df:
        def convert_value(x):
            if x == 0.0:
                return 0
            else:
                return 1
        for onoff in onoff_list:
            new_col = real_df[onoff].apply(convert_value)
            real_df.loc[:, onoff] = new_col
        On_nub = real_df[onoff_list].sum(axis=1)
        On_Temp = []
        for Temp, Onoff in zip(indoor_collist, onoff_list):
            On_Temp.append(real_df[Temp].multiply(real_df[Onoff]))

        real_df['Mean(Indoor temperature)'] = pd.concat(On_Temp, axis=1).sum(axis=1).div(On_nub)

        def compare_max(s):
            s_max = max(s)
            return s_max
        real_df['Max(Indoor temperature)'] = pd.concat(On_Temp, axis=1).apply(compare_max, axis=1)
        # real_df['Min(Indoor temperature)'] = real_df[indoor_collist].min(axis=1)
    else:
        real_df['Min(Indoor temperature)'] = real_df[indoor_collist].min(axis=1)
        real_df['Mean(Indoor temperature)'] = real_df[indoor_collist].mean(axis=1)
    if "Indoor unit cooling state 0" in real_df:
        for i in onoff_list:
            del real_df[i]

    
    # 剔除 CompressorFreq2 大于5的值
    O_row_nub = real_df.shape[0]
    real_df = real_df.loc[5 >= real_df['Compressor frequency 2']]
    del real_df['Compressor frequency 2']
    if if_print:
        print("可用数据中，有约{:.2f}%的数据可认为只开启了压缩机1(压缩机2频率小于5时忽略不计)".format(real_df.shape[0]/O_row_nub*100))
        print('COP均值为{:.3f}'.format(real_df['COP'].mean()))
        print(real_df.shape)

    # 删除带空的行
    # real_df = real_df.dropna(axis=0, how='any')

    return real_df
