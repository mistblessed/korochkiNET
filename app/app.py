from flask import Flask, render_template, redirect, flash, url_for, session, jsonify
from db_utils import execute_query
from config import Config
from werkzeug import security

app = Flask(__name__)
app.config.from_object(Config)

@app.route('/api/courses')
def get_courses():
    sql = 'SELECT course.id, course_name, description, price, image, currency.name FROM Course JOIN currency ON currency.id = course.currency'
    rows = execute_query(sql, fetch_all=True)

    courses = []
    for row in rows:
        image_path = '/static/' + row['image']  
        courses.append({
            'id': row['id'],
            'name': row['course_name'],
            'description': row["description"],
            'price': row["price"],
            'image': image_path,           
            'currency': row['name']
        })
    return jsonify(courses)
@app.route('/')
def home():
    return render_template('index.html')



if __name__ == '__main__':
    app.run(debug=True)