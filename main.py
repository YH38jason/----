#coding=utf-8
from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import sqlite3

app = Flask(__name__)

# 读取屏蔽词
with open('stopWord.txt', 'r', encoding='utf-8') as sw:
    stopWords = [i.strip() for i in sw.readlines()]

# 登录状态
def isLogin() -> bool:
    return bool(request.cookies.get("userName"))

# 首页
@app.route('/', methods=['POST', 'GET'])
def home():
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    sql = "SELECT * FROM POSTS"
    cur.execute(sql)
    posts = cur.fetchall()
    ans = (None, None, -1)
    for post in posts:
        if post[2] >= ans[2]:
            ans = post
    con.close()
    if len(posts) == 0:
        no_post = True
    else:
        no_post = False
    try:
        if isLogin():
            return render_template('home.htm', is_login=True, username=\
            request.cookies.get("userName"), author=ans[3], title=ans[0], like=ans[2], no_post=no_post)
        return render_template('home.htm', author=ans[3], title=ans[0], like=ans[2], no_post=no_post)
    except IndexError:
        return render_template('home.htm', is_login=isLogin(), no_post=no_post, username=request.cookies.get("userName"))


# 登录
@app.route('/login')
def login():
    return render_template('login.htm')

# 注销
@app.route('/user/unreg')
def unreg():
    red = redirect('/')
    red.delete_cookie('userName')
    return red

# 验证登录
@app.route('/login/check', methods=['POST', 'GET'])
def login_check():
    result = request.form
    # 判断用户名和密码是否正确
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute('SELECT * FROM USERS WHERE USER_NAME = ? AND PASSWORD = ?', \
        (result['Name'], result['Password']))
    if len(cur.fetchall()) != 0:
        red = redirect('/')
        red.set_cookie('userName', result["Name"], max_age=172800)
        return red
    else:
        return render_template('login.htm', error=True)

# 搜索
@app.route('/s', methods=['GET', 'POST'])
def search():
    form = request.form
    if form['keyword'] == '':
        return redirect('/')
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    sql = "SELECT TITLE FROM POSTS WHERE TITLE LIKE ?"
    cur.execute(sql, ('%'+form['keyword']+'%',))
    result = [i[0] for i in cur.fetchall()]
    if len(result) == 0:
        return redirect('/')
    results = json.dumps(result)
    return render_template('search.htm', results=results)
    # return str(results)
        
    
# 注册
@app.route('/reg')
def reg():
    return render_template('reg.htm')

# 处理表单
@app.route('/reg/action', methods=['POST', 'GET'])
def reg_action():
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    info = request.form
    user_name = info['Name']
    pwd = info['Password']
    pwd_confirm = info['PwdConfirm']
    if user_name == '' or pwd == '':
        return render_template('reg.htm', reg_fail=True)
    cur.execute('SELECT USER_NAME FROM USERS WHERE USER_NAME = ?', (user_name,))
    is_repeat = len(cur.fetchall()) != 0
    pwd_diff = pwd != pwd_confirm
    for word in stopWords:
        if word == user_name:
            sensitive = True
            break
    else:
        sensitive = False
    if is_repeat or pwd_diff or sensitive:
        return render_template('reg.htm', is_repeat=is_repeat, pwd_diff=pwd_diff, sensitive=sensitive)
    sql = "INSERT INTO USERS (USER_NAME, PASSWORD) VALUES (?, ?)"
    cur.execute(sql, (user_name, pwd))
    con.commit()
    con.close()
    return redirect(url_for('home'))

# 浏览帖子
@app.route('/postpage/<title>', methods=['GET', 'POST'])
def viewPost(title):
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    sql = "SELECT * FROM POSTS WHERE TITLE = ?"
    cur.execute(sql, (title,))
    post = cur.fetchall()[0]
    # return str(post)
    con.close()
    if request.cookies.get('userName') == post[3]:
        is_author = True
    else:
        is_author = False
    return render_template('post.html', title=post[0], content=post[1].replace('\r', '')\
        , like=post[2], author=post[3], is_author=is_author)

# 点赞帖子
@app.route('/postpage/<title>/like')
def like(title):
    if not request.cookies.get("userName"):
        return redirect('/login')
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute('SELECT ISLIKE FROM USERS WHERE USER_NAME = ?', (request.cookies.get("userName"),))
    if len(cur.fetchall()) == 0:
        sql = "UPDATE POSTS SET LIKE=LIKE+1 WHERE TITLE = ?"
        cur.execute(sql, (title,))
        con.commit()
        sql = "UPDATE USERS SET ISLIKE=? WHERE USER_NAME = ?"
        cur.execute(sql, (title, request.cookies.get("userName")))
        con.commit()
    else:
        cur.execute('SELECT ISLIKE FROM USERS WHERE USER_NAME = ?', (request.cookies.get("userName"),))
        likes = cur.fetchall()[0][0]
        if title in likes:
            return redirect(f'/postpage/{title}')
        else:
            sql = "UPDATE POSTS SET LIKE=LIKE+1 WHERE TITLE = ?"
            cur.execute(sql, (title,))
            con.commit()
            sql = "UPDATE USERS SET ISLIKE=? WHERE USER_NAME = ?"
            cur.execute(sql, (title, request.cookies.get("userName")))
            con.commit()
    con.close()
    return redirect(f'/postpage/{title}')

# 删帖
@app.route('/postpage/<title>/delete')
def delete_post(title):
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    cur.execute('DELETE FROM POSTS WHERE TITLE = ?', (title,))
    con.commit()
    con.close()
    return redirect('/')

# 发帖
@app.route('/posting')
def posting_page():
    if not isLogin():
        return redirect('/login')
    return render_template('posting.htm')

@app.route('/posting/action', methods=['GET', 'POST'])
def posting():
    form = request.form
    con = sqlite3.connect('data.db')
    cur = con.cursor()
    sql = "INSERT INTO POSTS (TITLE, CONTENT, AUTHOR) VALUES (?,?,?)"
    cur.execute(sql, (form['title'], form['content'], request.cookies.get("userName")))
    con.commit()
    con.close()
    return redirect('/')

if __name__ == '__main__':
    # 运行
    app.run(port=2651, debug=False)