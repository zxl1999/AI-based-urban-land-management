from flask import Flask, render_template, request, redirect, url_for, Response
import os
import geopandas as gpd
import folium
import time
import shutil
import signal


from funs.InitMap import init_map
from funs.drawEditMap import draw_editmap
from funs.useDeduct import useDeduction

app = Flask(__name__)

app.config['TEMPLATES_AUTO_RELOAD'] = True

UPLOAD_FOLDER = 'uploads'
SAVE_FOLDER = 'save'

app.config['SAVE_FOLDER'] = SAVE_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'cpg', 'dbf', 'prj', 'shx', 'shp'}

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
    '商业服务用地': 'red'
    # 添加其他分类及颜色的映射关系
}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/initMapView')
def initMapView():
    return render_template('map_with_legend.html')

@app.route('/drawMapView')
def drawMapView():
    return render_template('map_with_draw.html')

@app.route('/useDeduction')
def use_Deduction_Port():
    return render_template('useDeduction.html', color_map=color_map)

@app.route('/upload', methods=['POST'])
def upload_file():
    #cleanup()
    remove_files_except_index_html("templates")
    if 'file' not in request.files:
        return 'No file part'
    
    files = request.files.getlist('file')
    

    for file in files:
        if file and allowed_file(file.filename):
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            
    
        else:
            return 'Invalid file'
    
    #return 'File uploaded successfully'
    task = request.form['task']
    return redirect(url_for('process', message=task))

@app.route('/process')
def process():
    task = request.args.get('message')
    
    # 获取目录中的文件列表
    files = os.listdir(app.config['UPLOAD_FOLDER'])
        
    for i in files:
        if i.endswith('.shp'):
            file=i
            break
    
    if task=='land_management':
        init_map(file)
        return redirect(url_for('initMapView'))
    
    if task=='land_edit':
        draw_editmap(file)
        
        return redirect(url_for('drawMapView'))
    
    if task=='land_inference':
        useDeduction(file)
        
        return redirect(url_for('use_Deduction_Port'))
    
    return "Invalid file format. Please upload .cpg, .dbf, .prj, .shp, and .shx file."

#城市效应评估
@app.route('/pullEn', methods=['POST'])
def pullEn():
    data = request.json
    
    type_area=data['inputText']
    points=data['points']
    areas=data['areas']
    
    
    # 读取 Shapefile 文件
    folder_path = "uploads"
    shp_filenames = get_shp_filenames(folder_path)[0]
    
    
    gdf = gpd.read_file('uploads/'+shp_filenames)
    
    print(data)
    
    return 'ok'

#查看模式选择用地类型并修改
@app.route('/update_land_type', methods=['POST'])
def update_land_type():
    data = request.json
    print(data)
    
    landType=data['landType']
    index=data['index']
    
    # 读取 Shapefile 文件
    folder_path = "uploads"
    shp_filenames = get_shp_filenames(folder_path)[0]
    
    gdf = gpd.read_file('uploads/'+shp_filenames)
    
    gdf.loc[int(index), 'Level2_cn'] = landType
    
    # 指定保存文件的路径和文件格式（这里以 ESRI Shapefile 格式为例）
    output_file = "uploads/"+shp_filenames

    # 将 GeoDataFrame 保存到文件中
    gdf.to_file(output_file, encoding="utf-8")

    gdf.to_file('save/'+shp_filenames, encoding="utf-8")

    print("GeoDataFrame saved to:", output_file)
    
    init_map(shp_filenames)
    
    return redirect(url_for('initMapView'))
    #return "ok"
    
    

@app.route('/submit', methods=['POST'])
def submit():
    data = request.json
    #print(data)
    
    type_area=data['inputText']
    points=data['points']
    areas=data['areas']
    
    print(type_area,points,areas)
    
    import geopandas as gpd
    import folium
    from shapely.wkt import loads

    # 将给定的经纬度坐标点列表转换为 ArcGIS 中的 POLYGON 格式字符串
    polygon_string = "POLYGON (("

    # 构建多边形字符串
    for point in points:
        polygon_string += f"{point[1]} {point[0]}, "

    # 添加第一个坐标点以闭合多边形
    first_point = points[0]
    polygon_string += f"{first_point[1]} {first_point[0]}))"

    # 打印转换后的多边形字符串
    #print("ArcGIS Polygon string:", polygon_string)

    # 使用 Shapely 创建多边形几何对象
    polygon_geom = loads(polygon_string)

    # 读取 Shapefile 文件
    folder_path = "uploads"
    shp_filenames = get_shp_filenames(folder_path)[0]
    
    gdf = gpd.read_file('uploads/'+shp_filenames)
    
    Level1=type_area
    Level2=type_area
    
    # 计算经纬度的平均值
    mean_lat = sum(point[0] for point in points) / len(points)
    mean_lon = sum(point[1] for point in points) / len(points)

    # 添加新行数据
    new_row = {
        'Lon': mean_lon,
        'Lat': mean_lat,
        'F_AREA': areas,
        'City_CODE': 0,
        'UUID': 0,
        'Level1': Level1,
        'Level2': Level2,
        'Level1_cn': Level1,
        'Level2_cn': Level1,
        'geometry': polygon_geom  # 如果不包含几何信息，可以设置为 None
    }
    
    # 将新行数据添加到 gdf 中
    gdf = gdf.append(new_row, ignore_index=True)

    # 将 DataFrame 转换为 GeoDataFrame
    gdf = gpd.GeoDataFrame(gdf, geometry='geometry')

    # 指定保存文件的路径和文件格式（这里以 ESRI Shapefile 格式为例）
    output_file = "uploads/"+shp_filenames

    # 将 GeoDataFrame 保存到文件中
    gdf.to_file(output_file, encoding="utf-8")

    gdf.to_file('save/'+shp_filenames, encoding="utf-8")

    print("GeoDataFrame saved to:", output_file)
    
    return "ok"


def cleanup():
    uploads_folder = app.config['UPLOAD_FOLDER']
    save_folder = app.config['SAVE_FOLDER']
    
    # 备份 uploads 文件夹内容至 save 文件夹
    for filename in os.listdir(uploads_folder):
        file_path = os.path.join(uploads_folder, filename)
        if os.path.isfile(file_path):
            shutil.copy2(file_path, os.path.join(save_folder, filename))
    
    # 删除 uploads 文件夹内容并重新创建空的 uploads 文件夹
    shutil.rmtree(uploads_folder)
    os.mkdir(uploads_folder)
    
    
    
# 在按下 Ctrl+C 时执行清理和备份操作
def signal_handler(sig, frame):
    cleanup()
    print('Uploads folder cleaned up and saved.')
    exit(0)

def get_shp_filenames(folder_path):
    shp_filenames = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".shp"):
            shp_filenames.append(filename)
    return shp_filenames

def remove_files_except_index_html(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if filename != "index.html":
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                remove_files_except_index_html(file_path)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    app.run()
