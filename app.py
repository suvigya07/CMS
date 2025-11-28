from flask import Flask, render_template, request, redirect, url_for, session, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here_change_in_production'

# Helper functions to load data
def load_json(filename):
    filepath = os.path.join('data', filename)
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_json(filename, data):
    filepath = os.path.join('data', filename)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user_type = request.form.get('user_type')
        
        data = load_json('students.json')
        
        if user_type == 'student':
            for student in data.get('students', []):
                if student['email'] == email and student['password'] == password:
                    session['user_id'] = student['id']
                    session['user_name'] = student['name']
                    session['user_type'] = 'student'
                    return redirect(url_for('student_dashboard'))
            flash('Invalid credentials!', 'error')
        
        elif user_type == 'teacher':
            for teacher in data.get('teachers', []):
                if teacher['email'] == email and teacher['password'] == password:
                    session['user_id'] = teacher['id']
                    session['user_name'] = teacher['name']
                    session['user_type'] = 'teacher'
                    return redirect(url_for('teacher_dashboard'))
            flash('Invalid credentials!', 'error')
    
    return render_template('login.html')

@app.route('/student/dashboard')
def student_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'student':
        return redirect(url_for('login'))
    
    student_id = session['user_id']
    
    # Get student details
    students_data = load_json('students.json')
    student = next((s for s in students_data.get('students', []) if s['id'] == student_id), None)
    
    # Get marks
    marks_data = load_json('marks.json')
    marks = next((m for m in marks_data.get('marks', []) if m['student_id'] == student_id), None)
    
    # Get attendance
    attendance_data = load_json('attendance.json')
    attendance = next((a for a in attendance_data.get('attendance', []) if a['student_id'] == student_id), None)
    
    return render_template('student_dashboard.html', 
                         student=student, 
                         marks=marks, 
                         attendance=attendance)

@app.route('/teacher/dashboard')
def teacher_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'teacher':
        return redirect(url_for('login'))
    
    # Get all students
    students_data = load_json('students.json')
    students = students_data.get('students', [])
    
    # Get all attendance
    attendance_data = load_json('attendance.json')
    
    # Get all marks
    marks_data = load_json('marks.json')
    
    return render_template('teacher_dashboard.html', 
                         students=students,
                         attendance_data=attendance_data,
                         marks_data=marks_data)

@app.route('/teacher/mark_attendance', methods=['POST'])
def mark_attendance():
    if 'user_id' not in session or session.get('user_type') != 'teacher':
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id')
    status = request.form.get('status')  # 'present' or 'absent'
    
    attendance_data = load_json('attendance.json')
    
    for record in attendance_data.get('attendance', []):
        if record['student_id'] == student_id:
            record['total_classes'] += 1
            if status == 'present':
                record['attended'] += 1
            record['percentage'] = round((record['attended'] / record['total_classes']) * 100, 2)
            break
    
    save_json('attendance.json', attendance_data)
    flash('Attendance marked successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/teacher/update_marks', methods=['POST'])
def update_marks():
    if 'user_id' not in session or session.get('user_type') != 'teacher':
        return redirect(url_for('login'))
    
    student_id = request.form.get('student_id')
    subject = request.form.get('subject')
    marks = int(request.form.get('marks'))
    
    marks_data = load_json('marks.json')
    
    for record in marks_data.get('marks', []):
        if record['student_id'] == student_id:
            record['subjects'][subject] = marks
            break
    
    save_json('marks.json', marks_data)
    flash('Marks updated successfully!', 'success')
    return redirect(url_for('teacher_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, port=5000)