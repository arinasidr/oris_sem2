from flask import Flask, session, redirect, render_template, url_for, request
from db import get_connection
import datetime

with open('props.txt', 'r', encoding='utf-8') as f:
    lines = f.read().splitlines()

secret_key = lines[1].strip()

app = Flask(__name__)
app.secret_key = secret_key

#главная страница на нее можно попасть нажимая на логотип с левой стороны
@app.route('/')
def index():
    if session.get('user_id'):
        return redirect(url_for('profile'))
    return render_template('index.html')

#регистрация на нее можно попасть нажав на ссылку в правом углу, а также перейти из входа
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('users/register.html', error= 'нужно указать имя пользователя и пароль')

        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            'SELECT id FROM users WHERE username = %s',
            (username,)
        )

        if cur.fetchone():
            cur.close()
            conn.close()
            return render_template('users/register.html', error='пользователь уже существует')

        cur.execute("""
            INSERT INTO users (username, password)
            VALUES (%s, %s)
            RETURNING id
        """,(username, password))
        
        user_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO profiles (user_id, session_start_date)
            VALUES (%s, CURRENT_DATE)
        """,(user_id,))

        conn.commit()
        cur.close()
        conn.close()

        session['user_id'] = user_id
        return redirect(url_for('profile'))

    return render_template('users/register.html')

#логин аналогично регистрации
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('users/login.html', error='нужно указать имя пользователя и пароль')

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, password
            FROM users
            WHERE username = %s
        """,(username,))

        row = cur.fetchone()

        cur.close()
        conn.close()

        if not row or row[1] != password:
            return render_template('users/login.html',error='неверный логин или пароль')

        session['user_id'] = row[0]
        return redirect(url_for('profile'))

    return render_template('users/login.html')

#в профиль автоматически переходит после входа, а также в правом верхнем углу есть ссылка на профиль
@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT u.username, p.session_start_date
        FROM users u
        JOIN profiles p ON u.id = p.user_id
        WHERE u.id = %s
    """, (user_id,))

    row = cur.fetchone()
    if not row:
        return render_template('profiles/profile.html',error='пользователь не найден')
    
    cur.execute("""
        SELECT t.is_completed, t.deadline
        FROM tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE s.user_id = %s
    """, (user_id,))

    tasks = cur.fetchall()

    total = len(tasks)
    completed = 0
    prosral = 0
    today = datetime.date.today()

    for is_completed, deadline in tasks:
        if bool(is_completed):
            completed += 1
        elif deadline < today:
            prosral += 1

    if total > 0:
        precent_of_success = int((completed / total) * 100)
    else:
        precent_of_success = 0

    if total == 0:
        forecast = {
            'level': 'none',
            'title': 'Пока нет данных',
            'text': 'Добавьте предметы и задачи, чтобы увидеть прогноз на сессию.'
        }
    elif precent_of_success >= 80 and prosral == 0:
        forecast = {
            'level': 'good',
            'title': 'Ты молодчинка! Все под контролем!',
            'text': 'Ты уверенно идёшь к успешно сданной сессии.'
        }
    elif precent_of_success >= 50 or prosral > 3:
        forecast = {
            'level': 'warning',
            'title': 'Есть риски....',
            'text': 'Часть задач требует внимания. Лучше не откладывать. Терпи, ведь господь с тобой еще не закончил.....'
        }
    else:
        forecast = {
            'level': 'danger',
            'title': 'Высокий риск атщисления',
            'text': 'Много невыполненных или просроченных задач. Ужас!'
        }
    
    cur.close()
    conn.close()

    username, session_start_date = row
    return render_template(
        'profiles/profile.html',
        username=username,
        session_start_date=session_start_date,
        forecast=forecast,
        precent_of_success=precent_of_success
    )

#есть ссылка в профиле, а также в правом верхнем углу ссылка
@app.route('/subjects')
def subjects():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name
        FROM subjects
        WHERE user_id = %s
        ORDER BY id
    """, (user_id,))

    rows = cur.fetchall()

    cur.close()
    conn.close()

    subjects = [{'id': i[0], 'name': i[1]} for i in rows]

    return render_template('subjects/list.html',subjects=subjects)

#ссылка только на странице предметов
@app.route('/subjects/add', methods = ['GET', 'POST'])
def add_subjects():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()

        if not name:
            return render_template('subjects/add.html',error='Введите название предмета')

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO subjects (user_id, name)  VALUES (%s, %s)
        """, (user_id, name))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('subjects'))
    
    return render_template('subjects/add.html')

@app.route('/subjects/<int:subject_id>/edit', methods = ['GET', 'POST'])
def edit_subject(subject_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name FROM subjects
        WHERE id = %s AND user_id = %s
    """, (subject_id, user_id))

    subject = cur.fetchone()

    if not subject:
        cur.close()
        conn.close()
        return redirect(url_for('subjects'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        tags_input = request.form.get('tags', '')
        tags_list = [i.strip().lower() for i in tags_input.split(',') if i.strip()]

        cur.execute(
            "DELETE FROM subject_tags WHERE subject_id = %s",
            (subject_id,)
        )

        for tag_name in tags_list:
            cur.execute(
                "SELECT id FROM tags WHERE name = %s",
                (tag_name,)
            )
            row = cur.fetchone()

            if row:
                tag_id = row[0]
            else:
                cur.execute(
                    "INSERT INTO tags (name) VALUES (%s) RETURNING id",
                    (tag_name,)
                )
                tag_id = cur.fetchone()[0]

            cur.execute(
                "INSERT INTO subject_tags (subject_id, tag_id) VALUES (%s, %s)",
                (subject_id, tag_id)
            )

        if not name:
            cur.close()
            conn.close()
            return render_template(
                'subjects/edit.html',
                subject={'id': subject[0], 'name': subject[1]},
                error='Название не может быть пустым'
            )

        cur.execute("""
            UPDATE subjects SET name = %s WHERE id = %s AND user_id = %s
        """, (name, subject_id, user_id))

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('subjects'))
    
    cur.execute("""
        SELECT t.name
        FROM tags t
        JOIN subject_tags st ON t.id = st.tag_id
        WHERE st.subject_id = %s
        """,(subject_id,))
    
    row = cur.fetchall()
    tags = [i[0] for i in row]
    tags_string = ', '.join(tags)

    cur.close()
    conn.close()
    
    return render_template('subjects/edit.html', subject={'id': subject[0], 'name': subject[1]}, tags=tags_string)

@app.route('/subjects/<int:subject_id>/delete')
def delete_subject(subject_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "DELETE FROM tasks WHERE subject_id = %s",
        (subject_id,)
    )

    cur.execute(
        "DELETE FROM subject_tags WHERE subject_id = %s",
        (subject_id,)
    )

    cur.execute("""
        DELETE FROM subjects WHERE id = %s AND user_id = %s
    """, (subject_id, user_id))
    
    conn.commit()
    cur.close()
    conn.close()
    
    return redirect(url_for('subjects'))

@app.route('/subjects/<int:subject_id>')
def subject_detail(subject_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT id, name FROM subjects WHERE id = %s AND user_id = %s
    """, (subject_id, user_id))
    
    subject = cur.fetchone()
    if not subject:
        cur.close()
        conn.close()
        return redirect(url_for('subjects'))
    
    cur.execute("""
        SELECT id, title, deadline, is_completed
        FROM tasks
        WHERE subject_id = %s
        ORDER BY deadline
    """, (subject_id,))

    tasks_row = cur.fetchall()
    today = datetime.date.today()

    tasks = []
    for i in tasks_row:
        day_left = (i[2] - today).days
        tasks.append({
            'id': i[0],
            'title': i[1],
            'deadline': i[2],
            'is_completed': i[3],
            'days_left': day_left
        })

    cur.execute("""
        SELECT t.name
        FROM tags t
        JOIN subject_tags st ON t.id = st.tag_id
        WHERE st.subject_id = %s
    """, (subject_id,))

    row = cur.fetchall()
    tags = [i[0] for i in row]

    cur.close()
    conn.close()
    
    return render_template('subjects/detail.html',subject={'id': subject[0], 'name': subject[1]},tasks=tasks, tags=tags)

@app.route('/subjects/<int:subject_id>/tasks/add', methods=['GET', 'POST'])
def add_task(subject_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        deadline = request.form.get('deadline', '')

        if not title or not deadline:
            return render_template('tasks/add.html', error='Заполните все поля', subject_id=subject_id)
    
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO tasks (subject_id, title, deadline, is_completed)
            VALUES(%s, %s, %s, FALSE)
        """, (subject_id, title, deadline))
        
        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for('subject_detail', subject_id=subject_id))
    
    return render_template('tasks/add.html',subject_id=subject_id)

@app.route('/tasks/<int:task_id>/toggle', methods=['POST'])
def toggle_task(task_id):
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT t.is_completed
        FROM tasks t
        JOIN subjects s ON t.subject_id = s.id
        WHERE t.id = %s AND s.user_id = %s
    """,(task_id, user_id))
    row = cur.fetchone()

    if not row:
        cur.close()
        conn.close()
        return ''

    current_status = bool(row[0])
    new_status = not current_status

    cur.execute("""
        UPDATE tasks
        SET is_completed = %s,
            completed_at = CASE
                WHEN %s THEN CURRENT_DATE
                ELSE NULL
            END
        WHERE id = %s
    """,(new_status, new_status, task_id))

    conn.commit()
    cur.close()
    conn.close()

    return ''

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
