from datetime import datetime,timedelta
import pytz
import pandas as pd



def get_UCT_offset():
    pacific_now = datetime.now(pytz.timezone('Asia/Shanghai'))

    utc_offset=pacific_now.utcoffset().total_seconds()/60/60
    return utc_offset


def utc2local( utc_dtm ):
    # Convert UTC time to local time（ +8:00 ）
    offset = get_UCT_offset()
    local=utc_dtm + timedelta(hours=offset)
    return local.tz_localize(None)

def local2utc( local_dtm ):
    # Convert local time to UTC time（ -8:00 ）
    offset = get_UCT_offset()
    return local_dtm-timedelta(hours=offset)


def get_field_list(cols,tag_list=None):

    # cols.remove(time_stamp)
    if tag_list is None:
        tag_list=[]

    for i in tag_list:
        cols.remove(i)
    return cols

def fore_data_preprocessing(forecast_df,tag_list=None):
    n_rows = len(forecast_df)
    cols = forecast_df.columns.to_list()
    now_dt = forecast_df.index[0]
    # print(now_dt)


    field_dict = {}

    if tag_list is None:

        field_cols=get_field_list(cols,tag_list)

        for col in field_cols:
            field_dict[col] = dict([(col + "_" + str(i), None) for i in range(0, n_rows)])

            for idx, value in enumerate(forecast_df[col].values):
                field_dict[col][col + '_' + str(idx)] = value

        data_fields = {'datetime': [now_dt]}
        for sub_dict in field_dict.values():
            data_fields.update(sub_dict)

        forecast_df_new = pd.DataFrame(data_fields)




    else:
        field_cols=get_field_list(cols,tag_list)

        for col in field_cols:
            field_dict[col] = dict([(col + "_" + str(i), None) for i in range(0, n_rows)])

            for idx, value in enumerate(forecast_df[col].values):
                field_dict[col][col + '_' + str(idx)] = value

        data_fields = {'datetime': [now_dt]}
        for sub_dict in field_dict.values():
            data_fields.update(sub_dict)

        for tag in tag_list:
            data_fields.update({tag: [forecast_df[tag][0]]})

        forecast_df_new = pd.DataFrame(data_fields)
    forecast_df_new.set_index("datetime",inplace=True)
    # print(forecast_df_new.index)
    return forecast_df_new

def resultset_to_df(reusltset):
    if len(reusltset.items()) == 0:
        return pd.DataFrame()
    keys_list = list(reusltset.items()[0][1])

    cols = list(keys_list[0].keys())


    result = {}
    for s in cols:
        result[s] = []
    for dict in keys_list:
        for s in cols:
            result[s].append(dict[s])

    df = pd.DataFrame(result)
    # df.sort_values(by=['fieldKey'],inplace = True)
    return df

def fore_data_preprocessing_read(forecast_df,field_list,fore_horizon):
    # t_idx=forecast_df.index[0]
    result=[]
    for i in range(1,fore_horizon+1):
        result.append([ forecast_df[field_list[j]+'_'+str(i)][0] for j in range(len(field_list))])

    forecast_df_new=pd.DataFrame(result)
    forecast_df_new.columns = field_list
    return forecast_df_new