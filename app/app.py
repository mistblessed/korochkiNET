from flask import Flask, render_template, redirect, flash, url_for, session, jsonify, request
from db_utils import execute_query
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash

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

@app.route('/register', methods=['GET', 'POST'])
def auth():
    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']
        full_name = request.form['full_name']
        email = request.form['email']
        phone = request.form['phone']

        check_sql = 'SELECT id FROM Users WHERE login = %s'
        existing = execute_query(check_sql, (login,), fetch_one=True)

        if existing:
            flash('Пользователь с таким логином уже зарегестрирован')
            return redirect(url_for('auth'))
        
        hashed_password = generate_password_hash(password)

        insert_sql = '''
            INSERT INTO Users(login, password, full_name, email, phone)
            VALUES(%s, %s, %s, %s, %s)
            '''
        
        try:
            execute_query(insert_sql, (login, hashed_password, full_name, email, phone))
            flash('Регистрация успешна! Теперь войдите', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f'Ошибка базы данных: {e}', 'danger')
            return redirect(url_for('register'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form['login']
        password = request.form['password']

        sql = 'SELECT id, login, password FROM Users WHERE login = %s'
        user = execute_query(sql, (login,), fetch_one=True)

        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['login']
            flash(f"Добро пожаловать, {user['login']}", 'success')
            return redirect(url_for('home'))
        else:
            flash('Неверный логин или пароль', 'danger')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)

