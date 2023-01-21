from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Initialize Database
with app.app_context():
    class toDoList(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        task = db.Column(db.String(250), nullable=False)
        priority = db.Column(db.Boolean)
        complete = db.Column(db.Boolean)

        def __repr__(self):
            return f"{self.task}" 
   
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        user = db.Column(db.String(50), unique=True)
        password = db.Column(db.String(50))

        def __repr__(self):
            return f"{self.user}" 

    db.create_all()

#Initial conditions
to_do_list = []
signed_in = False
current_user = None

#Get Motivational Quotes
quote_url = "https://zenquotes.io/api/random/[your_key]"

def get_quote():
    response = requests.get(url=quote_url)
    response.raise_for_status()
    quote = response.json()
    return quote

#Website Functions
@app.route('/')
def home():
    if signed_in == False:
        return redirect(url_for('sign_in_page'))
    to_do_list = db.session.query(toDoList).filter_by(user_id=current_user).all()
    name = db.session.query(User).filter_by(id=current_user).first().user
    return render_template('index.html', to_do_list = to_do_list, quote=get_quote(), signed_in=signed_in, user=name)

@app.route('/sign_in_page')
def sign_in_page():
    return render_template('sign-in.html', signed_in=signed_in, no_user=False, incorrect=False)

@app.route('/sign_in', methods=['POST'])
def sign_in():
    global signed_in, current_user
    action = request.form['action']
    username = request.form['user']
    password = request.form['password']
    check_user = db.session.query(User).filter_by(user=username).first()
    if action == 'in':
        if check_user is None:
            return render_template('sign-in.html', no_user=True)
        if check_user is not None and check_user.password != password:
            return render_template('sign-in.html', incorrect=True)
        signed_in = True
        current_user = check_user.id
        return redirect(url_for('home'))
    if action == 'up':
        return redirect(url_for('sign_up_page'))

@app.route('/sign_up_page')
def sign_up_page():
    match = True
    empty = False
    exists = False
    return render_template('sign-up.html', match=match, empty=empty, exists=exists)

@app.route('/sign_up', methods=["POST"])
def sign_up():
    global signed_in, current_user
    pw = request.form['password']
    cpw = request.form['confirm_password']
    username = request.form['user']
    check_user = db.session.query(User).filter_by(user=username).first()
    if check_user is not None:
        exists = True
        return render_template('sign-up.html', exists=exists)
    if username == "" or pw == "":
        empty = True
        return render_template('sign-up.html', empty=empty)
    if pw != cpw:
        match = False
        return render_template('sign-up.html', match=match)
    if pw == cpw:
        signed_in = True
        new_user = User(
            user = request.form['user'],
            password = request.form['password']
        )
        db.session.add(new_user)
        db.session.commit()
        for row in db.session.query(User).filter_by(user=username):
            current_user = row.id
        return redirect((url_for('home')))

@app.route('/sign_out', methods=["POST"])
def sign_out():
    global signed_in, current_user
    signed_in = False
    current_user = None
    return redirect(url_for('sign_in_page'))

@app.route('/add', methods=['POST'])
def add():
    global current_user
    if request.form['task'] == "":
        return redirect(url_for('home'))

    new_to_do = toDoList(
        task=request.form['task'],
        user_id = current_user,
        complete = False,
        priority = False
    )
    db.session.add(new_to_do)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/delete')
def delete():
    task_id = request.args.get('id')
    task_to_delete = toDoList.query.get(task_id)
    db.session.delete(task_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/prioritize')
def prioritize():
    task_id = request.args.get('id')
    task_to_prioritize = toDoList.query.get(task_id)
    task_to_prioritize.priority = True
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/complete')
def complete():
    task_id = request.args.get('id')
    task_to_complete = toDoList.query.get(task_id)
    task_to_complete.complete = True
    task_to_complete.priority = False
    db.session.commit()
    return redirect(url_for('home'))

@app.route('/do_later')
def do_later():
    task_id = request.args.get('id')
    task_to_complete = toDoList.query.get(task_id)
    task_to_complete.complete = False
    task_to_complete.priority = False
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)