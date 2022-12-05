import numpy as np
import pandas as pd
import cvxpy
import datetime
import time

from Influxdb_API import ClientInfluxdb
import get_influxDB

class Controller_MPC():
    # This class is to calculate the optimal action for VRF units using Model Predictive Control (MPC).

    def __init__(self):

        """
        Resistance-Capacity (RC) zone model.

        x(t+1) = Ax(t) + Bu(t) + Ed(t)
        """

        self.A = np.array([[1, 1, 0, 0, 0, 0, 0],
                           [1, 1, 1, 1, 0, 0, 0],
                           [0, 1, 1, 1, 1, 0, 0],
                           [0, 0, 1, 1, 0, 0, 1],
                           [0, 0, 1, 0, 1, 1, 0],
                           [0, 0, 0, 0, 1, 1, 1],
                           [0, 0, 0, 1, 0, 1, 1]])
        self.nx = self.A.shape[1]

        self.B = np.array([[1, 0, 0, 0, 0, 0, 0],
                           [0, 1, 0, 0, 0, 0, 0],
                           [0, 0, 1, 0, 0, 0, 0],
                           [0, 0, 0, 1, 0, 0, 0],
                           [0, 0, 0, 0, 1, 0, 0],
                           [0, 0, 0, 0, 0, 1, 0],
                           [0, 0, 0, 0, 0, 0, 1]])
        self.nu = self.B.shape[1]

        # self.E = np.array([[0.031, 0.031, 0.031],
        #                    [0.031, 0.031, 0.031],
        #                    [0.031, 0.031, 0.031],
        #                    [0.031, 0.031, 0.031],
        #                    [0.031, 0.031, 0.031],
        #                    [0.031, 0.031, 0.031],
        #                    [0.031, 0.031, 0.031]])

        self.E = np.array([[0.031, 0.031],
                           [0.031, 0.031],
                           [0.031, 0.031],
                           [0.031, 0.031],
                           [0.031, 0.031],
                           [0.031, 0.031],
                           [0.031, 0.031]])
        self.nd = self.E.shape[1]

        self.nx = self.A.shape[1]
        self.nu = self.B.shape[1]
        self.nd = self.E.shape[1]

    def mpc_step(self, Tz, Ta_fore, DSWRF_fore):
        """

        Parameters
        ----------
        Tz: float
            Zone temperature in current time step.
        Ta_fore: dict
            Outdoor temperature predictions.
        DSWRF_fore: dict
            Solar radiation predictions.
        MELs_fore: dict
            Internal gains predictions, including occupant, lighting and plug load.

        Returns
        -------
        u: int
            Optimal control action in current time step.
            If u = 0, the VRF is kicked off; otherwise, the VRF is kicked on.

        """

        self.N = 24  # number of prediction horizon

        # Optimal variables
        self.x = cvxpy.Variable((self.nx, self.N + 1))  # state variable
        print("self.x:{}".format(self.x))
        self.u = cvxpy.Variable((self.nu, self.N), integer = True)  # control variable, 0 or 1.
        print("self.u:{}".format(self.u))
        self.s1 = cvxpy.Variable(1)  # slack variable
        self.s2 = cvxpy.Variable(1)  # slack variable

        # Initial conditions
        self.x0 = np.full((7, 1), Tz)
        print("x0:{}".format(self.x0))

        # Weighting factors for slack variables
        self.w1 = np.array([[5000]])
        self.w2 = np.array([[5000]])

        # Control variable bounds
        self.umax = 1
        self.umin = 0

        # State variable bounds
        self.xmax = np.full((1, 7), 26)
        self.xmin = np.full((1, 7), 24)

        # Disturbance prediction
        self.Ta_fore = Ta_fore
        self.DSWRF_fore = DSWRF_fore
        # self.MELs_fore = MELs_fore
        print("self.DSWRF_fore:{}".format(self.DSWRF_fore))

        costlist = 0.0
        constrlist = []

        for t in range(self.N):

            time = datetime.datetime.now() # current hour
            print("time:{}".format(time))
            d = np.array([[self.Ta_fore[t]], [self.DSWRF_fore[t]]])
            print("d:{}".format(d))

            # TODO：change the cooling capacity and power consumption
            # Objective cost
            costlist += (ToU_tariff(time + datetime.timedelta(hours = t))) * (np.full((1, 7), 555) * self.u[:, t]) + \
                        self.w1 @ self.s1 ** 2 + self.w2 @ self.s2 ** 2

            Ax = self.A @ self.x[:, t]
            print("Ax:{}".format(Ax))
            print("Ax.shape:{}".format(Ax.shape))
            Bu = self.B @ (-self.u[:, t])
            print("Bu:{}".format(Bu))
            print("Bu.shape:{}".format(Bu.shape))
            Ed = self.E @ d
            print("Ed:{}".format(Ed))
            print("Ed.shape:{}".format(Ed.shape))

            # Constraints
            constrlist += [self.x[:, t + 1] == self.A @ self.x[:, t] + self.B @ (-self.u[:, t]) + (self.E @ d).flatten()]  # zone temperature constraints
            constrlist += [self.x[:, t + 1] + self.s2 >= self.xmin[:, 0]]
            constrlist += [self.x[:, t + 1] - self.s1 <= self.xmax[:, 0]]

        # Terminal cost
        constrlist += [self.x[:, self.N] + self.s2 >= self.xmin[:, 0]]
        constrlist += [self.x[:, self.N] - self.s1 <= self.xmax[:, 0]]

        constrlist += [self.x[:, 0] == self.x0[:, 0]]  # initial state constraints
        constrlist += [self.u <= self.umax]  # input constraints
        constrlist += [self.u >= self.umin]  # input constraints
        constrlist += [self.s1 >= 0]  # slack variable non-negative
        constrlist += [self.s2 >= 0]  # slack variable non-negative

        prob = cvxpy.Problem(cvxpy.Minimize(costlist), constrlist)

        prob.solve(solver=cvxpy.CPLEX, verbose=False)

        print("self.u.value:{}".format(self.u.value))

        return self.u.value


def ToU_tariff(x):
    """
    This function is to determine the electricity price for each time step.

    Parameters
    ----------
    x: int
        Current hour.

    Returns
    -------
    The electricity price for each time step.

    """

    if x.hour in [11, 15, 16]:
        return 1.32476875

    if x.hour in [10, 14, 17, 18]:
        return 1.06536875

    if x.hour in [8, 9, 12, 13, 19, 20, 21, 22, 23]:
        return 0.63806875

    if x.hour in [0, 1, 2, 3, 4, 5, 6, 7]:
        return 0.25966875


def main():

    # database name
    db_zone = 'moserver'
    db_weather = 'moserveribms'

    # connect the database
    db_client_zone = ClientInfluxdb(db_name=db_zone)
    db_client_weather = ClientInfluxdb(db_name=db_weather)

    while True:
        # Obtain current zone temperature
        Tz = pd.DataFrame()  # an empty dataframe to store zone temperatures

        for i in range(0, 7):
            params_zone = {
                'measurement_name': 'modata',
                'start_time': pd.to_datetime('2022-11-01 00:00:00'),
                'end_time': pd.to_datetime(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                'field_list': ['roomTemp'],
                'tag_dict': {'nid': 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/' + str(i)},
                'fore': False,
                'fore_horizon': None,
                'interval': None
            }
            df_zone = db_client_zone.read_influxdb(**params_zone)
            print("df_zone:{}".format(df_zone))
            Tz = Tz.append(df_zone)
        Tz = Tz.values
        print("Tz:{}".format(Tz))

        # Ambient temp forecast for 24 time-step
        params_weather = {
            'measurement_name': 'weather_forecast',  # denote the measurement name
            'start_time': pd.to_datetime(datetime.datetime.now().replace(minute=0, second=0, microsecond=0)), # since we can only read forecast data at a certain timestamp point
            'end_time': pd.to_datetime(datetime.datetime.now().replace(minute=0, second=0, microsecond=0)),  # so start_time should be equal to end_time
            'field_list': ['DSWRF_fore', 'RH_fore', 'T_fore'],  # denote which fields you are going to retrieve
            'tag_dict': None,
            'fore': True,
            'fore_horizon': 24,  # #denote forecast horizon
            'interval': '60m'  # '60m' means the forecast interval is 60 minutes
        }
        df_weather = db_client_weather.read_influxdb(**params_weather)

        T_fore = df_weather['T_fore'].values
        DSWRF_fore = df_weather['DSWRF_fore'].values
        print("T_fore:{}".format(T_fore))
        print("DSWRF_fore:{}".format(DSWRF_fore))

        # MELs forecast for 24 time-step


        # Instantiate controllers
        con = Controller_MPC()

        # Advance simulation with control signal
        u = con.mpc_step(Tz, T_fore, DSWRF_fore)
        print("u:{}".format(u))

        # Control ac for every 10min
        time.sleep(10)


if __name__ == '__main__':
    """
    main function
    """
    main()
