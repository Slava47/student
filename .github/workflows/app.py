from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# Функция для создания списка дат с 1 сентября текущего года до сегодня
def generate_date_options():
    start_date = datetime(datetime.now().year, 9, 1)
    today = datetime.now()
    dates = []
    while start_date <= today:
        dates.append(start_date.strftime("%d.%m.%Y"))
        start_date += timedelta(days=1)
    return dates

date_options = generate_date_options()

# Создаем или подключаемся к базе данных
def init_db():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS students (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS attendance (
                        id INTEGER PRIMARY KEY,
                        student_id INTEGER,
                        date TEXT,
                        missed_hours INTEGER,
                        reason TEXT,
                        FOREIGN KEY(student_id) REFERENCES students(id))''')
    conn.commit()
    conn.close()

init_db()

# Главная страница с интерфейсом
@app.route("/")
def index():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students")
    students = cursor.fetchall()
    cursor.execute('''SELECT students.name, attendance.date, attendance.missed_hours, attendance.reason
                      FROM attendance
                      JOIN students ON attendance.student_id = students.id
                      ORDER BY attendance.date DESC''')
    attendance_records = cursor.fetchall()
    conn.close()
    return render_template("index.html", students=students, attendance_records=attendance_records, date_options=date_options)

# Маршрут для добавления студента
@app.route("/add_student", methods=["POST"])
def add_student():
    name = request.form.get("name")
    if name:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))

# Маршрут для редактирования студента
@app.route("/edit_student/<int:student_id>", methods=["POST"])
def edit_student(student_id):
    new_name = request.form.get("new_name")
    if new_name:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("UPDATE students SET name = ? WHERE id = ?", (new_name, student_id))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))

# Маршрут для удаления студента
@app.route("/delete_student/<int:student_id>", methods=["POST"])
def delete_student(student_id):
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))

# Маршрут для отметки пропуска по дате с причиной опоздания
@app.route("/mark_absent", methods=["POST"])
def mark_absent():
    student_id = request.form.get("student_id")
    date = request.form.get("date")
    hours = request.form.get("hours")
    reason = request.form.get("reason")
    if student_id and date and hours.isdigit():
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM attendance WHERE student_id = ? AND date = ?", (student_id, date))
        record = cursor.fetchone()
        if record:
            cursor.execute("UPDATE attendance SET missed_hours = ?, reason = ? WHERE id = ?", (hours, reason, record[0]))
        else:
            cursor.execute("INSERT INTO attendance (student_id, date, missed_hours, reason) VALUES (?, ?, ?, ?)",
                           (student_id, date, int(hours), reason))
        conn.commit()
        conn.close()
    return redirect(url_for("index"))

# Маршрут для экспорта данных в CSV
@app.route("/export_csv")
def export_csv():
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    cursor.execute('''SELECT students.name AS StudentName, attendance.date AS Date, attendance.missed_hours AS MissedHours, attendance.reason AS Reason 
                      FROM attendance 
                      JOIN students ON attendance.student_id = students.id''')
    
    records = cursor.fetchall()
    conn.close()
    
    if records:
        df = pd.DataFrame(records, columns=["StudentName", "Date", "MissedHours", "Reason"])
        df.to_csv('attendance_report.csv', index=False)
        return jsonify({"message": "Данные успешно экспортированы в 'attendance_report.csv'."})
    else:
        return jsonify({"message": "Нет данных для экспорта."})

if __name__ == "__main__":
    app.run(debug=True)
