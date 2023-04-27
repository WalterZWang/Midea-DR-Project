# Model Predictive Control Deployment

The code is used to deploy the control algorithm on Midea's [ibuilding](https://mbtibuilding.com/) platform.

## Structure of Code

- [main.py](#main)
- [controller_MPC.py](#controller_MPC)
- [Data2DB.py](#Data2DB)

## Mian

```Main.py``` is the entrance to the algorithm when deployed in the [ibuilding](https://mbtibuilding.com/) platform. It mainly includes the following functions: 
- entrance to the algorithm;
- Call the control algorithm program ```Controller_MPC.py```;
- Call the storage database program ```Data2DB.py```;
- Return control commands or error messages.

## Controller_MPC

```Controller_MPC.py``` is a model predictive control algorithm. It mainly includes the following functions: 
- Model predictive control algorithm;
- Return control commands and weather information.

## Data2DB

The function of ```Data2DB.py``` is to store data such as control instructions, indoor temperature, indoor disturbance and outdoor weather into InfluxDB. It mainly includes the following functions: 
- Get the index of the input parameter from the platform;
- Store data such as control instructions, indoor temperature, indoor disturbance and outdoor weather into InfluxDB.

    | :exclamation:  Tip: When running the code ```Data2DB.py``` you need to use ```./Midea-DR-Project/data/Influxdb_API```   |
    |-----------------------------------------|
    


