import mysql.connector
from mysql.connector import Error
import face_recognition
import cv2
import numpy as np
from datetime import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Function to create a connection to the MySQL database
def create_connection():
    try:
        conn = mysql.connector.connect(
            host='localhost',
            database='attendance_system',
            user='root',
            password='gruhit@2004'
        )
        return conn
    except Error as e:
        print(e)

# Function to create a table
def create_table(conn):
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS students (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), roll_no INT, date_time DATETIME)")
        cursor.close()  # Close the cursor when done
    except Error as e:
        print(e)

# ... Add your face recognition and known face data here ...

gruhit_image = face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\gruhit.jpg")
gruhit_encoding=face_recognition.face_encodings(gruhit_image)[0]

kushal_image=face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\kushal.jpg")
kushal_encoding=face_recognition.face_encodings(kushal_image)[0]

himanshu_image=face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\himanshu.jpg")
himanshu_encoding=face_recognition.face_encodings(himanshu_image)[0]

sanjay_image=face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\sanjay.jpg")
sanjay_encoding=face_recognition.face_encodings(sanjay_image)[0]

abhishek_image=face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\abhishek.jpg")
abhishek_encoding=face_recognition.face_encodings(abhishek_image)[0]

akul_image=face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\akul.jpg")
akul_encoding=face_recognition.face_encodings(akul_image)[0]

vanshika_image=face_recognition.load_image_file("C:\\Users\\gdk14\\Desktop\\app project\\images\\vanshika.jpg")
vanshika_encoding=face_recognition.face_encodings(vanshika_image)[0]





known_face_encoding=[
    gruhit_encoding,
    kushal_encoding,
    himanshu_encoding,
    sanjay_encoding,
    abhishek_encoding,
    akul_encoding,
    vanshika_encoding
]
known_faces_names=[
    "Gruhit",
    "Kushal",
    "Himanshu",
    "Sanjay",
    "Abhishek",
    "Akul",
    "Vanshika"
]
students=known_faces_names.copy()

# Add roll numbers for each student
known_faces_roll_nos = [41,7,19,14,66,29,21,27]

face_locations=[]
face_encodings=[]
face_names=[]
s=True
# Create an empty list to store the names of recognized students
recognized_students = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture')
def capture():
    return render_template('capture.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    global recognized_students
    video_capture = cv2.VideoCapture(0)
    s = True

    while s:
        _, frame = video_capture.read()
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = small_frame[:, :, ::-1]

        if s:
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encoding, face_encoding)
                name = ""
                roll_no = 0
                face_distance = face_recognition.face_distance(known_face_encoding, face_encoding)
                best_match_index = np.argmin(face_distance)

                if matches[best_match_index]:
                    name = known_faces_names[best_match_index]
                    roll_no = known_faces_roll_nos[best_match_index]

                    if name not in recognized_students:
                        date_time = datetime.now()
                        entities = (name, roll_no, date_time)
                        insert_values(conn, entities)
                        recognized_students.append(name)

                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

        cv2.imshow("attendance system", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            s = False

    video_capture.release()
    cv2.destroyAllWindows()

    return jsonify({'message': 'Attendance recorded successfully'})

def insert_values(conn, values):
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO students (name, roll_no, date_time) VALUES (%s, %s, %s)", values)
        conn.commit()
        cursor.close()
    except Error as e:
        print(e)

def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='gruhit@2004',
        database='attendance_system'
    )
    return conn
def get_teacher_data():
    conn = get_db_connection()
    if conn is None:
        return {'present': [], 'absent': []}

    cursor = conn.cursor()

    # Fetch the list of all students from the "student" table
    cursor.execute("SELECT roll_no, name FROM student")
    all_students = cursor.fetchall()

    # Fetch the list of students who are marked as present in the "students" table
    cursor.execute("SELECT DISTINCT roll_no FROM students")
    present_students_roll_numbers = [result[0] for result in cursor.fetchall()]

    cursor.close()
    conn.close()

    present_students_data = [{'roll_no': student[0], 'name': student[1]} for student in all_students if student[0] in present_students_roll_numbers]
    absent_students_data = [{'roll_no': student[0], 'name': student[1]} for student in all_students if student[0] not in present_students_roll_numbers]

    return {'present': present_students_data, 'absent': absent_students_data}


@app.route('/view_attendance', methods=['GET', 'POST'])
def view_attendance():
    if request.method == 'POST':
        role = request.form.get('role')
        if role == 'teacher':
            teacher_data = get_teacher_data()
            return render_template('teacher_attendance.html', present_students=teacher_data['present'], absent_students=teacher_data['absent'])
        elif role == 'student':
            roll_no = request.form.get('roll_no')
            if roll_no:
                return render_template('attendance_student.html', roll_no=roll_no, status=get_student_data(roll_no))
            else:
                return render_template('attendance_student.html')
        else:
            return render_template('index.html')
    elif request.method == 'GET':
        return render_template('role_selection.html')

def get_student_data(roll_no):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM students WHERE roll_no = {roll_no}")
    result = cursor.fetchone()
    cursor.close()

    return 'Present' if result else 'Absent'

if __name__ == '__main__':
    conn = create_connection()  # Create a connection to the database
    create_table(conn)  # Create the table if it doesn't exist
    app.run(debug=True)
