"""
Script for data quality assessment

Major parts:
- Usability
- Completeness
- Reliability
- Basic statistical quantities 
- Multivariable

@author: Zhenyu Wang (wangzhy237@mail2.sysu.edu.cn)
"""

import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
from matplotlib import font_manager
from matplotlib import rcParams
import numpy as np
import pandas as pd
import copy
import seaborn as sns
from scipy import stats
import scipy.stats.kde as kde
import pickle


# data quality assessment class
class DQA(object): 

    result_path = './results'
    label = 'original'
    step = 4*24*2

    def __init__(self, data:pd.DataFrame, data_range:dict, sampling_rate=4, days_backwards=2, save_result=False, result_path=None, **kw):
        '''
        data: dataframe
            Data to be assessed.
        data_range: dictionary
            The reasonable physical range of data for each column.
        sampling_rate: int
            Number of samples per hour.
        days_backwards:
            Calculate the missing rate of n days backward at each moment (Completeness).
        '''
        assert len(data_range) == len(data.columns), f"Please give a reasonable data range."
        
        self.data_range = data_range
        self.data = data
        self.sampling_rate = sampling_rate
        self.step = self.sampling_rate*24*days_backwards
        self.save_result = save_result

        for param, value in kw.items():
            setattr(self, param, value)
    

    def assess(self) -> None:

        data = self.data
        save = self.save_result
        path = self.result_path
        label = self.label
        step  = self.step
        data_range = self.data_range
        sampling_rate = self.sampling_rate

        statistic(df=data, save_result=save, result_path=path, label=label)
        usability(df=data, label=label)
        reliability(df=data, data_range=data_range, save_result=save, result_path=path, label=label)
        completeness(df=data, sampling_rate=sampling_rate, save_result=save, result_path=path, label=label, step=step)
        multi(df=data, data_range=data_range, save_result=save, result_path=path, label=label)
        consistency(df=data, label=label)

        return
        

    def evaluate(self):
        pass


def statistic(df:pd.DataFrame, save_result, result_path, label='original', **kw) -> None:
    '''
    Calculate statistics description and correlations of data.

    '''
    print('\nStatistic----------------------------------------')

    print(df.describe())
    print(df.corr())

    sns.heatmap(df.corr(), cmap="hot_r")

    plt.title('Pearson Correlation Coefficient')
    plt.gcf().set_size_inches(6.76, 5)
    plt.tight_layout()
    if save_result:
        plt.savefig(result_path+'\correlation'+f'_{label}.png', dpi=300)
    plt.show()

    return


def usability(df:pd.DataFrame, label='original', **kw) -> None:
    '''
    Determine whether the data type belongs to (int, float).

    '''
    print('\nUsability----------------------------------------')

    for col in df.columns:
        s = df[col]
        # 判断数据类型是否为 int 或 float，返回布尔值
        mask = s.apply(lambda x: isinstance(x, (int, float)))
        s_valid = s[mask]
        # 计算数量和占比
        valid_cnt = s_valid.shape[0]
        total_cnt = s.shape[0]
        valid_ratio = valid_cnt / total_cnt

        print(f'{label, col}: int和float类型数据的数量为{valid_cnt}, 数据总数为{total_cnt}, 有效数据占比为{valid_ratio: .2%}.')

    return


def reliability(df:pd.DataFrame, data_range:dict, save_result, result_path, label='original', **kw) -> None:
    '''
    - Whether the data is within a reasonable physical range.
    - Estimate the distribution of each column of data and calculate the highest posterior density interval (HPD).

    Parameters
    -----
    df: Dataframe.
    data_range: the reasonable physical range of data for each column.
    save_result: True/False.
    result_path: the path to save the resulting image.
    '''
    print('\nReliability----------------------------------------')
    data = copy.deepcopy(df)
    
    for col in data.columns:
        s = data[col]
        lower_bound = data_range[col][0]
        upper_bound = data_range[col][1]
        count = s[(s >= lower_bound) & (s <= upper_bound)].count()
        num_ratio = count / s.shape[0]
        print(f'{label, col}: 范围内的数据个数为{count}, 占比为{num_ratio: .2%}.')
        data[col] = s[(s >= lower_bound) & (s <= upper_bound)]

    for col in data.columns:
        s = data[col].to_frame().dropna()
        plot_hpd(s, roundto=2, alpha=0.0027, show_mode=False)
        plt.legend(loc=0, 
                #    fontsize=6
                   )
        # plt.xlabel(r"$\theta$")
        plt.xlabel('Data range')
        plt.title('KDE'+f'_{col}')
        plt.gcf().set_size_inches(6.76, 3.5)
        plt.tight_layout()
        if save_result:
            plt.savefig(result_path+'\KDE'+f'_{col}_{label}.png', dpi=300)
        plt.show()

    return


def completeness(df:pd.DataFrame, sampling_rate:int, save_result, result_path, step=4*24*2, label='original', **kw) -> None:
    '''
    - Calculate the missing rate for each column of data.
    - Count the missing time intervals of each column of data.

    Parameters
    -----
    df: Dataframe.
    save_result: True/False.
    result_path: the path to save the resulting image.
    '''
    print('\nCompleteness----------------------------------------')

    for col in df.columns:
        ms = 1 - (df[col].count() / df[col].shape[0])
        print(f'{label, col} 总缺失率: {ms: .2%}')

    missing_rate = pd.DataFrame(data=None, index=df.index, columns=df.columns)
    for col in df.columns:
        missing_rate[col] = 1 - (df[col].rolling(step, min_periods=0).count() / float(step))
    missing_rate.plot()
    plt.title(f'Missing Rate ({round(step/sampling_rate/24, 2)} days backward)')
    plt.gcf().set_size_inches(6.76, 5)
    plt.legend(loc = 'upper right', fontsize=6)
    plt.tight_layout()
    if save_result:
        plt.savefig(result_path+'\missing_rate'+f'_{label}.png', dpi=300)
    plt.show()
    print('statistics of missing rate:')
    print(missing_rate.describe())

    # df_intervals = pd.DataFrame(data=None, columns=data.columns)
    for col in df.columns:
        # 转换为DataFrame并添加标记缺失数据的列
        df_col = pd.DataFrame({'data': df[col]})
        df_col['is_missing'] = df_col['data'].isnull().astype(int)
        # 计算非缺失数据点之间的缺失时间间隔
        df_col['time_diff'] = df_col[df_col['is_missing'] == 0].index.to_series().diff().dt.total_seconds() / 3600
        # 筛选出所有缺失区间的后边界点（sampling_rate=4/h时，>0.25h即有缺失）
        diff_thresh = 1 / sampling_rate
        bound = df_col[df_col['time_diff'] > diff_thresh]['time_diff']

        print(f'{label, col} missing intervals <= 4h: {bound[bound<=4].count() / bound.shape[0]: .2%}.')
        print(f'{label, col} missing intervals <= 0.5h: {bound[bound<=0.5].count() / bound.shape[0]: .2%}.')
        print(bound[bound<=4].count(), bound.shape[0])

        interval_max = bound.max()
        plt.hist(bound, 
                bins=[n for n in np.arange(0, int(interval_max), 4)], 
                edgecolor='w', 
                density=True, 
                label=col)
        plt.title('Histogram of Missing Time Intervals')
        plt.xlabel('Hours of Missing Intervals')
        plt.ylabel('Frequency')
        plt.legend(loc = 'upper right')
        plt.gcf().set_size_inches(6.76, 3.5)
        plt.xlim(-5, 100)
        plt.tight_layout()
        if save_result:
            plt.savefig(result_path+'\missing_intervals_hist'+f'_{col}_{label}.png', dpi=300)
        plt.show()

    return


def consistency(df:pd.DataFrame, label='original', **kw):
    '''
    According to the constraint relationship of the Coefficient Of Performance (COP), 
    it is judged whether the cooling capacity and the energy consumption data of the VRF are reasonable.
    1 <= COP <= 10.

    '''
    print('\nConsistency----------------------------------------')

    lower_bound = 1
    upper_bound = 10

    data = df[['Qac', 'Pvrf']]
    # data.loc[:, 'COP'] = data['Qac'] / data['Pvrf']
    data.insert(loc=2, column='COP', value=data['Qac']/data['Pvrf'])
    # data.loc[:, 'COP'] = data['COP'].copy().replace([np.inf, -np.inf, 0], np.nan, inplace=False)
    data = data.replace({'COP':[np.inf, -np.inf, 0]}, np.nan)

    range_cnt = data['COP'][(data['COP'] >= 1) & (data['COP'] <= 10)].count()
    cnt = data['COP'].count()
    ratio = range_cnt / cnt
    print(f'{label}: 合理的COP数据条数为{cnt}, 范围内的COP数据条数为{range_cnt}, 占比为{ratio: .2%}.')

    sns.heatmap(data.T, vmin=0, vmax=100)
    plt.title('Multivariable Missing Status')
    data.plot(figsize=(12,6))
    plt.ylim(-20, 120)
    plt.show()
    # print(data.shape)

    return


def multi(df:pd.DataFrame, data_range:dict, save_result, result_path, label='original', **kw) -> None:
    '''
    Calculate the proportion of data that are both free of missing data and 
    within a reasonable physical range to all data.

    '''
    print('\nMulti----------------------------------------')

    df_dropna = df.dropna()
    ratio = df_dropna.shape[0] / df.shape[0]
    print(f'{label}: 同时无缺失的数据条数为{df_dropna.shape[0]}, 占比为{ratio: .2%}.')
    
    data = copy.deepcopy(df)
    for col in data.columns:
        lower_bound = data_range[col][0]
        upper_bound = data_range[col][1]
        data[col][(data[col] < lower_bound) | (data[col] > upper_bound)] = np.nan
    data_dropna = data.dropna()
    ratio = data_dropna.shape[0] / df.shape[0]
    print(f'{label}: 范围内同时无缺失的数据条数为{data_dropna.shape[0]}, 占比为{ratio: .2%}.')

    data.index = data.index.date
    sns.heatmap(data.T,
                vmin=-20, vmax=200,)
    plt.title('Multivariable Missing Status')
    plt.gcf().set_size_inches(6.76, 5)
    plt.tight_layout()
    if save_result:
        plt.savefig(result_path+'\multi_missing_status'+f'_{label}.png', dpi=300)
    plt.show()

    return


def hpd_grid(sample, alpha=0.05, roundto=2):
    """
    Calculate highest posterior density (HPD) of array for given alpha.
    The HPD is the minimum width Bayesian credible interval (BCI).
    The function works for multimodal distributions, returning more than one mode

    Parameters
    ----------
    sample : Numpy array or python list
        An array containing MCMC samples
    alpha : float
        Desired probability of type I error (defaults to 0.05)
    roundto: integer
        Number of digits after the decimal point for the results

    Returns
    ----------
    hpd: array with the lower

    """
    sample = np.asarray(sample)
    sample = sample[~np.isnan(sample)]
    # get upper and lower bounds
    l = np.min(sample)
    u = np.max(sample)
    density = kde.gaussian_kde(sample)
    x = np.linspace(l, u, 5000)
    y = density.evaluate(x)
    # y = density.evaluate(x, l, u) waitting for PR to be accepted
    xy_zipped = zip(x, y / np.sum(y))
    xy = sorted(xy_zipped, key=lambda x: x[1], reverse=True)
    xy_cum_sum = 0
    hdv = []
    for val in xy:
        xy_cum_sum += val[1]
        hdv.append(val[0])
        if xy_cum_sum >= (1 - alpha):
            break
    hdv.sort()
    diff = (u - l) / 20  # differences of 5%
    hpd = []
    hpd.append(round(min(hdv), roundto))
    for i in range(1, len(hdv)):
        if hdv[i] - hdv[i - 1] >= diff:
            hpd.append(round(hdv[i - 1], roundto))
            hpd.append(round(hdv[i], roundto))
    hpd.append(round(max(hdv), roundto))
    ite = iter(hpd)
    hpd = list(zip(ite, ite))
    modes = []
    for value in hpd:
        x_hpd = x[(x > value[0]) & (x < value[1])]
        y_hpd = y[(x > value[0]) & (x < value[1])]
        modes.append(round(x_hpd[np.argmax(y_hpd)], roundto))
    return hpd, x, y, modes


def plot_hpd(sample, alpha=0.05, show_mode=False, kde_plot=True, bins=50,
              ROPE=None, comp_val=None, roundto=2):
    """
    Plot posterior and HPD.

    Parameters
    ----------
    sample : Numpy array or python list
        An array containing MCMC samples
    alpha : float
        Desired probability of type I error (defaults to 0.05)
    show_mode: Bool
        If True the legend will show the mode(s) value(s), if false the mean(s)
        will be displayed
    kde_plot: Bool
        If True the posterior will be displayed using a Kernel Density Estimation
        otherwise an histogram will be used
    bins: integer
        Number of bins used for the histogram, only works when kde_plot is False
    ROPE: list or numpy array
        Lower and upper values of the Region Of Practical Equivalence
    comp_val: float
        Comparison value

    Returns
    -------
    post_summary : dictionary
        Containing values with several summary statistics

    """

    post_summary = {'mean': 0, 'median': 0, 'mode': 0, 'alpha': 0, 'hpd_low': 0,
                    'hpd_high': 0, 'comp_val': 0, 'pc_gt_comp_val': 0, 'ROPE_low': 0,
                    'ROPE_high': 0, 'pc_in_ROPE': 0}

    post_summary['mean'] = round(np.mean(sample), roundto)
    post_summary['median'] = round(np.median(sample), roundto)
    post_summary['alpha'] = alpha

    # Compute the hpd, KDE and mode for the posterior
    hpd, x, y, modes = hpd_grid(sample, alpha, roundto)
    post_summary['hpd'] = hpd
    post_summary['mode'] = modes

    ## Plot KDE.
    if kde_plot:
        plt.plot(x, y, color='k', lw=2)
    ## Plot histogram.
    else:
        plt.hist(sample, bins=bins, facecolor='b', edgecolor='w')

    # Display mode or mean:
    if show_mode:
        string = '{:g} ' * len(post_summary['mode'])
        plt.plot(0, label='mode =' + string.format(*post_summary['mode']), alpha=0)
    else:
        pass
        # plt.plot(0, label='mean = {:g}'.format(post_summary['mean']), alpha=0)
        # plt.plot(0, label='mean =' + '{:g}'.format(post_summary['mean'][0]), alpha=0)

    ## Display the hpd.
    hpd_label = ''
    for value in hpd:
        plt.plot(value, [0, 0], linewidth=10, color='gray')
        hpd_label = hpd_label + '[{:g}, {:g}]\n'.format(round(value[0], roundto), round(value[1], roundto))
    plt.plot(0, 0, linewidth=2, color='gray', label='HPD {:g}%\n{}'.format((1 - alpha) * 100, hpd_label))
    ## Display the ROPE.
    if ROPE is not None:
        pc_in_ROPE = round(np.sum((sample > ROPE[0]) & (sample < ROPE[1])) / len(sample) * 100, roundto)
        plt.plot(ROPE, [0, 0], linewidth=20, color='r', alpha=0.75)
        plt.plot(0, 0, linewidth=4, color='r', label='{:g}% in ROPE'.format(pc_in_ROPE))
        post_summary['ROPE_low'] = ROPE[0]
        post_summary['ROPE_high'] = ROPE[1]
        post_summary['pc_in_ROPE'] = pc_in_ROPE
    ## Display the comparison value.
    if comp_val is not None:
        pc_gt_comp_val = round(100 * np.sum(sample > comp_val) / len(sample), roundto)
        pc_lt_comp_val = round(100 - pc_gt_comp_val, roundto)
        plt.axvline(comp_val, ymax=.75, color='g', linewidth=4, alpha=0.75,
                    label='{:g}% < {:g} < {:g}%'.format(pc_lt_comp_val,
                                                        comp_val, pc_gt_comp_val))
        post_summary['comp_val'] = comp_val
        post_summary['pc_gt_comp_val'] = pc_gt_comp_val

    plt.legend(loc=0, framealpha=1)
    frame = plt.gca()
    frame.axes.get_yaxis().set_ticks([])
    return post_summary


#%%
if __name__ == '__main__':

    import json
    # with open(r'C:\Users\Wang\Desktop\dqa\87JG\data_point_all.json', 'r') as f:
    #     data_point = json.load(f)

    # start_time = pd.to_datetime('2022-05-01 00:00:00')
    # end_time = pd.to_datetime('2022-12-31 23:45:00')
    # rsp_time = '15 min'
    # data = preprocess.get_data(data_point, start_time, end_time, rsp_time)

    num_indoor = [0,1,2,3,4,5,6]

    # with open(r'C:\Users\Wang\Desktop\dqa\87JG\data_all.pkl', 'wb') as f:
    #     pickle.dump(data, f)
    with open(r'C:\Users\Wang\Desktop\dqa\1K0V\data_all.pkl', 'rb') as f:
        data = pickle.load(f)

    data['Qin'] = data['Qin'].diff()
    data['Pvrf'] = data['Pvrf'].diff()
    # unified units into KW, convenient to plot
    data['Qin'] = data['Qin'] / 0.25
    data['Pvrf'] = data['Pvrf'] / 0.25
    data['Qs'] = data['Qs'] / 1000
    data['Qac'] = data['Qac'] / 1000

    data['Pvrf_sys'] = data['Pvrf_sys'].diff()
    data['Pvrf_sys'] = data['Pvrf_sys'] / 0.25
    data['Qac_sys'] = data['Qac_sys'] / 1000

    for indoor_num in num_indoor:
        data[f'Qac{indoor_num}'] = data[f'Qac{indoor_num}'] / 1000

    data['Ti'] = data.filter(like='Ti').mean(axis=1)

    # data = data[['Pvrf', 'Pvrf_sys']]
    # # data = data[['Qac', 'Qac_sys']]
    # data, _ = preprocess.od_range(data, {'Pvrf': (0,100), 'Pvrf_sys': (0,100)})
    # data = data.dropna()
    # data.plot()
    # plt.show()
    # a = data['Pvrf_sys'].to_numpy()
    # b = data['Pvrf'].to_numpy()
    # rmse = np.sqrt(np.mean((a-b)**2))
    # print(rmse)


    # 使用 apply() 方法和 lambda 函数选择其中一列的数值
    data['Pvrf'] = data.apply(lambda row: row['Pvrf'] if pd.notnull(row['Pvrf']) else row['Pvrf_sys'], axis=1)
    # data['Qac'] = data.apply(lambda row: row['Qac'] if pd.notnull(row['Qac']) else row['Qac_sys'], axis=1)


    order = ['Ti', 'Ta', 'Qs', 'Qin', 'Qac', 'Pvrf']
    for indoor_num in num_indoor:
        order.append(f'Ti{indoor_num}')
        order.append(f'Sc{indoor_num}')
        order.append(f'Qac{indoor_num}')
    data = data[order]

    df = copy.deepcopy(data)
    df.index = df.index.date
    sns.heatmap(df.T, 
                vmin=-20, vmax=100,
                # xticklabels=labels
                )
    plt.title('Multivariable Missing Status')
    plt.show()

    data.plot()
    plt.ylim(-20, 100)
    plt.title('Data')
    plt.gcf().set_size_inches(6.76, 5)
    plt.legend(loc=1, 
            #    fontsize=4
            )
    plt.tight_layout()
    plt.savefig(r'C:\Users\Wang\Desktop\dqa\1K0V.png', dpi=300)
    plt.show()

    print(data.shape)


    data_range = {
        'Ti': (-10, 50),
        'Ta': (-10, 50),
        'Qs': (0, 100),
        'Qin': (0, 100),
        'Qac': (0, 100),
        'Pvrf': (0, 200),
        
        # 'Pvrf_sys': (0, 200),
        # 'COP': (1, 10),
    }

    linear_time_delta = {
            'Ti': '4 hours',
            'Ta': '4 hours',
            'Qs': '1 hours',
            'Qin': '4 hours',
            'Qac': '0.5 hours',
            'Pvrf': '0.5 hours',
    }

    for indoor_num in num_indoor:
        data_range[f'Ti{indoor_num}'] = (-10, 50)
        data_range[f'Qac{indoor_num}'] = (0, 100)
        data_range[f'Sc{indoor_num}'] = (0, 400)
        # data_range[f'Qac_sys{indoor_num}'] = (0, 100)

        linear_time_delta[f'Ti{indoor_num}'] = '4 hours'
        linear_time_delta[f'Qac{indoor_num}'] = '0.5 hours'
        linear_time_delta[f'Sc{indoor_num}'] = '0.5 hours'
        # column_type[f'Qac_sys{indoor_num}'] = 'Other'

    params = {
        # common parameters
        'sampling_time': pd.Timedelta('15 min'),
        'sampling_rate': 4,   # 4 times per hour, depends on sampling_time.

        # parameters of outlier detection
        'data_range': data_range,
        'kd_bandwidth': 1.0,
        'kd_ratio': 0.005,
        'abrupt_win_size': 5,
        'abrupt_thresh': 2.5,

        # parameters of data imputation
        # data missing for more than consecutive linear_time_delta will not be linear imputation.
        'linear_time_delta': linear_time_delta,

        # parameters of obtain valid data (by calculating missing rate)
        'ms_thresh': 0.0,   # the condition of missing rate (< ms_thresh) for multiple data.
        'mode': 'closest',   # 'closest'(time first), 'longset'(data length first).
        'interval_min_day': 3,   # minimum number of days needed for training.
        'interval_max_day': 14,   # maximum number of days needed for training.
    }


    column_type = {
        'Ti': 'T_amb',
        'Ta': 'T_amb',
        'Qs': 'Other',
        'Qin': 'Meter',
        'Qac': 'Other',
        'Pvrf': 'Meter',
        # 'Pvrf_sys': 'Meter',
        # 'COP': 'Other',
    }
    for indoor_num in num_indoor:
        column_type[f'Ti{indoor_num}'] = 'T_amb'
        column_type[f'Qac{indoor_num}'] = 'Other'
        column_type[f'Sc{indoor_num}'] = 'Other'
        # column_type[f'Qac_sys{indoor_num}'] = 'Other'

    path = r'C:\Users\Wang\Desktop\dqa\1K0V\merge\original'
    dqa = DQA(data=data, data_range=data_range, save_result=True, result_path=path, label='original')
    dqa.assess()

    # pre = preprocess.DataPreprocess(data=data, column_type=column_type, **params)
    # pre.process()
    # print('Preprocessing complete----------------------------------------')

    # pre.data_rmol.plot(figsize=(12,6))
    # plt.ylim(-20, 120)
    # plt.show()
    # pre.data_rmol_impute.plot(figsize=(12,6))
    # plt.ylim(-20, 120)
    # plt.show()

    #%%

    # path = r'C:\Users\Wang\Desktop\dqa\1K0V\merge\original'
    # dqa = DQA(data=pre.data, data_range=data_range, save_result=True, result_path=path, label='original')
    # dqa.assess()

    # path = r'C:\Users\Wang\Desktop\dqa\1K0V\od'
    # dqa = DQA(data=pre.data_rmol, data_range=data_range, save_result=True, result_path=path, label='od')
    # dqa.assess()

    # path = r'C:\Users\Wang\Desktop\dqa\1K0V\merge\od_impute'
    # dqa = DQA(data=pre.data_rmol_impute, data_range=data_range, save_result=True, result_path=path, label='od_impute')
    # dqa.assess()

    # %%
