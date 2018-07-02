# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
import pymysql

headers = {'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'}


def get_news_pool(root, start, end):
    news_pool = []
    for i in range(start, end, -1):
        page_url = ''
        if i != start:
            page_url = root + '_%d.shtml' % (i)
        else:
            page_url = root + '.shtml'
        try:
            response = requests.get(page_url, headers=headers)
            response.encoding = 'utf-8'
        except Exception as e:
            print("-----%s: %s-----" % (type(e), page_url))
            continue
        html = response.text
        soup = BeautifulSoup(html, "lxml")  # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        ul = soup.find('ul', class_="list")
        a = ul.find_all('a')
        span = ul.find_all('span')
        print(i)
        for i in range(len(a)):
            date_time = span[i].string
            url1 = a[i].get('href')
            url = urljoin(root, url1)
            title = a[i].string
            news_info = [date_time, url, title]
            news_pool.append(news_info)
    return (news_pool)


def crawl_news(news_pool, min_body_len, news_tag):
    conn = pymysql.connect( user='root', password='lilong', db='news_count', charset='utf8')
    cur = conn.cursor()
    i=0
    for news in news_pool:
        try:
            response = requests.get(news[1], headers=headers)
            response.encoding = 'utf-8'
        except Exception as e:
            print("-----%s: %s-----" % (type(e), news[1]))
            continue
        html = response.text
        soup = BeautifulSoup(html, "lxml")  # http://www.crummy.com/software/BeautifulSoup/bs4/doc.zh/
        try:
            body = soup.find('div', class_="art_txt").get_text()
        except Exception as e:
            print("-----%s: %s-----" % (type(e), news[1]))
            continue
        body = body.replace(" ", "")
        body = body.strip()
        if len(body) <= min_body_len:
            continue
        sql = "insert into news_table VALUES('%d','%s','%s', '%s', '%s', '%s')" % (i,news[0], news[1], news[2],body, news_tag)
        print(news[0], news[1], news[2], news_tag)
        cur.execute(sql)
        conn.commit()
    cur.close()
    conn.close()

if __name__ == '__main__':
    root = 'http://news.sxrb.com/sxxww/xwpd/sx/index'
    news_tag = '山西'
    news_pool = get_news_pool(root, 15, 1)
    crawl_news(news_pool, 100, news_tag)
    print('done!')