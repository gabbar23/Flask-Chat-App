from flask import Flask,render_template

app=Flask(__name__)
app.config["SECRET_KEY"]="SECRET"

@app.route('/')
def index_get():
    return render_template("index.html")

if __name__=="__main__":
    app.run(debug=True)