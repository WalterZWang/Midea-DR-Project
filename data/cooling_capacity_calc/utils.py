try:
    from const import *
except Exception as e:
    from .const import *
# 根据压力计算对应的饱和温度
def Tsat_P(P):
    if P < 1.35:
        Tsat_P = 20.0615342 * P ** 3 - 66.841711 * P ** 2 + 102.76964 * P - 45.649548
    else:
        Tsat_P = -2.1530949 * P ** 2 + 27.427854 * P - 12.266995
    return Tsat_P


# 计算温度对应的饱和压力
def Psat_T(T):
    Psat_T = 2.11E-06 * T ** 3 + 2.9964000E-04 * T ** 2 + 2.508741E-02 * T + 6.9884855E-01
    return Psat_T


# 计算温度对应的饱和气态焓值
def Hsat_gas_T(T):
    if T <= 27:
        Hsat_gas_T = -2.7720000E-05 * T ** 3 - 3.5795500E-03 * T ** 2 + 3.0214283E-01 * T + 4.2132125E+02
    elif 27 < T <= 36:
        Hsat_gas_T = 0.0000000E+00 * T ** 3 - 8.5319200E-03 * T ** 2 + 4.9743170E-01 * T + 4.1907132E+02
    elif 36 < T <= 46:
        Hsat_gas_T = -2.0743000E-04 * T ** 3 + 1.2776620E-02 * T ** 2 - 2.3639466E-01 * T + 4.2754859E+02
    elif 46 < T <= 60:
        Hsat_gas_T = 0.0000000E+00 * T ** 3 - 2.6313010E-02 * T ** 2 + 2.0852191E+00 * T + 3.8329794E+02
    else:
        Hsat_gas_T = -3.4182320E-02 * T ** 3 + 6.4551319E+00 * T ** 2 - 4.0771752E+02 * T + 9.0219588E+03
    return Hsat_gas_T


# 计算温度对应的饱和液态焓值
def Hsat_liq_T(T):
    if T <= 60:
        Hsat_liq_T = 4.2940000E-05 * T ** 3 + 2.2391800E-03 * T ** 2 + 1.5029478E+00 * T + 2.0004629E+02
    else:
        Hsat_liq_T = 3.9190850E-02 * T ** 3 - 7.4534322E+00 * T ** 2 + 4.7500448E+02 * T - 9.8253079E+03
    return Hsat_liq_T


# 计算冷凝压力Pc与排气过热度SH对应的气态焓值（过热度为实际温度-对应压力下的饱和温度）
def H_hp(Pc, SH):
    H_hp = df_H_hp.loc[Pc, 'A1'] * SH ** 3 + df_H_hp.loc[Pc, 'A2'] * SH ** 2 + df_H_hp.loc[Pc, 'A3'] * SH + df_H_hp.loc[
        Pc, 'A4']
    return H_hp


# 计算冷凝压力Pc与排气过热度SH对应的气态密度
def Den_hp(Pc, SH):
    Den_hp = df_Den_hp.loc[Pc, 'A1'] * SH ** 3 + df_Den_hp.loc[Pc, 'A2'] * SH ** 2 + df_Den_hp.loc[Pc, 'A3'] * SH + \
             df_Den_hp.loc[Pc, 'A4']
    return Den_hp


# 计算蒸发压力Pe与回气过热度SH对应的气态焓值
def H_lp(Pe, SH):
    Pe = int(Pe * 100)
    H_lp = df_H_lp.loc[Pe, 'A1'] * SH ** 3 + df_H_lp.loc[Pe, 'A2'] * SH ** 2 + df_H_lp.loc[Pe, 'A3'] * SH + df_H_lp.loc[
        Pe, 'A4']
    return H_lp


# 计算蒸发压力Pe与回气过热度SH对应的气态密度
def Den_lp(Pe, SH):
    Pe = int(Pe * 100)
    Den_lp = df_Den_lp.loc[Pe, 'A1'] * SH ** 3 + df_Den_lp.loc[Pe, 'A2'] * SH ** 2 + df_Den_lp.loc[Pe, 'A3'] * SH + \
             df_Den_lp.loc[Pe, 'A4']
    return Den_lp


# 计算温度T对应的液态焓值（一般认为液态下的焓值只与温度有关）
def H_liq(T):
    H_liq = 1.7403 * T + 197.82
    return H_liq


# 计算温度T对应的液态密度
def Den_liq(T):
    Den_liq = -5.7166 * T + 1202.2
    return Den_liq


# 计算T对应的饱和气态焓值
def Den_gas_sat(T):
    if 0 < T <= 60:
        Den_gas_sat = 0.0505 * T ** 2 - 0.5769 * T + 46.625
    return Den_gas_sat


# 计算T对应的饱和液态焓值
def Den_liq_sat(T):
    if 0 < T <= 60:
        Den_liq_sat = -0.0513 * T ** 2 - 2.4381 * T + 1153.9
    return Den_liq_sat


# 根据压缩机十系数计算压缩机的理论流量（十系数流量），Te为压缩机蒸发温度（回气压力对应饱和温度），Tc为冷凝温度（排气压力对应饱和温度），INV为压缩机转速
def Gr_ari(Comp, Te, Tc, INV):  # Comptype：1-AA55; 2-DC80; 3-SAVCO60 ; 4-SAVCO70; 5-SAVCO96
    Gr_ari = Comp.loc[INV, 'C1'] + Comp.loc[INV, 'C2'] * Te + Comp.loc[INV, 'C3'] * Tc + Comp.loc[INV, 'C4'] * Te ** 2 + \
             Comp.loc[INV, 'C5'] * Tc * Te + Comp.loc[INV, 'C6'] * Tc ** 2 + Comp.loc[INV, 'C7'] * Te ** 3 + Comp.loc[
                 INV, 'C8'] * Tc * Te ** 2 + Comp.loc[INV, 'C9'] * Te * Tc ** 2 + Comp.loc[INV, 'C10'] * Tc ** 3
    if Gr_ari < 0:
        Gr_ari = 0
    return Gr_ari


# 计算根据压比（Pr）拟合的理论排气温度，压比由排气压力与回气压力计算
def T7cS(Pc, Pe):
    Tc = Tsat_P(Pc)
    pr = (Pc + 0.1) / (Pe + 0.1)  # 这里+0.1是因为压比需要使用绝对压力计算，之前提及的压力一般均为表压
    if pr <= 4.75:
        T7cS = 0.19987367 * pr ** 3 - 2.90838056 * pr ** 2 + 17.35684441 * pr - 12.86053058 + Tc
    else:
        T7cS = 0.01184201 * pr ** 3 - 0.39347038 * pr ** 2 + 6.02414152 * pr + 4.48011635 + Tc
    if T7cS < 0:
        T7cS = 35
    elif T7cS > 90:
        T7cS = 90
    return T7cS


# 计算流量修正系数，Tn为实际的回气温度
def coff_k(Tn, Te, T7c, T7cS, Tc, Pc, Pe, Gr_ari, P_Comp):
    if T7c - T7cS < 2 and Tn - Te <= 2:
        pr = (Pc + 0.1) / (Pe + 0.1)
        delta_h = 0.0973 * pr ** 3 - 2.4261 * pr ** 2 + 25.704 * pr - 17.859
        ni = delta_h * Gr_ari / (P_Comp + 0.00000000000001) / 0.85 - 0.02
        ht7c = H_hp(Pc, T7c - Tc)
        ht7 = ht7c - delta_h / ni
        hpe_liq = Hsat_liq_T(Te)
        hpe_gas = Hsat_gas_T(Te)
        x = (ht7 - hpe_liq) / (hpe_gas - hpe_liq)
        coff_k = 2.5946 * x ** 2 - 5.8315 * x + 4.3386
    else:
        coff_k = 0.0001 * (Tn - Te) ** 2 - 0.0101 * (Tn - Te) + 1.1013
    return coff_k


# 计算另一个流量修正系数
def coff_k_2(Tn, Te):
    coff_k_2 = 0.0001 * (Tn - Te) ** 2 - 0.0101 * (Tn - Te) + 1.1013
    return coff_k_2


def Te_1(Fr, Pe):
    P_acc = 0.5436 * Fr / 1000
    Pe_1 = Pe - P_acc  # 回气压力修正值
    Te_1 = Tsat_P(Pe_1)
    return Te_1


# 回气焓值在回气过热度不足时需要进行相应修正
def Ht7_out(Tn, Te, T7c, T7cS, Tc, Pc, Pe, Gr_ari, P_Comp):
    if T7c - T7cS < 2 and Tn - Te <= 2:
        pr = (Pc + 0.1) / (Pe + 0.1)
        delta_h = 0.0973 * pr ** 3 - 2.4261 * pr ** 2 + 25.704 * pr - 17.859
        ni = delta_h * Gr_ari / (P_Comp + 0.000000000001) / 0.85 - 0.02
        ht7c = H_hp(Pc, T7c - Tc)
        Ht7_out = ht7c - delta_h / ni
    else:
        Ht7_out = H_lp(Pe, Tn - Te)
    return Ht7_out


# 另一种回气焓值修正方法
def Ht7_out_2(T2B, Te, T7c, T7cS, Tc, Pc, Pe, Gr_ari, P_Comp):
    if T7c - T7cS < 2 and T2B - Te <= 2:
        pr = (Pc + 0.1) / (Pe + 0.1)
        delta_h = 0.0973 * pr ** 3 - 2.4261 * pr ** 2 + 25.704 * pr - 17.859
        ni = delta_h * Gr_ari / (P_Comp + 0.000000000001) / 0.85 - 0.02
        ht7c = H_hp(Pc, T7c - Tc)
        Ht7_out_2 = ht7c - delta_h / ni
    else:
        Pe_odu = Pe + 0.03
        SH_eqv = T2B - Tsat_P(Pe_odu)
        Ht7_out_2 = H_lp(Pe, SH_eqv)
    return Ht7_out_2


# 另一种回气焓值修正方法，与上面方法相同
def Ht7_out_3(T2B, Te, T7c, T7cS, Tc, Pc, Pe, Gr_ari, P_Comp):
    if T7c - T7cS < 2 and T2B - Te <= 2:
        pr = (Pc + 0.1) / (Pe + 0.1)
        delta_h = 0.0973 * pr ** 3 - 2.4261 * pr ** 2 + 25.704 * pr - 17.859
        ni = delta_h * Gr_ari / (P_Comp + 0.000000000001) / 0.85 - 0.02
        ht7c = H_hp(Pc, T7c - Tc)
        Ht7_out_3 = ht7c - delta_h / ni
    else:
        Pe_odu = Pe + 0.03
        SH_eqv = T2B - Tsat_P(Pe_odu)
        Ht7_out_3 = H_lp(Pe_odu, SH_eqv)
    return Ht7_out_3


# 计算压缩机流量的另一种方法，根据容积效率计算
def Gr_Comp(Te, T7, Pe, INV, V_exh):
    if V_exh == 60:
        𝞰 = 0.936
    if V_exh == 70:
        𝞰 = 1
    if V_exh == 96:
        𝞰 = 1
    Gr_Comp = Den_lp(Pe, T7 - Te) * INV * V_exh * 𝞰 * 3.6 / 1000  # V_exh为气缸吸气容积
    return Gr_Comp


# 喷焓系数计算方法
def inj_00(Comptype, Pe, INV, T6a):
    P_inj = Psat_T(T6a)
    if Comptype == 1:
        inj_00 = (dff_AA55.loc[INV, 'A'] + dff_AA55.loc[INV, 'B'] * ((P_inj + 0.1) / (Pe + 0.1)))
    elif Comptype == 2:
        inj_00 = (dff_DC80.loc[INV, 'A'] + dff_DC80.loc[INV, 'B'] * ((P_inj + 0.1) / (Pe + 0.1)))
    elif Comptype == 3:
        inj_00 = (dff_SAVC060.loc[INV, 'A'] + dff_SAVC060.loc[INV, 'B'] * ((P_inj + 0.1) / (Pe + 0.1)))
    elif Comptype == 4:
        inj_00 = (dff_SAVC070.loc[INV, 'A'] + dff_SAVC070.loc[INV, 'B'] * ((P_inj + 0.1) / (Pe + 0.1)))
    inj_00 = inj_00
    inj_00 = max(min(inj_00, 0.20), 0)
    return inj_00


# 根据sv7阀门计算此部分旁通流量，up代表顶出风多联机，C栋2楼的所有机器均为顶出风
def Gr_bypass_up(Pc, Pe, T7c, Tc, HP, SV7, Cv_sv7):
    if 8 <= HP <= 12:
        Cv_total = Cv_sv7 * SV7 + 2.0E-05 + 3.0E-02
    elif 14 <= HP <= 18:
        Cv_total = Cv_sv7 * SV7 + 2.0E-05 + 5.0E-02
    elif 20 <= HP <= 24:
        Cv_total = Cv_sv7 * SV7 + 4.0E-05 + 5.0E-02
    elif 26 <= HP <= 28:
        Cv_total = Cv_sv7 * SV7 + 4.0E-05 + 3.0E-02
    elif 30 <= HP <= 32:
        Cv_total = Cv_sv7 * SV7 + 5.0E-05 + 3.0E-02
    elif 34 <= HP <= 42:
        Cv_total = Cv_sv7 * SV7 + 5.0E-05 + 5.0E-02
    Gr_bypass_up = 27.09 * Cv_total * (((Pc - Pe) * 10 * Den_hp(Pc, T7c - Tc)) ** 0.5)
    return Gr_bypass_up


# 根据sv7阀门计算此部分旁通流量，side代表侧出风
def Gr_bypass_side(Pc, Pe, T7c, Tc, HP, SV7, Cv_sv7):
    if 7 <= HP <= 20:
        Cv_total = Cv_sv7 * SV7 + 2.0E-05 + 3.0E-02
    Gr_bypass_side = 27.09 * Cv_total * (((Pc - Pe) * 10 * Den_hp(Pc, T7c - Tc)) ** 0.5)
    return Gr_bypass_side


# 根据内机匹数（匹数为内机固有信息）与内机电子膨胀阀开度（exv1opening点位）计算对应内机的cv值，即流量系数
def CV_Valve_in(Hp, pls):# Hp:内机匹数 pls：exv1opening
    if Hp <= 3:
        bore = 2.0
    elif Hp > 3:
        bore = 2.4  # 口径
    if bore == 2.0:
        if pls < 420:
            CV_Valve_in = min(-2.4650986E-07 * pls ** 2 + 4.5057327E-04 * pls - 9.9681000E-03, 0.175)
        else:
            CV_Valve_in = min(-1.8600709E-06 * pls ** 2 + 2.2114331E-03 * pls - 4.6567020E-01, 0.175)
    elif bore == 2.4:
        CV_Valve_in = min(-8.6785257E-07 * pls ** 2 + 1.0566637E-03 * pls - 2.98239E-02, 0.273)
    if CV_Valve_in < 0:
        return 0
    else:
        return CV_Valve_in

    # 外机中的exvc阀cv值计算，计算c阀流量需要使用


def Cv_Valve_exvC(pls):
    Cv_Valve_exvC = min(-8.6785257E-07 * pls ** 2 + 1.0566637E-03 * pls - 2.98239E-02, 0.273)
    if Cv_Valve_exvC <= 0:
        return 0
    else:
        return Cv_Valve_exvC

    # 顶出风机型主阀-exvA的cv值计算，需要使用外机的匹数与A阀开度


def CV_Valve_up_exvA(Hp, pls):
    if Hp <= 18:
        bore = 4.5
    elif 18 < Hp <= 42:
        bore = 6.1  # 口径
    if bore == 6.1:
        if pls < 1000:
            CV_Valve_up_exvA = min(4.2711907E-09 * pls ** 2 + 4.3969752E-04 * pls - 2.9568000E-02, 0.85)
        else:
            CV_Valve_up_exvA = min(-7.289181E-08 * pls ** 2 + 5.1129793E-04 * pls - 3.0337800E-02, 0.85)
    elif bore == 4.5:
        CV_Valve_up_exvA = min(-4.7134E-06 * pls ** 2 + 4.7415536E-03 * pls - 1.8347114E-01, 0.995)
    if CV_Valve_up_exvA < 0:
        return 0
    else:
        return CV_Valve_up_exvA

    # 侧出风机型主阀cv值计算


def CV_Valve_side_exvA(Hp, pls):
    if Hp <= 14:
        bore = 4.5
    elif 14 < Hp <= 24:
        bore = 6.1  # 口径
    if bore == 6.1:
        if pls < 1000:
            CV_Valve_side_exvA = min(4.2711907E-09 * pls ** 2 + 4.3969752E-04 * pls - 2.9568000E-02, 0.85)
        else:
            CV_Valve_side_exvA = min(-7.289181E-08 * pls ** 2 + 5.1129793E-04 * pls - 3.0337800E-02, 0.85)
    elif bore == 4.5:
        CV_Valve_side_exvA = min(-4.7134E-06 * pls ** 2 + 4.7415536E-03 * pls - 1.8347114E-01, 0.995)
    return CV_Valve_side_exvA


# 计算冷凝过程的压降
def P_cond_up(HP, Gr_cond):
    if 8 <= HP <= 12:
        d1 = 1.0E-07
        e1 = 4.0E-05
        f1 = -0.0031
    elif 14 <= HP <= 16:
        d1 = 1.0E-07
        e1 = 2.0E-05
        f1 = -0.0005
    elif HP == 18:
        d1 = 2.0E-07
        e1 = -0.0002
        f1 = 0.0799
    elif 20 <= HP <= 22:
        d1 = 8.0E-08
        e1 = 2.0E-05
        f1 = -0.0022
    elif HP == 24:
        d1 = 2.0E-07
        e1 = -2.0E-04
        f1 = 0.0816
    elif 26 <= HP <= 28:
        d1 = 2.0E-08
        e1 = 9.0E-06
        f1 = -0.0033
    elif 30 <= HP <= 36:
        d1 = 1.0E-08
        e1 = 4.0E-05
        f1 = -0.0253
    elif 38 <= HP <= 42:
        d1 = 2.0E-08
        e1 = -2.0E-07
        f1 = 0.0085
    P_cond_up_0 = d1 * Gr_cond ** 2 + e1 * Gr_cond + f1
    P_cond_up = max(0, P_cond_up_0)
    return P_cond_up


# 计算过冷部分的压降
def P_micro(HP, Gr_cond):
    if 8 <= HP <= 24:
        d2 = 8.0E-07
        e2 = -1.2E-03
        f2 = 0.4892
    elif 26 <= HP <= 42:
        d2 = 6.0E-08
        e2 = 1.0E-04
        f2 = -0.0492
    P_micro_0 = 8.0E-7 * Gr_cond ** 2 - 1.2E-03 * Gr_cond + 0.4892
    P_micro = max(0, P_micro_0)
    return P_micro


# 计算A阀压降（顶出风）
def P_exvA_up(Gr_cond, CV_Valve_up_exvA, χ_Tl, TL, δ):
    Den_gas_sat = 0.0505 * TL ** 2 - 0.5769 * TL + 46.625
    Den_liq_sat = -0.0513 * TL ** 2 - 2.4381 * TL + 1153.9
    ρ_hex_out = χ_Tl * Den_gas_sat + (1 - χ_Tl) * Den_liq_sat
    if CV_Valve_up_exvA != 0:
        P_exvA_up_0 = (1 / (ρ_hex_out)) * ((Gr_cond / (27.09 * CV_Valve_up_exvA)) ** 2) * δ
        P_exvA_up = max(0, P_exvA_up_0)
    else:
        P_exvA_up = 0
    return P_exvA_up


# 计算A阀压降（侧出风）
def P_exvA_side(Gr_cond, CV_Valve_side_exvA, χ_Tl, TL, δ):
    ρ_hex_out = χ_Tl * Den_gas_sat(TL) + (1 - χ_Tl) * Den_liq_sat(TL)
    P_exvA_side = (1 / (ρ_hex_out)) * ((Gr_cond / (27.09 * CV_Valve_side_exvA)) ** 2) * δ
    return P_exvA_side


# C阀流量计算方式一
def Gr_exvc0(γ, Cv_Valve_exvC, Pm, Pc, Pe, T5):
    Gr_exvc0 = (abs(27.09 * γ * Cv_Valve_exvC * ((max((Pm - Pe), (Pc - Pe) * 0.5) * 10 * Den_liq(T5))))) ** 0.5
    return Gr_exvc0  # 此处压差是预估的，准确计算中压会提高精度，T5过冷度须判定


# C阀流量计算方式二
def Gr_exvc1(Gr_comp, inj, Gr_bypass, α, Cv_Valve_exvC, β, CV_Valve_inSum):
    inj = inj + 1
    if (Cv_Valve_exvC > 0) & (CV_Valve_inSum > 0):
        Gr_exvc1 = (Gr_comp * (1 + inj) - Gr_bypass) * α * Cv_Valve_exvC / (α * Cv_Valve_exvC + β * CV_Valve_inSum)
    else:
        Gr_exvc1 = 0
    return Gr_exvc1


def Gr_exvc(Gr_exvc0, Gr_exvc1):
    Gr_exvc = min(Gr_exvc0, Gr_exvc1)
    return Gr_exvc


def max0(m1, m2):
    max0 = max(m1, m2)
    return max0


def min0(n1, n2):
    min0 = min(n1, n2)
    return min0


def min00(k1, k2, k3):
    min00 = min(k1, k2, k3)
    return min00


"""
def α_cor(Cv_Valve_exvC):
    α_cor = (388.19*Cv_Valve_exvC*Cv_Valve_exvC-181.01*Cv_Valve_exvC+26.607)/(1+388.19*Cv_Valve_exvC*Cv_Valve_exvC-181.01*Cv_Valve_exvC+26.607)
    return α_cor   """


# 获取alpha与beta的值
def α_scope(α_exvc):
    α_scope = min(1.6, max(0.6, α_exvc))
    return α_scope


def β_scope(β_idu):
    β_scope = min(1.0, max(0.6, β_idu))
    return β_scope


# 后续不需要使用
def Gr_ms(Pc, Pe):
    cv_anti_liq = 0.02979
    Gr_ms = 27.09 * cv_anti_liq * ((Pc - Pe) * 10 * Den_hp(Pc, 1)) ** 0.5
    return Gr_ms


# 低能力时的修正精度函数
def DataMin_Prec(precision):
    DataMin_Prec = min(precision, 0.1)
    return DataMin_Prec


# 根据内机风机档位计算内机功率
def Watt_in(Fan):
    if Fan == 0:
        Watt_in = 0
    elif 0 < Fan <= 7:
        Watt_in = 80
    elif 7 < Fan <= 14:
        Watt_in = 150
    elif 14 < Fan <= 21:
        Watt_in = 210
    elif 21 < Fan <= 28:
        Watt_in = 320
    elif 28 < Fan <= 35:
        Watt_in = 380
    elif 35 < Fan <= 42:
        Watt_in = 500
    return Watt_in