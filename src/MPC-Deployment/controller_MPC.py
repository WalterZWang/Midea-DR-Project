import numpy as np
import cvxpy
import urllib
import uuid
import json
from flask import json
import datetime


class Controller_MPC(object):
    # This function is to calculate the optimal action.

    def __init__(self, nid):

        """
        Different rooms' RC model
        """
        if nid == 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/0':
            self.A = np.array([[0.999]])
            self.B = np.array([[0.0046]])
            self.E = np.array([[0.0035, 0.0022, 0.00066]])
        elif nid == 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/1':
            self.A = np.array([[0.885]])
            self.B = np.array([[0.0032]])
            self.E = np.array([[0.459, 1.58e-10, 0.00119]])
        elif nid == 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/2':
            self.A = np.array([[0.917]])
            self.B = np.array([[0.0041]])
            self.E = np.array([[0.332, 0.0028, 0.00109]])
        elif nid == 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/3':
            self.A = np.array([[0.834]])
            self.B = np.array([[0.0030]])
            self.E = np.array([[0.662, 0.0121, 0.00128]])
        elif nid == 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/4':
            self.A = np.array([[0.835]])
            self.B = np.array([[0.0024]])
            self.E = np.array([[0.661, 9.25e-5, 0.00128]])
        elif nid == 'vrf/vrf_0000CC311178CCM26232341000271K0V/indoor/5':
            self.A = np.array([[0.897]])
            self.B = np.array([[0.0044]])
            self.E = np.array([[0.412, 1.24e-10, 0.00081]])
        else:
            self.A = np.array([[0.832]])
            self.B = np.array([[0.0067]])
            self.E = np.array([[0.671, 1.02e-10, 0.00108]])

        self.nx = self.A.shape[1]
        self.nu = self.B.shape[1]
        self.nd = self.E.shape[1]

    def mpc_step(self, y, Ta, sol_rad, MELs, logger):
        """
        Parameters
        ----------
        y: room temperature in current time step
        Ta: outdoor temperature predictions
        sol_rad: solar radiation predictions
        Returns
        -------
        u: optimal control action in current time step
        self.u.value: optimal control value for prediction horizons
        """

        N = 24  # number of prediction horizon

        self.x = cvxpy.Variable((self.nx, N + 1))  # state variable
        self.u = cvxpy.Variable((self.nu, N), integer=True)  # control variable
        self.s1 = cvxpy.Variable(1)  # slack variable
        self.s2 = cvxpy.Variable(1)  # slack variable

        # initial conditions
        x0 = np.array([[y]])

        # weighting factors for slack variables
        w1 = np.array([[1000]])
        w2 = np.array([[1000]])

        # control variable bounds
        umax = 1
        umin = 0

        # state variable bounds
        xmax = np.array([[23]])
        xmin = np.array([[21]])

        # weather prediction
        self.Ta = Ta
        self.sol_rad = sol_rad
        self.MELs = MELs

        costlist = 0.0
        constrlist = []

        for t in range(N):
            time = datetime.datetime.now()

            d = np.array([self.Ta[t], self.sol_rad[t], self.MELs[t]])

            # objective cost
            costlist += (1 / 4 * tou_match(time + 15 * datetime.timedelta(minutes=t))) * (
                        2940 * self.u[:, t]) + w1 @ self.s1 ** 2 + w2 @ self.s2 ** 2

            # constraints
            constrlist += [self.x[:, t + 1] == self.A @ self.x[:, t] + self.B @ (
                        -self.u[:, t] * 4000) + self.E @ d]  # room temperature constraints
            constrlist += [self.x[:, t + 1] + self.s2 >= xmin[:, 0]]
            constrlist += [self.x[:, t + 1] - self.s1 <= xmax[:, 0]]

        # terminal cost
        constrlist += [self.x[:, N] + self.s2 >= xmin[:, 0]]
        constrlist += [self.x[:, N] - self.s1 <= xmax[:, 0]]

        constrlist += [self.x[:, 0] == x0[:, 0]]  # initial state constraints
        constrlist += [self.u <= umax]  # input constraints
        constrlist += [self.u >= umin]  # input constraints
        constrlist += [self.s1 >= 0]  # slack variable non-negative
        constrlist += [self.s2 >= 0]  # slack variable non-negative

        prob = cvxpy.Problem(cvxpy.Minimize(costlist), constrlist)

        prob.solve(solver=cvxpy.CPLEX, verbose=False)

        logger.info("室内温度预测")
        logger.info(self.x.value)
        logger.info("control action")
        logger.info(self.u.value)
        logger.info("软约束s1")
        logger.info(self.s1)
        logger.info("软约束s2")
        logger.info(self.s2)

        if np.round(self.u.value[:, 0]) == 0:
            tempSetting = 30
            onOff = 0
        elif np.round(self.u.value[:, 0]) == 1:
            tempSetting = 16
            onOff = 1

        return tempSetting, onOff


def tou_match(x):
    """
    This function is to determine the electricity price for each time step.
    Parameters
    ----------
    x: current hour
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


def mpc(param, logger, item_dir):
    # 获取索引值
    indoor_item = item_dir['indoor_item']
    in_EMeter_item = item_dir['in_EMeter_item']

    # 省略算法逻辑
    logger.info("算法逻辑运行中")
    logger.info(param)
    # 获取设备nid
    nid = param['deviceData'][indoor_item]['nid']
    logger.info("设备nid")
    logger.info(nid)

    # # 取设备室内温度列表
    y = param['deviceData'][indoor_item]['props']['roomTemp'][0]
    logger.info("当下室内温度")
    logger.info(y)

    # MELs forcast and linearize for 24 time-step
    MELs_0 = param['deviceData'][in_EMeter_item]['props']['E'][-3] - param['deviceData'][in_EMeter_item]['props']['E'][
        -2]
    MELs_1 = param['deviceData'][in_EMeter_item]['props']['E'][-2] - param['deviceData'][in_EMeter_item]['props']['E'][
        -1]
    MELs = [MELs_0 * 1000, MELs_1 * 1000]
    for i in range(25):
        MELs_fore = round(sum(MELs[-2:]) / 2, 3)
        MELs.append(MELs_fore)
        i = i + 1
    MELs_fore = MELs[2:-1]

    logger.info("MELs_fore预测")
    logger.info(MELs_fore)

    url = 'http://caiyunapi.market.alicloudapi.com/forecast/24hour/113,23'
    appcode = 'f963fc47fe7540b8a1d923c484d63315'

    # Ambient temp forcast and linearize for 24 time-step
    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    request.add_header('X-Ca-Nonce', str(uuid.uuid4()))
    response = urllib.request.urlopen(request)
    Ta = np.zeros(1)
    content = json.loads(str(response.read(), 'utf-8'))
    for i in range(0, 6):
        T1 = content["result"]["hourly"]["temperature"][i]["value"]
        T4 = content["result"]["hourly"]["temperature"][i + 1]["value"]
        a = (T4 - T1) / 60
        T2 = T1 + 15 * a
        T3 = T2 + 15 * a
        for T in [T1, T2, T3, T4]:
            Ta = np.append(Ta, T)
    Ta_fore = np.delete(Ta, 0)
    logger.info("室外温度预测")
    logger.info(Ta_fore)

    # Solar radiation forcast and linearize for 24 time-step
    request = urllib.request.Request(url)
    request.add_header('Authorization', 'APPCODE ' + appcode)
    request.add_header('X-Ca-Nonce', str(uuid.uuid4()))
    response = urllib.request.urlopen(request)
    sol_rad = np.zeros(1)
    content = json.loads(str(response.read(), 'utf-8'))
    for i in range(0, 6):
        r1 = content["result"]["hourly"]["dswrf"][i]["value"]
        r4 = content["result"]["hourly"]["dswrf"][i + 1]["value"]
        a = (r4 - r1) / 60
        r2 = r1 + 15 * a
        r3 = r2 + 15 * a
        for r in [r1, r2, r3, r4]:
            sol_rad = np.append(sol_rad, r)
    sol_rad_fore = np.delete(sol_rad, 0)
    logger.info("太阳辐射预测")
    logger.info(sol_rad_fore)

    # Instantiate controller
    con = Controller_MPC(nid)
    onOff, tempSetting = con.mpc_step(y, Ta_fore, sol_rad_fore, MELs_fore, logger)

    obj = {"nid": nid,
           "control": {
               "runMode": 2,
               "onOff": onOff,
               "tempSetting": tempSetting
           }
           }

    Weather_dir = {
        "OutdoorTemp": Ta_fore[0],
        "SolarRadiation": sol_rad_fore[0],
    }

    return {"actionArray": [obj]}, Weather_dir
