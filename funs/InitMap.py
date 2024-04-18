import os
from flask import Flask, render_template, request, redirect, url_for
import geopandas as gpd
import folium
import joblib
import os
import geopandas as gpd
import pandas as pd
import numpy as np

def init_map(file):
    filename = file
    filepath = os.path.join('uploads', filename)
    
        
    # 读取 Shapefile 文件
    gdf = gpd.read_file(filepath)
    #gdf = gpd.read_file('uploads/阿克苏地区.shp')
    #print(gdf.shape)
    
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
    m.save('templates/map_with_legend.html')
        
    # 读取整个HTML文件内容并存储在列表中
    with open('templates/map_with_legend.html', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 要插入的JavaScript函数
    js_function = """
    var index;
        function onGeoJsonClick(event) {
            var lat = event.latlng.lat;
            var lon = event.latlng.lng;
            //console.log(lat, lon);
            //console.log(event);
            //console.log(event.target._tooltip._content);
            var str = event.target._tooltip._content;
           var pattern = /索引:\s*(\d+)\s*[\s\S]*?面积:\s*([\d.]+)\s*[\s\S]*?([^<]+)\s*<\/div>/; // 使用正则表达式来匹配字符串中的 <div> 和 </div> 之间的内容
	//console.log(pattern);
            var match = str.match(pattern);

            if (match) {
                index = match[1]; // 提取索引后的数字
                var area = match[2]; // 提取索引后的数字
    	var landType = match[3].trim(); // 提取工业用地等信息，并去除首尾空白字符
                //console.log("type:", landType);
                //console.log("area:", area);
	//console.log("index:", index);
	updateTable(index,lat, lon,area, landType) 
            } else {
                console.log("未匹配到内容");
            }
                    }

function updateTable(index,lat, lon,area, landType) {
    var table = document.getElementById("info-table");
    
    // 清空表格内容
    while (table.rows.length > 1) {
        table.deleteRow(1);
    }

    // 插入新数据
    var row = table.insertRow(-1);
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);
    var cell4 = row.insertCell(3);
    var cell5 = row.insertCell(4);
    cell1.innerHTML = index;
    cell2.innerHTML = lat.toFixed(6);
    cell3.innerHTML = lon.toFixed(6);
    cell4.innerHTML = area;
    cell5.innerHTML = landType;
}

function submitLandType() {
        var selectedLandType = document.getElementById("land-type").value;
        // 执行将选项值传递给后端的操作，可以使用fetch或其他方式发送POST请求给Flask后端
        // 示例：使用fetch发送POST请求给Flask后端
        // 执行将选项值和序号传递给后端的操作
        fetch('/update_land_type', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ landType: selectedLandType, index: index })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Success:', data);
            // 在成功响应后执行的操作，例如更新页面内容等
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
    with open('templates/map_with_legend.html', 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(line)

    print("JavaScript 函数已成功添加到 HTML 文件中。")


    # 打开HTML文件进行读取
    with open('templates/map_with_legend.html', 'r', encoding='utf-8') as file:
        # 逐行读取文件内容
        lines = file.readlines()

        # 用于存储匹配到的元素的列表
        matched_elements = []

        # 使用正则表达式匹配带有特定元素的行
        import re
        for line in lines:
            # 此处假设您要匹配的元素是类似于var geo_json_7850b6c049010cd2b6fe16562b3fad31这样的变量定义行
            match = re.search(r'var\s+geo_json_\w+\s+=\s+', line)
            if match:
                matched_elements.append(line.strip())

    # 输出匹配到的元素列表
    #print("匹配到的元素:")
    #for element in matched_elements:
        #print(element)

    result=[]
    for i in matched_elements:
        # 使用正则表达式进行匹配
        match = re.match(r'var\s+(geo_json_\w+)\s+=\s+L\.geoJson', i)

        if match:
            field_name = match.group(1)
            result.append(field_name)
                
    # 读取整个HTML文件内容并存储在列表中
    with open('templates/map_with_legend.html', 'r', encoding='utf-8') as file:
        lines = file.readlines()

    # 要插入的JavaScript函数
    js_function = """"""

    for i in result:
        js_function+=i+".on('click', onGeoJsonClick);\n"

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
    with open('templates/map_with_legend.html', 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(line)

    print("JavaScript 函数已成功添加到 HTML 文件中。")
        
    # 读取 map.html 文件
    with open('templates/map_with_legend.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
        
    # 将 height: 100.0%; 修改为 height: 97.0%;
    modified_html_content = html_content.replace('height: 100.0%;', 'height: 97.0%;')
        
    # 将修改后的内容写入到新文件中
    with open('templates/map_with_legend.html', 'w', encoding='utf-8') as file:
        file.write(modified_html_content)
            
    with open('templates/map_with_legend.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
        
    # 在<body>标签后添加所需内容
    insertion_point = '<body>'
    inserted_content = '''<table id="info-table" border="1" class="left-table">
        <tr>
            <th>序号</th>
            <th>经度</th>
            <th>纬度</th>
            <th>占地面积</th>
            <th>用地类型</th>
        </tr>
    </table> 
    
    <!-- 下拉列表 -->
<select id="land-type">
    <option value="医疗卫生用地">医疗卫生用地</option>
    <option value="体育与文化用地">体育与文化用地</option>
    <option value="公园与绿地用地">公园与绿地用地</option>
    <option value="工业用地">工业用地</option>
    <option value="交通场站用地">交通场站用地</option>
    <option value="居住用地">居住用地</option>
    <option value="商务办公用地">商务办公用地</option>
    <option value="教育科研用地">教育科研用地</option>
    <option value="行政办公用地">行政办公用地</option>
    <option value="机场设施用地">机场设施用地</option>
    <option value="商业服务用地">商业服务用地</option>
    <!-- 添加更多选项 -->
</select>

<!-- 按钮 -->
<button onclick="submitLandType()">确认</button>
    
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
    with open('templates/map_with_legend.html', 'w', encoding='utf-8') as file:
        file.write(modified_html_content)
        
    with open('templates/map_with_legend.html', 'r', encoding='utf-8') as file:
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
    with open('templates/map_with_legend.html', 'w', encoding='utf-8') as file:
        file.write(modified_html_content)
    