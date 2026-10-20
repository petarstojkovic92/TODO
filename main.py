from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

app.config['SECRET_KEY'] = '7T5mfTf<5<s#P&cm&<YyT65[8iIaHj20|&K&!gA@$=G'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    tasks = db.relationship('Todo', backref='author', lazy=True, cascade='all, delete-orphan')

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    due_date = db.Column(db.Date)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exist!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('You have successfully registered!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Successfully login', 'success')
            return redirect(url_for('show_tasks'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@app.route('/', methods=['GET', 'POST'])
@login_required
def create_task():
    if request.method == 'POST':
        title = request.form['title']
        new_task = Todo(title=title, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('show_tasks'))
    return render_template('index.html')

@app.route('/task', methods=['GET', 'POST'])
@login_required
def show_tasks():
    if request.method == 'POST':
        title = request.form['title']
        new_task = Todo(title=title, user_id=current_user.id)
        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('show_tasks'))

    edit_id = request.args.get('edit_id', type=int)
    tasks = Todo.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=tasks, edit_id=edit_id)

@app.route('/<int:task_id>/delete', methods=['GET', 'POST'])
@login_required
def delete(task_id):
    task = Todo.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('You cannot delete this task!', 'danger')
        return redirect(url_for('show_tasks'))

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('show_tasks'))

@app.route('/<int:task_id>/update', methods=['GET', 'POST'])
@login_required
def update(task_id):
    task = Todo.query.get_or_404(task_id)

    if task.user_id != current_user.id:
        flash('You cannot update this task!', 'danger')
        return redirect(url_for('show_tasks'))

    if request.method == 'POST':
        title = request.form['title']
        due_date_str = request.form.get('due_date')
        due_date = None
        if due_date_str:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
        task.title = title
        task.due_date = due_date
        db.session.commit()
        return redirect(url_for('show_tasks'))
    return redirect(url_for('show_tasks', edit_id=task.id))

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
