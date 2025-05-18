from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Define base directory
basedir = os.path.abspath(os.path.dirname(__file__))

# Upload folders
UPLOAD_FOLDER = os.path.join(basedir, 'static', 'uploads')
COVER_FOLDER = os.path.join(basedir, 'static', 'cover')
INSTANCE_FOLDER = os.path.join(basedir, 'instance')

# Create necessary folders
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(COVER_FOLDER, exist_ok=True)
os.makedirs(INSTANCE_FOLDER, exist_ok=True)

# File type whitelist
ALLOWED_EXTENSIONS = {
    'mp4', 'mov', 'avi',
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic',
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Admin login credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234'

# Database configuration
db_path = os.path.join(INSTANCE_FOLDER, 'site.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database models
class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    mobile = db.Column(db.String(15), nullable=False)

class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
    text = db.Column(db.Text, nullable=False)

# Create database tables if not exist
with app.app_context():
    print("Creating database tables if not exist...")
    db.create_all()
    print("Database tables created.")

# Cover photo load
COVER_PHOTO = None
cover_path = os.path.join(COVER_FOLDER, 'cover.jpg')
if os.path.exists(cover_path):
    COVER_PHOTO = 'cover/cover.jpg'

# -------------------- Routes --------------------

@app.route('/')
def home():
    files = os.listdir(UPLOAD_FOLDER)
    global COVER_PHOTO
    return render_template('index.html', files=files, cover_photo=COVER_PHOTO)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            flash("Admin successfully logged in.", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("தவறான Username அல்லது Password!", "danger")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

@app.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        flash("Admin login required!", "warning")
        return redirect(url_for('login'))
    files = os.listdir(UPLOAD_FOLDER)
    requests = Request.query.all()
    return render_template('admin.html', files=files, requests=requests, cover_photo=COVER_PHOTO)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('admin_logged_in'):
        flash("Admin login required!", "warning")
        return redirect(url_for('login'))
    if request.method == 'POST':
        file = request.files.get('file')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            flash("கோப்பு வெற்றிகரமாக அப்லோட் செய்யப்பட்டது!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("அனுமதிக்கப்படாத கோப்பு வகை!", "danger")
    return render_template('upload.html')

@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if not session.get('admin_logged_in'):
        flash("Admin login required!", "warning")
        return redirect(url_for('login'))
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"{filename} நீக்கப்பட்டது.", "success")
    else:
        flash("கோப்பு இல்லை!", "danger")
    return redirect(url_for('admin_dashboard'))

@app.route('/upload_cover', methods=['GET', 'POST'])
def upload_cover():
    if not session.get('admin_logged_in'):
        flash("Admin login required!", "warning")
        return redirect(url_for('login'))
    global COVER_PHOTO
    if request.method == 'POST':
        file = request.files.get('cover_photo')
        if file and allowed_file(file.filename):
            filename = 'cover.jpg'
            file.save(os.path.join(COVER_FOLDER, filename))
            COVER_PHOTO = 'cover/cover.jpg'
            flash("Cover photo மாற்றப்பட்டது!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("அனுமதிக்கப்படாத கோப்பு வகை!", "danger")
    return render_template('upload_cover.html')

@app.route('/customer-register', methods=['GET', 'POST'])
def customer_register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        mobile = request.form['mobile']
        files = request.files.getlist('files')

        if Customer.query.filter_by(username=username).first():
            flash("இந்த username ஏற்கனவே உள்ளது.", "danger")
        else:
            new_user = Customer(username=username, password=password, mobile=mobile)
            db.session.add(new_user)
            db.session.commit()

            for file in files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file.save(os.path.join(UPLOAD_FOLDER, filename))

            flash("பதிவு வெற்றிகரமாக முடிந்தது. இப்போது login செய்யவும்.", "success")
            return redirect(url_for('customer_login'))
    return render_template('customer_register.html')

@app.route('/customer-login', methods=['GET', 'POST'])
def customer_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = Customer.query.filter_by(username=username, password=password).first()
        if user:
            session['customer_logged_in'] = True
            session['customer_id'] = user.id
            session['customer_username'] = user.username
            flash("வாழ்த்துக்கள்! உள்நுழைந்தது.", "success")
            return redirect(url_for('customer_requests'))
        else:
            flash("தவறான Username அல்லது Password!", "danger")
    return render_template('customer_login.html')

@app.route('/customer-logout')
def customer_logout():
    session.pop('customer_logged_in', None)
    session.pop('customer_id', None)
    session.pop('customer_username', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('home'))

@app.route('/requests', methods=['GET', 'POST'])
def customer_requests():
    if not session.get('customer_logged_in'):
        flash("Customer login required!", "warning")
        return redirect(url_for('customer_login'))
    if request.method == 'POST':
        text = request.form['request_text']
        new_request = Request(customer_id=session['customer_id'], text=text)
        db.session.add(new_request)
        db.session.commit()
        flash("கோரிக்கை சமர்ப்பிக்கப்பட்டது!", "success")
    requests = Request.query.filter_by(customer_id=session['customer_id']).all()
    return render_template('requests.html', requests=requests)

if __name__ == "__main__":
    app.run(debug=True)
