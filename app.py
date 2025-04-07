from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'rakuto'

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id):
        self.id = id

users = {'testuser': {'password': 'testpass'}}

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

def load_user_data(base_name):
    filename = f"{current_user.id}_{base_name}"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_user_data(base_name, data):
    filename = f"{current_user.id}_{base_name}"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username]['password'] == password:
            login_user(User(username))
            return redirect(url_for('index'))
        return render_template('login.html', error='ログイン失敗')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    todos = load_user_data('todo.json')
    schedule = load_user_data('timetable.json')
    weekday_map = ['月', '火', '水', '木', '金', '土', '日']
    today_weekday = weekday_map[datetime.today().weekday()]
    today_schedule = [item for item in schedule if item['day'] == today_weekday]

    today_todos = []
    for subject in today_schedule:
        related_tasks = []
        for todo in todos:
            if todo.get("class_name") == subject['class_name']:
                if todo.get("due_date"):
                    days_left = (datetime.strptime(todo["due_date"], "%Y-%m-%d") - datetime.today()).days
                    todo["days_left"] = days_left
                related_tasks.append(todo)
        if related_tasks:
            today_todos.append({'class_name': subject['class_name'], 'tasks': related_tasks})

    for todo in todos:
        if todo.get("due_date"):
            days_left = (datetime.strptime(todo["due_date"], "%Y-%m-%d") - datetime.today()).days
            todo["days_left"] = days_left

    if request.method == 'POST':
        task = request.form['task']
        class_name = request.form['class_name']
        due_date = request.form['due_date']
        if task:
            todos.append({
                'task': task,
                'class_name': class_name,
                'due_date': due_date if due_date else None,
                'done': False
            })
            save_user_data('todo.json', todos)
        return redirect(url_for('index'))

    return render_template('index.html', todos=todos, today_schedule=today_schedule, today_todos=today_todos)

@app.route('/schedule', methods=['GET', 'POST'])
@login_required
def schedule_page():
    schedule = load_user_data('timetable.json')
    grades_data = load_user_data('grades.json')
    if request.method == 'POST':
        schedule.append({
            'class_name': request.form['class_name'],
            'day': request.form['day'],
            'period': int(request.form['period']),
            'room': request.form['room'],
            'teacher': request.form['teacher']
        })
        save_user_data('timetable.json', schedule)
        return redirect(url_for('schedule_page'))
    return render_template('schedule.html', schedule=schedule, grades=grades_data)

@app.route('/delete/<int:index>')
@login_required
def delete_schedule(index):
    schedule = load_user_data('timetable.json')
    if 0 <= index < len(schedule):
        schedule.pop(index)
        save_user_data('timetable.json', schedule)
    return redirect(url_for('schedule_page'))

@app.route('/grades', methods=['GET', 'POST'])
@login_required
def grades_page():
    grades_data = load_user_data('grades.json')
    if request.method == 'POST':
        items = []
        for name, w in zip(request.form.getlist('item_name[]'), request.form.getlist('weight[]')):
            items.append({'name': name, 'weight': int(w), 'score': None})
        grades_data.append({'class_name': request.form['class_name'], 'items': items, 'total_score': None})
        save_user_data('grades.json', grades_data)
        return redirect(url_for('grades_page'))
    return render_template('grades.html', grades=grades_data)

@app.route('/grades/edit/<int:index>', methods=['GET', 'POST'])
@login_required
def edit_grade(index):
    grades_data = load_user_data('grades.json')
    if index < 0 or index >= len(grades_data):
        return "データが見つかりません", 404

    grade = grades_data[index]
    if request.method == 'POST':
        total = 0
        all_entered = True
        for i, item in enumerate(grade["items"]):
            score_str = request.form.get(f"score_{i}")
            if score_str:
                try:
                    score = float(score_str)
                    item["score"] = score
                    total += score * (item["weight"] / 100)
                except ValueError:
                    item["score"] = None
                    all_entered = False
            else:
                item["score"] = None
                all_entered = False
        grade["total_score"] = round(total, 1) if all_entered else None
        save_user_data('grades.json', grades_data)
        return redirect(url_for('grades_page'))

    return render_template('edit_grade.html', grade=grade)

@app.route('/todo/done/<int:index>')
@login_required
def mark_done(index):
    todos = load_user_data('todo.json')
    if 0 <= index < len(todos):
        todos[index]['done'] = not todos[index]['done']
        save_user_data('todo.json', todos)
    return redirect(url_for('index'))

@app.route('/todo/delete/<int:index>')
@login_required
def delete_todo(index):
    todos = load_user_data('todo.json')
    if 0 <= index < len(todos):
        todos.pop(index)
        save_user_data('todo.json', todos)
    return redirect(url_for('index'))
