# -*- coding: utf-8 -*-
"""
Created on Tue Jan 11 19:46:50 2022

@author: Mingyue Guo
"""

import math
from pytz import timezone
import pandas as pd

# Note: re moduule only used for parsing lat long from string

    
def leapyear(year):  
    if year % 400 == 0:   return True
    elif year % 100 == 0: return False  
    elif year % 4 == 0:   return True  
    else: return False

def leapYearsSince1949(year):
    leapYearsTo1949 = 472 # Number of leap years is theoretical based on current leap year rules.
    leapDaysInAYear = 0.2425
    leapYearsToGivenYear = int(year * leapDaysInAYear)
    leapYearsBetweenYears = leapYearsToGivenYear - leapYearsTo1949
    return leapYearsBetweenYears

def calc_time(year, month, day, hour=12, minute=0, sec=0):
    # Get day of the year, e.g. Feb 1 = 32, Mar 1 = 61 on leap years
    month_days = [0,31,28,31,30,31,30,31,31,30,31,30]
    day = day + sum(month_days[:month])
    leapdays = leapyear(year) and day >= 60 and (not (month==2 and day==60))
    if leapdays: day += 1

    # Get Julian date - 2400000
    hour = hour + minute / 60.0 + sec / 3600.0 # hour plus fraction
    delta = year - 1949
    leap = leapYearsSince1949(year) # former leapyears
    jd = 32916.5 + (delta * 365) + leap + day + (hour / 24.0)
    # The input to the Astronomer's almanac is the difference between
    # the Julian date and JD 2451545.0 (noon, 1 January 2000)
    time = jd - 51545
    return time

def meanLongitudeDegrees(time):
    return ((280.460 + 0.9856474 * time) % 360)

def meanAnomalyRadians(time):
    return (math.radians((357.528 + 0.9856003 * time) % 360))

def eclipticLongitudeRadians(mnlong, mnanomaly):
    return (math.radians((mnlong + 1.915 * math.sin(mnanomaly) + 0.020 * math.sin(2 * mnanomaly)) % 360))


def eclipticObliquityRadians(time):
    return (math.radians(23.439 - 0.0000004 * time))

def rightAscensionRadians(oblqec, eclong):
    num = math.cos(oblqec) * math.sin(eclong)
    den = math.cos(eclong)
    ra = math.atan(num / den)
    if den<0: ra += math.pi
    if (den >= 0 and num < 0): ra += 2 * math.pi
    return (ra)

def rightDeclinationRadians(oblqec, eclong):
    return (math.asin(math.sin(oblqec) * math.sin(eclong)))

def greenwichMeanSiderealTimeHours(time, hour):
    return ((6.697375 + 0.0657098242 * time + hour) % 24)

def localMeanSiderealTimeRadians(gmst, longitude):
    return (math.radians(15 * ((gmst + longitude / 15.0) % 24)))

def hourAngleRadians(lmst, ra):
    return (((lmst - ra + math.pi) % (2 * math.pi)) - math.pi)

def elevationRadians(lat, dec, ha):
    return (math.asin(math.sin(dec) * math.sin(lat) + math.cos(dec) * math.cos(lat) * math.cos(ha)))

def solarAzimuthRadiansCharlie(lat, dec, ha):
    zenithAngle = math.acos(math.sin(lat) * math.sin(dec) + math.cos(lat) * math.cos(dec) * math.cos(ha))
    az = math.acos((math.sin(lat) * math.cos(zenithAngle) - math.sin(dec)) / (math.cos(lat) * math.sin(zenithAngle)))
    if ha > 0:
        az = az + math.pi
    else:
        az = (3 * math.pi - az) % (2 * math.pi)
    return (az)

def sun_position(year, month, day, hour=12, minute=0, sec=0,
                lat = 46.5, longitude = 6.5):

    time = calc_time(year, month, day, hour, minute, sec)
    hour = hour + minute / 60.0 + sec / 3600.0
    # Ecliptic coordinates  
    mnlong = meanLongitudeDegrees(time)   
    mnanom = meanAnomalyRadians(time)  
    eclong = eclipticLongitudeRadians(mnlong, mnanom)     
    oblqec =  eclipticObliquityRadians(time)
    # Celestial coordinates
    ra = rightAscensionRadians(oblqec, eclong)
    dec = rightDeclinationRadians(oblqec, eclong)
    # Local coordinates
    gmst = greenwichMeanSiderealTimeHours(time, hour)  
    lmst =localMeanSiderealTimeRadians(gmst, longitude)
    # Hour angle
    ha = hourAngleRadians(lmst, ra)
    # Latitude to radians
    lat = math.radians(lat)
    # Azimuth and elevation
    el = elevationRadians(lat, dec, ha)
    #azJ = solarAzimuthRadiansJosh(lat, dec, ha, el)
    azC = solarAzimuthRadiansCharlie(lat, dec, ha)

    elevation = math.degrees(el)
##    azimuthJ  = math.degrees(azJ)
    azimuth  = math.degrees(azC)
    return ( azimuth, elevation)

def datetime_as_timezone(date_time):
    tz = timezone('Asia/Shanghai')
    utc = timezone('UTC')
    return date_time.replace(tzinfo=tz).astimezone(utc)


def S_module(S_incident,beta,psi,alpha,theta):
    S_module = S_incident * (math.cos(alpha)*math.sin(beta)*math.cos(psi-theta) + math.sin(alpha)*math.cos(beta))
    return S_module

#%%
def angles_main(start_time = '20200401', end_time = '20220101'):
    # #HK
    # lat = 22.38
    # lon=114.05
    #Shunde
    lat = 22.76
    lon=113.28

    S_incident = 1
    beta = 90
    psi = 180
    
    time_range = pd.date_range(start_time,end_time ,freq = '15T', closed = 'left')
    angles = pd.DataFrame(index = time_range)
    angles.reset_index(inplace = True)
    angles.rename(columns = {'index':'Timestamp'},inplace = True)
    angles['UTC'] = angles['Timestamp'].apply(lambda x:datetime_as_timezone(x))
    angles['Elevation angle'] = angles['UTC'].apply(lambda x:sun_position(x.year,x.month,x.day,x.hour
                                                                        ,x.minute, x.second, lat=lat, longitude=lon)[1])
    angles['Azimuth angle'] = angles['UTC'].apply(lambda x:sun_position(x.year,x.month,x.day,x.hour
                                                                        ,x.minute, x.second, lat=lat, longitude=lon)[0])
    angles['S(module)'] = angles.apply(lambda x:S_module(S_incident,beta,psi,x['Elevation angle'],x['Azimuth angle']),axis = 1)
    angles['Timestamp'] = angles['Timestamp'].apply(lambda x:x.replace(tzinfo=timezone('Asia/Shanghai')))

    angles.drop(['UTC'],axis = 1, inplace = True)
    angles.rename(columns={'Timestamp':'time'}, inplace = True)

    angles.set_index('time', inplace = True)
    # angles.to_csv(r'angle1.csv',index = False)
    # #UTC need convert
    # HK_time  =  datetime.datetime.strptime('2020-09-01 00:00:00','%Y-%m-%d %H:%M:%S')
    # UTC_time = datetime_as_ti·mezone(HK_time)
    # # (azimuth, elevation)
    # a = sun_position(UTC_time.year,UTC_time.month,UTC_time.day,UTC_time.hour,
    #                  UTC_time.minute, UTC_time.second, lat=lat, longitude=lon)
    return angles
