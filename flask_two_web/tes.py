import sqlite3
import pymysql
import re
sq3_conn = sqlite3.connect('database.db')
sq3_c = sq3_conn.cursor()
sq3_sql = "select username from users"
sq3_c.execute(sq3_sql)
sq3_datas = sq3_c.fetchall()
sq3_c.close()
sq3_conn.close()
print(sq3_datas)
my_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data',
                          charset='utf8')
my_cur = my_conn.cursor()
sq4 = " select TABLE_NAME from information_schema.tables where TABLE_SCHEMA='behavior_data' "
my_cur.execute(sq4)
data = my_cur.fetchall()
print(data)
data_lie = []
for i in range(0, len(data)):
    data_lie.append(re.match(re.compile("(.*)?(id|index|key)$"), data[i][0]).group(1))
print(list(set(data_lie)))
for sq3_data in sq3_datas:
        if sq3_data[0] not in data_lie:
            my_sql = "create table %s (id INT UNSIGNED AUTO_INCREMENT, key_word VARCHAR(15) NOT NULL, key_count INT UNSIGNED NOT NULL, PRIMARY KEY(id))" % (
                sq3_data[0] + 'key',)
            my_cur.execute(my_sql)
            my_sql2 = "create table %s (id INT UNSIGNED AUTO_INCREMENT, user_id INT UNSIGNED NOT NULL, id_count INT UNSIGNED NOT NULL, PRIMARY KEY(id))" % (sq3_data[0] + 'id',)
            my_cur.execute(my_sql2)
            my_sql3 = "create table %s (id INT UNSIGNED AUTO_INCREMENT, news_id INT UNSIGNED NOT NULL, PRIMARY KEY(id))" % (
                sq3_data[0] + 'index',)
            my_cur.execute(my_sql3)
my_cur.close()
my_conn.close()