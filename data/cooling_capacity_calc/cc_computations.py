import pandas as pd

try:
    from const import *
    from utils import *
except Exception as e:
    from .const import *
    from .utils import *


def cc_calc(df:pd.DataFrame(),single_sys_odu_addr,single_sys_idu_addr,single_idu_hp):
    # 计算TpS(T7cS(Pc,Pe))
    for oud_addr in single_sys_odu_addr:
        oud_addr = str(oud_addr)
        df['odu_' + oud_addr + '_T7cS'] = df.apply(
            lambda x: T7cS(x['odu_' + oud_addr + '_highPressure'], x['odu_' + oud_addr + '_lowPressure']), axis=1)




    # 根据压缩机型号分配压缩机流量计算方法

    for odu_addr in single_sys_odu_addr:
        odu_addr = str(odu_addr)
        # 根据读取的信息得到压缩机排量单位
        if (df['odu_' + odu_addr + '_compressorCCUnit'].mean()) == 0:
            cc_unit_temp = 1
        elif (df['odu_' + odu_addr + '_compressorCCUnit'].mean()) == 1:
            cc_unit_temp = 0.5
        elif (df['odu_' + odu_addr + '_compressorCCUnit'].mean()) == 2:
            cc_unit_temp = 0.1
        comp1_discharge = cc_unit_temp * (df['odu_' + odu_addr + '_compressor1Displacement'].mean())
        comp2_discharge = cc_unit_temp * (df['odu_' + odu_addr + '_compressor2Displacement'].mean())

        # #计算压缩机十系数流量，系统内存在两台压缩机
        # #由于C栋2楼的压缩机品牌相同，因此这里只考虑了一个压缩机品牌60与70排量的十系数
        if (df['odu_' + odu_addr + '_compressorBrand']).mean() == 0:
            if comp1_discharge == 60:
                df['odu_' + odu_addr + '_comp1_Gr_ari'] = df.apply(
                    lambda x: Gr_ari(df_SAVCO60, x['odu_' + odu_addr + '_lowPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_compressor1Frequency']), axis=1)
            elif comp1_discharge == 70:
                df['odu_' + odu_addr + '_comp1_Gr_ari'] = df.apply(
                    lambda x: Gr_ari(df_SAVCO70, x['odu_' + odu_addr + '_lowPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_compressor1Frequency']), axis=1)
            elif comp1_discharge == 0:
                df['odu_' + odu_addr + '_comp1_Gr_ari'] = 0

            if comp2_discharge == 60:
                df['odu_' + odu_addr + '_comp2_Gr_ari'] = df.apply(
                    lambda x: Gr_ari(df_SAVCO60, x['odu_' + odu_addr + '_lowPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_compressor2Frequency']), axis=1)
            elif comp2_discharge == 70:
                df['odu_' + odu_addr + '_comp2_Gr_ari'] = df.apply(
                    lambda x: Gr_ari(df_SAVCO70, x['odu_' + odu_addr + '_lowPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                                     x['odu_' + odu_addr + '_compressor2Frequency']), axis=1)
            elif comp2_discharge == 0:
                df['odu_' + odu_addr + '_comp2_Gr_ari'] = 0
        # #计算压缩机功率
        df['odu_' + odu_addr + '_comp1_power'] = df.apply(
            lambda x: x['odu_' + odu_addr + '_compressor1Electricity'] * x['odu_' + odu_addr + '_directVoltage1'],
            axis=1)
        df['odu_' + odu_addr + '_comp2_power'] = df.apply(
            lambda x: x['odu_' + odu_addr + '_compressor2Electricity'] * x['odu_' + odu_addr + '_directVoltage2'],
            axis=1)
        # #计算压缩机的流量修正
        df['odu_' + odu_addr + '_comp1_coef_k'] = df.apply(
            lambda x: coff_k(x['odu_' + odu_addr + '_tgTemp'], x['odu_' + odu_addr + '_lowPressureSaturationTemp'],
                             x['odu_' + odu_addr + '_dischargeTemp1'], x['odu_' + odu_addr + '_T7cS'],
                             x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                             x['odu_' + odu_addr + '_highPressure'], x['odu_' + odu_addr + '_lowPressure'],
                             x['odu_' + odu_addr + '_comp1_Gr_ari'], x['odu_' + odu_addr + '_comp1_power']), axis=1)
        df['odu_' + odu_addr + '_comp2_coef_k'] = df.apply(
            lambda x: coff_k(x['odu_' + odu_addr + '_tgTemp'], x['odu_' + odu_addr + '_lowPressureSaturationTemp'],
                             x['odu_' + odu_addr + '_dischargeTemp2'], x['odu_' + odu_addr + '_T7cS'],
                             x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                             x['odu_' + odu_addr + '_highPressure'], x['odu_' + odu_addr + '_lowPressure'],
                             x['odu_' + odu_addr + '_comp2_Gr_ari'], x['odu_' + odu_addr + '_comp2_power']), axis=1)
        # #计算修正后压缩机流量
        df['odu_' + odu_addr + '_Gr_comp1'] = df.apply(
            lambda x: x['odu_' + odu_addr + '_comp1_coef_k'] * x['odu_' + odu_addr + '_comp1_Gr_ari'], axis=1)
        df['odu_' + odu_addr + '_Gr_comp2'] = df.apply(
            lambda x: x['odu_' + odu_addr + '_comp2_coef_k'] * x['odu_' + odu_addr + '_comp2_Gr_ari'], axis=1)




        # 计算旁通部分对应cv值
        df['CV_total'] = 0.185 * df['odu_129_SV7'] + 2.0E-05 + 3.0E-02
        # 计算排气过热度
        df['Tdsh'] = df['odu_129' + '_dischargeTemp1'] - df['odu_129' + '_highPressureSaturationTemp']
        # 根据排气过热度计算密度
        df['Den_hp'] = df.apply(lambda x: Den_hp(x['odu_129' + '_highPressure'], x['Tdsh']), axis=1)
        for odu_addr in single_sys_odu_addr:
            odu_addr = str(odu_addr)
            # 计算sv7旁通流量
            df['odu_' + odu_addr + '_Gr_bypass'] = df.apply(
                lambda x: Gr_bypass_up(x['odu_' + odu_addr + '_highPressure'], x['odu_' + odu_addr + '_lowPressure'],
                                       x['odu_' + odu_addr + '_dischargeTemp1'],
                                       x['odu_' + odu_addr + '_highPressureSaturationTemp'],
                                       x['odu_' + odu_addr + '_outdoorPlateHorses'], x['odu_' + odu_addr + '_SV7'],
                                       0.185), axis=1)
            # #计算C阀的cv值
            df['odu_' + odu_addr + '_Cv_exvC'] = df.apply(
                lambda x: Cv_Valve_exvC(x['odu_' + odu_addr + '_exv3Opening']), axis=1)  # 新增-V8
            df.loc[df['odu_' + odu_addr + '_Cv_exvC'] <= 0, 'odu_' + odu_addr + '_Cv_exvC'] = 0  # Cv值小于0的数据赋值为0
            # #计算喷焓系数
            # #制冷工况下，喷焓系数恒定为0
            # #此部分引用压缩机类型有错误，但由于只计算制冷工况，所以不影响结果
            df.loc[df[(df['odu_' + odu_addr + '_SV8'] == 1) & (df['odu_' + odu_addr + '_SV5'] == 0)].index, 'inj'] = df[
                (df['odu_' + odu_addr + '_SV8'] == 1) & (df['odu_' + odu_addr + '_SV5'] == 0)].apply(
                lambda x: inj_00(len(single_sys_idu_addr), x['odu_' + odu_addr + '_lowPressure'],
                                 x['odu' + odu_addr + '_compressor1Frequency'], x['odu' + odu_addr + '_inletT6ATemp']),
                axis=1)
            df.loc[df['odu_' + odu_addr + '_Cv_exvC'] <= 0, 'inj'] = 0
            # #计算主阀开度
            df['odu_' + odu_addr + '_Cv_up_exvA'] = df.apply(
                lambda x: CV_Valve_up_exvA(df['odu_' + odu_addr + '_outdoorPlateHorses'].mean(),
                                           x['odu_' + odu_addr + '_exv1Opening']), axis=1)  # 新增-V8
            df.loc[df['odu_' + odu_addr + '_Cv_up_exvA'] <= 0, 'odu_' + odu_addr + '_Cv_up_exvA'] = 0 # Cv值小于0的数据赋值为0
            # #计算喷焓压力
            df['odu_' + odu_addr + '_inlet_saturated_p'] = df.apply(
                lambda x: Psat_T(x['odu_' + odu_addr + '_inletT6ATemp']), axis=1)
            df['odu_' + odu_addr + '_enthalpy_p_ratio'] = (df['odu_' + odu_addr + '_inlet_saturated_p'] + 0.1) / (
                        df['odu_' + odu_addr + '_lowPressure'] + 0.1)





        # 计算所有内机的总cv值
        # 此部分的idu_i_CV_in即对应了序号为i内机的CV值，后续的能力分配也需要根据内机的CV值进行分配

        df['CV_in_sum'] = 0
        df['exv1Opening_in_sum']=0
        for j in range(len(single_idu_hp)):
            df['idu_' + str(single_sys_idu_addr[j]) + '_CV_in'] = df.apply(
                lambda x: CV_Valve_in(single_idu_hp[j], x['idu_' + str(single_sys_idu_addr[j]) + '_exv1Opening']),
                axis=1)
            df['CV_in_sum'] = df['CV_in_sum'] + df['idu_' + str(single_sys_idu_addr[j]) + '_CV_in']
            df['exv1Opening_in_sum']+=df['idu_' + str(single_sys_idu_addr[j]) + '_exv1Opening']

        # 计算总压缩机流量
        df['Gr_comp'] = df['odu_129_Gr_comp1'] + df['odu_129_Gr_comp2']
        # 计算除去sv7旁通的流量
        df['Gr_comp_0'] = df['Gr_comp'] - df['odu_129_Gr_bypass']
        # 计算c阀与内机对应系数
        df['α_exvc'] = -2.3662 * df['odu_129_Cv_exvC'] / 0.273 + 1.8659
        df['α_exvc'] = df.apply(lambda x: α_scope(x['α_exvc']), axis=1)
        df['β_idu'] = -1.3954 * df['CV_in_sum'] / len(single_idu_hp) / 0.273 + 1.0902
        df['β_idu'] = df.apply(lambda x: β_scope(x['β_idu']), axis=1)
        # 计算c阀流量
        df.loc[df['CV_in_sum'] != 0, 'Gr_exvc_1'] = df.apply(
            lambda x: Gr_exvc1(x['Gr_comp_0'], x['inj'], x['odu_129_Gr_bypass'], x['α_exvc'], x['odu_129_Cv_exvC'],
                               x['β_idu'], x['CV_in_sum']), axis=1)

        # 读取匹数信息
        HP = df['odu_129_outdoorPlateHorses'].mean()
        # 计算A阀后的中压
        df.loc[df['runMode'] == 2, 'P_cond'] = df.apply(lambda x: P_cond_up(HP, x['Gr_comp_0']), axis=1)
        df.loc[df['runMode'] == 2, 'P_micro'] = df.apply(lambda x: P_micro(HP, x['Gr_comp_0']), axis=1)
        df.loc[df['runMode'] == 2, 'P_exvA'] = df.apply(
            lambda x: P_exvA_up(x['Gr_comp_0'], x['odu_129_Cv_up_exvA'], 0.1, x['odu_129_tLTemp'], 0.13836), axis=1)
        df.loc[df['runMode'] == 2, 'Pm'] = df['odu_129_highPressure'] - df['P_cond'] - df['P_micro'] - df['P_exvA']
        df.loc[df['odu_129_Cv_exvC']<=0,'odu_129_Cv_exvC']=0
        # df['odu_129_Cv_exvC'][df['odu_129_Cv_exvC'] <= 0] = 0
        # 另一种C阀流量计算值
        df.loc[df['runMode'] == 2, 'Gr_exvc_0'] = df.apply(
            lambda x: Gr_exvc0(1, x['odu_129_Cv_exvC'], x['Pm'], x['odu_129_highPressure'], x['odu_129_lowPressure'],
                               x['odu_129_t5Temp'], ), axis=1)
        df.loc[df['runMode'] == 2, 'Gr_exvc'] = df.apply(lambda x: min0(x['Gr_exvc_0'], x['Gr_exvc_1']), axis=1)
        # 蒸发器流量=压缩机流量-sv7旁通流量-c阀流量
        df.loc[df['runMode'] == 2, 'Gr_eva'] = df['Gr_comp'] - df['Gr_exvc'] - df['odu_129_Gr_bypass']
        # 计算蒸发器入口焓值
        df.loc[df['runMode'] == 2, 'H_eva_in_1'] = df.apply(lambda x: Hsat_liq_T(x['odu_129_t5Temp']), axis=1)
        df.loc[df['runMode'] == 2, 'H_eva_in_2'] = df.apply(lambda x: H_liq(x['odu_129_t5Temp']), axis=1)
        df.loc[df['runMode'] == 2, 'H_eva_in'] = df.apply(lambda x: min0(x['H_eva_in_1'], x['H_eva_in_2']), axis=1)
        # 计算蒸发器出口焓值
        df.loc[df['runMode'] == 2, 'H_eva_out_1'] = df.apply(
            lambda x: Ht7_out(x['odu_129_tgTemp'], x['odu_129_lowPressureSaturationTemp'], x['odu_129_dischargeTemp1'],
                              x['odu_129_T7cS'], x['odu_129_highPressureSaturationTemp'], x['odu_129_highPressure'],
                              x['odu_129_lowPressure'], x['odu_129_comp1_Gr_ari'], x['odu_129_comp1_power']), axis=1)
        # 流量与焓值差计算制冷量
        df.loc[df['runMode'] == 2, 'Q_cool'] = df['Gr_eva'] * (df['H_eva_out_1'] - df['H_eva_in']) / 3.6
        df.loc[df['runMode'] == 0, 'Q_cool'] = 0


        # idu_i_CV_in即对应了序号为i内机的CV值，根据内机的CV值分配制冷量
        for j in range(len(single_idu_hp)):
            df.loc[df['runMode'] == 2,'idu_' + str(single_sys_idu_addr[j])+'_Q_cool'] = df.apply(
                lambda x:x['idu_' + str(single_sys_idu_addr[j]) + '_CV_in']/(x['CV_in_sum'])*x['Q_cool']
                if x['CV_in_sum']!=0 and not np.isnan(x['CV_in_sum']) else (0 if x['CV_in_sum'] == 0 else np.nan) ,axis=1)
            df.loc[df['runMode'] == 0, 'idu_' + str(single_sys_idu_addr[j])+'_Q_cool'] = 0

            df.loc[df['runMode'] == 2, 'idu_' + str(single_sys_idu_addr[j]) + '_Q_cool2'] = df.apply(lambda x:
            x['idu_' + str(single_sys_idu_addr[j]) + '_exv1Opening'] / x['exv1Opening_in_sum'] * x['Q_cool']
            if x['exv1Opening_in_sum'] != 0 and not np.isnan(x['exv1Opening_in_sum']) else (0 if x['exv1Opening_in_sum'] ==0 else np.nan), axis=1)
            # df.loc[df['runMode'] == 2, 'idu_' + str(single_sys_idu_addr[j]) + '_Q_cool2'] = df.apply(lambda x:
            # x['idu_' + str(single_sys_idu_addr[j]) + '_exv1Opening'] / x['exv1Opening_in_sum'] * x['Q_cool'], axis=1)
            df.loc[df['runMode'] == 0, 'idu_' + str(single_sys_idu_addr[j]) + '_Q_cool'] = 0

        return df['Q_cool'],df['runMode'],df
