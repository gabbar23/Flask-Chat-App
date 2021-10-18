from enum import unique
from flask import Flask,render_template,redirect,request,flash
from flask.helpers import url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_required,logout_user,login_user,current_user
from urllib.parse import urlparse, urljoin
from werkzeug.security import generate_password_hash, check_password_hash


app=Flask(__name__)
app.config["SECRET_KEY"]="SECRET"
app.config["SQLALCHEMY_DATABASE_URI"]="sqlite:///user_data.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"]=False


loginmanager=LoginManager()
loginmanager.init_app(app)
loginmanager.login_view="login"

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))

    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

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
    password=db.Column(db.String(20))

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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__=="__main__":
    app.run(debug=True)