import geopandas as gpd
import numpy as np
import rasterio
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve, precision_score, recall_score, f1_score, accuracy_score
import matplotlib.pyplot as plt
from shapely.geometry import Point
from sklearn.metrics import classification_report
import pandas as pd
from shapely.geometry import Point, MultiPolygon, Polygon
import folium
from pylab import *
from matplotlib.font_manager import FontProperties
mpl.rcParams['font.sans-serif']=['SimHei']
mpl.rcParams['axes.unicode_minus']=False
import plotly.graph_objects as go
import plotly.io as pio

def useDeduction(file):
    filename = file
    filepath = os.path.join('uploads', filename)

    # 从shp文件中导入物种点数据
    species_shp = gpd.read_file(filepath)
    
    roads_shp=gpd.read_file('roads/'+filename)
    
    # 计算地区的最大经纬度范围
    minx, miny, maxx, maxy = species_shp.geometry.total_bounds
    
    # 定义背景点函数(生成的背景点周围5km范围内没有物种点)
    def generate_background_points(species, seed=None, buffer_distance=5000):
        bounding_box = species.total_bounds
        np.random.seed(seed)
        minx, miny, maxx, maxy = bounding_box
        # 将数据转换到世界墨卡托投影 (EPSG:3857)
        species_mercator = species.to_crs(epsg=3857)
        points = []
        for _ in range(len(species)):
            valid = False
            while not valid:
                x = np.random.uniform(minx, maxx)
                y = np.random.uniform(miny, maxy)
                point = Point(x, y)
                point_mercator = gpd.GeoSeries([point], crs=species.crs).to_crs(epsg=3857)[0]  # 转换点到墨卡托投影
                # 检查距离
                min_distance = species_mercator.distance(point_mercator).min()
                if min_distance >= buffer_distance:
                    points.append(point)
                    valid = True
        return gpd.GeoDataFrame({'geometry': points}, crs=species.crs)
    # 生成背景点
    background_points = generate_background_points(species_shp, seed=42, buffer_distance=5000)
    
    def extract_values(points, raster_path):
        with rasterio.open(raster_path) as src:
            # 将几何对象转换为几何中心点
            points['centroid'] = points['geometry'].centroid
            # 提取几何中心点的坐标
            points['x'] = points['centroid'].x
            points['y'] = points['centroid'].y
            # 删除不必要的几何中心点列
            #points.drop('centroid', axis=1, inplace=True)
            
            # 使用几何中心点坐标进行采样
            return [val[0] for val in src.sample(zip(points['x'], points['y']))]
    
    
    data_matrix=species_shp[['Lon', 'Lat']]
    
    labels=species_shp['Level2']
    
    # 获取 'Level2' 和 'Level2_cn' 的唯一值
    unique_level2 = species_shp['Level2'].unique()
    unique_level2_cn = species_shp['Level2_cn'].unique()
    
    # 创建一个空字典，用于存储 'Level2' 和 'Level2_cn' 的对应关系
    level2_to_cn = {}
    
    # 遍历唯一值，将其对应起来
    for level2, level2_cn in zip(unique_level2, unique_level2_cn):
        level2_to_cn[level2] = level2_cn
    
    # 划分数据集
    X_train, X_test, y_train, y_test = train_test_split(data_matrix, labels, test_size=0.2, random_state=42)
    
    print("开始第一次训练")
    # 训练随机森林模型
    rf = RandomForestClassifier(n_estimators=300, class_weight={505: 100},random_state=42)
    rf.fit(X_train, y_train)
    
    y_pred = rf.predict(X_test)
    
    y_test=y_test.values
    
    report = classification_report(y_test, y_pred)
    
    print(report)
    
    #import lightgbm as lgb
    
    #lgb_model = lgb.LGBMClassifier(n_estimators=300, class_weight={505: 100}, random_state=42)
    #lgb_model.fit(X_train, y_train)
    
    #y_pred = lgb_model.predict(X_test)
    
    #print(report)
    
    # 生成经度范围
    lons = np.arange(minx, maxx + 0.01, 0.01)
    
    # 生成纬度范围
    lats = np.arange(miny, maxy + 0.01, 0.01)
    
    # 生成经纬度网格
    grid = pd.DataFrame([(lon, lat) for lon in lons for lat in lats], columns=['Lon', 'Lat'])
    
    
    
    y_pred = rf.predict(grid)
    
    lab=[level2_to_cn[x] for x in y_pred]
    
    grid['Level2_cn']=lab
    
    #grid.to_excel('2345.xlsx',index=False)
    
    # 定义用地分类到颜色的映射关系
    color_map = {
            '医疗卫生用地': 'blue',
            '体育与文化用地': 'lime',
            '公园与绿地用地': 'green',
            '工业用地': 'orange',
            '交通场站用地': 'purple',
            '居住用地': 'yellow',
            '商务办公用地': 'cyan',
            '教育科研用地': 'pink',
            '行政办公用地': 'gray',
            '机场设施用地': 'brown',
            '商业服务用地': 'red',
            # 添加其他分类及颜色的映射关系
    }
    
    # 创建一个新的图形
    plt.figure(figsize=(10, 8))
    
    # 绘制 roads_shp
    roads_shp.plot(ax=plt.gca(), color='black', linewidth=1)
    
    
    # 绘制散点图
    for level, group in grid.groupby("Level2_cn"):
        plt.scatter(group["Lon"], group["Lat"], label=level, color=color_map.get(level, 'gray'), alpha=0.5)
    
    # 添加图例
    #plt.legend()
    
    # 添加标题和轴标签
    plt.title("Land Use Map with Scatter Plot")
    plt.xlabel("Longitude")
    plt.ylabel("Latitude")
    
    # 显示图形
    #plt.show()
    plt.savefig('static/images/useDeduction.png')

    # 定义用地分类到颜色的映射关系
    color_map = {
            '医疗卫生用地': 'blue',
            '体育与文化用地': 'lime',
            '公园与绿地用地': 'green',
            '工业用地': 'orange',
            '交通场站用地': 'purple',
            '居住用地': 'yellow',
            '商务办公用地': 'cyan',
            '教育科研用地': 'pink',
            '行政办公用地': 'gray',
            '机场设施用地': 'brown',
            '商业服务用地': 'red',
            # 添加其他分类及颜色的映射关系
    }

    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Land Use Legend</title>
        <style>
            .legend {
                font-family: Arial, sans-serif;
                background-color: #fff;
                padding: 10px;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
            .legend-item {
                margin-bottom: 5px;
            }
            .legend-color {
                width: 20px;
                height: 20px;
                display: inline-block;
                margin-right: 5px;
            }
        </style>
    </head>
    <body>
        <div class="legend">
            {% for level, color in color_map.items() %}
            <div class="legend-item">
                <div class="legend-color" style="background-color: {{ color }};"></div> {{ level }}
            </div>
            {% endfor %}
        </div>
        <img src="{{ url_for('static', filename='images/useDeduction.png') }}" alt="Land Use Map">
    </table>
        
    </body>
    </html>
    """
    
    # 将HTML代码写入文件
    with open('templates/useDeduction.html', 'w') as f:
        f.write(html_content)


    '''
    # 创建一个新的 HTML 文件
    with open("templates/useDeduction.html", "w") as f:
        # 写入 HTML 头部信息
        f.write("<!DOCTYPE html>\n")
        f.write("<html>\n")
        f.write("<head>\n")
        f.write("<title>Land Use Map</title>\n")
        f.write("</head>\n")
        f.write("<body>\n")
        
        f.write("<img src={{ url_for('static', filename='images/useDeduction.png') }} alt='Land Use Map'>\n")
        
        
        
        # 写入 HTML 尾部信息
        f.write("</body>\n")
        f.write("</html>\n")
    '''


    return 1