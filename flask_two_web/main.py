#!congding = utf-8

from flask import Flask, render_template, request

from flask_two_web.search_rank import Search_rank

from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_required, login_user, current_user, logout_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import InputRequired, Length, Email
from werkzeug.security import generate_password_hash, check_password_hash

import sqlite3
import configparser
import time
import pymysql
import re

import jieba


db_path = ''
global page
global keys
dbdir = "sqlite:///" + "/home/zhang/Downloads/final_biyesheji/flask_two_web/database.db"
print(dbdir)
app = Flask(__name__)
app.config["SECRET_KEY"] = "SomeSecret"
app.config["SQLALCHEMY_DATABASE_URI"] = dbdir
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
class Users(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)

def init():
    config = configparser.ConfigParser()
    config.read('../config.ini', 'utf-8')
    global  db_path
    db_path = config['DEFAULT']['db_path']

@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

class RegisterForm(FlaskForm):
    username = StringField("用户名", validators=[InputRequired(), Length(min=5, max=50)])
    email = StringField("邮箱", validators=[InputRequired(), Length(min=5, max=50), Email()])
    password = PasswordField("密码", validators=[InputRequired(), Length(min=6, max=80)])
    submit = SubmitField("注册")

class LoginForm(FlaskForm):
    username = StringField("用户名",)
    password = PasswordField("密码",)
    remember = BooleanField("记住我")
    submit = SubmitField("登录")


@app.route('/')
def main():
    init()
    if hasattr(current_user, "username"):
        return redirect(url_for("denglu"))
    else:
        docs = behavi_find()
        print(time.clock())
        return render_template('search.html', error=False, hast=hasattr(current_user, "username"), reco_docs=docs)

@app.route('/denglu/')
@login_required
def denglu():
    return redirect(url_for("sim_mend"))


@app.route("/denglu/signup", methods=["GET", "POST"])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        sq3_li_conn = sqlite3.connect('database.db')
        sq3_li_c = sq3_li_conn.cursor()
        sq3_li_sql = "select username, email from users"
        sq3_li_c.execute(sq3_li_sql)
        sq3_li_datas = sq3_li_c.fetchall()
        sq3_li_c.close()
        sq3_li_conn.close()
        for sq3_li_data in sq3_li_datas:
            if sq3_li_data[0]==form.username.data:
                flash("账号已存在，请重新注册")
                return redirect(url_for("signup"))
            elif sq3_li_data[1]==form.email.data:
                flash("邮箱已存在，请重新注册")
                return redirect(url_for("signup"))
        hashed_pw = generate_password_hash(form.password.data, method="sha256")
        new_user = Users(username=form.username.data, email=form.email.data, password=hashed_pw)
        print('==================================', form.username.data)
        db.session.add(new_user)
        db.session.commit()
        create_recom_table()
        flash("你已经成功注册,现在可以登录")
        return redirect(url_for("login"))
    return render_template("signup.html", form=form)

@app.route("/denglu/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember)
            print(user.username, '=========>', type(user))
            return redirect(url_for("main"))
        flash("账号或密码有误,请重新输入")
        return render_template("login.html", form=form)
    return render_template("login.html", form=form)

@app.route("/denglu/logout")
@login_required
def logout():
    logout_user()
    #flash("You were logged out. See you soon!")
    return redirect(url_for('main'))
    #return render_template('search.html', error=True)



# 读取表单数据，获得doc_ID
@app.route('/search/', methods=['POST'])
def search():

    try:
        global keys
        global checked
        checked = ['checked="true"', '', '']
        keys = request.form['key_word']
        print('keys--------------', keys)
        if keys not in ['']:
            print(time.clock())
            flag,page = searchidlist(keys)
            if flag==0:
                return render_template('search.html', error=False, hast=hasattr(current_user, "username"))
            docs = cut_page(page, 0)
            print(time.clock())
            if hasattr(current_user, "username"):

                my_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data',charset='utf8')
                my_cur = my_conn.cursor()
                my_sql2 = "select key_count from %s where key_word='%s'  "%(current_user.username+'key', keys)
                my_cur.execute(my_sql2)
                my_data = my_cur.fetchall()
                if len(my_data) == 0:
                    my_sql = "insert into  %s values('%d', '%s', '%d')" % (current_user.username+'key', 0, keys, 1)
                    my_cur.execute(my_sql)
                else:
                    my_sql3 = "update %s set key_count='%d' where key_word='%s'" %(current_user.username+'key', my_data[0][0]+1, keys)
                    my_cur.execute(my_sql3)
                my_conn.commit()
                my_cur.close()
                my_conn.close()
                print(current_user.username)
                return render_template('high_search.html', checked=checked, key=keys, docs=docs, page=page, error=True, hast=hasattr(current_user, "username"))
            else:

                return render_template('high_search.html', checked=checked, key=keys, docs=docs, page=page, error=True, hast=hasattr(current_user, "username"))
        else:
            return render_template('search.html', error=False, hast=hasattr(current_user, "username"))

    except:
        print('search error')


def searchidlist(key, selected=0):
    global page
    global doc_id
    se = Search_rank('../config.ini', 'utf-8')
    flag, id_scores = se.search(key, selected)

    # 返回docid列表
    doc_id = [i for i, s in id_scores]

    page = []
    for i in range(1, (len(doc_id) // 10 + 2)):
        page.append(i)
    return flag,page


def cut_page(page, no):
    docs = find(doc_id[no*10:page[no]*10])

    return docs


# 将需要的数据以字典形式打包传递给search函数
def find(docid, extra=False):
    global db_path
    docs = []
    con = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count', charset='utf8')
    cur = con.cursor()
    for idd in docid:
        sql = "select id, url, title, body, date_time from news_table where id='%d'"%(idd,)
        cur.execute(sql)
        data = cur.fetchone()
        url = data[1]
        title = data[2]
        body = data[3]
        snippet = data[3][0:120] + '……'
        time1 = data[4].split(' ')[0]
        datetime = data[4]
        doc = {'url': url, 'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time1, 'body': body,'id': idd, 'extra': []}
        if extra:
            temp_doc = get_k_nearest(db_path, idd)
            for i in temp_doc:
                sql21 = "select title from news_table where id='%d'" % (i,)
                cur.execute(sql21)
                data21 = cur.fetchone()
                title = data21[0]
                doc['extra'].append({'id': i, 'title': title})
        docs.append(doc)
    cur.close()
    con.close()
    return docs


@app.route('/search/page/<page_no>/', methods=['GET'])
def next_page(page_no):
    try:
        page_no = int(page_no)
        docs = cut_page(page, (page_no-1))
        return render_template('high_search.html', checked=checked, key=keys, docs=docs, page=page, error=True, hast=hasattr(current_user, "username"))
    except:
        print('next error')


@app.route('/search/<key>/', methods=['POST'])
def high_search(key):
    try:

        selected = int(request.form['order'])
        for i in range(0, 3):
            if i == selected:
                checked[i] = 'checked="true"'

            else:
                checked[i] = ''

        flag,page = searchidlist(key, selected)

        if flag==0:
            return render_template('search.html', error=False, hast=hasattr(current_user, "username"))

        docs = cut_page(page, 0)
        return render_template('high_search.html', checked=checked, key=keys, docs=docs, page=page, error=True, hast=hasattr(current_user, "username"))
    except:
        print('high search error')


@app.route('/search/<int:id>/', methods=['GET', 'POST'])
def content(id):
    try:
        doc = find([id], extra=True)
        print('=================', id)
        if hasattr(current_user, "username"):
            my_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data',charset='utf8')
            my_cur = my_conn.cursor()
            my_sql2 = "select id_count from %s where user_id='%d'" % (current_user.username + 'id', id)
            my_cur.execute(my_sql2)
            my_data = my_cur.fetchall()
            if len(my_data) == 0:
                my_sql = "insert into  %s values('%d', '%d', '%d')" % (current_user.username + 'id', 0, id, 1)
                my_cur.execute(my_sql)
            else:
                my_sql3 = "update %s set id_count='%d' where user_id='%d'" % (current_user.username + 'id', my_data[0][0] + 1, id)
                my_cur.execute(my_sql3)
            my_conn.commit()
            my_cur.close()
            my_conn.close()
            return render_template('content.html', doc=doc[0])
        else:
            return render_template('content.html', doc=doc[0])
    except:
        print('content error')



@app.route("/denglu/sim_recom/", methods=["GET", "POST"])
def sim_mend():
    docs = behavi_find()
    print(time.clock())
    return render_template('behavi_hell.html', docs=docs)

@app.route('/kind/<ne_kind>/', methods=['GET', 'POST'])
def reco_kind(ne_kind):
    docs = kind_find(ne_kind)
    return render_template('kind_recom.html', docs=docs, hast=hasattr(current_user, "username"),  tags=ne_kind)

def kind_find(ne_kind):
    mpe_doc = []
    mpe_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count',charset='utf8')
    mpe_cur = mpe_conn.cursor()
    mpe_sql = "select id, url, title, body,date_time from news_table where tag='%s'" %(ne_kind,)
    mpe_cur.execute(mpe_sql)
    mpe_data = mpe_cur.fetchall()
    mpe_sql2 = "select count(*) from news_table where tag='%s'" %(ne_kind,)
    mpe_cur.execute(mpe_sql2)
    mpe_data2 = mpe_cur.fetchone()[0]
    mpe_cur.close()
    mpe_conn.close()
    for mpe_it in range(0, mpe_data2):
        url = mpe_data[mpe_it][1]
        title = mpe_data[mpe_it][2]
        body = mpe_data[mpe_it][3]
        snippet = mpe_data[mpe_it][3][0:120] + '……'
        time = mpe_data[mpe_it][4].split(' ')[0]
        datetime = mpe_data[mpe_it][4]
        doc = {'url': url, 'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time, 'body': body, 'id': mpe_it+1}
        mpe_doc.append(doc)
    return mpe_doc


def behavi_find():
    docs = []
    if hasattr(current_user, "username"):
        my_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data',charset='utf8')
        my_cur = my_conn.cursor()
        my_sql = "select  key_word from %s order by key_count" %(current_user.username+'key',)
        my_cur.execute(my_sql)
        data_key = my_cur.fetchall()
        my_sql2 = "select count(*) from %s" %(current_user.username+'key',)
        my_cur.execute(my_sql2)
        data_key_count = my_cur.fetchone()[0]
        my_sql4 = "select user_id from %s order by id_count" %(current_user.username+'id',)
        my_cur.execute(my_sql4)
        data_id = my_cur.fetchall()
        my_sql5 = "select count(*) from %s" %(current_user.username+'id',)
        my_cur.execute(my_sql5)
        data_id_count = my_cur.fetchone()[0]
        my_sql7 = "truncate table %s" %(current_user.username+'index',)
        my_cur.execute(my_sql7)
        my_cur.close()
        my_conn.close()
        if data_key_count >= 3 and data_id_count >=5:
            my_conn_two = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data',charset='utf8')
            my_cur_two = my_conn_two.cursor()
            for i in range(0, 3):
                se = Search_rank('../config.ini', 'utf-8')
                flag, id_scores = se.search(data_key[i][0], 2)
                if flag == 1:
                    if(len(id_scores) >= 8):
                        for id_sc in range(0, 8):
                            my_sql3 = "insert into %s values('%d', '%d') " %(current_user.username+'index', 0, id_scores[id_sc][0])
                            my_cur_two.execute(my_sql3)
                            my_conn_two.commit()
                    else:
                        for id_sc in range(0, len(id_scores)):
                            my_sql3 = "insert into %s values('%d', '%d') " % (current_user.username + 'index', 0, id_scores[id_sc][0])
                            my_cur_two.execute(my_sql3)
                            my_conn_two.commit()
                else:
                    continue
            #相似新闻索引填写
            for id_i in range(0, 5):

                data_id_new = get_k_nearest(db_path, data_id[id_i][0], k=5)
                for data_ine in data_id_new:
                    my_sql6 = "insert into %s values('%d', '%d') " % (current_user.username + 'index', 0, data_ine)
                    my_cur_two.execute(my_sql6)
                    my_conn_two.commit()
            sql7 = "select news_id from %s" %(current_user.username+'index',)
            my_cur_two.execute(sql7)
            data_new_url = my_cur_two.fetchall()
            my_cur_two.close()
            my_conn_two.close()
        else:
            data_new_url = reco_ine_news()
    else:
        data_new_url = reco_ine_news()
    news_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count',charset='utf8')
    news_cur = news_conn.cursor()
    for data_new_u in data_new_url:
        sql8 = "select date_time, url, title, body, tag from news_table where id='%d'" %(data_new_u[0],)
        news_cur.execute(sql8)
        data_new_indefo = news_cur.fetchone()
        url =data_new_indefo[1]
        title = data_new_indefo[2]
        body = data_new_indefo[3]
        snippet = data_new_indefo[3][0:120] + '……'
        time = data_new_indefo[0].split(' ')[0]
        datetime = data_new_indefo[0]
        tag_news = data_new_indefo[4]
        doc = {'url': url, 'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time, 'body': body,
               'id': data_new_u[0], 'tag': tag_news, 'extra': []}
        docs.append(doc)
    news_cur.close()
    news_conn.close()
    return docs


def reco_ine_news():
    ite_tags = ['山西', '国际', '财经', '科技', '体育', '旅游', '军事']
    tq_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='news_count',charset='utf8')
    tq_cur = tq_conn.cursor()
    sql10 = "truncate table recom_table"
    tq_cur.execute(sql10)
    for ite_tag in ite_tags:
        sql9 = "select id from news_table where tag='%s' order by date_time desc" % (ite_tag,)
        tq_cur.execute(sql9)
        tw_data = tq_cur.fetchall()[0:8]
        for tw_i in tw_data:
            tq_sql = "insert into recom_table values('%d', '%d')" % (0, tw_i[0])
            tq_cur.execute(tq_sql)
            tq_conn.commit()

    tq_sql2 = "select newyt_id from recom_table order by rand()"
    tq_cur.execute(tq_sql2)
    data_new_url = tq_cur.fetchall()
    tq_cur.close()
    tq_conn.close()
    return data_new_url


def create_recom_table():
    sq3_conn = sqlite3.connect('database.db')
    sq3_c = sq3_conn.cursor()
    sq3_sql = "select username from users"
    sq3_c.execute(sq3_sql)
    sq3_datas = sq3_c.fetchall()
    sq3_c.close()
    sq3_conn.close()
    my_conn = pymysql.connect(host='127.0.0.1', port=3306, user='root', password='lilong', db='behavior_data',charset='utf8')
    my_cur = my_conn.cursor()
    sq4 = " select TABLE_NAME from information_schema.tables where TABLE_SCHEMA='behavior_data' "
    my_cur.execute(sq4)
    data = my_cur.fetchall()
    data_lie = []
    for i in range(0, len(data)):
        data_lie.append(re.match(re.compile("(.*)?(id|index|key)$"), data[i][0]).group(1))
    #print(list(set(data_lie)))
    for sq3_data in sq3_datas:
        if sq3_data[0] not in data_lie:
            my_sql = "create table %s (id INT UNSIGNED AUTO_INCREMENT, key_word VARCHAR(15) NOT NULL, key_count INT UNSIGNED NOT NULL, PRIMARY KEY(id))" % (sq3_data[0] + 'key',)
            my_cur.execute(my_sql)
            my_sql2 = "create table %s (id INT UNSIGNED AUTO_INCREMENT, user_id INT UNSIGNED NOT NULL, id_count INT UNSIGNED NOT NULL, PRIMARY KEY(id))" % (
            sq3_data[0] + 'id',)
            my_cur.execute(my_sql2)
            my_sql3 = "create table %s (id INT UNSIGNED AUTO_INCREMENT, news_id INT UNSIGNED NOT NULL, PRIMARY KEY(id))" % (sq3_data[0] + 'index',)
            my_cur.execute(my_sql3)
    my_cur.close()
    my_conn.close()


def get_k_nearest(db_path, docid, k=5):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM knearest WHERE id=?", (docid,))
    docs = c.fetchone()
    #print(docs)
    c.close()
    conn.close()
    return docs[1: 1 + (k if k < 5 else 5)]  # max = 5

if __name__ == '__main__':
    jieba.initialize()  # 手动初始化（可选）
    db.create_all()
    app.run()
