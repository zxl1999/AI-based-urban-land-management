import os
from flask import Flask, render_template, request, redirect, url_for
import geopandas as gpd
import folium

import os
from flask import Flask, render_template, request, redirect, url_for
import geopandas as gpd
import folium
import joblib
import os
import geopandas as gpd
import pandas as pd
import numpy as np

def draw_editmap(file):
    filename = file
    filepath = os.path.join('uploads', filename)
    
        
    # 读取 Shapefile 文件
    gdf = gpd.read_file(filepath)
    
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
    predictions_rounded = np.round(predictions, 4)
    
    print(predictions)

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
                    name=str(idx)+' '+category,
                    style_function=lambda feature, color=color: {
                        'fillColor': color,
                        'color': 'black',
                        'weight': 1,
                        'fillOpacity': 0.7,
                    },
                    tooltip=f'索引: {idx}\n面积: {row["F_AREA"]}\n{row["Level2_cn"]}'  # 设置鼠标悬停在地物上时显示的信息
                ).add_to(m)

    try:
        gdf2 = gpd.read_file('roads/'+filename)
        # 将第二个 GeoDataFrame 添加到地图上
        folium.GeoJson(
            gdf2,
            name='roads'
        ).add_to(m)
    except:
        pass

    # 添加一个 LayerControl 控制器，允许用户切换图层的可见性
    folium.LayerControl().add_to(m)

    # 保存地图为 HTML 文件
    m.save('templates/map_with_draw.html')
        
        
    
    import re
    from bs4 import BeautifulSoup
    # 打开HTML文件进行读取
    with open('templates/map_with_draw.html', 'r', encoding='utf-8') as file:
        # 逐行读取文件内容
        html_content = file.read()

    # 使用 BeautifulSoup 解析 HTML
    soup = BeautifulSoup(html_content, 'html.parser')

    # 使用正则表达式查找 div 元素的 id 属性
    pattern = re.compile(r"map_\w+")
    div = soup.find("div", {"class": "folium-map", "id": pattern})

    if div:
        div_id = div.get("id")
        print("Div id:", div_id)
    else:
        print("No div found with the specified class and id pattern")

        
    # 读取整个HTML文件内容并存储在列表中
    with open('templates/map_with_draw.html', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 要插入的JavaScript函数
    js_function = """
    
    var color_map = {
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
    '商业服务用地': 'red'
    // 添加其他分类及颜色的映射关系
};

            // 添加点击事件处理函数
    var points = [];
    var polyline;
    var areas;
    var polygon;\n
    """+div_id+""".on('click', function(e){
        var lat = e.latlng.lat;
        var lng = e.latlng.lng;
        points.push([lat, lng]);
        
        // 清除之前的线条和多边形
        /*if (polyline) {\n
    """+div_id+""".removeLayer(polyline);
        }
        if (polygon) {\n
    """+div_id+""".removeLayer(polygon);
        }*/
        
        // 绘制新的线条
        polyline = L.polyline(points, {color: 'blue'}).addTo(\n"""+div_id+""");
        
        // 如果点的数量大于3，则绘制闭合多边形
        /*if (points.length > 3) {
            polygon = L.polygon(points, {color: 'red', fill: true, fillOpacity: 0.5}).addTo(\n"""+div_id+""");
        }*/

    	console.log(points);
    var points_cp=points.slice();
    points_cp.push(points[0]);
    console.log(points_cp)
        // 创建 Turf.js 多边形对象
    var polygon_cp = turf.polygon([points_cp]);

    // 计算多边形面积
    areas = turf.area(polygon_cp) / 1000000;

    // 打印多边形面积
    console.log("Area:", areas);
    pullEn();
    });
            """

    # 查找最后一个 </script> 标签的位置
    last_script_tag_index = -1
    for i, line in enumerate(lines):
        if '</script>' in line:
            last_script_tag_index = i

    # 在最后一个 </script> 标签之前插入 JavaScript 函数
    if last_script_tag_index != -1:
        lines.insert(last_script_tag_index, js_function)
    else:
        # 如果找不到 </script> 标签，则直接在文件末尾添加 JavaScript 函数
        lines.append(js_function)

    # 将更新后的 HTML 内容写回文件
    with open('templates/map_with_draw.html', 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(line)
            
    # 打开 HTML 文件并读取内容
    with open("templates/map_with_draw.html", "r", encoding='utf-8') as file:
        html_content = file.read()

    # 在 Leaflet.awesome-markers 库的引用之后添加 Turf.js 库的引用
    leaflet_awesome_markers_script = '<script src="https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js"></script>'
    turf_script = '<script src="https://cdn.jsdelivr.net/npm/@turf/turf@6.3.0/turf.min.js"></script>'
    html_content = html_content.replace(leaflet_awesome_markers_script, leaflet_awesome_markers_script + "\n" + turf_script)

    # 将修改后的内容写回到文件中
    with open("templates/map_with_draw.html", "w", encoding='utf-8') as file:
        file.write(html_content)

    # 读取 map.html 文件
    with open('templates/map_with_draw.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
            
    # 将 height: 100.0%; 修改为 height: 97.0%;
    modified_html_content = html_content.replace('height: 100.0%;', 'height: 97.0%;')
            
    # 将修改后的内容写入到新文件中
    with open('templates/map_with_draw.html', 'w', encoding='utf-8') as file:
        file.write(modified_html_content)

    with open('templates/map_with_draw.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
        
    # 在<body>标签后添加所需内容
    insertion_point = '<body>'
    inserted_content = '''<form id="myForm" class="left-table">
        <label for="textInput">添加用地类型：</label>
        <input type="text" id="textInput" name="inputText">
        <button type="button" onclick="sendData()">提交</button>
    </form>
    
    <table id="info-table-env" border="1" class="right-table">
        <tr>
            <th>PM2.5</th>
        <th>PM10</th>
        <th>So2</th>
        <th>No2</th>
        <th>Co</th>
        <th>O3</th>
        </tr>
        <tr>
        <td>'''+str(predictions_rounded[0])+'''</td>
        <td>'''+str(predictions_rounded[1])+'''</td>
        <td>'''+str(predictions_rounded[2])+'''</td>
        <td>'''+str(predictions_rounded[3])+'''</td>
        <td>'''+str(predictions_rounded[4])+'''</td>
        <td>'''+str(predictions_rounded[5])+'''</td>
    </table>
    
    '''
    modified_html_content = html_content.replace(insertion_point, insertion_point + inserted_content)
                
    # 将修改后的内容写入到新文件中
    with open('templates/map_with_draw.html', 'w', encoding='utf-8') as file:
        file.write(modified_html_content)

    
    # 读取整个HTML文件内容并存储在列表中
    with open('templates/map_with_draw.html', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 要插入的JavaScript函数
    js_function = """
            function sendData() {
            var inputText = document.getElementById("textInput").value;
            
            var color = color_map[inputText];
            
            polygon = L.polygon(points, {color: color, fill: true, fillOpacity: 0.5}).addTo(\n"""+div_id+""");
            // 将数据组装成对象
            var data = {
                inputText: inputText,
                points: points,
                areas: areas
            };

            // 使用 fetch 发送 POST 请求给 Flask 后端
            fetch('/submit', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
            })
            .catch((error) => {
                console.error('Error:', error);
            });
            
            // 重置 points 和 areas
            points = [];
            areas = undefined;
        }
        
        function pullEn() {
        var inputText = document.getElementById("textInput").value;
        
        // 将数据组装成对象
        var data = {
            inputText: inputText,
            points: points,
            areas: areas
        };

        // 使用 fetch 发送 POST 请求给 Flask 后端
        fetch('/pullEn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
        })
        .catch((error) => {
            console.error('Error:', error);
        });
        
        
    }
        
        """

    # 查找最后一个 </script> 标签的位置
    last_script_tag_index = -1
    for i, line in enumerate(lines):
        if '</script>' in line:
            last_script_tag_index = i

    # 在最后一个 </script> 标签之前插入 JavaScript 函数
    if last_script_tag_index != -1:
        lines.insert(last_script_tag_index, js_function)
    else:
        # 如果找不到 </script> 标签，则直接在文件末尾添加 JavaScript 函数
        lines.append(js_function)

    # 将更新后的 HTML 内容写回文件
    with open('templates/map_with_draw.html', 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(line)


    print("JavaScript 函数已成功添加到 HTML 文件中。")

    with open('templates/map_with_draw.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
        
    # 在<body>标签后添加所需内容
    insertion_point = '<style>'
    inserted_content = '''/* 样式化两个表格 */
    .left-table {
        float: left; /* 向左浮动 */
        width: 50%; /* 设置表格宽度为页面的一半 */
    }

    .right-table {
        float: right; /* 向右浮动 */
        width: 50%; /* 设置表格宽度为页面的一半 */
    }

    th, td {
        border: 1px solid black;
        padding: 8px;
        text-align: left;
    }
    
    '''
    modified_html_content = html_content.replace(insertion_point, insertion_point + inserted_content)
                
    # 将修改后的内容写入到新文件中
    with open('templates/map_with_draw.html', 'w', encoding='utf-8') as file:
        file.write(modified_html_content)