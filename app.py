from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import os
import uuid
from werkzeug.utils import secure_filename
from ai_traffic import TrafficAnalyzer
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'traffic_management_secret_key_2024'

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# Initialize traffic analyzer
traffic_analyzer = TrafficAnalyzer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Simple authentication (in production, use proper authentication)
        if username == 'admin' and password == 'admin123':
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials!')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out!')
    return redirect(url_for('index'))

@app.route('/upload')
def upload():
    # Protect upload route - require login
    if not session.get('logged_in'):
        flash('Please login first!')
        return redirect(url_for('login'))
    return render_template('upload.html')

@app.route('/dashboard')
def dashboard():
    # Protect dashboard route - require login
    if not session.get('logged_in'):
        flash('Please login first!')
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/analysis')
def analysis():
    return render_template('analysis.html')

@app.route('/upload_video', methods=['POST'])
def upload_video():
    if 'video' not in request.files:
        flash('No video file selected')
        return redirect(url_for('upload'))
    
    file = request.files['video']
    if file.filename == '':
        flash('No video file selected')
        return redirect(url_for('upload'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        
        flash('Video uploaded successfully!')
        return redirect(url_for('analysis', video_id=unique_filename))
    else:
        flash('Invalid file type. Please upload MP4, AVI, MOV, or MKV files.')
        return redirect(url_for('upload'))

@app.route('/analyze_traffic/<video_id>')
def analyze_traffic(video_id):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
    
    if not os.path.exists(video_path):
        flash('Video not found')
        return redirect(url_for('upload'))
    
    try:
        # Analyze traffic using AI
        results = traffic_analyzer.analyze_video(video_path)
        
        return render_template('result.html', 
                             video_id=video_id,
                             results=results)
    except Exception as e:
        flash(f'Error analyzing video: {str(e)}')
        return redirect(url_for('upload'))

@app.route('/api/traffic_analysis/<video_id>')
def api_traffic_analysis(video_id):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], video_id)
    
    if not os.path.exists(video_path):
        return jsonify({'error': 'Video not found'}), 404
    
    try:
        results = traffic_analyzer.analyze_video(video_path)
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/live_analysis')
def live_analysis():
    # Simulate live traffic data
    import random
    lanes = ['Lane 1', 'Lane 2', 'Lane 3', 'Lane 4']
    
    live_data = {
        'timestamp': str(datetime.now()),
        'lanes': []
    }
    
    for lane in lanes:
        lane_data = {
            'name': lane,
            'vehicle_count': random.randint(5, 25),
            'avg_speed': random.uniform(20, 60),
            'density': random.choice(['Low', 'Medium', 'High']),
            'signal_status': random.choice(['Red', 'Yellow', 'Green'])
        }
        live_data['lanes'].append(lane_data)
    
    return jsonify(live_data)

if __name__ == '__main__':
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
