import calendar
import os

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from Influxdb_API.Influxdb_API import ClientInfluxdb
from cooling_capacity_calc.const import *
from cooling_capacity_calc.cc_computations import cc_calc

vrf_system_SN=['0000CC311178CCM26221641000108104','0000CC311178CCM26232341000271K0V',
                '0000CC311178CCM262323410008787JG','0000CC311178CCM2623234100089GUN5',
                '0000CC311178CCM2625204100009J8UW','0000CC311178CCM2625194100032JSJR']


def data_processing(df, resample_freq):
    """
    Performs post-processing operations on a DataFrame.

    Args:
        df (pd.DataFrame): The DataFrame to be processed.
        resample_freq (str): The frequency at which to resample the DataFrame, e.g. '5min', 'H', etc.

    Returns:
        The processed DataFrame.
    """

    # Convert the data type of the DataFrame to float32.
    df = df.astype('float32')

    # Resample the DataFrame at the specified frequency and take the mean value of each group.
    df = df.resample(resample_freq).mean()

    # Drop any rows that contain missing values.
    df = df.dropna(how='any')

    return df


def plot_figure(df,resample_freq,title,system_code:int=None,idu:int=None):
    """
        Plots a figure using a DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to plot.
            resample_freq (str): The frequency at which to resample the DataFrame, e.g. '5min', 'H', etc.
            title (str): The title of the plot.
            system_code (int): The code of the VRF system to plot the data for.
            idu (int): The ID of the indoor unit to plot the data for.

        Returns:
            None.
        """

    if isinstance(df,pd.Series):
        df=df.to_frame()
    font_size = 13
    fig, ax = plt.subplots(figsize=(20, 8))
    df.index = pd.to_datetime(df.index)
    df = df.resample(resample_freq).mean()
    column_name = df.columns[0]
    color = 'tab:blue'
    ax.plot(df.index, df[column_name],marker='o',color=color,label='cool capacity')

    ax.tick_params(axis='y', labelcolor=color, labelsize=font_size)
    start_time = df.index[0]
    end_time = df.index[-1]

    # Calculate the duration of the time range in hours
    duration_hours = (end_time - start_time).total_seconds() // 3600

    # Set the x-axis interval based on the duration of the time range
    if duration_hours <= 24:
        interval = 1
    elif duration_hours <= 168:
        interval = 6
    elif duration_hours <= 720:##One month
        interval = 2 * 24
    elif duration_hours <= 720*2:#two month
        interval = 4 * 24
    elif duration_hours <= 720*4:
        interval=7*24
    elif duration_hours <= 720*6:
        interval=2*7*24
    else:
        interval=30*7*24

    locator = mdates.HourLocator(interval=interval)
    ax.xaxis.set_major_locator(locator)

    formatter = mdates.DateFormatter('%Y-%m-%d %H')
    ax.xaxis.set_major_formatter(formatter)
    # ax.set_ylim(0, 4000)
    ax.tick_params(axis='x', labelcolor='black', labelsize=font_size)
    if idu is not None:
        db_name = 'moserver'
        params = {
            'measurement_name': 'modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['roomTemp'],
            'tag_dict': {'nid': f'vrf/vrf_{vrf_system_SN[system_code]}/indoor/{idu}'},
            'fore': False,
            'fore_horizon': None,
            'interval': None
        }
        db_client = ClientInfluxdb(db_name=db_name)  # connect the database
        df = db_client.read_influxdb(**params)

        # Clean up temperature data and plot on secondary y-axis
        df = df.astype('float32')
        df = df.replace(0, np.nan)
        color = 'tab:green'
        ax2= ax.twinx()
        ax2.plot(df.index,df['roomTemp'],label=f'idu_{idu}_Temp',color=color)
        ax2.tick_params(axis='y', labelcolor=color,labelsize=font_size)
        ax2.set_ylim(20, 42)

        ax.legend(loc='upper left', fontsize=14)
        ax2.legend(loc='upper right',fontsize=14)
    # fig.savefig(f'/home/wanfu/Downloads/time{i}.png', dpi=500)


    plt.xticks(rotation=45);  # ; at the end of the line of code suppresses the output of the tick marks and labels by telling Jupyter Notebook to not print the output of the last line of code. In other words, the semicolon terminates the line of code without printing the output.
    plt.title(title)
    plt.show()

def query_cp(start_time:str,end_time:str,resample_freq:str,vrf_systems:list,plot:bool=False,
             save_result:bool=False,folder:str='./cooling_capacity_result'):
    """
        Calculate cooling capacity data for VRF (Variable Refrigerant Flow) systems using data from an InfluxDB database.

        Args:
            start_time (str): The start time of the data to retrieve from the database.
            end_time (str): The end time of the data to retrieve from the database.
            vrf_systems (list): The indexes of VRF systems to retrieve data for.
            plot (bool): A boolean indicating whether or not to plot the data retrieved. Default is False.
            save_result (bool): A boolean indicating whether or not to save the data to a file. Default is False.
            folder (str): The folder to save the data to. Default is './cooling_capacity_result'.

        Returns:

        """
    # Convert start_time and end_time to datetime objects
    start_time = pd.to_datetime(start_time)
    end_time = pd.to_datetime(end_time)

    # db_name variable is used later to connect to an InfluxDB database with that name.
    db_name = 'moserver'

    vrf_emeter_data={'vrf_system_SN':['0000CC311178CCM26221641000108104','0000CC311178CCM26232341000271K0V',
                                      '0000CC311178CCM262323410008787JG','0000CC311178CCM2623234100089GUN5',
                                      '0000CC311178CCM2625204100009J8UW','0000CC311178CCM2625194100032JSJR']}

    vrf_emeter=pd.DataFrame(vrf_emeter_data)


    # 内机匹数信息
    idu_hp_data = [[4.0, 2.0, 3.2, 2.0, 4.0, 2.0, 4.0, 3.2, 4.0, 3.2, 3.2, 4.0, 2.5], [4.0, 3.0, 3.0, 3.0, 3.2, 4.0, 4.0],
              [3.6, 3.6, 3.6], [2.5, 5.0, 2.5, 2.5], [3.2, 2.5, 3.2, 1.7, 2.5, 3.2, 3.2, 2.5, 3.2, 2.5, 2.5]]
    # 内机地址信息
    sys_addr_data = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                [0, 1, 2, 3, 4, 5, 6],
                [0, 1, 2],
                [0, 1, 2, 3],
                [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 20]]

    # 外机地址信息
    sys_odu_addr_data = [[129], [129], [129], [129], [129]]

    idu_hp=[idu_hp_data[i] for i in vrf_systems]

    sys_addr=[sys_addr_data[i] for i in vrf_systems]

    sys_odu_addr=[sys_odu_addr_data[i] for i in vrf_systems]

    #1.读取外机数据

    df_dict_list = [{} for i in range(len(sys_odu_addr))]
    for i in range(len(sys_odu_addr)):
        for addr in sys_odu_addr[i]:

            # Set the nid variable to a string containing the specific vrf_emeter element, the current addr value, and the string 'vrf/vrf_' and '/outdoor/'.
            # which is used to identify a particular data point.
            nid = 'vrf/vrf_' + vrf_emeter.iloc[vrf_systems[i], 0] + '/outdoor/' + str(addr)
            # Set the field_list variable to a list of field names to retrieve from the database
            field_list = ['compressor1Frequency', 'compressor2Frequency', 'compressor1Electricity',
                          'compressor2Electricity', 'directVoltage1', 'directVoltage2', 'dischargeTemp1',
                          'dischargeTemp2', 't3bTemp', 't3Temp', 't4Temp', 't5Temp', 'inletT6ATemp', 'outletT6BTemp',
                          't8Temp', 't9Temp', 'tgTemp', 'tLTemp', 'exv1Opening', 'exv2Opening', 'exv3Opening',
                          'highPressure', 'lowPressure', 'highPressureSaturationTemp', 'lowPressureSaturationTemp',
                          'SV1', 'SV2', 'SV3', 'SV4', 'SV5', 'SV6', 'SV7', 'SV8', 'SV8B', 'SV9', 'compressorCCUnit',
                          'compressorBrand', 'compressor1Displacement', 'compressor2Displacement', 'airOutType',
                          'outdoorPlateHorses']

            # Set the params variable to a dictionary of parameters used in the read_influxdb method of the ClientInfluxdb class.

            params = {
                'measurement_name': 'modata',
                'start_time': start_time,
                'end_time': end_time,
                'field_list': field_list,
                'tag_dict': {'nid': nid},
                'fore': False,
                'fore_horizon': None,
                'interval': None
            }

            # Create a new ClientInfluxdb instance and connect to the database.
            db_client = ClientInfluxdb(db_name=db_name)  # connect the database
            # Call the read_influxdb method of the ClientInfluxdb instance with the params dictionary and assign the returned dataframe to the df variable.
            try:
                df = db_client.read_influxdb(**params)
            except:
                continue


            df=data_processing(df,resample_freq)
            # the nearest integer using the round() function. This is done to remove any decimal points that may be present in the values
            df['compressor1Frequency'] = df['compressor1Frequency'].round()
            df['compressor2Frequency'] = df['compressor2Frequency'].round()

            # rounds off the values in the highPressure column of the df DataFrame to 2 decimal places using the round() function.
            df['highPressure'] = df['highPressure'].apply(lambda x: round(x, 2))
            df['lowPressure'] = df['lowPressure'].apply(lambda x: round(x, 2))


            # create a new key-value pair in the dictionary, where the key is the original field name,
            # and the value is the new name which consists of "odu_" concatenated with the addr variable
            # (which represents the address of the system outdoor unit) and the original field name.
            rename_columns = {field:'odu_' + str(addr) + '_' + field for field in field_list}
            # rename the columns of the DataFrame according to the rename_columns dictionary.
            df.rename(columns=rename_columns, inplace=True)

            # add the renamed DataFrame to the dictionary df_dict_list, with a key of "sys_odu" concatenated
            # with the addr variable (which represents the address of the system outdoor unit).
            # This creates a nested dictionary where each outdoor unit's data is stored under the corresponding key.
            df_dict_list[i]['sys_odu' + str(addr)] = df

    # 2.读取内机数据
    for i,system_code in enumerate(vrf_systems):

        for addr in sys_addr[i]:
            nid = 'vrf/vrf_' + vrf_emeter.iloc[vrf_systems[i], 0] + '/indoor/' + str(addr)
            params = {
                'measurement_name': 'modata',
                'start_time': start_time,
                'end_time': end_time,
                'field_list': ['exv1Opening'],
                'tag_dict': {'nid': nid},
                'fore': False,
                'fore_horizon': None,
                'interval': None}
            db_client = ClientInfluxdb(db_name=db_name)  # connect the database
            df = db_client.read_influxdb(**params)

            ##debug 时用
            # folder_name = f'{folder}/sys{system_code}'
            # file_path = os.path.join(folder_name, f'sys{system_code}_idu_{addr}_raw.csv')
            # df.to_csv(file_path, encoding='utf-8', index=True)

            df=data_processing(df,resample_freq)
            df.rename(columns={'exv1Opening': 'idu_' + str(addr) + '_exv1Opening'}, inplace=True)
            df_dict_list[i]['sys_idu' + str(addr)] = df
    # 3.读取系统数据
    for i,system_code in enumerate(vrf_systems):
        nid = 'vrf/vrf_' + vrf_emeter.iloc[vrf_systems[i], 0]
        params = {
            'measurement_name': 'modata',
            'start_time': start_time,
            'end_time': end_time,
            'field_list': ['runMode'],
            'tag_dict': {'nid': nid},
            'fore': False,
            'fore_horizon': None,
            'interval': None
        }
        db_client = ClientInfluxdb(db_name=db_name)  # connect the database
        df = db_client.read_influxdb(**params)

        # ##debug 时用
        # folder_name = f'{folder}/sys{system_code}'
        # file_path = os.path.join(folder_name, f'sys{system_code}_runMode_raw.csv')
        # df.to_csv(file_path, encoding='utf-8', index=True)

        df=data_processing(df,resample_freq)
        df['runMode'][df.runMode > 0] = 2
        df_dict_list[i]['sys_vrf'] = df


    # 4.merge dataframe
    df_list = []
    for df_dict in df_dict_list:

        for df_name, df in df_dict.items():

            if df_name == 'sys_vrf':
                continue
            df_dict['sys_vrf'] = df_dict['sys_vrf'].join(df)

        df_dict['sys_vrf'] = df_dict['sys_vrf'].dropna(how='any')
        df_list.append(df_dict['sys_vrf'])

    for idx,system_code in enumerate(vrf_systems):
        df = df_list[idx]

        # 内机地址信息
        single_sys_idu_addr = sys_addr[idx]

        # 外机地址信息
        single_sys_odu_addr = sys_odu_addr[idx]

        single_idu_hp = idu_hp[idx]
        df_Qcool, df_runmode, df_total = cc_calc(df, single_sys_odu_addr, single_sys_idu_addr, single_idu_hp)

        if save_result:
            folder_name = f'{folder}/sys{system_code}'

            if not os.path.exists(folder_name):
                os.makedirs(folder_name)


            file_path = os.path.join(folder_name, f'sys{system_code}_Qcool_calc_{resample_freq}.csv')

            file_path2=os.path.join(folder_name,f'sys{system_code}_df_totoal_{resample_freq}.csv')

            df_Qcool.to_csv(file_path, encoding='utf-8', index=True)
            df_total.to_csv(file_path2, encoding='utf-8', index=True)

            for j in range(len(single_idu_hp)):
                file_name = f'sys{system_code}_idu_{str(single_sys_idu_addr[j])}_Qcool_calc_{resample_freq}.csv'
                file_path = os.path.join(folder_name, file_name)
                df_total[['idu_' + str(single_sys_idu_addr[j]) + '_Q_cool']].to_csv(file_path, encoding='utf-8',
                                                                                     index=True)

            file_name = f'sys{system_code}_runmode_{resample_freq}.csv'
            file_path = os.path.join(folder_name, file_name)
            df_runmode.to_csv(file_path, encoding='utf-8', index=True)


        if plot:
            plot_figure(df_Qcool,resample_freq,title=f'vrf_{system_code} total cooling capacity {resample_freq}')

            for j in range(len(single_idu_hp)):
                plot_figure(df_total[['idu_' + str(single_sys_idu_addr[j]) + '_Q_cool']],resample_freq,title=f'vrf_{system_code} idu_{j} cooling capacity {resample_freq}',
                            system_code=system_code,idu=j)




if __name__ == '__main__':
    query_cp(start_time='2022-05-01 12:00:00',end_time='2022-08-01 18:00:00',
             resample_freq='2Min',vrf_systems=[0],plot=True,save_result=True,folder='./cooling_capacity_result')





