from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'


@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('home.html')

@app.route("/add", methods=['GET', 'POST'])
def add():
    return render_template('AddEmp.html')

@app.route("/delete", methods=['GET', 'POST'])
def delete():
    return render_template('DeleteEmp.html')


@app.route("/about", methods=['GET','POST'])
def about():
    return render_template('AboutUs.html')

@app.route("/get", methods=['GET', 'POST'])
def get():
    return render_template('GetEmp.html')


@app.route("/addemp", methods=['POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    payscale = request.form['payscale']
    hire_date = request.form['hire_date']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
    cursor = db_conn.cursor()

    if emp_image_file.filename == "":
        return "Please select a file"

    try:

        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, payscale, hire_date))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)


# Define the fetchdata route
@app.route('/fetchdata', methods=['POST'])
def fetchdata():
    emp_id = request.form['emp_id']
    cursor = db_conn.cursor()
    cursor.execute("SELECT * FROM employee WHERE emp_id = %s", (emp_id,))
    result = cursor.fetchone()
    cursor.close()
    if result is not None:
        emp_data = {
            'id': result[0],
            'fname': result[1],
            'lname': result[2],
            'pri_skill': result[3],
            'location': result[4],
            'payscale': result[5],
            'hiredate': result[6]
        }
        return render_template('GetEmpOutput.html', **emp_data)
    else:
        return "Employee not found"

@app.route("/deleteemp", methods=['POST'])
def DeleteEmp():
    emp_id = request.form['emp_id']
    cursor = db_conn.cursor()

    try:
        # Delete image file from S3 bucket
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')
        s3.Object(custombucket, emp_image_file_name_in_s3).delete()

        # Delete employee from database
        cursor.execute("DELETE FROM employee WHERE emp_id = %s", (emp_id,))
        db_conn.commit()

    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('DeleteEmpOutput.html', id=emp_id)
    
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)

