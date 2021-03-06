import json
import codecs
import datetime
import pandas as pd
from LTPFunc import LTPFunction
import utils
from tqdm import tqdm
import pickle
import os
import random
'''
# 将json数据转换为csv格式, 并根据文章内容进行去重
dataList = []   # 数据列表
text_list = []  # 用于存储比较文章内容
sim_score = 50  # 设置相似度的阈值
with codecs.open("data/南海航行自由.txt",'r','utf-8') as f:
    for line in f.readlines():
        sim_flag = False    # 判断相似
        result = json.loads(line) # dict格式
        try:
            time = result['time'].replace(' CST','')
            result['time'] = str(datetime.datetime.strptime(time,'%a %b %d %H:%M:%S %Y')) # 将time格式化, 详细信息查阅 http://blog.chinaunix.net/uid-27659438-id-3350887.html
            result['text'] = result['text'].replace('\n','')
            for t in text_list:
                score = fuzz.ratio(result['text'], t)
                if score > sim_score:   # 计算文本相似度
                    sim_flag = True
                    print(score, ":", result['text'], "   ", t)
                    break
            if sim_flag:
                continue
            else:
                text_list.append(result['text'])
                dataList.append(result)
        except:
            print(result)

data_df = pd.DataFrame(dataList)
data_df['time'] = pd.to_datetime(data_df['time'])
data_df.sort_values('time', inplace=True)
data_df.to_csv("data/南海自由航行_去重.csv", index=False)
'''


'''
# 根据内容间的编辑距离去重
title_list = []
with codecs.open("data/南海航行自由.txt",'r','utf-8') as f:
    for line in f.readlines():
        sim_flag = False
        result = json.loads(line) # dict格式
        for t in title_list:
            score = fuzz.ratio(result['text'], t)
            if score > 50:   # 计算文本相似度
                sim_flag = True
                print(score, ":", result['text'], "   ", t)
                break
        if sim_flag:
            continue
        else:
            title_list.append(result['text'])

print(len(title_list))
'''

'''
# 根据关键词检索数据
df = pd.read_csv("data/南海_2018-01-01_2020-02-10.csv")
df = df.dropna(subset=["content", "title"]) # 删除content, title中值为Nan的行
result = df[df['original_text'].str.contains('海军|南海|航行')] # https://blog.csdn.net/htbeker/article/details/79645651
result.to_csv("result/南海航行观点筛选.csv", index=False)
# print(df['news_id'])
'''

'''
# 根据news_id检索数据库中的观点
theme_name = "南海自由航行"
news_df = pd.read_csv("data/" + theme_name + "_news.csv")
news_id = list(news_df.news_id) # 将数据中的news_id提取出来送入观点库中提取
vps_list = find_viewpoints_by_news_id(news_id, size=3000)   # 从观点库中根据news_id查找对应的观点
vps_df = pd.DataFrame(vps_list)
vps_df.to_csv("data/" + theme_name + "_views.csv", index=False) # 将观点数据存入文件中
'''

'''
# 根据新闻评论计算新闻影响力指数
theme_name = "南海自由航行"
news_df = pd.read_csv("data/" + theme_name + "_news.csv")
result = utils.news_comment_deal(news_df)
with codecs.open("result/news_influence.json", "w", "utf-8") as wf:
    json.dump(result, wf, indent=4)
'''

'''
# 根据bd56部署的知识图谱查询 专家人名信息/机构信息, 对观点数据进行补全
import requests
# result = requests.get("http://10.1.1.56:9000/eav?entity=李华敏&attribute=国籍")

# 根据ownthink知识图谱查找人名所对应的国籍
def findCountry(entity):
    result = requests.get("http://10.1.1.56:9000/eav?entity=" + entity + "&attribute=国籍")
    r = json.loads(result.text)
    if r != []:
        return r[0]
    else:
        result = requests.get("https://api.ownthink.com/kg/knowledge?entity=" + entity)
        result = json.loads(result.text)
        if 'avp' not in result['data']: return 'N'
        country = [i[1] if i[0] == "国籍" else "" for i in result["data"]["avp"]]
        r = []
        for i in country:
            if i != "":
                r.append(i)
        if r != []:
            return r[0]
        else:
            return "N"


views_df = pd.read_csv("data/南海自由航行_views.csv")

with codecs.open("dict/zhcountry_convert.json",'r','utf-8') as jf:
    zhcountry_convert_dict = json.load(jf)

# 加载echarts世界地图国家中文名
pkl_rf = open('dict/echarts_zhcountry_set.pkl','rb')
zhcountry_set = pickle.load(pkl_rf)

#加载之前存储的{专家：国家}字典
pkl_rf = open('dict/per_country.pkl','rb')
per_country_dict = pickle.load(pkl_rf)

org2per_count = 0
view_country_list = []
for i in range(0, len(views_df)):
    row = views_df.iloc[i]
    per = row['person_name']
    org = str(row['org_name']) + str(row['pos'])
    # print(org)
    per_country = "N"
    
    # 如果该专家之前已经处理过
    if per in per_country_dict:
        if per_country_dict[per] is not "N":    # 该专家的国家名称不为N 
            # views_df.iloc[i]['country'] = per_country_dict[per] # 获取专家所在的国家
            view_country_list.append(per_country_dict[per])
            continue # 该专家已经存在库中则进行跳过

    # 先判断org中是否包含set中的国家
    for con in zhcountry_set:
        if con in org:
            per_country = con
            break
    
    # 如果在org中找到了符合要求的则进行存储并continue
    if per_country is not "N":
         if isinstance(per, str):
             org2per_count += 1 
             per_country_dict[per] = per_country # 根据org字段补全专家国籍
         # row['country'] = per_country
         view_country_list.append(per_country)
         continue

    # 根据per来查找知识图谱中的信息
    if isinstance(per, str): # 如果per字段不为空
        country = findCountry(per)
        # 在进行国家对比的时候先进行转换
        if country in zhcountry_convert_dict:
            country = zhcountry_convert_dict[country]
        # 如果该国家在echarts中的中文国家字典中
        if country in zhcountry_set:
            per_country = country
        per_country_dict[per] = per_country

    # row['country'] = per_country
    view_country_list.append(per_country)

print("补全专家人数:" + str(org2per_count))
views_df['country'] = view_country_list # 新增一列国家


# 保存{人名:国家}字典
pklf = open("dict/per_country.pkl","wb") 
pickle.dump(per_country_dict, pklf) 


with codecs.open("result/per_country.txt","w","utf-8") as wf:
    for key, value in per_country_dict.items():
        wf.write(key + ": " + value + "\n")

views_df.to_csv("data/南海自由航行_new_views.csv", index=False) # 将增加国家数据的观点数据存入文件中
'''
'''
theme_name = "南海"
views_df = pd.read_csv("data/南海自由航行_views.csv")
# 统计该专题下的{国家-观点数量分布}

country_view_dict = {}
for country in views_df["country"]:
    if country is "N": continue
    if country in country_view_dict:
        country_view_dict[country] += 1
    else:
        country_view_dict[country] = 1

# 存储不同专题的国家-观点数量信息
pklf = open("dict/" + theme_name+ "_countryviews_dict.pkl","wb") 
pickle.dump(country_view_dict, pklf)

# 加载echarts世界地图国家中文名
pkl_rf = open('dict/echarts_zhcountry_set.pkl','rb')
zhcountry_set = pickle.load(pkl_rf)
zhcountry_set.add("科特迪瓦") # 增加科特迪瓦国家信息
pklf = open("dict/echarts_zhcountry_set.pkl","wb") 
pickle.dump(zhcountry_set, pklf)
'''

'''
from googletrans import Translator
translator = Translator(service_urls=[
      'translate.google.cn',]) # 如果可以上外网，还可添加 'translate.google.com' 等

with codecs.open("dict/WJWords.json",'r','utf-8') as rf:
    wj_words_dict = json.load(rf)

# 制作各个语言的危机字典
result_dict = {}
for key in wj_words_dict.keys():
    tmp_list = []
    for word in wj_words_dict[key]:
        trans = translator.translate(word, src='zh-cn', dest='ko')
        tmp_list.append(trans.text.lower())
    result_dict[key] = tmp_list

with codecs.open('dict/WJWords_ko.json','w','utf-8') as wf:
    json.dump(result_dict, wf, indent=4, ensure_ascii=False)
'''

#加载之前存储的{专家：国家}字典
pkl_rf = open('dict/per_country.pkl','rb')
per_country_dict = pickle.load(pkl_rf)

with codecs.open('dict/per_country.json','w','utf-8') as wf:
    json.dump(per_country_dict, wf, indent=4, ensure_ascii=False)



