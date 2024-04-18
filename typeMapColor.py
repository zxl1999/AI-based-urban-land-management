import geopandas as gpd
import folium

# 读取 Shapefile 文件
gdf = gpd.read_file('遵义市.shp')

# 创建一个地图对象
m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=10)

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

# 创建图例
legend_html = '<div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000; background-color: white; padding: 10px; border: 1px solid black;">'
legend_html += '<p><strong>图例</strong></p>'
for category, color in color_map.items():
    legend_html += f'<p><i class="fa fa-square fa-1x" style="color:{color}"></i>&nbsp;{category}</p>'
legend_html += '</div>'

# 将图例添加到地图上
m.get_root().html.add_child(folium.Element(legend_html))

# 遍历每个类别，并将它们添加到地图上
for category, color in color_map.items():
    # 筛选出对应类别的地理数据
    category_data = gdf[gdf['Level2_cn'] == category]
    # 遍历每个地理数据，并添加到地图上
    for _, row in category_data.iterrows():
        # 获取索引值
        idx = row.name
        folium.GeoJson(
            row.geometry,
            style_function=lambda feature, color=color: {
                'fillColor': color,
                'color': 'black',
                'weight': 1,
                'fillOpacity': 0.7,
            },
            tooltip=f'索引: {idx}\n面积: {row["F_AREA"]}\n{row["Level2_cn"]}'  # 设置鼠标悬停在地物上时显示的信息
        ).add_to(m)

# 保存地图为 HTML 文件
m.save('map_with_legend.html')
