from enum import unique
from flask import Flask,render_template,redirect,request,flash,session
from flask_session import Session
from flask_socketio import SocketIO, join_room, leave_room, emit
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_required,logout_user,login_user,current_user
from urllib.parse import urlparse, urljoin
from werkzeug.security import generate_password_hash, check_password_hash
import random
import os


app=Flask(__name__)
app.config["SECRET_KEY"]=os.environ.get("SECRET_KEY")
app.config["SESSION_TYPE"]='filesystem'


uri =  os.environ.get("DATABASE_URL")
if uri:
    if uri.startswith("postgres://"):
        uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri or "sqlite:///users_data.db"

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Session(app)
socketio = SocketIO(app, manage_session=False)


loginmanager=LoginManager()
loginmanager.init_app(app)
loginmanager.login_view="login"



def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc



def generator():
    letters = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
    room_name=""
    for n in range(6):
        room_name+=random.choice(letters)
    return room_name



@loginmanager.user_loader
def load_user(user_id):
    try:
        return Users.query.get(user_id)

    except:
        return None



db=SQLAlchemy(app)
class Users(UserMixin,db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(10),unique=True)
    password=db.Column(db.String(100))


class Rooms(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    room_id=db.Column(db.String(10),unique=True)

db.create_all()





@app.route('/',methods=['GET','POST'])
@login_required
def index():
    return render_template("index.html")





@app.route('/login',methods=["GET",'POST'])
def login():
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method=="POST":
        username=request.form['username']
        password=request.form['password']
        user=Users.query.filter_by(username=username).first()
        if user and check_password_hash(user.password,password):
            login_user(user)
            return redirect(url_for('index'))
        return render_template("login.html")

    return render_template("login.html")





@app.route("/register",methods=["GET",'POST'])
def register():
    err_msg=""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method=="POST":
        hash_and_salted_password = generate_password_hash(
            request.form['password'],
            method='pbkdf2:sha256',
            salt_length=8
        )
        
        if Users.query.filter_by(username=request.form['username']).first():
            err_msg="Username Already Exists! Please Try Again"
            flash(err_msg,'error')
            return redirect(url_for('register'))
        user=Users(username=request.form['username'],password=hash_and_salted_password)
        
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for('index'))
    return render_template("register.html")




@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.args.get('a')=="True":
        session['username'] = current_user.username
        a=True
        while a:
            temp_room=generator()
            if not Rooms.query.filter_by(room_id=temp_room).first():
                a=False
        new_room=Rooms(room_id=temp_room)
        db.session.add(new_room)
        db.session.commit()
        session['room']=temp_room
        return render_template('chat.html', session = session)
    err_msg=""
    if(request.method=='POST'):
        room = request.form['room_id']
        if Rooms.query.filter_by(room_id=room).first():
            #Store the data in session
            session['username'] = current_user.username
            session['room'] = room
            return render_template('chat.html', session = session)
        else:
            err_msg="Room Doesn't Exist! Please Create one Below"
            flash(err_msg,'error')
            return redirect(url_for('index'))
    else:
        if(session.get('username') is not None):
            return render_template('chat.html', session = session)
        else:
            return redirect(url_for('index'))



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))





@socketio.on('join', namespace='/chat')
def join(message):   
    room = session.get('room')
    join_room(room)
    emit('status', {'msg':  session.get('username') + ' has entered the room.'}, room=room)



@socketio.on('text', namespace='/chat')
def text(message):
    room = session.get('room')
    emit('message', {'msg': session.get('username') + ' : ' + message['msg']}, room=room)



@socketio.on('left', namespace='/chat')
def left(message):
    room = session.get('room')
    username = session.get('username')
    leave_room(room)
    session.pop('room')
    emit('status', {'msg': username + ' has left the room.'}, room=room)



if __name__ == '__main__':
    app.run()