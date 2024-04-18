import os
from flask import Flask, render_template, request, redirect, url_for
import geopandas as gpd
import folium
import joblib
import os
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon, MultiPolygon, Point, LineString

# 读取 Shapefile 文件
gdf = gpd.read_file('data/阿克苏地区.shp')

shapefile_path2 = "roads/阿克苏地区.shp"
gdf2 = gpd.read_file(shapefile_path2)

grouped_sum = gdf.groupby('Level2_cn')['F_AREA'].sum()

print('绿地面积:')
print(grouped_sum.values.tolist()[2])



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
        

df_transposed=df_transposed.values*100

#df_transposed[0][2]=10
# 加载模型
loaded_model = joblib.load('multi_output_regressor_model.pkl')

predictions = loaded_model.predict(df_transposed)[0]
#print(predictions)

# 保留两位小数
predictions_rounded = np.round(predictions, 2)

print(predictions)

average_pollution=sum(predictions_rounded)/6

# 为每个区域生成随机的污染数值
gdf['pollution'] = np.random.uniform(15, 100, len(gdf))

buffer_distance = 0.0001  # 缓冲区距离

polygonList=gdf['geometry'].values.tolist()

# 模拟城市扩张
for i in range(2):
    for index, row in gdf.iterrows():
        if row['pollution'] > average_pollution:
            if row['Level2_cn'] == '公园与绿地用地':
                # 如果缓冲区与其他用地相交，并且相交的用地不是绿地，则重新选择扩张方向
                    
                other_polygons=[]
                    
                for i in polygonList:
                    if i==row['geometry']:
                        continue
                    other_polygons.append(i)
                    
                other_polygons=MultiPolygon(other_polygons)
                if isinstance(row['geometry'], MultiPolygon)!=True:
                    row['geometry']=MultiPolygon([row['geometry']])
                
                # 指定缓冲区距离（以单位距离为例，可以是米、千米等）
                buffer_distance = 0.0001  # 单位距离
    
                # 根据原有形状生成缓冲区
                buffered_shape = row['geometry'].buffer(buffer_distance)
    
                flag=0
    
                for geom in other_polygons:
                    if geom.intersects(buffered_shape):
                        intersection_geom = geom.intersection(row['geometry'])
                        flag=1
                        break
                
                roads= gdf2['geometry'].values.tolist()
                
                for geom in roads:
                    if geom.intersects(buffered_shape):
                        intersection_geom = geom.intersection(row['geometry'])
                        flag=1
                        break
                    
                print(flag)
                if flag==0:
                    gdf.at[index, 'geometry'] =buffered_shape

gdf.to_file('阿克苏地区.shp', encoding="utf-8")

