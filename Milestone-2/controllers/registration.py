from flask_wtf import Form
from wtforms import TextField,PasswordField, IntegerField, TextAreaField, RadioField, SubmitField  # type: ignore
from wtforms.validators import ValidationError, DataRequired 
class Registration(Form):
    name=TextField(label="Username", validators=[DataRequired ()])
    passWord=PasswordField(label="Password", validators=[DataRequired ()]) 
    phoneNumber=IntegerField(label="Enter mobile number",validators=[DataRequired()])
    gender=RadioField(label= 'Gender', choices=[ 'Male', 'Female'])  # type: ignore
    address=TextAreaField(label="Address")
    age=IntegerField(label="Age")
    submit=SubmitField("Send" )