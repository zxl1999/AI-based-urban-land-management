import os
from pypinyin import pinyin, Style
import time

shp_file_path = 'data/'

# 获取文件夹中所有文件的文件名
file_names = os.listdir(shp_file_path)

# 去除后缀并使用集合来去重
unique_file_names = {name.rsplit('.', 1)[0] for name in file_names}
# 打印去重后的文件名列表
print(unique_file_names)

new_list=[]

for i in unique_file_names:
    if len(i)==3:
        new_list.append(i[:-1])
        
# 将中文转换为拼音
pinyin_list = []
for word in new_list:
    string=''
    pinyin_word = pinyin(word, style=Style.NORMAL)
    for i in pinyin_word:
        string+=i[0]
        
    pinyin_list.append(string)

# 打印转换后的拼音列表
pinyin_list.sort()
print(pinyin_list)

import pandas as pd
import matplotlib
import requests
import time
from bs4 import BeautifulSoup

# 爬虫
url1 = 'http://www.tianqihoubao.com/aqi/beijing-202209.html'
url2 = 'http://www.tianqihoubao.com/aqi/beijing-202210.html'


def get_url_info(url):
    """
    获取单个url（某城市某个月的天气信息url）的信息
    return : DataFrame 为表格信息
    """

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Cookie': "__51cke__=; ASP.NET_SessionId=fkkucvjbb02l3y2owpcvnl55; __tins__21287555=%7B%22sid%22%3A%201671355464098%2C%20%22vd%22%3A%2012%2C%20%22expires%22%3A%201671358170641%7D; __51laig__=12",
        'Host': 'www.tianqihoubao.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'

    }

    response = requests.get(url=url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    table_tag = soup.find('table')
    lines_lst = table_tag.find_all('tr')

    res_lst = []
    for line in lines_lst:
        temp_lst = []
        for col in line.find_all('td'):
            temp_lst.append(col.text.strip())
        res_lst.append(temp_lst)
    df = pd.DataFrame(res_lst)

    return df

# 保留指定列
selected_columns = ['PM2.5', 'PM10', 'So2', 'No2', 'Co', 'O3']

for i in pinyin_list[19:]:
    try:
        new_df=pd.DataFrame()
        for j in range(1,13):
            if j<10:
                url='http://www.tianqihoubao.com/aqi/'+i+'-20180'+str(j)+'.html'
            else:
                url='http://www.tianqihoubao.com/aqi/'+i+'-2018'+str(j)+'.html'
            print(url)
            tables = pd.read_html(url,encoding = 'utf-8')
            tables=tables[0]
            tables=tables.rename(columns=tables.iloc[0]).drop(0).reset_index(drop=True)
            tables=tables[selected_columns]
            new_df = pd.concat([new_df,tables],axis=0)
            #new_df = new_df.rename(columns=new_df.iloc[0]).drop(0).reset_index(drop=True)
            time.sleep(5)
            print(j)
        new_df.to_csv('weather/'+i+'.csv',index=False)
        print(i,end="\t")
        print(pinyin_list.index(i))
    except:
        continue
    
