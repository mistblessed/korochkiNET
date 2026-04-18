from flask import Flask, render_template, redirect, flash, url_for, session, jsonify, request
from db_utils import execute_query
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps

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

# Декоратор для проверки прав администратора
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Необходимо войти в систему', 'danger')
            return redirect(url_for('login'))
        
        # Проверяем роль пользователя
        user_id = session['user_id']
        sql = 'SELECT role_id FROM users WHERE id = %s'
        user = execute_query(sql, (user_id,), fetch_one=True)
        
        if not user:
            session.clear()
            flash('Сессия устарела', 'danger')
            return redirect(url_for('login'))
        
        role_id = user['role_id'] if isinstance(user, dict) else user[0]
        
        # role_id = 1 - администратор
        if role_id != 1:
            flash('Доступ запрещён. Требуются права администратора.', 'danger')
            return redirect(url_for('home'))
        
        return f(*args, **kwargs)
    return decorated_function

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

        sql = 'SELECT id, login, password, role_id FROM Users WHERE login = %s'
        user = execute_query(sql, (login,), fetch_one=True)

        if user:
            if isinstance(user, dict):
                user_id = user['id']
                user_login = user['login']
                user_password = user['password']
                role_id = user['role_id']
            else:
                user_id = user[0]
                user_login = user[1]
                user_password = user[2]
                role_id = user[3]
            
            if check_password_hash(user_password, password):
                session['user_id'] = user_id
                session['user_login'] = user_login
                session['role_id'] = role_id
                session.permanent = True
                print(f"User logged in: {user_login}, role_id: {role_id}")
                
                flash(f"Добро пожаловать, {user_login}!", 'success')
                return redirect(url_for('home'))
            else:
                flash('Неверный логин или пароль', 'danger')
        else:
            flash('Неверный логин или пароль', 'danger')
        
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('home'))

@app.route('/api/check_auth')
def check_auth():
    """Проверка авторизации пользователя"""
    is_authenticated = 'user_id' in session
    return jsonify({'is_authenticated': is_authenticated})

@app.route('/api/enroll_course', methods=['POST'])
def enroll_course():
    """Создание заявки на курс и связь с пользователем"""
    # Проверяем авторизацию
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Необходимо войти в систему'}), 401
    
    data = request.get_json()
    course_id = data.get('course_id')
    sposob_oplati_id = data.get('sposob_oplati_id')
    prefer_time_str = data.get('prefer_time')
    user_id = session['user_id']
    
    # Валидация
    if not course_id:
        return jsonify({'success': False, 'message': 'ID курса не указан'}), 400
    
    if not sposob_oplati_id:
        return jsonify({'success': False, 'message': 'Выберите способ оплаты'}), 400
    
    # Проверяем существование курса
    check_course_sql = 'SELECT id, course_name, price FROM course WHERE id = %s'
    course = execute_query(check_course_sql, (course_id,), fetch_one=True)
    
    if not course:
        return jsonify({'success': False, 'message': 'Курс не найден'}), 404
    
    # Проверяем существование способа оплаты
    check_payment_sql = 'SELECT id, sposob FROM sposob_oplati WHERE id = %s'
    payment_method = execute_query(check_payment_sql, (sposob_oplati_id,), fetch_one=True)
    
    if not payment_method:
        return jsonify({'success': False, 'message': 'Способ оплаты не найден'}), 404
    
    # Преобразуем строку даты/времени в объект datetime
    prefer_time = None
    if prefer_time_str:
        try:
            prefer_time = datetime.strptime(prefer_time_str, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                prefer_time = datetime.strptime(prefer_time_str, '%Y-%m-%d %H:%M')
            except ValueError:
                prefer_time = datetime.now() + timedelta(days=1)
    else:
        prefer_time = datetime.now() + timedelta(days=1)
    
    # Проверяем, нет ли уже активной заявки на этот курс
    check_existing_sql = '''
        SELECT a.id, a.status 
        FROM user_applications ua
        JOIN application a ON a.id = ua.application_id
        WHERE ua.user_id = %s AND a.course_id = %s AND a.status = 'active'
    '''
    existing = execute_query(check_existing_sql, (user_id, course_id), fetch_one=True)
    
    if existing:
        return jsonify({'success': False, 'message': 'У вас уже есть активная заявка на этот курс'})
    
    # Создаём новую заявку
    insert_application_sql = '''
        INSERT INTO application (course_id, prefer_time, sposob_oplati_id, status)
        VALUES (%s, %s, %s, 'active')
        RETURNING id
    '''
    
    try:
        # 1. Вставляем заявку
        result = execute_query(
            insert_application_sql, 
            (course_id, prefer_time, sposob_oplati_id), 
            fetch_one=True
        )
        
        # Получаем ID созданной заявки
        if isinstance(result, dict):
            application_id = result.get('id')
        elif isinstance(result, (tuple, list)):
            application_id = result[0]
        else:
            application_id = result
        
        if not application_id:
            return jsonify({'success': False, 'message': 'Не удалось создать заявку'}), 500
        
        # 2. Связываем заявку с пользователем
        insert_user_app_sql = '''
            INSERT INTO user_applications (user_id, application_id)
            VALUES (%s, %s)
        '''
        execute_query(insert_user_app_sql, (user_id, application_id))
        
        # Получаем информацию для ответа
        course_name = course['course_name'] if isinstance(course, dict) else course[1]
        
        return jsonify({
            'success': True, 
            'message': f'Заявка на курс "{course_name}" успешно создана!',
            'application_id': application_id
        })
        
    except Exception as e:
        print(f"Error in enroll_course: {str(e)}")
        return jsonify({'success': False, 'message': f'Ошибка при создании заявки: {str(e)}'}), 500

@app.route('/api/get_sposob_oplati', methods=['GET'])
def get_sposob_oplati():
    """Получение списка способов оплаты"""
    sql = 'SELECT id, sposob FROM sposob_oplati ORDER BY id'
    rows = execute_query(sql, fetch_all=True)
    
    sposob_list = []
    for row in rows:
        sposob_list.append({
            'id': row['id'] if isinstance(row, dict) else row[0],
            'name': row['sposob'] if isinstance(row, dict) else row[1]
        })
    
    return jsonify(sposob_list)

@app.route('/profile')
def profile():
    """Страница личного кабинета"""
    if 'user_id' not in session:
        flash('Пожалуйста, войдите в систему', 'warning')
        return redirect(url_for('login'))
    return render_template('profile.html')

@app.route('/api/get_user_applications')
def get_user_applications():
    """Получение всех заявок текущего пользователя"""
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    user_id = session['user_id']
    
    sql = '''
        SELECT 
            a.id,
            a.course_id,
            a.prefer_time,
            a.sposob_oplati_id,
            a.status,
            a.created_at,
            c.course_name,
            c.description as course_description,
            c.price,
            c.image,
            cur.name as currency_name,
            s.sposob as payment_method
        FROM user_applications ua
        JOIN application a ON a.id = ua.application_id
        JOIN course c ON c.id = a.course_id
        LEFT JOIN currency cur ON cur.id = c.currency
        LEFT JOIN sposob_oplati s ON s.id = a.sposob_oplati_id
        WHERE ua.user_id = %s
        ORDER BY a.created_at DESC
    '''
    
    rows = execute_query(sql, (user_id,), fetch_all=True)
    
    if not rows:
        return jsonify([])
    
    applications = []
    for row in rows:
        if isinstance(row, dict):
            app = {
                'id': row['id'],
                'course_id': row['course_id'],
                'course_name': row['course_name'],
                'course_description': row['course_description'],
                'price': row['price'],
                'currency': row['currency_name'],
                'image': '/static/' + row['image'] if row['image'] else '/static/img/placeholder.jpg',
                'prefer_time': row['prefer_time'].strftime('%d.%m.%Y %H:%M') if row['prefer_time'] else 'Не указано',
                'created_at': row['created_at'].strftime('%d.%m.%Y') if row['created_at'] else 'Не указано',
                'payment_method': row['payment_method'],
                'status': row['status']
            }
        else:
            # Если rows - список кортежей (добавляем created_at как row[5])
            app = {
                'id': row[0],
                'course_id': row[1],
                'course_name': row[6],
                'course_description': row[7],
                'price': row[8],
                'currency': row[10],
                'image': '/static/' + row[9] if row[9] else '/static/img/placeholder.jpg',
                'prefer_time': row[2].strftime('%d.%m.%Y %H:%M') if row[2] else 'Не указано',
                'created_at': row[5].strftime('%d.%m.%Y') if len(row) > 5 and row[5] else 'Не указано',
                'payment_method': row[11] if len(row) > 11 else None,
                'status': row[4]
            }
        applications.append(app)
    
    return jsonify(applications)

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Не авторизован'}), 401
    
    data = request.get_json()
    rating = data.get('rating')
    comment = data.get('comment')
    user_id = session['user_id']
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({'success': False, 'message': 'Оценка должна быть от 1 до 5'})
    if not comment or len(comment) < 5:
        return jsonify({'success': False, 'message': 'Отзыв слишком короткий'})
    
    sql = '''
        INSERT INTO reviews (user_id, rating, comment, status)
        VALUES (%s, %s, %s, 'pending')
    '''
    try:
        execute_query(sql, (user_id, rating, comment))
        return jsonify({'success': True, 'message': 'Отзыв отправлен'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/admin')
@admin_required
def admin_panel():
    return render_template('admin.html')

# API: получение всех заявок для администратора
@app.route('/api/admin/applications')
@admin_required
def admin_get_applications():
    """Получение всех заявок с информацией о пользователях и курсах"""
    sql = '''
        SELECT 
            a.id,
            a.course_id,
            a.prefer_time,
            a.sposob_oplati_id,
            a.status,
            a.created_at,
            c.course_name,
            c.price,
            c.image,
            cur.name as currency_name,
            s.sposob as payment_method,
            u.id as user_id,
            u.login,
            u.full_name,
            u.email,
            u.phone
        FROM application a
        JOIN user_applications ua ON ua.application_id = a.id
        JOIN users u ON u.id = ua.user_id
        JOIN course c ON c.id = a.course_id
        LEFT JOIN currency cur ON cur.id = c.currency
        LEFT JOIN sposob_oplati s ON s.id = a.sposob_oplati_id
        ORDER BY a.created_at DESC
    '''
    
    rows = execute_query(sql, fetch_all=True)
    
    applications = []
    for row in rows:
        if isinstance(row, dict):
            app = {
                'id': row['id'],
                'course_id': row['course_id'],
                'course_name': row['course_name'],
                'price': row['price'],
                'currency': row['currency_name'],
                'image': '/static/' + row['image'] if row['image'] else '/static/img/placeholder.jpg',
                'prefer_time': row['prefer_time'].strftime('%d.%m.%Y %H:%M') if row['prefer_time'] else 'Не указано',
                'created_at': row['created_at'].strftime('%d.%m.%Y %H:%M') if row['created_at'] else 'Не указано',
                'payment_method': row['payment_method'],
                'status': row['status'],
                'user_id': row['user_id'],
                'user_login': row['login'],
                'user_name': row['full_name'],
                'user_email': row['email'],
                'user_phone': row['phone']
            }
        else:
            app = {
                'id': row[0],
                'course_id': row[1],
                'course_name': row[6],
                'price': row[7],
                'currency': row[9],
                'image': '/static/' + row[8] if row[8] else '/static/img/placeholder.jpg',
                'prefer_time': row[2].strftime('%d.%m.%Y %H:%M') if row[2] else 'Не указано',
                'created_at': row[5].strftime('%d.%m.%Y %H:%M') if row[5] else 'Не указано',
                'payment_method': row[10],
                'status': row[4],
                'user_id': row[11],
                'user_login': row[12],
                'user_name': row[13],
                'user_email': row[14],
                'user_phone': row[15]
            }
        applications.append(app)
    
    return jsonify(applications)

@app.route('/api/admin/update_status', methods=['POST'])
@admin_required
def admin_update_status():
    """Обновление статуса заявки"""
    data = request.get_json()
    application_id = data.get('application_id')
    new_status = data.get('status')
    
    if not application_id or not new_status:
        return jsonify({'success': False, 'message': 'Не указаны ID заявки или статус'}), 400
    
    # Проверяем допустимые статусы
    valid_statuses = ['active', 'in_progress', 'completed', 'cancelled']
    status_mapping = {
        'новая': 'active',
        'идет обучение': 'in_progress', 
        'обучение завершено': 'completed',
        'отменена': 'cancelled'
    }
    
    # Если пришло русское название статуса
    if new_status in status_mapping:
        new_status = status_mapping[new_status]
    
    if new_status not in valid_statuses:
        return jsonify({'success': False, 'message': f'Недопустимый статус: {new_status}'}), 400
    
    # Обновляем статус
    update_sql = 'UPDATE application SET status = %s WHERE id = %s'
    
    try:
        execute_query(update_sql, (new_status, application_id))
        return jsonify({'success': True, 'message': 'Статус успешно обновлён'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    
    

if __name__ == '__main__':
    app.run(debug=True)

