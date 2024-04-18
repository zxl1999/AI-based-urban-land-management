# 读取整个HTML文件内容并存储在列表中
with open('map_with_legend.html', 'r', encoding='utf-8') as file:
    lines = file.readlines()

# 要插入的JavaScript函数
js_function = """
function onGeoJsonClick(event) {
    var lat = event.latlng.lat;
    var lon = event.latlng.lng;
    console.log(lat, lon);
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
with open('map_with_legend.html', 'w', encoding='utf-8') as file:
    for line in lines:
        file.write(line)

print("JavaScript 函数已成功添加到 HTML 文件中。")


# 打开HTML文件进行读取
with open('map_with_legend.html', 'r', encoding='utf-8') as file:
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
print("匹配到的元素:")
for element in matched_elements:
    print(element)

result=[]
for i in matched_elements:
    # 使用正则表达式进行匹配
    match = re.match(r'var\s+(geo_json_\w+)\s+=\s+L\.geoJson', i)

    if match:
        field_name = match.group(1)
        result.append(field_name)
        
# 读取整个HTML文件内容并存储在列表中
with open('map_with_legend.html', 'r', encoding='utf-8') as file:
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
with open('map_with_legend.html', 'w', encoding='utf-8') as file:
    for line in lines:
        file.write(line)

print("JavaScript 函数已成功添加到 HTML 文件中。")