# -*- coding: utf-8 -*-
"""
Created on Sun Oct 30 18:56:31 2022

@author: Mingyue Guo
"""
#%% import
import data_processing as dp
import pandas as pd
import numpy as np
import scipy
from scipy.integrate import odeint
from scipy import optimize
import pykalman
from pykalman import KalmanFilter
import math
from sklearn.metrics import explained_variance_score, mean_absolute_error as MAE, mean_squared_error as MSE, r2_score
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression
import lightgbm as lgb

#%% models
class VRFModel():
    def __init__(self
                 , VRF_model_data
                 ):
        self.modelNO = VRF_model_data.modelNO
        self.analysis_vrf = VRF_model_data.analysis_vrf
        self.VRF_df_reg = VRF_model_data.VRF_df_reg
        self.target = VRF_model_data.target
        self.x_co = VRF_model_data.x_co
        self.cross_valid = VRF_model_data.cross_valid
        self.X_train_list = VRF_model_data.X_train_list
        self.y_train_list = VRF_model_data.y_train_list
        self.X_test_list = VRF_model_data.X_test_list
        self.y_test_list = VRF_model_data.y_test_list
        # self.VRF_model_train()
        
    def VRF_model_train(self):
        for i in range(len(self.X_train_list)): 
            # print('train_index:%s , test_index: %s ' %(train_index,test_index))
            X_train = self.X_train_list[i]
            y_train = self.y_train_list[i]
            X_test = self.X_test_list[i]
            y_test = self.y_test_list[i]
            linreg = LinearRegression()
            self.model = linreg.fit(X_train, y_train)
            # intercept = linreg.intercept_
            # coef = linreg.coef_
            self.train_error = []
            self.test_error = []
            self.y_pred = self.model.predict(X_test)
            y_pred_train = self.model.predict(X_train)
            self.train_cv_rmse = math.sqrt(MSE(y_train.values, y_pred_train)) / y_train.values.mean()
            self.train_error.append(self.train_cv_rmse)
            print('train cv rmse:{}'.format(self.train_cv_rmse))
            self.valid_cv_rmse = math.sqrt(MSE(y_test.values, self.y_pred)) / y_test.values.mean()
            self.test_error.append(self.valid_cv_rmse)
            print('valid cv rmse:{}'.format(self.valid_cv_rmse))
            
            plt.plot(y_train.values, alpha = 0.6, label = 'measured')
            plt.plot(y_pred_train, alpha = 0.6, linestyle = '--', label = 'predict')

            plt.legend()
            plt.ylabel(self.target)
            plt.xlabel('index')
            plt.title('model {} train cv_rmse: {}'.format(self.modelNO,self.train_cv_rmse.round(3)))
            plt.show()
            
            plt.plot(y_test.values, alpha = 0.6, label = 'measured')
            plt.plot(self.y_pred, alpha = 0.6, linestyle = '--', label = 'predict')

            plt.legend()
            plt.ylabel(self.target)
            plt.xlabel('index')
            plt.title('model {} valid cv_rmse: {}'.format(self.modelNO,self.valid_cv_rmse.round(3)))
            plt.show()
            return self.y_pred, self.valid_cv_rmse
    
    def VRF_model_pred(self, X_test, y_test, plt_res = True):
            self.y_pred = self.model.predict(X_test)
            if plt_res:
                plt.plot(self.y_pred, alpha = 0.6, linestyle = '--', label = 'predict')
                plt.legend()
                plt.ylabel(self.target)
                plt.xlabel('index')
                plt.title('predict result')
                plt.show()
            return self.y_pred


#TODO: predict data is not prepared
class RoomModel():
    def __init__(self
                 , RC_all
                 , unmeasured_method = None
                 ):
        self.analysis_vrf = RC_all.analysis_vrf
        self.neighbor_vrfs = RC_all.neighbor_vrfs
        self.unmeasured_method = unmeasured_method
        # RC_data.__dict__.keys()
        self.train_df = RC_all.train_df
        self.train_list = RC_all.train_list
        self.valid_list = RC_all.valid_list
        # self.RC_model_train()
        # TODO prediction data
        # self.RC_model_predict()
    
    def RC_model_train(self
                 , init = [1/0.1,1/10,1/10,1/1000]
                 ):
        init = init
        for nei in range(len(self.neighbor_vrfs)):
            init += [1/0.01]

        para_co =  ['Ra', 'Cac', 'Cmels','Csolar']
        for nei in range(len(self.neighbor_vrfs)):
            para_co.append('Rn'+str(nei+1))
        if self.unmeasured_method == 'L1':
            init += [1,1]  #lambda_L1, theta
            para_co += ['lambda_L1', 'theta']
        # TODO kalman filter
        
        self.para_identification = pd.DataFrame(columns = para_co)
        self.errors = pd.DataFrame(columns = ['r2', 'cv_rmse', 'rmse'])
        # not_meet_cons = []
        for i in range(len(self.train_list)):
            train_data = self.train_list[i].copy()
            ta = train_data['ta']
            tnei_list = []
            for j in range(len(self.neighbor_vrfs)):
                tnei_list.append(train_data['neighborTemp' + str(j+1)])
            tn = train_data['roomTemp']
            solar = train_data['irradiance']
            ac = -train_data['Q'] / 1000
            MELs = train_data['MELs'] / 1000
            tn1 = train_data['tn1_measured']
            # deltaTime = train_data['deltaTime']
            deltaTime = train_data['deltaTime'].cumsum(axis=0)
            bds= ((1E1,1E5),(1E-5,1E1),(1E-5,1),(1E-5,1))
            for nei in range(len(self.neighbor_vrfs)):
                bds += ((1E1,1E7),)
            if self.unmeasured_method == 'L1':
                bds += ((None, None), (0,1))
            # bds= ((1E-9,None),(1E-9,None),(1E-9,None),(1E-9,None))
            # for nei in range(len(self.neighbor_vrfs)):
            #     bds += ((1E-9,None),)
            result = optimize.minimize(self.obj_func_r2c1_scipy, x0=[init]
                                       , args = (ta, tnei_list, tn, solar, ac, MELs, tn1, deltaTime, self.unmeasured_method)
                                       , bounds = bds
                                       )
            self.para_identification.loc[self.para_identification.shape[0]] = result.x
            train_data['tn1_pred'] = self.simulation_odeint_r2c1( result.x
                                                               ,ta, tnei_list, tn, solar, ac, MELs, deltaTime)
            train_data['tn1_pred'] = train_data['tn1_pred'].round(3)
            
            
            error_df = self.error_cal(train_data['tn1_measured'], train_data['tn1_pred'])
            self.errors = self.errors.append(error_df)
            # visualize train result
            (train_data['tn1_measured'] - 273.15).plot()
            (train_data['tn1_pred'] - 273.15).plot()
            (train_data['ta'] - 273.15).plot()
            plt.ylabel('temperature ℃')
            plt.legend()
            plt.title('train {} rmse is: {}'.format(i, error_df['rmse'].values[0].round(3)))
            plt.show()
        
        # hist of parameters
        for co in self.para_identification.columns:
            (1/self.para_identification[co]).hist()
            plt.xlabel(co)
            plt.show()
                
        # validation
        self.paras_mean = self.para_identification.mean(axis = 0)
        for i in range(len(self.valid_list)):
            valid_data = self.valid_list[i]
            ta = valid_data['ta']
            tnei_list = []
            for j in range(len(self.neighbor_vrfs)):
                tnei_list.append(valid_data['neighborTemp' + str(j+1)])
            tn = valid_data['roomTemp']
            solar = valid_data['irradiance']
            ac = valid_data['Q'] /100
            MELs = valid_data['MELs'] /100
            tn1 = valid_data['tn1_measured']
            deltaTime = valid_data['deltaTime']
            valid_data['tn1_pred'] = self.simulation_odeint_r2c1( self.paras_mean
                                                     , ta, tnei_list, tn, solar, ac, MELs, deltaTime)
            
            valid_data['tn1_pred'] = valid_data['tn1_pred'].apply(lambda x: float(x))
            valid_data['tn1_pred'] = valid_data['tn1_pred'].round(3)

            error_df = self.error_cal(valid_data['tn1_measured'], valid_data['tn1_pred'])
            self.errors = self.errors.append(error_df)
            # valid data visulize
            (valid_data['tn1_measured']- 273.15).plot()
            (valid_data['tn1_pred'] - 273.15).plot()
            (valid_data['ta'] - 273.15).plot()
            plt.ylabel('temperature ℃')
            plt.legend()
            plt.title('valid {} rmse is: {}'.format(i, error_df['rmse'].values[0].round(3)))
            plt.show()

        self.para_identification = 1/ self.para_identification
        self.paras_mean = 1 / self.paras_mean
        return self.errors, self.para_identification, self.paras_mean
        
    def error_cal(self,ground_truth, prediction):
        error_df = pd.DataFrame()
        error_df['r2'] = [r2_score(ground_truth, prediction)]
        error_df['cv_rmse'] = [math.sqrt(MSE(ground_truth, prediction)) / np.mean(ground_truth)]
        error_df['rmse'] = [math.sqrt(MSE(ground_truth, prediction))]
        return error_df
    
    
    def L1NormPartial(self,lambda_l1, theta):
        return np.sign(theta) * lambda_l1
    
    def Kalman1D(self,observations,damping=1):
        # To return the smoothed time series data
        observation_covariance = damping
        initial_value_guess = observations[0]
        transition_matrix = 1
        transition_covariance = 0.1
        initial_value_guess
        kf = KalmanFilter(
                initial_state_mean=initial_value_guess,
                initial_state_covariance=observation_covariance,
                observation_covariance=observation_covariance,
                transition_covariance=transition_covariance,
                transition_matrices=transition_matrix
            )
        pred_state, state_cov = kf.filter(observations)
        return pred_state
    
    def simulation_odeint_r2c1(self,paras, ta, tnei_list, tn, solar, ac, MELs, deltaTime):
        def rc_func(y,t, ta, tneis, solar, ac, MELs, paras):
            tni = y
            right = paras[0] * (ta-tni) + paras[1] + ac + paras[2] * MELs + paras[3] * solar
            for j in range(len(tneis)):
                right += paras[4+j] * (tneis[j] - tni)
            dTndt =  right
            return dTndt
        tn1_seq = [tn[0]]
        for i in range(len(deltaTime)):
            t_arr = np.array([0,deltaTime[i]])
            # y_init = tn1_seq[-1]
            y_init = tn1_seq[0] # i.e. tn[0]
            tneis = []
            for j in range(len(tnei_list)):
                tneis.append(tnei_list[j][i])
            tn1 = odeint(rc_func, y_init, t_arr, args = (ta[i], tneis,  solar[i], ac[i], MELs[i], paras))
            tn1_seq.append(tn1[-1][0])
        return tn1_seq[1:]
    
    def obj_func_r2c1_scipy(self, paras
                            , ta, tnei_list, tn, solar, ac, MELs, tn1, deltaTime
                            , unmeasured_method = 'L1'
                            # ,lambda_l1, theta # parameters of L1
                            ):
        # tn1 = simulation_diff(para,train_data)
        if unmeasured_method == None:
            tn1_pred = self.simulation_odeint_r2c1(paras, ta, tnei_list, tn, solar, ac, MELs, deltaTime)
            object_value = math.sqrt(MSE(tn1,tn1_pred)) / np.mean(tn1)
        if unmeasured_method == 'L1':
            tn1_pred = self.simulation_odeint_r2c1(paras[:-2], ta, tnei_list, tn, solar, ac, MELs, deltaTime)
            object_value = math.sqrt(MSE(tn1,tn1_pred)) / np.mean(tn1) + self.L1NormPartial(paras[-2], paras[-1])
        # if unmeasured_method == 'L1':
        #     tn1_pred = simulation_odeint_r2c1(paras[:-2], ta, tnei_list, tn, solar, ac, MELs, deltaTime)
        #     object_value = math.sqrt(MSE(tn1,tn1_pred)) / np.mean(tn1) + L1NormPartial(paras[-2], paras[-1])
        if unmeasured_method == 'KF':
            tn1_pred = self.simulation_odeint_r2c1(paras, ta, tnei_list, tn, solar, ac, MELs, deltaTime)
            tn1_pred = self.Kalman1D(tn1_pred,damping=1)
            object_value = math.sqrt(MSE(tn1,tn1_pred)) / np.mean(tn1) + self.L1NormPartial(paras[-2], paras[-1])
        return object_value
    
    def RC_model_predict(self
                         , pred_data # = self.valid_list[-1]
                         , external_para = None# Series, if get external_para from database, then training is not necessary
                         ):
        self.pred_data = pred_data
        if external_para != None:
            self.paras_pred = 1 / external_para
        else:
            self.paras_pred = 1 / self.paras_mean
        ta = self.pred_data['ta']
        tnei_list = []
        for j in range(len(self.neighbor_vrfs)):
            tnei_list.append(self.pred_data['neighborTemp' + str(j+1)])
        tn = self.pred_data['roomTemp']
        solar = self.pred_data['irradiance']
        ac = self.pred_data['Q'] /100
        MELs = self.pred_data['MELs'] /100
        deltaTime = self.pred_data['deltaTime']
        self.pred_data['tn1_pred'] = self.simulation_odeint_r2c1( self.paras_pred
                                                 , ta, tnei_list, tn, solar, ac, MELs, deltaTime)
        self.pred_data['tn1_pred'] = self.pred_data['tn1_pred'].apply(lambda x: float(x))
        self.pred_data['tn1_pred'] = self.pred_data['tn1_pred'].round(3)
        self.pred_result = self.pred_data['tn1_pred']
        # valid data visulize
        (self.pred_data['tn1_pred'] - 273.15).plot()
        (self.pred_data['ta'] - 273.15).plot()
        plt.xlabel('time')
        plt.ylabel('temperature ℃')
        plt.legend()
        plt.title('predict plot')
        plt.show()
        return self.pred_data['tn1_pred']


class PVModel():
    def __init__(self
                 , PV_data
                 , external_hyper_para = None # None or para_dict
                 ):
        self.predict_cos = PV_data.predict_cos
        self.X_train = PV_data.X_train
        self.X_test = PV_data.X_test
        self.y_train = PV_data.y_train
        self.y_test = PV_data.y_test
        self.external_hyper_para = external_hyper_para
        self.one_day_pv_predict(method='heuristic')

    def one_day_pv_predict(self, method):
        if method == 'heuristic':
            self.one_day_pv_predict_heuristic()
        elif method == 'lgb':
            self.one_day_pv_predict_lgb()

    #TODO: implement heuristic prediction
    def one_day_pv_predict_heuristic(self):


        return None, self.y_pred, self.valid_cv_rmse

    def one_day_pv_predict_lgb(self):
        for y_co in self.predict_cos:
            if self.external_hyper_para == None:
                params = {
                        "objective": "regression",
                        "boosting": "gbdt",
                        "learning_rate":1.9, #0.06, 0.7:0.5
                        "n_estimators": 100, #400,
                        "max_depth":2,
                        "num_leaves": 4,
                        "min_data_in_leaf":9, #20,
                        "max_bin":7,
                        "feature_fraction": 0.8, #0.7
                        "bagging_fraction": 0.6, #0.1,
                        "bagging_freq":10,
                        "reg_alpha":0.001, #0.001,  0.2:0.119
                        "reg_lambda":0.2, #0.00001,
                        "metric": "rmse",
                        "verbosity":0
                        }
            else:
                params = self.external_hyper_para
            nround = 1000
            categorical_features = []
            d_train = lgb.Dataset(self.X_train, label = self.y_train, categorical_feature = categorical_features, free_raw_data=False)
            d_valid = lgb.Dataset(self.X_test, label = self.y_test, categorical_feature = categorical_features, free_raw_data=False)
            self.model = lgb.train(params, train_set = d_train, num_boost_round = nround, valid_sets = [d_valid], early_stopping_rounds = 100)
            y_pred_train = self.model.predict(self.X_train)
            self.y_pred = self.model.predict(self.X_test)
            
            train_cv_rmse = math.sqrt(MSE(self.y_train.values, y_pred_train)) / self.y_train.values.mean()
            print('train cv rmse:{}'.format(train_cv_rmse))
            self.valid_cv_rmse = math.sqrt(MSE(self.y_test.values, self.y_pred)) / self.y_test.values.mean()
            # valid_cv_rmse = MAE(y_test.values, self.y_pred) / y_test.values.mean()
            print('valid cv rmse:{}'.format(self.valid_cv_rmse))
            
            plt.plot(self.y_train.values, alpha = 0.6, label = 'Measured')
            plt.plot(y_pred_train, alpha = 0.6, linestyle = '--', label = 'Estimated')
            plt.legend()
            plt.ylabel(y_co)
            plt.xlabel('index')
            plt.title('{} train cv_rmse: {}'.format(y_co,train_cv_rmse.round(3)))
            plt.show()
            
            plt.plot(self.y_test.values, alpha = 0.6, label = 'Measured')
            plt.plot(self.y_pred, alpha = 0.6, linestyle = '--', label = 'Estimated')
            plt.legend()
            plt.ylabel(y_co)
            plt.xlabel('index')
            plt.title('{} valid cv_rmse: {}'.format(y_co,self.valid_cv_rmse.round(3)))
            plt.show()
            return self.model, self.y_pred, self.valid_cv_rmse

    #TODO: train stage: get params
    # def train_hyper_para():
        # for y_co in self.predict_cos:
        #     # data_train = data_train[[y_co] + x_co].copy().dropna(how = 'any')
        #     x_axis = np.arange(1.9,3,0.1)
        #     errors = []
        #     for i in x_axis:
        #         params = {
        #                 "objective": "regression",
        #                 "boosting": "gbdt",
        #                 "learning_rate":1.9, #0.06, 0.7:0.5
        #                 "n_estimators": 100, #400,
        #                 "max_depth":2,
        #                 "num_leaves": 4,
        #                 "min_data_in_leaf":9, #20,
        #                 "max_bin":7,
        #                 "feature_fraction": 0.8, #0.7
        #                 "bagging_fraction": 0.6, #0.1,
        #                 "bagging_freq":10,
        #                 "reg_alpha":0.001, #0.001,  0.2:0.119
        #                 "reg_lambda":0.2, #0.00001,
        #                 "metric": "rmse",
        #                 "verbosity":0
        #                 }
        #         nround = 1000
        #         categorical_features = []
        #         d_train = lgb.Dataset(X_train, label = y_train, categorical_feature = categorical_features, free_raw_data=False)
        #         d_valid = lgb.Dataset(X_test, label = y_test, categorical_feature = categorical_features, free_raw_data=False)
        #         model = lgb.train(params, train_set = d_train, num_boost_round = nround, valid_sets = [d_valid], early_stopping_rounds = 100)
        #         y_pred_train = model.predict(X_train)
        #         y_pred = model.predict(X_test)
        #         errors.append(util.cv_rmse(y_test,y_pred).round(3))
        #     plt.plot(x_axis, errors)
        #     print('best parameter: {}'.format(x_axis[errors.index(min(errors))]))
            
        #     train_cv_rmse = math.sqrt(MSE(y_train.values, y_pred_train)) / y_train.values.mean()
        #     print('train cv rmse:{}'.format(train_cv_rmse))
        #     valid_cv_rmse = math.sqrt(MSE(y_test.values, y_pred)) / y_test.values.mean()
        #     # valid_cv_rmse = MAE(y_test.values, y_pred) / y_test.values.mean()
        #     print('valid cv rmse:{}'.format(valid_cv_rmse))
            
        #     plt.plot(y_train.values, alpha = 0.6, label = 'Measured')
        #     plt.plot(y_pred_train, alpha = 0.6, linestyle = '--', label = 'Estimated')
        #     plt.legend()
        #     plt.ylabel(y_co)
        #     plt.xlabel('index')
        #     plt.title('{} train cv_rmse: {}'.format(y_co,train_cv_rmse.round(3)))
        #     plt.show()
            
        #     plt.plot(y_test.values, alpha = 0.6, label = 'Measured')
        #     plt.plot(y_pred, alpha = 0.6, linestyle = '--', label = 'Estimated')
        #     plt.legend()
        #     plt.ylabel(y_co)
        #     plt.xlabel('index')
        #     plt.title('{} valid cv_rmse: {}'.format(y_co,valid_cv_rmse.round(3)))
        #     plt.show()




        
        
        
        
        
        
        
