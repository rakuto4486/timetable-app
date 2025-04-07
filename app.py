from flask import Flask, render_template, request, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

TODO_FILE = 'todo.json'

def load_todos():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_todos(todos):
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)

todos = load_todos()

# 保存先ファイル
DATA_FILE = 'timetable.json'

# 成績データを保存するファイル
GRADES_FILE = 'grades.json'

# 📥 JSONファイルから時間割を読み込む
def load_schedule():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# JSONファイルから成績を読み込む
def load_grades():
    if os.path.exists(GRADES_FILE):
        with open(GRADES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# JSONファイルに成績を書き込む
def save_grades(data):
    with open(GRADES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

grades_data = load_grades()

# 💾 JSONファイルに時間割を保存する
def save_schedule(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# グローバル変数：アプリ全体で使う
schedule = load_schedule()

@app.route('/', methods=['GET', 'POST'])
def index():
    global todos

    # 1. 今日の曜日を取得
    weekday_map = ['月', '火', '水', '木', '金', '土', '日']
    today_weekday = weekday_map[datetime.today().weekday()]

    # 2. 今日の授業を抽出
    today_schedule = [item for item in schedule if item['day'] == today_weekday]

    # 3. 授業名ごとにToDoを紐づけ
    today_todos = []
    for subject in today_schedule:
        related_tasks = []
        for todo in todos:
            if todo.get("class_name") == subject['class_name']:
                # 日数計算
                if todo.get("due_date"):
                    days_left = (datetime.strptime(todo["due_date"], "%Y-%m-%d") - datetime.today()).days
                    todo["days_left"] = days_left
                related_tasks.append(todo)

        if related_tasks:
            today_todos.append({
                'class_name': subject['class_name'],
                'tasks': related_tasks
            })

    # 通常のToDoにも日数追加（全体表示用）
    for todo in todos:
        if todo.get("due_date"):
            days_left = (datetime.strptime(todo["due_date"], "%Y-%m-%d") - datetime.today()).days
            todo["days_left"] = days_left

    # 4. POST（ToDo追加）処理
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
            save_todos(todos)
        return redirect(url_for('index'))

    return render_template(
        'index.html',
        todos=todos,
        today_schedule=today_schedule,
        today_todos=today_todos
    )


@app.route('/schedule', methods=['GET', 'POST'])
def schedule_page():
    global schedule
    if request.method == 'POST':
        class_name = request.form['class_name']
        day = request.form['day']
        period = int(request.form['period'])
        room = request.form['room']
        teacher = request.form['teacher']

        schedule.append({
            'class_name': class_name,
            'day': day,
            'period': period,
            'room': room,
            'teacher': teacher
        })

        save_schedule(schedule)
        return redirect(url_for('schedule_page'))

    return render_template('schedule.html', schedule=schedule, grades=grades_data)  # ← ここを追加

# 🔥 削除処理もファイルに反映
@app.route('/delete/<int:index>')
def delete_schedule(index):
    global schedule
    if 0 <= index < len(schedule):
        schedule.pop(index)
        save_schedule(schedule)
    return redirect(url_for('schedule_page'))

@app.route('/grades', methods=['GET', 'POST'])
def grades_page():
    global grades_data
    if request.method == 'POST':
        class_name = request.form['class_name']
        item_names = request.form.getlist('item_name[]')
        weights = request.form.getlist('weight[]')

        items = []
        for name, w in zip(item_names, weights):
            items.append({
                'name': name,
                'weight': int(w),
                'score': None
            })

        grades_data.append({
            'class_name': class_name,
            'items': items,
            'total_score': None
        })

        save_grades(grades_data)
        return redirect(url_for('grades_page'))

    return render_template('grades.html', grades=grades_data)

@app.route('/grades/edit/<int:index>', methods=['GET', 'POST'])
def edit_grade(index):
    global grades_data

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
        save_grades(grades_data)
        return redirect(url_for('grades_page'))

    return render_template('edit_grade.html', grade=grade)

@app.route('/todo/done/<int:index>')
def mark_done(index):
    global todos
    if 0 <= index < len(todos):
        todos[index]['done'] = not todos[index]['done']
        save_todos(todos)
    return redirect(url_for('index'))

@app.route('/todo/delete/<int:index>')
def delete_todo(index):
    global todos
    if 0 <= index < len(todos):
        todos.pop(index)
        save_todos(todos)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True,host='0.0.0.0', port=5000)

