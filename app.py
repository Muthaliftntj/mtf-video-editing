from flask import Flask, render_template, request, redirect, url_for, session
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Admin credentials
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234'

# Allowed file types
ALLOWED_EXTENSIONS = {
    'mp4', 'mov', 'avi',                # videos
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'heic',  # images
    'pdf', 'doc', 'docx', 'ppt', 'pptx', 'txt'     # documents
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    files = os.listdir(UPLOAD_FOLDER)
    return render_template('index.html', files=files)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == ADMIN_USERNAME and request.form['password'] == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('upload'))
        else:
            return "தவறான Username அல்லது Password!"
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)
            return redirect(url_for('home'))
        else:
            return "அனுமதிக்கப்படாத கோப்பு வகை!"
    return render_template('upload.html')

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect(url_for('home'))

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)
