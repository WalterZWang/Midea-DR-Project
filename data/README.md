## model

Code for unit testing. Test every code before you push it to the repo

## Structure

``cooling_capacity_calc``: Unit functions to calculate cooling capacity of indoor and outdoor unit

``influxdb_API``: API to access, download, and upload data to the influxddb database

``previous_version``: old version of data, not used any more

``caiyunAPI.py``: API to access and download weather forecast data

``calculate_cooling_capacity.py``: Calculate cooling capacility data for each indoor and outdoor unit

``data_quality_assessment.py``: evaluate the data quality from the following five perspectives (Usability, Completeness, Reliability, Basic statistical quantities, Multivariable). A Jupyternote file is also provided to demonstrate how it can be used

``preprocess.py``: outlier detection and missing data imputation, then identify a valid data section for model training. A Jupyternote file is also provided to demonstrate how it can be used

``solar_angle.py``: calculate solar angle for a given location and give timestamp