#!/usr/bin/env python 
# -*- coding:utf-8 -*-
import requests
import re
import bs4
from bs4 import BeautifulSoup
import lxml
import pymysql
import configparser


#获取满足条件（武汉+金融/投资/证券+保险+银行）的总页面
def get_total_page():
    url='https://search.51job.com/list/180200,000000,0000,03%252C43%252C42,9,99,%2520,2,1.html?lang=c&stype=&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&providesalary=99&lonlat=0%2C0&radius=-1&ord_field=0&confirmdate=9&fromType=&dibiaoid=0&address=&line=&specialarea=00&from=&welfare='
    res=requests.get(url)
    res.encoding=res.apparent_encoding
    html=res.text
    total_page=re.findall(r'共(\d+)页',html)[0].strip()
    return total_page


#循环的获取每条工作的网页链接
def get_href_list():
    total_page = int(get_total_page())
    href_list=[]
    for p in range(1,total_page+1):
        try:
            url='https://search.51job.com/list/180200,000000,0000,03%252C43%252C42,9,99,%2520,2,{p}.html?lang=c&stype=&postchannel=0000&workyear=99&cotype=99&degreefrom=99&jobterm=99&companysize=99&providesalary=99&lonlat=0%2C0&radius=-1&ord_field=0&confirmdate=9&fromType=&dibiaoid=0&address=&line=&specialarea=00&from=&welfare=' \
                    .format(p=str(p))
            res=requests.get(url=url,timeout=20)
            res.encoding=res.apparent_encoding
            soup=BeautifulSoup(res.text,'lxml')
            resultList=soup.find('div',id='resultList').find_all('div',class_='el')[1:]
            # print(resultList)
            for result in resultList:
                href=result.find('a')['href'].strip()
                print(href)
                href_list.append(href)
        except Exception as e:
            print(e)
    return href_list



#根据网页链接获取所有的工作信息
def get_data():
    href_list=get_href_list()
    for href in href_list:
        try:
            res=requests.get(url=href,timeout=20)
            res.encoding=res.apparent_encoding
            html=res.text
            # print(html)
            soup=BeautifulSoup(html,'lxml')
            result=soup.find('div',class_='cn')
            job_name=result.find('h1').text.strip()     #职位名称
            company_name=result.find('p',class_='cname').find('a')['title'].strip()  #公司名称
            try:
                salary=result.find('strong').text.strip()    #薪资
            except:
                salary=''
            tag=result.find('p',class_='msg ltype').text
            address=tag.split(r'|')[0].strip()  #地点
            if '经验' in tag.split(r'|')[1].strip():
                experience=tag.split(r'|')[1].strip()  #经验
                level = tag.split(r'|')[2].strip()  # 学历
            elif '招' or '发布' in tag.split(r'|')[1].strip():
                experience = ''
                level = ''
            else:
                experience = ''
                level = tag.split(r'|')[1].strip()

            print(job_name,company_name,salary,address,experience,level)
            sql="insert into job_data values('%s','%s','%s','%s','%s','%s')" \
                        %(job_name,company_name,salary,address,experience,level)
            try:
                cursor.execute(sql)
                db.commit()
            except Exception as e:
                print(e)
                db.rollback()
        except:
            pass
    cursor.close()
    db.close()

#连接MySQL数据库并新建表job_data
def login_mysql():
    #获取配MySQL的用户置文件并连接
    config=configparser.ConfigParser()
    config.read('config.ini')
    host=config.get('MYSQL','host')
    port=config.get('MYSQL','port')
    user = config.get('MYSQL', 'user')
    password = config.get('MYSQL', 'password')
    database = config.get('MYSQL', 'database')
    db = pymysql.connect(host=host,port=int(port),user=user,password=password,database=database)
    cursor=db.cursor()
    #新建表job_data
    sql1='drop table if exists job_data'
    sql2='''create table job_data(job_name varchar(50),company_name varchar(50),salary varchar(30),
                              address varchar(50),experience varchar(30),level varchar(20))'''
    try:
        cursor.execute(sql1)
        cursor.execute(sql2)
        db.commit()
    except Exception as e:
        print(e)
        db.rollback()
    return db,cursor


if __name__=='__main__':
    db,cursor=login_mysql()
    get_data()
