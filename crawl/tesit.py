import pymysql

conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data', charset='utf8')
cur = conn.cursor()
sql = "select news_id from %s" %(current_user)
cur.execute(sql)
data = cur.fetchall()
cur.close()
conn.close()
data2 = len(data[208][1])
print(data2)
import pymysql
import time
from flask import Flask
from flask import render_template
app = Flask(__name__)


def find():
    docs = []
    conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count', charset='utf8')
    cur = conn.cursor()
    sql = 'select date_time, url, title, body, tag from news_table where tag="山西"'
    cur.execute(sql)
    data = cur.fetchall()
    sql2 = 'select count(*) from news_table where tag="山西"'
    cur.execute(sql2)
    count_news = int(cur.fetchone()[0])
    cur.close()
    conn.close()
    for i in range(0,count_news):
        url = data[i][1]
        title = data[i][2]
        body = data[i][3]
        snippet = data[i][3][0:120] + '……'
        time = data[i][0].split(' ')[0]
        datetime = data[i][0]
        tag_news = data[i][4]
        doc = {'url': url, 'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time, 'body': body,
               'id': i, 'tag': tag_news, 'extra': []}
        docs.append(doc)
        #print(doc['tag'])
    return docs

@app.route('/')
def search():
    docs = find()
    print(time.clock())
    return render_template('hello.html', docs=docs)


@app.route('/<int:id>/', methods=['GET', 'POST'])
def content(id):
    try:
        doc = find()
        return render_template('coniet.html', doc=doc[id-1])
    except:
        print('content error')


if __name__ == '__main__':
    app.run(port=5001)