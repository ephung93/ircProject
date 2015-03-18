import os
import uuid
import psycopg2
import psycopg2.extras
from flask import Flask, session, redirect
from flask.ext.socketio import SocketIO, emit

app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

messages = [{'text':'test', 'name':'testName'}]
users = {}

def connectToDB():
  connectionString = 'dbname=irc_db user=postgres password=ep4554345 host=localhost'
  try:
    return psycopg2.connect(connectionString)
  except:
    print("Can't connect to database")
    
def updateRoster():
    names = []
    for user_id in  users:
        print users[user_id]['username']
        if len(users[user_id]['username'])==0:
            names.append('Anonymous')
        else:
            names.append(users[user_id]['username'])
    print 'broadcasting names'
    emit('roster', names, broadcast=True)
    

@socketio.on('connect', namespace='/chat')
def test_connect():
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT name, message FROM messages JOIN users ON messages.user_id=users.user_id"
    cur.execute(query)
    results = cur.fetchall()
    print results
    session['uuid']=uuid.uuid1()
    session['username']='starter name'
    print 'connected'
    
    users[session['uuid']]={'username':'New User'}
    updateRoster()

        
    
    for result in results:
        result = {'name': result[0], 'text': result[1]}
        emit('message', result)
    

@socketio.on('message', namespace='/chat')
def new_message(message):
    #tmp = {'text':message, 'name':'testName'}
    tmp = {'text':message, 'name':users[session['uuid']]['username']}
    messages.append(tmp)
    
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "INSERT INTO messages VALUES (default, %s, %s)"
    cur.execute(query, (message, session['id']))
    conn.commit()
    emit('message', tmp, broadcast=True)
    
@socketio.on('identify', namespace='/chat')
def on_identify(message):
    print 'identify' + message
    users[session['uuid']]={'username':message}
    updateRoster()


@socketio.on('login', namespace='/chat')
def on_login(data):
    
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    query = "SELECT user_id, name, password FROM users WHERE name = %s AND password = %s"
    cur.execute(query, (data['username'], data['password']))
    result = cur.fetchone()
    
    if result:
        users[session['uuid']]={'username': data['username']}
        session['username'] = data['username']
        session['id']=result["user_id"]
        print("successful login")
        updateRoster()
        
    
    else:
        print("Incorrect username or password.")
        return redirect('https://demo-project-ephung.c9.io/',301)
        #return app.send_static_file('badLogin.html')
    conn.commit()

    
    #users[session['uuid']]={'username':message}
    #updateRoster()
@socketio.on('search', namespace='/chat')
def search(search):
    print search
    conn = connectToDB()
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    search = '%' + search + '%'
    query = "SELECT name, message FROM messages join users on messages.user_id= users.user_id WHERE message LIKE %s or user LIKE %s"
    cur.execute(query, (search,search))
    results = cur.fetchone()
    print results

    emit('clearResults', {})
    for result in results:
        result = {'name': result[0:200], 'text': result[0:200]}
        emit('search', result, broadcast=True)  
    
@socketio.on('disconnect', namespace='/chat')
def on_disconnect():
    print 'disconnect'
    if session['uuid'] in users:
        del users[session['uuid']]
        updateRoster()

@app.route('/')
def hello_world():
    
    return app.send_static_file('index.html')
    
@app.route('/badLogin')
def BL():
    
    return app.send_static_file('badLogin.html')
    

@app.route('/js/<path:path>')
def static_proxy_js(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('js', path))
    
@app.route('/css/<path:path>')
def static_proxy_css(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('css', path))
    
@app.route('/img/<path:path>')
def static_proxy_img(path):
    # send_static_file will guess the correct MIME type
    return app.send_static_file(os.path.join('img', path))
    
if __name__ == '__main__':
    print "A"

    socketio.run(app, host=os.getenv('IP', '0.0.0.0'), port=int(os.getenv('PORT', 8080)))
     