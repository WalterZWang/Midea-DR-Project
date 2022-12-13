# Meeting Notes

- [June](#2022-06-15)
- [Dec.](#2022-12-13)

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