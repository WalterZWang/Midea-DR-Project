# Meeting Notes

- [Nov.](#2022-11-17)

## 2022-11-17
### Job description
- Short-term: available data for modeling (room, external unit, internal unit)
- Mid-term
    - Outlier detection
    - Imputation
    - Evaluate: scaler (dataset evaluation for MPC purpose)
- Long-term
    - Schematic modeling: BRICK
    - Standard

### Recording
- [link](https://hkust.zoom.us/rec/share/jP7m-3n5phf8amoOZKhzBf66vVk-0rhO1IDED4EUBdAhh0z4_MEinG3bkYsDB3GC.Q1awr4ImnyBqvAzZ?startTime=1668672066000)


## 2022-11-21
### Tasks for the coming weeks
- Use outlier detection algorithm before calculate the missing rate
- Develop a simple imputation method (the key is the threshold for imputation) before calculate the missing rate
- Conduct similar analysis for other VRFs
- Think about how to find the nearest useable data for self-adaptive learning


##  Code review comments for `data_evaluation.py`
- Lack of adequent comments, difficult to read
- "Do not repeat yourself", there is a huge chunk of repetitive code in cal_missing_rate1 and cal_missing_rate2
- What is the difference between cal_missing_rate1 and cal_missing_rate2?
- Lack of high level design of your code. For instance if I ask you to do a similar analysis for another external unit, you need to replace "VRF_1K0V" with anoth VRF ID, which is difficult and easy to make mistakes in your current code architecture. Instead, if you set "VRF_1K0V" as an input to your code, it would be make easier to revise