import json
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import bcrypt

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://admin:esdproject@database-1.cxqk0bo2fppg.ap-southeast-1.rds.amazonaws.com:3306/employee'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Employee(db.Model):
    __tablename__ = 'employee'

    username = db.Column(db.String(50), primary_key=True)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(150), nullable=False)

    def __init__(self, username, password, email):
        self.username = username
        self.set_password(password)
        self.email = email

    def set_password(self, password):
        """Securely hash the password."""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

    def check_password(self, password):
        """Check if the provided password is correct."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    def json(self):
        return {"username": self.username, "email": self.email}



@app.route("/Employee/<string:username>", methods=['POST'])
def addUser(username):
    if (Employee.query.filter_by(username=username).first()):
        return jsonify({"message": "A username with '{}' already exists.".format(username)}), 400

    data = request.get_json()
    employee = Employee(username, **data)

    try:
        db.session.add(employee)
        db.session.commit()
    except:
        return jsonify({"message": "An error occurred creating the account."}), 500

    return jsonify({"success": "Account successfully created"}), 201

@app.route("/Employee", methods=['GET'])
def get_all():
    return jsonify({"users": [employee.json() for employee in Employee.query.all()]})

#Authenticate user method
@app.route("/AEmployee/<string:username>", methods=["POST"])
def find_by_username(username):
#Getting the data
    data = request.get_json()
    #gets the password with key password in json data
    inputpassword = data["password"]
    #if user exist check pass otherwise return does not exist
    user = Employee.query.filter_by(username=username).first()
    if user and user.check_password(inputpassword):
        return jsonify({"message": "Login successful"}), 200
    else:
        return jsonify({"message": "Invalid username or password"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0',port=5001, debug=True)
