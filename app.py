from flask import Flask,render_template,redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager,UserMixin,login_required,logout_user,login_user,current_user


app=Flask(__name__)
app.config["SECRET_KEY"]="SECRET"
app.config["SQLALCHEMY_DATABASE_URI"]

@app.route('/')
def index():
    return render_template("index.html")

if __name__=="__main__":
    app.run(debug=True)