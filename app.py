from flask import Flask, redirect, url_for, request, session, flash, render_template, abort
from urllib.parse import quote_plus, urlencode
from flask_migrate import Migrate
import datetime
from dotenv import load_dotenv
from functools import wraps
from authlib.integrations.flask_client import OAuth
import asyncio
import os
from models import db, Employee, Department

from permit import Permit

app = Flask(__name__)

load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///company.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
migrate = Migrate(app, db)

oauth = OAuth(app)
oauth.register(
    "oauth",
    client_id=os.getenv("AUTH0_CLIENT_ID"),
    client_secret=os.getenv("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{os.getenv("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# Intialize the Permit SDK
permit = Permit(
    pdp="http://localhost:7766",
    token=os.getenv("PDP_API_KEY"),
)

# Policy enforcement point
def check_permission(resource, action_name, context=None):
    def decorator(f):
        @wraps(f)
        async def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user or "userinfo" not in user:
                abort(401, description="Unauthorized: User not logged in")

            user_email = user['userinfo']['email']

            result = await permit.check(
                user=user_email,
                resource=resource,
                action=action_name,
                context=context 
            )

            if not result:
                abort(403, description="Access denied")

            return f(*args, **kwargs)
        return wrapped
    return decorator


# Sync users and assign roles
@app.route('/login/callback')
def callback():
    token = oauth.oauth.authorize_access_token()
    session["user"] = token

    user_email = token["userinfo"]["email"]
    async def sync_and_assign():
        await permit.api.users.sync({
            "key": user_email,
            "email": user_email,
        })

        await permit.api.users.assign_role(
            {
                "user": user_email,
                "role": "administrator",
                "tenant": "default",
            }
        )

    asyncio.run(sync_and_assign())
    return redirect(url_for('homepage'))

@app.route('/login')
def login():
    if "user" in session:
        abort(404)
    return oauth.oauth.authorize_redirect(redirect_uri=url_for('callback', _external=True))


@app.route('/logout')
def logout():
    """
    Logs the user out of the session and from the Auth0 tenant
    """
    session.clear()
    return redirect(
        "https://" + os.getenv("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("homepage", _external=True),
                "client_id": os.getenv("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route('/')
def homepage():
    if "user" not in session:
        return redirect(url_for('login'))
    departments = Department.query.all()
    return render_template('homepage.html', departments=departments)


# Add permission checks

@app.route('/add_department', methods=['GET', 'POST'])
@check_permission(resource="departments", action_name="create_department")
def add_department():
    if request.method == 'POST':
        name = request.form['name']
        new_department = Department(name=name)
        db.session.add(new_department)
        db.session.commit()
        flash('Department added successfully!')
        return redirect(url_for('homepage'))
    return render_template('add_department.html')


@app.route('/department/<int:department_id>')
@check_permission(resource="departments:{department_id}", action_name="view_department")
def department(department_id):
    dept_employees = Employee.query.filter_by(department_id=department_id).all()
    return render_template('department.html', employees=dept_employees)

@app.route('/delete_department/<int:department_id>', methods=['GET', 'POST'])
@check_permission(resource="departments:{department_id}", action_name="delete_department")
def delete_department(department_id):
    department = Department.query.get(department_id)
    if department:
        Employee.query.filter_by(department_id=department_id).delete()
        db.session.delete(department)
        db.session.commit()
        flash('Department and all related employees deleted successfully!')
    else:
        flash('Department not found!')
    return redirect(url_for('homepage'))

@app.route('/update_department/<int:department_id>', methods=['GET', 'POST'])
@check_permission(resource="departments:{department_id}", action_name="update_department")
def update_department(department_id):
    department = Department.query.get(department_id)
    if request.method == 'POST':
        new_name = request.form['name']
        department.name = new_name
        db.session.commit()
        flash('Department updated successfully!')
        return redirect(url_for('homepage'))
    return render_template('update_department.html', department=department)


# Employees

@app.route('/add_employee', methods=['GET', 'POST'])
@check_permission(resource="employees", action_name="create_employee")
def add_employee():
    if request.method == 'POST':
        username = request.form['username']
        name = request.form['name']
        gender = request.form['gender']
        location = request.form['location']
        start_year = int(request.form['start_year'])
        hobbies = request.form['hobbies']
        department_id = int(request.form['department_id'])
        position = request.form['position']

        new_employee = Employee(
            username=username,
            name=name,
            gender=gender,
            position=position,
            location=location,
            start_year=start_year,
            hobbies=hobbies,
            department_id=department_id
        )

        db.session.add(new_employee)
        db.session.commit()
        flash("Employee added successfully.")
        return redirect(url_for('department', department_id=department_id))

    current_year = datetime.datetime.now().year
    departments = Department.query.all()
    return render_template('add_employee.html', current_year=current_year, departments=departments)


@app.route('/employee/<int:employee_id>')
@check_permission(resource="employees:{employee_id}", action_name="view_employee")
def employee(employee_id):
    emp = Employee.query.get(employee_id)
    return render_template('employee.html', employee=emp)

@app.route('/update_employee/<int:employee_id>', methods=['GET', 'POST'])
@check_permission(resource="employees:{employee_id}", action_name="update_employee")
def update_employee(employee_id):
    employee = Employee.query.get(employee_id)
    current_year = datetime.datetime.now().year
    if request.method == 'POST':
        employee.name = request.form['name']
        employee.gender = request.form['gender']
        employee.location = request.form['location']
        employee.start_year = request.form['start_year']
        employee.hobbies = request.form['hobbies']
        db.session.commit()
        flash('Employee updated successfully!')
        return redirect(url_for('department', department_id=employee.department_id))
    return render_template('update_employee.html', employee=employee, current_year=current_year)


@app.route('/delete_employee/<int:employee_id>', methods=['GET', 'POST'])
@check_permission(resource="employees:{employee_id}", action_name="delete_employee")
def delete_employee(employee_id):
    employee = Employee.query.get(employee_id)
    if employee:
        db.session.delete(employee)
        db.session.commit()
        flash('Employee deleted successfully!')
    else:
        flash('Employee not found!')
    return redirect(url_for('department', department_id=employee.department_id))


if __name__ == '__main__':
    app.run(debug=True)
