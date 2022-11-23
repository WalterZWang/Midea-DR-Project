import urllib
import uuid
import sys
import sqlite3
from sqlite3 import Error
import schedule
import time
import pandas as pd
import numpy as np


def get_data():
    
    appcode = '789ec652cb99459694b7789ceeb51e66'
    # url = "http://latlon1.market.alicloudapi.com/realtime/114,22?alert=false"
    url = 'http://latlon1.market.alicloudapi.com/forecast/hourly/113.28,22.76?hourlysteps=48'

    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    request.add_header('X-Ca-Nonce', str(uuid.uuid4()))
    response = urllib.request.urlopen(request)
    content = eval(str(response.read(),'utf-8'))

    return content


def create_table():
    
    con = sqlite3.connect("real_time.db")
    c = con.cursor()
    
    sql = '''
       create table real_time
           (time text not null,
           temp real not null,
           humi real not null,
           dswrf real not null);

     '''
  
    c.execute(sql) 
    con.commit()
    con.close()
    
    print("table established")
    
def insert_data():     # forecast solar radiance for next 24h
    
    content = get_data()
    con = sqlite3.connect("real_time.db")
    c = con.cursor()
    current_time = time.strftime('%b %d %H:%M', time.localtime())
    
    temp_data = (current_time,
                 content["result"]["realtime"]["temperature"],
                 content["result"]["realtime"]["humidity"],
                 content["result"]["realtime"]["dswrf"],
)
    
    sql = '''
       insert into real_time (time, temp, humi, dswrf)
           values (?,?,?,?)
           
           '''
    c.execute(sql, temp_data) 
    con.commit()
    print("done")

    con.close() 
   
   
# create_table()
# insert_data()

# schedule.every(15).minutes.do(insert_data)

# while True:
#     schedule.run_pending()
#     time.sleep(1)

def to_dataframe(content):
    hourly_forecast = content['result']['hourly']
    all_df = pd.DataFrame()

    for key,item in hourly_forecast.items():
        # print(type(item))
        if 'list' in str(type(item)):
            df = pd.DataFrame(item)
            df = df.rename(columns = {'value': key})
            all_df = pd.concat([all_df, df],axis = 1)
    all_df = all_df.drop_duplicates().T.drop_duplicates().T
    all_df['datetime'] = pd.to_datetime(all_df['datetime'])
    df_excel = all_df.copy()
    df_excel['datetime'] = df_excel['datetime'].map(lambda x: x.replace(tzinfo=None))
    df_excel.set_index('datetime', inplace = True)
    df_excel.to_excel(str(df_excel.index[0].date()) + '_' +str(df_excel.index[0].hour) +'.xlsx')
    return all_df

if __name__ == "__main__":
    content = get_data()
    all_df = to_dataframe(content)
    
