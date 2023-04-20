# -*- coding: utf-8 -*-
"""
@Project ：Midea-DR-Project-main 
@File    ：VRF_Model.py
@Time: 01/06/2023 23:59
@Author: Mingchen Li
@Note: Each time the model "$$$" is replenished, some components need be added:
- the model function, which is defined out of the "VRFModel" class, and must be named as "model_$$$"
- the inputs of the model, which is defined in "VRFModel" class -> "__init__" function -> "self.X_$$$ = (x1, x2, ...)"
- the initial point "p_$$$" of the model parameters, which is defined in "VRFModel" class -> "TrainingPhysicsModel" function
- the list "Namelist", which is defined in "VRFModel" class -> "TrainingPhysicsModel" function
"""
import time
import numpy as np
import pandas as pd

from scipy.optimize import curve_fit
from sklearn import svm
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
from sklearn.model_selection import train_test_split

import xgboost as xgb
from keras.models import Sequential
from keras.layers import Dense
from keras import backend as K
from Data_preprocessing_Brick import Data2VRFData
from sklearn.model_selection import KFold


Save_path = '1VS3_Results_rate'


def flatten_list(nested_list):
    flat_list = []
    for item in nested_list:
        if type(item) == list:
            flat_list.extend(flatten_list(item))
        else:
            flat_list.append(item)
    return flat_list


def DF2Excel(data_path, data_list, sheet_name_list):
    write = pd.ExcelWriter(data_path)
    for da, sh_name in zip(data_list, sheet_name_list):
        da.to_excel(write, sheet_name=sh_name, index=True)

    # 必须运行write.save()，不然不能输出到本地
    write.save()
    print('Saving \'' + data_path + '\' successful')


def model_Baseline(X, COP):
    Q_cool = X
    W = Q_cool / COP
    return W


def model_Hong(X, a0, a1, a2, a3, a4, a5, a6):
    Tc, Te, V_fan = X
    VdV_rate = V_fan / 50.
    W = a0 + a1 * VdV_rate + a2 * Tc + a3 * Te + a4 * Tc ** 2 + a5 * Tc * Te + a6 * Te ** 2
    return W


def model_Torregrosa(X, b, Q_rate, COP_rate, b0, b1, b2, b3, b4, b5, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9):
    Q_cool, Tc, T_in = X
    T_inwb = T_in + b
    CAPFT = b0 + b1 * T_inwb + b2 * T_inwb ** 2 + b3 * Tc + b4 * Tc ** 2 + b5 * T_inwb * Tc
    PLR = Q_cool / Q_rate
    EIRFT = a0 + a1 * T_inwb + a2 * T_inwb ** 2 + a3 * Tc + a4 * Tc ** 2 + a5 * T_inwb * Tc
    EIRFPLR = a6 + a7 * PLR + a8 * PLR ** 2 + a9 * PLR ** 3

    W = (Q_rate * CAPFT / COP_rate) * EIRFT * EIRFPLR * 1

    return W


def model_Li_2009(X, b, a, Q_rate, a0, a1, a2, a3, a4, a5, a6, a7, a8, ):
    V_fan, Tc, Q_cool, T_in = X
    T_inwb = T_in + b
    ff = a * V_fan
    PLR = Q_cool / Q_rate
    EIR_temp = a0 + a1 * T_inwb + a2 * T_inwb ** 2 + a3 * Tc + a4 * Tc ** 2 + a5 * Tc * T_inwb
    EIR_Flow = a6 + a7 * ff + a8 * ff ** 2
    EIR = EIR_temp * EIR_Flow
    W = Q_cool * EIR * PLR

    return W


def model_Guo(X, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15, a16, a17, a18, a19):
    Tc, Te, f = X
    W = a0 + a1 * Te + a2 * Tc + a3 * f + a4 * Te ** 2 + a5 * Tc ** 2 + a6 * f ** 2 + a7 * Tc * Te + a8 * Te * f + a9 * Tc * f + a10 * Te ** 3 + \
        a11 * Tc ** 3 + a12 * f ** 3 + a13 * Te ** 2 * Tc + a14 * Te ** 2 * f + a15 * Tc ** 2 * Te + a16 * Tc ** 2 * f + a17 * f ** 2 * Te + a18 * f ** 2 * Tc + \
        a19 * Te * Tc * f
    return W


def model_Shao(X, a0, a1, a2, a3, a4, a5, a6, a7, a8):
    Tc, Te, f = X
    f_rate = 50.
    W_ref = a3 + a4 * Tc ** 2 + a5 * Tc + a6 * Tc * Te + a7 * Te ** 2 + a8 * Te
    W = (a0 + a1 * (f - f_rate) ** 2 + a2 * (f - f_rate)) * W_ref
    return W


def model_Aprea(X, a0, a1, a2, a3, a4, a5):
    Tc, Te = X
    W = a0 + a1 * Tc ** 2 + a2 * Tc + a3 * Tc * Te + a4 * Te ** 2 + a5 * Te
    return W


def model_Park(X, a0, a1, a2, a3, a4, a5):
    Tc, Te, f = X
    W = f * (a0 + a1 * Tc ** 2 + a2 * Tc + a3 * Tc * Te + a4 * Te ** 2 + a5 * Te)
    return W


def model_Hu(X, b, b0, b1, b2, b3, b4, b5, c0, c1, c2, c3, c4, c5):
    T_out, f, T_in = X
    T_inwb = T_in + b
    Q = (b0 + b1 * T_inwb + b2 * T_out) * (1 + b3 * f + b4 * f ** 2 + b5 * f ** 3)
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f + c4 * f ** 2 + c5 * f ** 3)
    W = Q / COP

    return W


def model_Hu_1(X, b, b0, b1, b2, b3, b4, b5, c0, c1, c2, c3):
    T_out, f, T_in, Q = X
    T_inwb = T_in + b
    Q = (b0 + b1 * T_inwb + b2 * T_out) * (1 + b3 * f + b4 * f ** 2 + b5 * f ** 3)
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f)
    W = Q / COP

    return W


def model_Hu_3(X, b, b0, b1, b2, b3, b4, b5, c0, c1, c2, c3, c4, c5):
    T_out, f, T_in, Q = X
    T_inwb = T_in + b
    Q = (b0 + b1 * T_inwb + b2 * T_out) * (1 + b3 * f + b4 * f ** 2 + b5 * f ** 3)
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f + c4 * f ** 2 + c5 * f ** 3)
    W = Q / COP

    return W


def model_Hu_1_rate(X, b, b0, b1, b2, b3, b4, b5, c0, c1, c2, c3, Q_max, COP_rate):
    T_out, f, T_in, Q = X
    T_inwb = T_in + b
    Q = (b0 + b1 * T_inwb + b2 * T_out) * (1 + b3 * f + b4 * f ** 2 + b5 * f ** 3) * Q_max
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f) * COP_rate
    W = Q / COP

    return W


def model_Hu_3_rate(X, b, b0, b1, b2, b3, b4, b5, c0, c1, c2, c3, c4, c5, Q_max, COP_rate):
    T_out, f, T_in, Q = X
    T_inwb = T_in + b
    Q = (b0 + b1 * T_inwb + b2 * T_out) * (1 + b3 * f + b4 * f ** 2 + b5 * f ** 3) * Q_max
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f + c4 * f ** 2 + c5 * f ** 3) * COP_rate
    W = Q / COP

    return W


def model_Hu_1_COP(X, b, c0, c1, c2, c3):
    T_out, f, T_in = X
    T_inwb = T_in + b
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f)

    return COP


def model_Hu_3_COP(X, b, c0, c1, c2, c3, c4, c5):
    T_out, f, T_in = X
    T_inwb = T_in + b
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f + c4 * f ** 2 + c5 * f ** 3)

    return COP


def model_Hu_1_COP_rate(X, b, c0, c1, c2, c3, COP_rate):
    T_out, f, T_in = X
    T_inwb = T_in + b
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f) * COP_rate

    return COP


def model_Hu_3_COP_rate(X, b, c0, c1, c2, c3, c4, c5, COP_rate):
    T_out, f, T_in = X
    T_inwb = T_in + b
    COP = (c0 + c1 * T_inwb + c2 * T_out) * (1 + c3 * f + c4 * f ** 2 + c5 * f ** 3) * COP_rate

    return COP


def model_Cheung(X, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, ):
    T_out, Q_cool, V_fan = X
    W_max = a7 + a8 * T_out
    Q_max = a9 + a10 * T_out
    QdQ_max = Q_cool / Q_max
    VdV_max = V_fan / 50.
    W = W_max * (
            a0 + a1 * QdQ_max + a2 * QdQ_max ** 2 + a3 * QdQ_max * VdV_max + a4 * QdQ_max ** 3 + a5 * VdV_max ** 3 +
            a6 * QdQ_max * VdV_max ** 2)
    return W


def model_Li_2015(X, a0, a1, a2, a3):
    T_out, f = X
    W = a0 + a1 * T_out + a2 * f + a3 * f * T_out
    return W


def model_Cai(X, b, a, Q_rate, EIR_rate, b0, b1, b2, b3, b4, b5, b6, b7, b8, b9, b10, c0, c1, c2, c3, c4, c5, c6, c7,
              c8, c9, c10):
    T_out, V_fan, f, T_in = X
    T_inwb = T_in + b
    omega = f * a
    VdV_rate = V_fan / 50.
    Q = (b0 + b1 * T_inwb + b2 * T_inwb ** 2 + b3 * T_out + b4 * T_out ** 2 + b5 * T_inwb * T_out) * \
        (1 + b6 * VdV_rate + b7 * VdV_rate ** 2) * (1 + b8 * omega + b9 * omega ** 2 + b10 * omega ** 3) * Q_rate
    EIR = (c0 + c1 * T_inwb + c2 * T_inwb ** 2 + c3 * T_out + c4 * T_out ** 2 + c5 * T_inwb * T_out) * \
          (1 + c6 * VdV_rate + c7 * VdV_rate ** 2) * (1 + c8 * omega + c9 * omega ** 2 + c10 * omega ** 3) * EIR_rate
    W = Q * EIR
    return W


def model_Kim(X, a0, a1, a2, a3):
    Tc, Te, f = X
    W = a0 + a1 * f + a2 * Tc + a3 * f * Te
    return W


def model_Mackensen(X, a0, a1, a2, a3):
    P_suc, P_dis = X
    eta = a1 + a2 * P_suc + a3 * P_dis
    W = (a0 / (a0 - 1) * P_suc * P_suc * ((P_dis / P_suc) ** ((a0 - 1) / a0) - 1)) / eta
    return W


def model_Ndiaye(X, a0, a1, a2, a3, a4, a5, a6, a7, a8, a9):
    P_suc, P_dis = X
    W = a0 + a1 * P_suc + a2 * P_dis + a3 * P_suc ** 2 + a4 * P_suc * P_dis + a5 * P_dis ** 2 + a6 * P_suc ** 3 + a7 * P_suc ** 2 * P_dis + \
        a8 * P_suc * P_dis ** 2 + a9 * P_dis ** 3
    return W


def evaluation(y_real, y_predict, metric=None):
    if isinstance(y_real, pd.Series):
        y_real = y_real.values
    if isinstance(y_predict, pd.Series):
        y_predict = y_predict.values

    mae = mean_absolute_error(y_real, y_predict)
    mse = mean_squared_error(y_real, y_predict)
    rmse = np.sqrt(mean_squared_error(y_real, y_predict))
    cvrmse = rmse/(np.mean(y_real)) * 100
    mape = (abs(y_predict - y_real) / y_real).mean()
    r_2 = r2_score(y_real, y_predict)
    if not metric:
        return mae, rmse, mape, r_2, cvrmse
    else:
        return eval(metric.lower())


class VRFModel(object):

    def __init__(self, VRF_model_data, IndoorTemp='Mean(Indoor temperature)', NubOfIndoor=7):
        self.NubOfIndoor = NubOfIndoor
        self.LGBM_Model = None
        self.dataset_O = VRF_model_data
        self.Cross_Dataset_ML = None
        self.data_all = Data2VRFData(VRF_model_data.iloc[:, 1:], plot=False, if_print=False)
        self.BestModelOfName = None
        self.ANN_Model = None
        self.Xgb_Model = None
        self.SVM_Model = None
        self.params = None
        self.Result_train = None
        self.Result_test = None
        self.ML_Result_train = None
        self.ML_Result_test = None
        self.Evaluations_train = {}
        self.Evaluations_test = {}
        self.ML_Evaluations_train = {}
        self.ML_Evaluations_test = {}
        self.DataSize = {}
        self.IndoorTemp = IndoorTemp
        self.IndoorTempList = ['Indoor temperature ' + str(i) for i in range(NubOfIndoor)] + \
                              ['Indoor unit cooling state ' + str(i) for i in range(NubOfIndoor)]
        self.data = VRF_model_data
        self.Y = VRF_model_data['diff(Outdoor unit power)']
        self.X_Baseline = 'Cooling capacity'

        self.X_Hong = [
            'Outdoor unit Condensing temperature',
            'Outdoor unit Evaporating temperature',
            'Outdoor unit fan speed'
        ]

        self.X_Torregrosa = [
            'Cooling capacity',
            'Outdoor unit Condensing temperature',
            *self.IndoorTempList,
        ]

        self.X_Li_2009 = [
            'Outdoor unit fan speed',
            'Outdoor unit Condensing temperature',
            'Cooling capacity',
            *self.IndoorTempList,
        ]

        self.X_Guo = [
            'Outdoor unit Condensing temperature',
            'Outdoor unit Evaporating temperature',
            'Compressor frequency 1',
            'Compressor frequency 2'
        ]

        self.X_Shao = [
            'Outdoor unit Condensing temperature',
            # 'Outdoor dry bulb temperature',
            'Outdoor unit Evaporating temperature',
            # *self.IndoorTempList,
            'Compressor frequency 1',
            'Compressor frequency 2'
        ]

        self.X_Aprea = [
            'Outdoor unit Condensing temperature',
            'Outdoor unit Evaporating temperature',
        ]

        self.X_Park = [
            'Outdoor unit Condensing temperature',
            'Outdoor unit Evaporating temperature',
            'Compressor frequency 1',
            'Compressor frequency 2'
        ]

        self.X_Hu = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
        ]

        self.X_Hu_1 = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
            'Cooling capacity'
        ]

        self.X_Hu_3 = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
            'Cooling capacity'
        ]

        self.X_Hu_1_rate = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
            'Cooling capacity'
        ]

        self.X_Hu_3_rate = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
            'Cooling capacity'
        ]

        self.X_Hu_1_COP = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
        ]

        self.X_Hu_3_COP = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
        ]

        self.X_Hu_1_COP_rate = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
        ]

        self.X_Hu_3_COP_rate = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
        ]

        self.X_Cheung = [
            'Outdoor dry bulb temperature',
            'Cooling capacity',
            'Outdoor unit fan speed'
        ]

        self.X_Li_2015 = [
            'Outdoor dry bulb temperature',
            'Compressor frequency 1',
            'Compressor frequency 2'
        ]

        self.X_Cai = [
            'Outdoor dry bulb temperature',
            'Outdoor unit fan speed',
            'Compressor frequency 1',
            'Compressor frequency 2',
            *self.IndoorTempList,
        ]

        self.X_Kim = [
            'Outdoor unit Condensing temperature',
            'Outdoor unit Evaporating temperature',
            'Compressor frequency 1',
            'Compressor frequency 2'
        ]

        self.X_Mackensen = [
            'Compressor suction pressure',
            'Compressor discharge pressure',
        ]

        self.X_Ndiaye = [
            'Compressor suction pressure',
            'Compressor discharge pressure',
        ]

        # self.Name_list = ['Baseline',
        #                   'Hong',
        #                   'Torregrosa',
        #                   'Li_2009',
        #                   'Li_2015',
        #                   # 'Cai',
        #                   'Guo',
        #                   'Shao',
        #                   'Cheung',
        #                   'Aprea',
        #                   'Park',
        #                   'Kim',
        #                   'Hu',
        #                   'Mackensen',
        #                   'Ndiaye']
        self.Name_list = ['Baseline', 'Hu_1_rate', 'Hu_3_rate']

    def DataPreprocessing_All(self, BestPhysicsList=['Hu'], test_size=0.2, random_state=None, if_print=True):
        '''

        Parameters
        ----------
        test_size: 测试集比例
        random_state: 随机种子

        Returns: 不做返回，向self传递每个模型的训练集和测试集
        -------

        '''

        # 数据预处理
        Dataset = self.data_all
        shape0 = Dataset.shape[0]
        statement = '经过COP和压缩机筛选后，共有{}组数据'.format(shape0)
        Dataset = Dataset.dropna(how='any')
        shape1 = Dataset.shape[0]
        statement += "，之后删除了{}组含有nan的行".format(shape0 - shape1)
        Dataset = Dataset[(Dataset.astype(bool) == True).all(1)]
        shape2 = Dataset.shape[0]
        statement += '，又删除了{}组含有0的行'.format(shape1 - shape2)
        statement += '，最后还有{}组数据。'.format(shape2)
        if if_print:
            print(statement)
        # 划分数据集
        # 对于数据集1
        y = Dataset['diff(Outdoor unit power)']
        X = Dataset['Cooling capacity']

        temp_dataset = train_test_split(X, y, test_size=test_size, random_state=random_state)
        self.__setattr__('Dataset_Baseline', temp_dataset)
        # 对于其他数据集
        for Name in self.Name_list:
            if 'COP' in Name:
                if if_print:
                    print("正在划分{}模型的数据集".format(Name))
                Temp_columns = self.__getattribute__('X_' + Name)

                # 删除非变量列
                if 'Compressor frequency 2' in Temp_columns:
                    del Temp_columns[Temp_columns.index('Compressor frequency 2')]
                if self.IndoorTempList[0] in Temp_columns:
                    for i in self.IndoorTempList:
                        del Temp_columns[Temp_columns.index(i)]
                    Temp_columns.append(self.IndoorTemp)

                Temp_columns.extend(['COP', 'diff(Outdoor unit power)', 'Cooling capacity'])

                Temp_Dataset = Dataset[Temp_columns]
                y = Temp_Dataset[['COP', 'diff(Outdoor unit power)', 'Cooling capacity']]
                del Temp_Dataset['COP']
                del Temp_Dataset['diff(Outdoor unit power)']
                del Temp_Dataset['Cooling capacity']
                X = Temp_Dataset
                self.__setattr__('Cross_Dataset_' + Name, (X, y))
                temp_dataset = train_test_split(X, y, test_size=test_size, random_state=random_state)
                self.__setattr__('Dataset_' + Name, temp_dataset)

            else:
                if Name == 'Baseline':
                    continue
                if if_print:
                    print("正在划分{}模型的数据集".format(Name))
                Temp_columns = self.__getattribute__('X_' + Name)

                # 删除非变量列
                if 'Compressor frequency 2' in Temp_columns:
                    del Temp_columns[Temp_columns.index('Compressor frequency 2')]
                if self.IndoorTempList[0] in Temp_columns:
                    for i in self.IndoorTempList:
                        del Temp_columns[Temp_columns.index(i)]
                    Temp_columns.append(self.IndoorTemp)

                Temp_columns.append('diff(Outdoor unit power)')

                Temp_Dataset = Dataset[Temp_columns]
                y = Temp_Dataset['diff(Outdoor unit power)']
                del Temp_Dataset['diff(Outdoor unit power)']
                X = Temp_Dataset
                self.__setattr__('Cross_Dataset_' + Name, (X, y))
                temp_dataset = train_test_split(X, y, test_size=test_size, random_state=random_state)
                self.__setattr__('Dataset_' + Name, temp_dataset)

        ML_dataset_col = []
        for Name in BestPhysicsList:
            ML_dataset_col.append(self.__getattribute__('X_' + Name))

        # 扁平化列表&列表去重
        ML_dataset_col = flatten_list(ML_dataset_col)
        ML_dataset_col = list(set(ML_dataset_col))

        # 加入label
        ML_dataset_col.append('diff(Outdoor unit power)')

        # 修改输入VS_Temp：
        # if 'Outdoor dry bulb temperature' in ML_dataset_col:
        #     ML_dataset_col.remove('Outdoor dry bulb temperature')

        # 对于ML数据集
        if 'Compressor frequency 2' in ML_dataset_col:
            ML_dataset_col.remove('Compressor frequency 2')
        if 'Indoor unit cooling state 0' in ML_dataset_col:
            for i in range(self.NubOfIndoor):
                ML_dataset_col.remove('Indoor unit cooling state ' + str(i))
                ML_dataset_col.remove('Indoor temperature ' + str(i))
            ML_dataset_col.append(self.IndoorTemp)
        ML_Dataset = Dataset[ML_dataset_col]

        # ML_Dataset.to_csv('Results/430_0224.csv', index=False)
        # 删除非变量列
        if 'Compressor frequency 2' in ML_Dataset:
            del ML_Dataset[ML_Dataset.index('Compressor frequency 2')]
        if self.IndoorTempList[0] in ML_Dataset:
            for i in self.IndoorTempList[0: self.NubOfIndoor]:
                del ML_Dataset[i]
            ML_Dataset.append(self.IndoorTemp)

        # 划分数据集
        ML_y = ML_Dataset['diff(Outdoor unit power)']
        ML_Dataset.drop(columns=['diff(Outdoor unit power)'], inplace=True)

        ML_X = ML_Dataset

        # 将ML数据集返回给self
        temp_dataset = train_test_split(ML_X, ML_y, test_size=test_size, random_state=random_state)
        self.__setattr__('Dataset_ML', temp_dataset)

    def TrainingPhysicsModel(self, maxfev=8000, if_print=True, fold=5, random_state=None):
        # 模型一
        COP_mean = self.data_all['COP'].mean()
        if 'Baseline' in self.Name_list:
            model1_param = [COP_mean]
            model_params = [model1_param]
        else:
            model_params = []

        # 参数起始点
        Q_max = self.data_all['Cooling capacity'].max()
        p_Hong = (0., 1., 1., 1., 1., 1., 1.)
        p_Torregrosa = (0., Q_max, COP_mean, 0., 1., 1., 1., 1., 1., 0., 1., 1., 1., 1., 1., 0., 1., 1., 1.)
        p_Li_2009 = (0., 1., Q_max, 0., 1., 1., 1., 1., 1., 0., 1., 1.)
        p_Guo = tuple([0.] + [1.] * 19)
        p_Shao = tuple([0., 1., 1., 0.] + [1.] * 5)
        p_Aprea = tuple([0.] + [1.] * 5)
        p_Park = tuple([0.] + [1.] * 5)
        p_Hu = tuple([0.] + ([0.] + [1.] * 5) * 2)
        p_Cheung = tuple([0.] + [1.] * 6 + ([0., 1.] * 2))
        p_Li_2015 = (0., 1., 1., 1.)
        p_Kim = (0., 1., 1., 1.)
        p_Cai = tuple([0., 50, Q_max, 1 / COP_mean] + 2 * ([0.] + [1.] * 10))
        p_Mackensen = (0.5, 0., 1., 1.)
        p_Ndiaye = tuple([0.] + [1.] * 9)
        p_Hu_3_rate = tuple([0.] + ([0.] + [1.] * 5) * 2 + [Q_max, COP_mean])
        p_Hu_1_rate = tuple([0.] + ([0.] + [1.] * 5) + ([0.] + [1.] * 3) + [Q_max, COP_mean])
        p_Hu_1_COP = (0., 0., 1., 1., 1.)
        p_Hu_3_COP = (0., 0., 1., 1., 1., 1., 1.)
        p_Hu_1_COP_rate = (0., 0., 1., 1., 1., COP_mean)
        p_Hu_3_COP_rate = (0., 0., 1., 1., 1., 1., 1., COP_mean)
        p_Hu_3 = tuple([0.] + ([0.] + [1.] * 5) * 2)
        p_Hu_1 = tuple([0.] + ([0.] + [1.] * 5) + ([0.] + [1.] * 3))

        # 模型依次拟合
        for Name in self.Name_list:

            # 模型1不需要拟合
            if Name == 'Baseline':
                continue

            # 获得训练集数据
            if 'COP' in Name:
                X_train = self.__getattribute__('Dataset_' + Name)[0]
                y_train = self.__getattribute__('Dataset_' + Name)[2]['COP']
            else:
                X_train = self.__getattribute__('Dataset_' + Name)[0]
                y_train = self.__getattribute__('Dataset_' + Name)[2]
            cv = KFold(n_splits=fold, shuffle=True, random_state=random_state)

            # 五重交叉验证
            best_score = 1000
            best_param = None
            for train_index, val_index in cv.split(X_train):

                X_cv_train, X_cv_val = X_train.iloc[train_index], X_train.iloc[val_index]
                y_cv_train, y_cv_val = y_train.iloc[train_index], y_train.iloc[val_index]

                # 拟合并获得模型参数
                temp_param = curve_fit(
                    globals()['model_' + Name],
                    tuple(X_cv_train.values.T.tolist()),
                    y_cv_train.values.tolist(),
                    locals()['p_' + Name],
                    maxfev=maxfev
                )[0]

                # 在验证集上评估性能
                y_pre = globals()['model_' + Name](X_cv_val.values.T, *temp_param)
                score = evaluation(y_cv_val, y_pre, 'CVRMSE')

                if score < best_score:
                    best_score = score
                    best_param = temp_param

            # 保存模型参数
            if if_print:
                print("模型{}已训练完成".format(Name))
            model_params.append(best_param)

        # 返回至self
        self.params = model_params

    def GetPhysicsEvaluation(self, saving=False, saving_name='Result.xlsx'):
        n = 0
        for Name in self.Name_list:

            if 'COP' in Name:
                # 获取训练集和测试集
                X_train = self.__getattribute__('Dataset_' + Name)[0]
                X_test = self.__getattribute__('Dataset_' + Name)[1]
                # 计算W的准确率
                # y_train = self.__getattribute__('Dataset_' + Name)[2]['diff(Outdoor unit power)']
                # y_test = self.__getattribute__('Dataset_' + Name)[3]['diff(Outdoor unit power)']
                # 计算COP的准确率
                y_train = self.__getattribute__('Dataset_' + Name)[2]['COP']
                y_test = self.__getattribute__('Dataset_' + Name)[3]['COP']
            else:
                # 获取训练集和测试集
                X_train = self.__getattribute__('Dataset_' + Name)[0]
                X_test = self.__getattribute__('Dataset_' + Name)[1]
                y_train = self.__getattribute__('Dataset_' + Name)[2]
                y_test = self.__getattribute__('Dataset_' + Name)[3]

            # 对数据集进行数据转换
            if Name == 'Baseline':
                X_train_input = pd.Series(X_train.tolist())
                X_test_input = pd.Series(X_test.tolist())
            else:
                X_train_input = tuple([pd.Series(i) for i in X_train.values.T.tolist()])
                X_test_input = tuple([pd.Series(i) for i in X_test.values.T.tolist()])
            y_train_input = pd.Series(y_train.values.tolist())
            y_test_input = pd.Series(y_test.values.tolist())

            # 获得各个模型参数
            temp_p = self.params[n]

            # 开始测试
            for X, y, state, item in zip([X_train_input, X_test_input], [y_train_input, y_test_input], ['train', 'test'], [2, 3]):
                if 'COP' in Name:
                    # 计算W的准确率
                    # pre_COP = globals()['model_' + Name](X, *temp_p)
                    # real_CC = self.__getattribute__('Dataset_' + Name)[item]['Cooling capacity']
                    # real_CC = real_CC.reset_index(drop=True)
                    # pre_W = real_CC/pre_COP
                    # temp_Eva = evaluation(y, pre_W)
                    # self.__getattribute__('Evaluations_' + state)[Name] = temp_Eva

                    # 计算COP的准确率
                    pre_W = globals()['model_' + Name](X, *temp_p)
                    temp_Eva = evaluation(y, pre_W)
                    self.__getattribute__('Evaluations_' + state)[Name] = temp_Eva

                else:
                    pre_W = globals()['model_' + Name](X, *temp_p)
                    temp_Eva = evaluation(y, pre_W)
                    self.__getattribute__('Evaluations_' + state)[Name] = temp_Eva
            n += 1

        # 将结果写入excel表格
        for state in ['train', 'test']:
            result_df = pd.DataFrame(data=self.__getattribute__('Evaluations_' + state))
            result_df.index = ['MAE', 'RMSE', 'MAPE', 'R^2', 'CVRMSE']
            data_list = []
            sheet_name_list = ['result', 'MAE', 'RMSE', 'MAPE', 'R^2', 'CVRMSE']
            if saving:
                for index in sheet_name_list:
                    if index == 'result':
                        data_list.append(result_df.round(3))
                    elif index == 'R^2':
                        data_list.append(result_df.sort_values(axis=1, by=index, ascending=False).round(3))
                    else:
                        data_list.append(result_df.sort_values(axis=1, by=index).round(3))
                DF2Excel('Results/' + state + '_' + saving_name, data_list, sheet_name_list)
            # 将每个模型的结果返回给self
            self.__setattr__('Result_' + state, result_df)

    def TrainingMLModel(self, fold=5, random_state=None):
        # 数据集准备
        X_train = self.__getattribute__('Dataset_ML')[0]
        y_train = self.__getattribute__('Dataset_ML')[2]

        cv = KFold(n_splits=fold, shuffle=True, random_state=random_state)

        # SVM
        # 五重交叉验证
        best_score = 1000
        best_model = None
        for train_index, val_index in cv.split(X_train):

            X_cv_train, X_cv_val = X_train.iloc[train_index], X_train.iloc[val_index]
            y_cv_train, y_cv_val = y_train.iloc[train_index], y_train.iloc[val_index]

            # 拟合并获得模型参数
            # SVM
            SVM_params = {"kernel": "rbf",
                          "C": 138.95380318401027,
                          "epsilon": 0.7104280884202305}

            # reg = svm.SVR()
            reg = svm.SVR(**SVM_params)
            reg.fit(X_cv_train, y_cv_train)

            # 在验证集上评估性能
            y_pre = reg.predict(X_cv_val)
            score = evaluation(y_pre, y_cv_val, 'RMSE')

            if score < best_score:
                best_score = score
                best_model = reg

        self.SVM_Model = best_model

        # Xgb_Model

        # 五重交叉验证
        best_score = 1000
        best_model = None

        params = {'colsample_bytree': 0.7025492933597903, 'gamma': 0.7865834708315065,
                  'learning_rate': 0.015186413429008963, 'max_depth': 1, 'min_child_weight': 2, 'n_estimators': 897,
                  'reg_alpha': 0.47410207584226693, 'reg_lambda': 0.004106202897448452,
                  'subsample': 0.30770935083492523}
        # params = {'n_estimators': 153, 'learning_rate': 0.11137879345092681, 'max_depth': 1,
        #           'subsample': 0.8412648509105591, 'gamma': 1.5869078722818886,
        #           'colsample_bytree': 0.9813174569594559, 'reg_lambda': 0.0005459900426614539,
        #           'reg_alpha': 0.0032045693630570133, 'min_child_weight': 4}
        # params = {'n_estimators': 153, 'learning_rate': 0.11137879345092681, 'max_depth': 1,
        #           'subsample': 0.8412648509105591, 'gamma': 1.5869078722818886,
        #           'colsample_bytree': 0.9813174569594559, 'reg_lambda': 0.004106202897448452,
        #           'reg_alpha': 0.47410207584226693, 'min_child_weight': 4}

        for train_index, val_index in cv.split(X_train):

            X_cv_train, X_cv_val = X_train.iloc[train_index], X_train.iloc[val_index]
            y_cv_train, y_cv_val = y_train.iloc[train_index], y_train.iloc[val_index]

            # 拟合并获得模型参数
            # XGB
            xgb_model = xgb.XGBRegressor(**params, n_jobs=-1)
            xgb_model.fit()

            # 在验证集上评估性能
            y_pre = xgb_model.predict(X_cv_val)
            score = evaluation(y_pre, y_cv_val, 'RMSE')

            if score < best_score:
                best_score = score
                best_model = xgb_model

        self.Xgb_Model = best_model

        # ANN_model

        best_score = 1000
        best_model = None
        for train_index, val_index in cv.split(X_train):

            X_cv_train, X_cv_val = X_train.iloc[train_index], X_train.iloc[val_index]
            y_cv_train, y_cv_val = y_train.iloc[train_index], y_train.iloc[val_index]

            # 拟合并获得模型参数
            # ANN

            K._get_available_gpus()
            ANN_model = Sequential()
            ANN_model.add(Dense(122, activation='relu', input_dim=X_train.shape[1]))
            ANN_model.add(Dense(1, activation='linear'))
            ANN_model.compile(loss='mean_squared_error', optimizer='adam')
            history = ANN_model.fit(X_cv_train, y_cv_train, epochs=100, batch_size=32, validation_split=0.2)

            # 在验证集上评估性能
            y_pre = ANN_model.predict(X_cv_val)
            score = evaluation(y_pre, y_cv_val, 'RMSE')

            if score < best_score:
                best_score = score
                best_model = ANN_model

        self.ANN_Model = best_model

        # LGBM

        # params = {'learning_rate': 0.12541960431280894,
        #           'max_depth': 1, 'n_estimators': 200,
        #           'num_leaves': 2, 'reg_alpha': 0.36376601607098774, 'reg_lambda': 2.5938363093123145,
        #           "bagging_fraction": 0.6173864599140055,
        #           'feature_fraction': 0.6792127681824223,
        #           "min_data_in_leaf": 13
        #           }

        params = {'bagging_fraction': 0.7308558067701578,
                  'feature_fraction': 0.25394164259502583,
                  'learning_rate': 0.07399359321024458,
                  'max_depth': 1, 'min_data_in_leaf': 5, 'n_estimators': 634,
                  'num_leaves': 2, 'reg_alpha': 2.5662718054531575,
                  'reg_lambda': 20.74700754411094}

        params = {'bagging_fraction': 0.5730673600526089, 'feature_fraction': 0.2578593712756325,
                  'learning_rate': 0.05016796352481905, 'max_depth': 1, 'n_estimators': 328, 'num_leaves': 2,
                  'reg_alpha': 0.20688074747844398, 'reg_lambda': 26.079420161294387}

        # 五重交叉验证
        # best_score = 1000
        # best_model = None
        # for train_index, val_index in cv.split(X_train):
        #
        #     X_cv_train, X_cv_val = X_train.iloc[train_index], X_train.iloc[val_index]
        #     y_cv_train, y_cv_val = y_train.iloc[train_index], y_train.iloc[val_index]
        #
        #     # 拟合并获得模型参数
        #     # LGBM
        #     LGBM_model = lgb.LGBMRegressor(**params)
        #     LGBM_model.fit(X_cv_train, y_cv_train)
        #     # 在验证集上评估性能
        #     y_pre = LGBM_model.predict(X_cv_val)
        #     score = evaluation(y_pre, y_cv_val, 'RMSE')
        #
        #     if score < best_score:
        #         best_score = score
        #         best_model = LGBM_model
        #
        # self.LGBM_Model = best_model

        # params = {'bagging_fraction': 0.2202253013773151, 'feature_fraction': 0.4883746289829387,
        #           'learning_rate': 0.23126972472784804, 'max_depth': 1, 'min_data_in_leaf': 9,
        #           'n_estimators': 544, 'num_leaves': 2, 'reg_alpha': 3.2645677545668605,
        #           'reg_lambda': 86.85515063202888}

    def GetMLEvaluation(self, saving=False, saving_name='Result.xlsx'):
        X_train = self.__getattribute__('Dataset_ML')[0]
        X_test = self.__getattribute__('Dataset_ML')[1]
        y_train = self.__getattribute__('Dataset_ML')[2]
        y_test = self.__getattribute__('Dataset_ML')[3]

        for X, y, state in zip([X_train, X_test], [y_train, y_test], ['train', 'test']):
            # for model_name in ['SVM', 'Xgb', 'ANN', 'LGBM']:
            for model_name in ['SVM', 'Xgb', 'ANN']:
            # for model_name in ['Xgb']:
                if model_name == "Xgb":
                    # Xgb_X = xgb.DMatrix(X)
                    # pre_W = self.__getattribute__(model_name + '_Model').predict(Xgb_X)
                    pre_W = self.__getattribute__(model_name + '_Model').predict(X)

                else:
                    pre_W = self.__getattribute__(model_name + '_Model').predict(X)
                temp_Eva = evaluation(y, pre_W)
                self.__getattribute__('ML_Evaluations_' + state)[model_name] = temp_Eva

        for state in ['train', 'test']:
            result_df = pd.DataFrame(data=self.__getattribute__('ML_Evaluations_' + state))
            result_df.index = ['MAE', 'RMSE', 'MAPE', 'R^2', 'CVRMSE']
            data_list = []
            sheet_name_list = ['result', 'MAE', 'RMSE', 'MAPE', 'R^2', 'CVRMSE']
            if saving:
                for index in sheet_name_list:
                    if index == 'result':
                        data_list.append(result_df.round(3))
                    elif index == 'R^2':
                        data_list.append(result_df.sort_values(axis=1, by=index, ascending=False).round(3))
                    else:
                        data_list.append(result_df.sort_values(axis=1, by=index).round(3))
                DF2Excel("Results/ML_" + state + '_' + saving_name, data_list, sheet_name_list)
            self.__setattr__('ML_Result_' + state, result_df)

    def XGB_feature_importance(self, importance_type='total_gain'):
        importance = self.Xgb_Model.get_booster().get_score(importance_type=importance_type)
        importance_df = pd.DataFrame({'feature': list(importance.keys()), importance_type: list(importance.values())})
        importance_df.set_index('feature', inplace=True)
        return importance_df


def PhysicsCrossEvaluation(VRFData, matrix='RMSE', iteration_nub=100, fold=5, save=False, get_param=False):
    all_seeds = []
    n = 0
    pic_train_result_list = []
    pic_test_result_list = []
    best_params_list = []
    while 1:

        try:
            print("-----------------------------------------")
            print("进入第{}次迭代".format(n))

            VRF_Model = VRFModel(VRFData)
            VRF_Model.DataPreprocessing_All(test_size=0.2, if_print=False, random_state=n,
                                            BestPhysicsList=['Li_2015', 'Cheung', 'Hu'])

            # training model
            VRF_Model.TrainingPhysicsModel(maxfev=150000, if_print=False, fold=fold, random_state=n, )
            # Save result
            VRF_Model.GetPhysicsEvaluation(saving=False, saving_name="Result_Brick.xlsx")

            # 保存每次实验结果
            pic_train_result_list.append(VRF_Model.Result_train.loc[matrix])
            pic_test_result_list.append(VRF_Model.Result_test.loc[matrix])
            best_params_list.append(VRF_Model.params[0])

        except RuntimeError:
            print("第{}次迭代失败".format(n))
            n += 1
            continue

        all_seeds.append(n)
        print("第{}次迭代成功".format(n))
        n += 1
        if len(all_seeds) == iteration_nub:
            break

    pic_train_result = pd.concat(pic_train_result_list, axis=1).T.reset_index(drop=True)
    pic_test_result = pd.concat(pic_test_result_list, axis=1).T.reset_index(drop=True)
    if save:
        pic_train_result.to_excel(Save_path + '/pic_train_result_CVRMSE.xlsx', index=False)
        pic_test_result.to_excel(Save_path + '/pic_test_result_CVRMSE.xlsx', index=False)
    print(all_seeds)
    if get_param:
        max_row = pic_test_result['Hu'].idxmax()
        best_param = best_params_list[max_row]
        return best_param


def MLCrossEvaluation(VRFData, matrix='RMSE', iteration_nub=1, fold=3, save=False, importance_type="total_gain"):
    all_seeds = []
    n = 0
    pic_train_result_list = []
    pic_test_result_list = []
    pic_feature_result_list = []
    Best_RMSE = 1000
    Best_model = None
    while 1:
        try:
            print("-----------------------------------------")
            print("进入第{}次迭代".format(n))
            VRF_Model = VRFModel(VRFData)
            VRF_Model.DataPreprocessing_All(BestPhysicsList=['Li_2015', 'Cheung', 'Hu'], test_size=0.2,
                                            random_state=n, if_print=False)

            df_trains = []
            df_tests = []
            df_feature = []
            # training model
            VRF_Model.TrainingMLModel(fold=fold, random_state=n)
            # Save result
            VRF_Model.GetMLEvaluation(saving=False)
            pic_train_result_list.append(VRF_Model.ML_Result_train.loc[matrix])
            pic_test_result_list.append(VRF_Model.ML_Result_test.loc[matrix])
            pic_feature_result_list.append(VRF_Model.XGB_feature_importance(importance_type=importance_type))

        except RuntimeError:
            n += 1
            print("第{}次迭代失败".format(n))
            continue

        # if VRF_Model.ML_Result_test.iloc['Xgb', matrix].values < Best_RMSE:
        #     Best_RMSE = VRF_Model.ML_Result_test.iloc['Xgb', matrix].values
        #     Best_model = VRF_Model.Xgb_Model
        all_seeds.append(n)
        print("第{}次迭代成功".format(n))
        n += 1
        if len(all_seeds) == iteration_nub:
            break

    # Best_model.save_model('Best_model.bin')


    pic_train_result = pd.concat(pic_train_result_list, axis=1).T
    pic_test_result = pd.concat(pic_test_result_list, axis=1).T
    debug_train_result = pic_train_result.median()
    debug_test_result = pic_test_result.median()
    pic_feature_result = pd.concat(pic_feature_result_list, axis=1).T
    if save:
        pic_train_result.to_excel(Save_path + '/pic_ML_train_result.xlsx', index=False)
        pic_test_result.to_excel(Save_path + '/pic_ML_test_result.xlsx', index=False)
        pic_feature_result.to_excel(Save_path + '/pic_ML_feature_result.xlsx', index=False)
    print(all_seeds)


if __name__ == '__main__':
    start_time = time.time()
    VRFData = pd.read_csv("Results/temp_1.csv")
    # 测试物理模型
    VRF_Model = VRFModel(VRFData)
    # VRF_Model.DataPreprocessing_All(test_size=0.2, random_state=0)
    # VRF_Model.TrainingPhysicsModel(maxfev=200000)
    # VRF_Model.GetPhysicsEvaluation(saving=True, saving_name='All_Physics_Result.xlsx')
    Best_param = PhysicsCrossEvaluation(VRFData, iteration_nub=100, fold=5, save=True, get_param=False, matrix="CVRMSE")
    # print(list(Best_param))

    # 测试机器学习模型
    # MLCrossEvaluation(VRFData, iteration_nub=100, fold=5, save=True, importance_type='total_gain', matrix="CVRMSE")

    # 记录结束时间
    end_time = time.time()

    # 计算时间差，即代码运行时长
    duration = end_time - start_time

    print("代码运行时长：{:.3f}秒".format(duration))
