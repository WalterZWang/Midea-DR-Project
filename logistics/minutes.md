# Meeting Notes

- [June](#2022-06-15)

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
            - Power with frequency, try linear model with only ON data
            - Power with the number of running indoor unit
            - Power with condensing and evaporating temperature
        - Fan: power with frequency 
    - Improve visualization
        - Revise color legend: think about the implication of color (red for hot, blue for cold), percentage using [sequential or diverging color](https://matplotlib.org/stable/tutorials/colors/colormaps.html)
        - Use `axvspan` of `matplotlib` to represent the ON/OFF period, see figure 12 of [paper](https://doi.org/10.1016/j.apenergy.2022.119104)
        - Use boxplot to summarize the daily variation at the same hour of the day, see figure 15 of [paper](https://doi.org/10.1016/j.apenergy.2022.119104)
    - Refactor the code using **Jupyter Notebook** and upload to the github under sub-folder `model`
    - Analyze other VRFs
- Read the two papers on VRF data mining: [E&B](https://www.sciencedirect.com/science/article/pii/S0378778820315425), [BS](https://link.springer.com/article/10.1007/s12273-020-0670-x)
- Weather underground data
- Think about the model

