import os
from pypinyin import pinyin, Style
import time

shp_file_path = 'data/'

# 获取文件夹中所有文件的文件名
file_names = os.listdir(shp_file_path)

pull_names=os.listdir('weather')


pull_list=[x[:-4] for x in pull_names]
    

# 去除后缀并使用集合来去重
unique_file_names = {name.rsplit('.', 1)[0] for name in file_names}
# 打印去重后的文件名列表
print(unique_file_names)

new_list=[]

for i in unique_file_names:
    new_list.append(i[:-1])
        
# 将中文转换为拼音
pinyin_list = []
for word in new_list:
    string=''
    pinyin_word = pinyin(word, style=Style.NORMAL)
    for i in pinyin_word:
        string+=i[0]
        
    pinyin_list.append(string)




shp_index=[]
for i in pull_list:
    shp_index.append(pinyin_list.index(i))

dd=[]

unique_file_names=list(unique_file_names)


import geopandas as gpd
import pandas as pd




for i in shp_index:
    dd.append('data/'+unique_file_names[i]+'.shp')

    

new_area=pd.DataFrame() 

for i in dd:
    gdf=gpd.read_file(i)
    grouped_sum = gdf.groupby('Level2_cn')['F_AREA'].sum()

    df_transposed = pd.DataFrame(columns=grouped_sum.index)  
      
    # 将汇总值设置为DataFrame的唯一行  
    df_transposed.loc[0] = grouped_sum.values  
    new_area = pd.concat([new_area,df_transposed],axis=0)
    
new_area.fillna(0, inplace=True)

def rank_elements(lst):  
    # 初始化排名和已排序元素的集合  
    rank = 1  
    sorted_elements = sorted(lst)  
    
    # 遍历已排序的元素和原始列表的索引  
    for elem in sorted_elements:  
        # 查找当前元素在原始列表中的位置  
        for i in range(len(lst)):  
            if lst[i] == elem:  
                # 输出排名和原始索引（如果需要的话）  
                print(f"Element at index {i} has rank {rank}")  
                break  
        # 增加排名计数器
        lst[i]=rank
        rank += 1  
    
    return lst

ll=rank_elements(shp_index)

new_averages=pd.DataFrame()

for i in ll:
    dh=pd.read_csv('weather/'+pull_names[i-1])
    

    # 初始化一个空的列表来存储结果  
    averages = []  
      
    # 定义每个块的行数  
    chunk_size = 30  
      
    # 计算需要遍历的次数，不超过12个块  
    num_chunks = min(len(dh) // chunk_size+1, 12)  
    
    # 遍历每个块  
    for j in range(num_chunks):  
        # 计算当前块的开始和结束索引  
        start_idx = j * chunk_size  
        end_idx = min((j + 1) * chunk_size, len(dh))  # 确保不会超出DataFrame的范围  
          
        # 提取当前块的数据  
        chunk = dh.iloc[start_idx:end_idx]  
          
        # 计算当前块的平均值  
        chunk_average = chunk.mean()  
          
        # 将平均值添加到列表中  
        averages.append(chunk_average) 
        
    averages_df = pd.DataFrame(averages) 
    new_averages = pd.concat([new_averages,averages_df],axis=0)
    
    
# 重复new_area的每一行12次  
repeated_new_area = pd.concat([new_area] * 12, ignore_index=True)  
  
# 确保averages_df和repeated_new_area的行数相同  
#assert len(averages_df) == len(repeated_new_area), "DataFrames must have the same number of rows after repeating"  
  
# 将repeated_new_area的列添加到averages_df中  
for col in repeated_new_area.columns:  
    new_averages[col] = repeated_new_area[col]  
  
# 输出结果  
print(new_averages)

new_averages.to_excel('city_pull.xlsx',index=False)

import pandas as pd  
import numpy as np  
from sklearn.model_selection import train_test_split
import lightgbm as lgb
from sklearn.multioutput import MultiOutputRegressor 

# 假设new_averages是您的DataFrame  
X = new_averages[['体育与文化用地', '公园与绿地用地', '医疗卫生用地', '商业服务用地', '商务办公用地', '居住用地', '工业用地', '教育科研用地', '机场设施用地', '行政办公用地', '交通场站用地']]  
y = new_averages[['PM2.5', 'PM10', 'So2', 'No2', 'Co', 'O3']]  

X=X*100

# 将数据划分为训练集和测试集  
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)  

# 构建LightGBM模型
params = {
    'boosting_type': 'gbdt',
    'objective': 'regression',
    'metric': 'rmse',
    'num_leaves': 31,
    'learning_rate': 0.05,
    'feature_fraction': 0.9,
    'bagging_fraction': 0.8,
    'bagging_freq': 5,
    'verbose': 0
}

model = lgb.LGBMRegressor(**params)

# 使用每个目标的最佳估计器创建一个多输出回归器  
multi_output_regressor = MultiOutputRegressor(model)  

# 训练多输出回归器  
multi_output_regressor.fit(X_train, y_train)  

# 预测  
y_pred = multi_output_regressor.predict(X_test)

# 指定要保存模型的文件路径
model_file_path = 'multi_output_regressor_model.pkl'

import joblib

# 使用 joblib 库保存模型
joblib.dump(multi_output_regressor, model_file_path)

print("模型已成功保存到文件:", model_file_path)



import joblib
import os
import geopandas as gpd
import pandas as pd
import numpy as np
# 读取 Shapefile 文件
folder_path = "uploads"
shp_filenames = get_shp_filenames(folder_path)[0]


gdf = gpd.read_file('uploads/'+shp_filenames)

grouped_sum = gdf.groupby('Level2_cn')['F_AREA'].sum()

df_transposed = pd.DataFrame(columns=grouped_sum.index)  
  
# 给定的键列表
keys = ['医疗卫生用地', '体育与文化用地', '公园与绿地用地', '工业用地', '交通场站用地', '居住用地', '商务办公用地', '教育科研用地', '行政办公用地', '机场设施用地', '商业服务用地']

# 将汇总值设置为DataFrame的唯一行  
df_transposed.loc[0] = grouped_sum.values

visited=np.ones(len(keys))

for i in range(len(keys)):
    if keys[i] not in df_transposed.columns:
        visited[i]=0

for i in range(len(visited)):
    if visited[i]==0:
        df_transposed[keys[i]]=0
        

df_transposed=df_transposed.values


# 加载模型
loaded_model = joblib.load('multi_output_regressor_model.pkl')

predictions = loaded_model.predict(df_transposed)[0]


# 保留两位小数
predictions_rounded = np.round(predictions, 2)

# 打印预测结果
print("预测结果:")
print(predictions_rounded)