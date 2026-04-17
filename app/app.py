from flask import Flask, render_template, redirect, flash, url_for, session
from db_utils import execute_query
from config import Config
from werkzeug import security

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/')
def home():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)