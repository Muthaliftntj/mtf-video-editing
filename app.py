# Reporter-Driven News Upload System (Flask)

from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Folders
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
COVER_FOLDER = os.path.join(basedir, 'static', 'cover')
INSTANCE_FOLDER = os.path.join(basedir, 'instance')

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COVER_FOLDER, exist_ok=True)
os.makedirs(INSTANCE_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'mp4', 'mov', 'avi'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(INSTANCE_FOLDER, 'site.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- Database Models ----------------
class Reporter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)
    is_approved = db.Column(db.Boolean, default=False)
    news = db.relationship('News', backref='reporter', lazy=True)  # Relationship to News

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')
    reporter_id = db.Column(db.Integer, db.ForeignKey('reporter.id'), nullable=False)
    filename = db.Column(db.String(200))
    approved = db.Column(db.Boolean, default=False)

# ---------------- Initial Setup ----------------
with app.app_context():
    db.create_all()

# ---------------- Routes ----------------
@app.route('/')
def home():
    news_items = News.query.filter_by(approved=True).all()
    return render_template('index.html', news_items=news_items)

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == '1234':
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("\u0ba4\u0bb5\u0bb1\u0bbe\u0ba9\u0bcd Admin \u0ba4\u0b95\u0bb5\u0bb2\u0bcd", "danger")
    return render_template('admin/login.html')

@app.route('/admin-dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))

    news_list = News.query.all()
    pending_reporters = Reporter.query.filter_by(is_approved=False).all()

    return render_template(
        'admin/dashboard.html',
        news_list=news_list,
        pending_reporters=pending_reporters
    )

@app.route('/approve/<int:news_id>')
def approve_news(news_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    news = News.query.get(news_id)
    news.approved = True
    db.session.commit()
    flash("\u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bbf \u0b92\u0baa\u0bcd\u0baa\u0bc1\u0ba4\u0bb2\u0bcd \u0baa\u0bc6\u0bb1\u0bcd\u0bb1\u0ba4\u0bc1", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/delete/<int:news_id>')
def delete_news(news_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    news = News.query.get(news_id)
    db.session.delete(news)
    db.session.commit()
    flash("\u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bbf \u0ba8\u0bc0\u0b95\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/edit/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    news = News.query.get(news_id)
    if request.method == 'POST':
        news.title = request.form['title']
        news.content = request.form['content']
        db.session.commit()
        flash("\u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bbf \u0ba4\u0bbf\u0bb0\u0bc1\u0ba4\u0bcd\u0ba4\u0baa\u0bcd\u0baa\u0b9f\u0bc1", "success")
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_news.html', news=news)

@app.route('/news/<int:news_id>')
def view_news(news_id):
    news = News.query.get_or_404(news_id)
    return render_template('view_news.html', news=news)

@app.route('/approve-reporter/<int:reporter_id>')
def approve_reporter(reporter_id):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    reporter = Reporter.query.get(reporter_id)
    reporter.is_approved = True
    db.session.commit()
    flash("\u0ba8\u0bbf\u0bb0\u0bc1\u0baa\u0bb0\u0bcd \u0b92\u0baa\u0bcd\u0baa\u0bc1\u0ba4\u0bb2\u0bcd \u0baa\u0bc6\u0bb1\u0bcd\u0bb1\u0bbe\u0bb0\u0bcd", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/reporter-register', methods=['GET', 'POST'])
def reporter_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mobile = request.form['mobile']
        if Reporter.query.filter_by(username=username).first():
            flash("Username \u0b8f\u0bb1\u0bcd\u0b95\u0ba3\u0bc7\u0bb5\u0bc7 \u0b89\u0bb3\u0bcd\u0bb3\u0ba4\u0bc1", "danger")
        else:
            db.session.add(Reporter(username=username, password=password, mobile=mobile))
            db.session.commit()
            flash("\u0baa\u0ba4\u0bbf\u0bb5\u0bc1 \u0bb5\u0bc6\u0bb1\u0bcd\u0bb1\u0bbf\u0b95\u0bb0\u0bae\u0bbe\u0b95 \u0bae\u0bc1\u0b9f\u0bbf\u0ba8\u0bcd\u0ba4\u0ba4\u0bc1! Admin \u0b92\u0baa\u0bcd\u0baa\u0bc1\u0ba4\u0bb2\u0bcd \u0b95\u0bbf\u0b9f\u0bc8\u0b95 \u0bb5\u0bc6\u0ba3\u0bcd\u0b9f\u0bc1\u0bae\u0bcd.", "success")
            return redirect(url_for('reporter_login'))
    return render_template('reporter/register.html')

@app.route('/reporter-login', methods=['GET', 'POST'])
def reporter_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Reporter.query.filter_by(username=username, password=password).first()
        if user:
            if not user.is_approved:
                flash("Admin Approval \u0ba8\u0bbf\u0bb2\u0bc1\u0bb5\u0bc8\u0baf\u0bc7\u0bb1\u0bcd\u0bb1\u0bc1\u0bb2\u0bcd\u0bb3\u0ba4\u0bc1", "warning")
                return redirect(url_for('reporter_login'))
            session['reporter'] = user.id
            return redirect(url_for('submit_news'))
        flash("\u0ba4\u0bb5\u0bb1\u0bbe\u0ba9 Username/Password", "danger")
    return render_template('reporter/login.html')

@app.route('/submit-news', methods=['GET', 'POST'])
def submit_news():
    if 'reporter' not in session:
        return redirect(url_for('reporter_login'))
    reporter = Reporter.query.get(session['reporter'])
    if not reporter.is_approved:
        flash("Admin Approval \u0baa\u0bc6\u0bb1 \u0b95\u0bc7\u0b9f\u0bc1\u0bae\u0bcd.", "warning")
        return redirect(url_for('reporter_login'))
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        file = request.files.get('file')
        filename = None
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
        news = News(title=title, content=content, reporter_id=session['reporter'], filename=filename)
        db.session.add(news)
        db.session.commit()
        flash("\u0b9a\u0bc6\u0baf\u0bcd\u0ba4\u0bbf \u0b9a\u0bae\u0bb0\u0bcd\u0baa\u0bcd\u0baa\u0bbf\u0ba9\u0bcd\u0baa\u0baa\u0bcd\u0baa\u0b9f\u0bc1! Admin \u0b92\u0baa\u0bcd\u0baa\u0bc1\u0ba4\u0bb2\u0bcd \u0baa\u0bbf\u0bb1\u0b95\u0bc1 \u0bb5\u0bc6\u0bb3\u0bbf\u0baf\u0bbf\u0b9f\u0baa\u0bcd\u0baa\u0b9f\u0bc1\u0bae\u0bcd.", "success")
        return redirect(url_for('submit_news'))
    return render_template('reporter/submit_news.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("\u0bb5\u0bc6\u0bb3\u0bbf\u0baf\u0bc7\u0bb1\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0bc1", "info")
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
