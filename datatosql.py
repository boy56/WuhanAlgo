# -*- coding: UTF-8 -*-
# 将数据依赖models中的样式导入mysql中

import pandas as pd
from utils import clean_zh_text
from datetime import datetime
from sqlalchemy import create_engine
from models import NewsInfo, mysql_db
import math
from ClassifyFunc import ClassifyFunc

# 新闻csv导入mysql, 默认文件类型为从Hbase导出的数据
def newscsvtosql(path, theme, datatype=1):
    # 从csv文件读入数据
    df = pd.read_csv(path)
    df['time'] = pd.to_datetime(df['time'])
    df = df.fillna('')  # 填充NA数据
    classifyFunc = ClassifyFunc()

    # 遍历读取处理
    news_data = []
    for index, row in df.iterrows():
        tmp = {}
        tmp['newsid'] = row['news_id']
        tmp['title'] = row['title']
        tmp['time'] = datetime.strftime(row['time'],'%Y-%m-%d %H:%M:%S')    # 格式化时间字符串
        tmp['content'] = clean_zh_text(row['content'])  # 清洗正文内容
        tmp['url'] = row['url']
        tmp['customer'] = row['customer']
        tmp['emotion'] = row['emotion']
        tmp['entities'] = row['entities']
        tmp['keyword'] = row['keyword']
        tmp['location'] = row['location']
        tmp['pageview'] = row['pageview']
        tmp['userview'] = row['userview']
        tmp['words'] = row['words']

        # 需要计算得到的字段
        tmp['theme_label'] = theme
        tmp['content_label'] = row['content_label']
        tmp['country_label'] = row['country_label']

        # 运行分类算法得到相应标签
        # tmp['content_label'] = classifyFunc.classify_title(title_words, 2)
        # tmp['country_label'] = classifyFunc.classify_title(title_words, 2)

        news_data.append(tmp)

    # write data to mysql
    mysql_db.connect()
    
    # 插入新闻数据
    if not NewsInfo.table_exists(): # 如果表不存在则创建
        NewsInfo.create_table()
    else: # bug调好后注释掉, 改为增量
        NewsInfo.delete().execute() # 每次重新更新之前清空数据表
    
    # 根据切片分批次插入
    slice_size = 300    # 切片大小
    nslices = math.floor(len(news_data) / slice_size)
    for i in range(0, nslices-1):
        with mysql_db.atomic():
            NewsInfo.insert_many(news_data[i * slice_size: (i + 1) * slice_size]).execute() # 批量插入

    # 插入最后一个切片的数据
    with mysql_db.atomic():
        NewsInfo.insert_many(news_data[nslices*slice_size:]).execute() # 批量插入

    mysql_db.close()

# 观点csv导入mysql, 默认文件类型为经过vps查询得到的观点数据列表
def viewscsvtosql(path, datatype=1):
    return 

# 数据库建库建表
if __name__ == "__main__":
    
    newscsvtosql("data/南海自由航行_news_newlabel.csv",'南海')

   
