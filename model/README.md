## model

Models for VRF and thermal zones 

## Structure

``data``:  Code about retrieve data and EDA.

``main.py``:  Call all class and functions in this file. Some high-level but temporary functions also in this file but have been commented out.

``get_infuxDB.py``: Get data from influxDB.  

``influxDB_OldPort.py``:  Get data from influxDB port 21621.

``data_processing.py``:  Include basic data clean code and classes of input data for different models.

``models.py``:  Include room model, PV models and VRF model.   

``EDA_west.py``:  EDA code of data from Midea office building  located in west district.

``solar_angle.py``:  Get features about angles which is used in PV prediction part.

``utility.py``:  Functions will be called in various files.


TODO

- [ ] ``plug_light_prediction.py``: Need to be tidy up
