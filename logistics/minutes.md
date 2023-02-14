# Meeting Notes

- [2022](#2022-06-15)
- [2023](#2023-01-03)

## 2022-06-15
### Agenda
- Feedback and discussion on this morning's meeting with Media
### Progress
|Who|Item|Description|Progress|
|---|---|---|---|
|Mingyue|VRF System EDA|Analyze the data of VRF 2HUY|`done`|

### Next step
- Revise and complete EDA
    - Ambient weather: weather station vs. sensor on outdoor unit, difference for both ON/OFF periods
    - Power decomposition: analyze the power percentage of indoor fan, outdoor fan, and compressor 
    - Power regression
        - Compressor
            - Power with frequency, try linear model with only ON data, *Page 14*
            - Power with the number of running indoor unit
            - Power with condensing and evaporating temperature
        - Fan: power with frequency 
    - Analyze the tracking error of temperature set-point
    - Improve visualization
        - Revise color legend: think about the implication of color (red for hot, blue for cold), percentage using [sequential or diverging color](https://matplotlib.org/stable/tutorials/colors/colormaps.html), *page 21, 22*
        - Use `axvspan` of `matplotlib` to represent the ON/OFF period, see figure 12 of [paper](https://doi.org/10.1016/j.apenergy.2022.119104), *page 22, left bottom*
        - The figure title, legend, axis title and label must be complete, clear, readable and free of abbrevation, *page 22*
        - Use boxplot to summarize the daily variation at the same hour of the day, see figure 15 of [paper](https://doi.org/10.1016/j.apenergy.2022.119104), *page 25*
    - Refactor the code using **Jupyter Notebook** and upload to the github under sub-folder `model`
    - Analyze the relation of different condenser and evaporator temperatures after the system graph is available
    - Analyze other VRFs when all the above problems are solved
- Read the two papers on VRF data mining: [E&B](https://www.sciencedirect.com/science/article/pii/S0378778820315425), [BS](https://link.springer.com/article/10.1007/s12273-020-0670-x)
- Weather underground data
- Think about the model

## 2022-06-20
### Agenda
- Literature review by Wutao
- EDA by Mingyue
- [Model for MPC](https://gohkust-my.sharepoint.com/:f:/r/personal/cezhewang_ust_hk/Documents/%E7%BE%8E%E7%9A%84-%E6%B8%AF%E7%A7%91%E5%A4%A7/%E4%BC%9A%E8%AE%AE/0622?csf=1&web=1&e=n9PR2F)

### Progress
|Who|Item|Description|Progress|
|---|---|---|---|
|Mingyue|VRF System EDA|Analyze the data of VRF|Identified power data problem|
|Wutao|Literature review|Two VRF data mining paper by Mingyan Qian|`done`|

### Next step
- Mingyue
    - Add take-home messages to each slides. Identify and clarify on the data problem with Midea team
    - Think about the room level R-C model, read some paper if you have time
- Wutao
    - Literature review on VRF modeling methods for MPC purpose, starting from papers published by [Donghun Kim](https://scholar.google.com/citations?hl=en&user=Og5AGMMAAAAJ&view_op=list_works&sortby=pubdate)

## 2022-12-13
### Discussion
- Details of the data-driven method, why it is more accurate than RC model?
- Which data you have used for training

### Next steps
#### Zhenyu
- Refactor your code using the new structure in the main branch
- Outlier detection: understand, implement, compare different methods, and recommend the suitable one for different type of data
    - Something to start with: 3-sigma, DBSCAN, isolation forest, KernelDensity. 
        - You can find an open source outlier detection code [here](https://github.com/apachecn/ml-mastery-zh/blob/master/docs/algo/anomaly-detection-with-isolation-forest-and-kernel-density-estimation.md)
    - Read other paper, and propose more
- Missing data imputation
    - Start from this [paper](https://ieeexplore.ieee.org/abstract/document/9378230)
    - Propose and compare more
#### Wanfu
- Add detailed comments
- PV prediction using heristic method
- Push the cooling capacity result to Influxdb
- Implement the cooling capacity calculation code, and deploy it online
#### Dan
- Another version of open loop control, start at 0:00 AM every morning, do a 24 hour optimization without replanning
- Standardize the workflow and structure, make it also suitable for other VRFs

## 2022-12-20
### Discussion
- Dan introduced the difference between optimal control problem (OCP, no real-time feedback and re-planning) and model predictive control (MPC), in many cases the temperature is out of control
- Zhenyu introduced the code of selecting the usable data (no missing rate) for training

### Next steps
#### Zhenyu
- Revise the parameters of ``valid_data``
- Continue the outlier detection and missing data imputation work as described [above](#2022-12-13)
#### Wanfu
- Continue the work as described [above](#2022-12-13)
- Revise the MPC-RL paper
#### Dan
- Explore the difference between OCP and MPC
- Revise the MPC-RL paper
#### Mingchen & Dajun
- Explore the VRF model

## 2023-01-03
### Next steps
#### Zhenyu
- BRICK schema
    - Prepare a slide to introduce BRICK Schema to the team
    - Develop a BRICK model for VRF 1K0V
    - Ultimate goal: use BRICK to simplify the controller development process for other VRFs
- Data cleaning: outlier detection and missing data imputation
    - Target is to write a journal article on this
    - The goal is to proof that after data cleaning, more data is usable and the model accuracy is higher
#### Wanfu
- Revise the MPC-RL paper
- PV prediction using heristic method
- Implement the cooling capacity calculation code, and deploy it online
#### Dan
- Enhance the accuracy of RC model
- Revise the MPC-RL paper
#### Mingchen
- Work on the VRF model
    - Use Tc and Te collected by the system sensor
    - Remove data with COP less than 1
- Write VRF modeling paper, you will be the co-first author

## 2023-01-10
### Next steps
#### Zhenyu
- Data cleaning: outlier detection and missing data imputation
    - Target is to write a journal article on this
    - The goal is to proof that after data cleaning, more data is usable and the model accuracy is higher
    - Discuss with Dan if you have any questions on the RC model
#### Wanfu
- Revise the MPC-RL paper, send the revised version to Dan by 11:59 PM 12th Jan.
- Implement the cooling capacity calculation code, and deploy it online, Siqi has shared with you the updated code
#### Dan
- Revise the Shenzhen field test paper
- Revise the MPC-RL paper
- Continue work on the RL model. I personally think it is fine if R12 is different with R21, because the identified R is very likely not to be the real value of R. If needed, we can schedule a meeting to discuss the RC model
- Mingyue's code is just a reference. There may be some bugs, especially for the Kalman Filter part
#### Mingchen
- Work on the VRF model
    - Develop data-driven model, analyze the fearture importantce
    - Prepare the slides and discussion points with Midea
    - Develop a Brick model for the VRF system, which will be included in our paper

## 2023-01-31
### Next steps
#### Zhenyu
- Find a chuck of data with relatively good quality, share it with Dan by 1st Feb. 23:59.
- Develop a RC model using this data
- Schedule a meeting to discuss the RC model in the week (6th-10th Feb.)
#### Wanfu
- Calculate the cooling capacity for 1k0V (by 1st Feb. 23:59) and others
- Deploy the code online
#### Dan
- Develop a RC model using the cleaned data
- Summarize all the questions we have about RC model for the discussion
#### Mingchen
- Present the VRF Brick model and workflow this Thursday
- Continue the work on the VRF paper
#### Zhe
- Propose a paper outline for the weather forecast uncertainty paper, share it with Wanfu and Laura

## 2023-02-07
### Next steps
#### Zhenyu
- Introduce the outlier detection work this Thursday, add one page to introduce each method you used
- Think about what metrics can be used to evaluate the outlier detection and missing data imputation work
    - VRF or RC model accuracy
    - Numberical experiement: randomly create some outlier or delete some data from a complete dataset (e.g. HKUST campus environmental and energy monitoring data) 
- The outlier detection and missing data imputation method should be data-specific
    - For each type of data, which approach is recommended
    - Any way to embed physical knowledge into this process?
    - Interpolation (linear or non-linear) can not be applied to non-continuous data (such as cooling load, chiller frequency, etc.)
- RC Model
    - To create the clean data, the only imputation method that can be used is linear intepolation for temperature measurement with missing gap less than 2 hours 
#### Wanfu
- Introduce the cooling load calculation work this Thursday
    - Code structure
    - Result, compared with Siqi's data and influxdb database data
    - Analyze on the missing rate, and what are the major causes for those missing data
    - Any other problems to be discussed
    - Share the slides by Wed. night
- Continue working on the weather forecast generator for BopTest
#### Dan
- RC Model
    - Remove the data with sudden indoor temperature change
    - For multiple step forecast, use "minimizing the multiple step forecast error" as the training objective
    - Summarize all the questions we have about RC model for the discussion
#### Mingchen
- Present the VRF modeling work this Thursday
    - Use all the available data for each model
    - Share the slides by Wed. night
#### Zhe
- Schedule a meeting with Dave to discuss on BopTest

## 2023-02-14
### Next steps
#### Zhenyu
- Present the VRF modeling work this Thursday
- Package your outlier detection code, pass it to Dan's RC model to validate its performance
#### Wanfu
- Learn cvxpy, do the tutorial and exercises
- Try to implement the algorithms discussed in the MPC lecture
#### Mingchen
- Present the VRF modeling work this Thursday
- Try lightGBM, further improve GBM model
- Feature importance analysis
- Paper writing