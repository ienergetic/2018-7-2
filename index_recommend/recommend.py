# -*- coding: utf-8 -*-

import jieba
import jieba.analyse
import sqlite3
import configparser
from datetime import *
import math
import pymysql

import pandas as pd
import numpy as np

from sklearn.metrics import pairwise_distances


class RecommendationModule:
    stop_words = set()
    k_nearest = []

    config_path = ''
    config_encoding = ''

    stop_words_path = ''
    stop_words_encoding = ''
    idf_path = ''
    db_path = ''

    def __init__(self, config_path, config_encoding):
        self.config_path = config_path
        self.config_encoding = config_encoding
        config = configparser.ConfigParser()
        config.read(config_path, config_encoding)

        self.doc_encoding = config['DEFAULT']['doc_encoding']
        self.stop_words_path = config['DEFAULT']['stop_words_path']
        self.stop_words_encoding = config['DEFAULT']['stop_words_encoding']
        self.idf_path = config['DEFAULT']['idf_path']
        self.db_path = config['DEFAULT']['db_path']

        f = open(self.stop_words_path, encoding=self.stop_words_encoding)
        words = f.read()
        self.stop_words = set(words.split('\n'))

    def write_k_nearest_matrix_to_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute('''DROP TABLE IF EXISTS knearest''')
        c.execute('''CREATE TABLE knearest
                     (id INTEGER PRIMARY KEY, first INTEGER, second INTEGER,
                     third INTEGER, fourth INTEGER, fifth INTEGER)''')

        for docid, doclist in self.k_nearest:
            c.execute("INSERT INTO knearest VALUES (?, ?, ?, ?, ?, ?)", tuple([docid] + doclist))

        conn.commit()
        conn.close()

    def is_number(self, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    def construct_dt_matrix(self, files, topK=200):
        jieba.analyse.set_stop_words(self.stop_words_path)
        jieba.analyse.set_idf_path(self.idf_path)
        con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count',
                               charset='utf8')
        cur = con.cursor()
        sql1 = 'select title,body,id from news_table'
        cur.execute(sql1)
        data = cur.fetchall()
        sql2 = 'select count(*) from news_table'
        cur.execute(sql2)
        M = int(cur.fetchone()[0])
        cur.close()
        con.close()
        N = 1
        terms = {}
        dt = []

        for i in data:
            title = str(i[0])
            body = str(i[1])
            docid = int(i[2])
            # 返回关键词和权重
            tags = jieba.analyse.extract_tags(title + '。' + body, topK=topK, withWeight=True)
            # tags = jieba.analyse.extract_tags(title, topK=topK, withWeight=True)
            cleaned_dict = {}
            for word, tfidf in tags:
                word = word.strip().lower()
                if word == '' or self.is_number(word):
                    continue
                cleaned_dict[word] = tfidf
                if word not in terms:
                    terms[word] = N
                    N += 1
            dt.append([docid, cleaned_dict])
        dt_matrix = [[0 for i in range(N)] for j in range(M)]
        i = 0
        for docid, t_tfidf in dt:
            dt_matrix[i][0] = docid
            for term, tfidf in t_tfidf.items():
                dt_matrix[i][terms[term]] = tfidf
            i += 1

        dt_matrix = pd.DataFrame(dt_matrix)
        dt_matrix.index = dt_matrix[0]
        print('dt_matrix shape:(%d %d)' % (dt_matrix.shape))
        return dt_matrix

    def construct_k_nearest_matrix(self, dt_matrix, k):
        # 寻找与某一条新闻最相近的5条新闻
        # 计算相似度
        tmp = np.array(1 - pairwise_distances(dt_matrix[dt_matrix.columns[1:]], metric="cosine"))
        similarity_matrix = pd.DataFrame(tmp, index=dt_matrix.index.tolist(), columns=dt_matrix.index.tolist())
        for i in similarity_matrix.index:
            tmp = [int(i), []]
            j = 0
            while j < k:
                # 找出值最大的行号
                max_col = similarity_matrix.loc[i].idxmax(axis=1)
                similarity_matrix.loc[i][max_col] = -1
                if max_col != i:
                    tmp[1].append(int(max_col))  # max column name
                    j += 1
            self.k_nearest.append(tmp)
        # print(self.k_nearest)
        # print(len(self.k_nearest))

    def gen_idf_file(self):
        con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count',
                               charset='utf8')
        cur = con.cursor()
        sql1 = 'select title,body from news_table'
        cur.execute(sql1)
        data = cur.fetchall()
        sql2 = 'select count(*) from news_table'
        cur.execute(sql2)
        n = float(cur.fetchone()[0])
        cur.close()
        con.close()

        idf = {}
        for i in data:
            title = str(i[0])
            body = str(i[1])
            seg_list = jieba.lcut(title + '。' + body, cut_all=False)
            seg_list = set(seg_list) - self.stop_words
            for word in seg_list:
                word = word.strip().lower()
                if word == '' or self.is_number(word):
                    continue
                if word not in idf:
                    idf[word] = 1
                else:
                    idf[word] = idf[word] + 1
        idf_file = open(self.idf_path, 'w', encoding='utf-8')
        for word, df in idf.items():
            idf_file.write('%s %.9f\n' % (word, math.log(n / df)))
        idf_file.close()

    def find_k_nearest(self, k, topK):
        self.gen_idf_file()
        con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count',
                               charset='utf8')
        cur = con.cursor()
        sql = 'select count(*) from news_table'
        cur.execute(sql)
        count_news = int(cur.fetchone()[0])
        cur.close()
        con.close()
        dt_matrix = self.construct_dt_matrix(count_news, topK)
        self.construct_k_nearest_matrix(dt_matrix, k)
        self.write_k_nearest_matrix_to_db()


if __name__ == "__main__":
    print('-----start time: %s-----' % (datetime.today()))
    rm = RecommendationModule('../config.ini', 'utf-8')
    rm.find_k_nearest(5, 25)
    print('-----finish time: %s-----' % (datetime.today()))
