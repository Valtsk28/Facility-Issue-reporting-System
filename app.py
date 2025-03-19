import os
from flask import Flask, render_template, request, jsonify
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_key_change_in_production")

# In a real application, this would be stored securely in a database
MAINTENANCE_PASSWORD_HASH = generate_password_hash("International")
ADMIN_PASSWORD_HASH = generate_password_hash("Administrators")

# Temporary storage for reports (in a real app, this would be a database)
maintenance_reports = []

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/active-reports')
def active_reports():
    return render_template('active_reports.html', reports=maintenance_reports)

@app.route('/verify-password', methods=['POST'])
def verify_password():
    password = request.json.get('password')
    password_type = request.json.get('type', 'maintenance')
    
    if password_type == 'admin':
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            return jsonify({"success": True})
    else:  # maintenance password
        if check_password_hash(MAINTENANCE_PASSWORD_HASH, password):
            return jsonify({"success": True})
            
    return jsonify({"success": False, "message": "Invalid password"}), 401

@app.route('/submit-report', methods=['POST'])
def submit_report():
    try:
        report_data = {
            'category': request.form.get('category'),
            'location': request.form.get('location'),
            'description': request.form.get('description'),
            'urgency': request.form.get('urgency'),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'images': []
        }

        # Handle multiple image uploads
        if 'images' in request.files:
            files = request.files.getlist('images')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    unique_filename = f"{timestamp}_{filename}"
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
                    report_data['images'].append(unique_filename)

        maintenance_reports.append(report_data)
        return jsonify({"success": True, "message": "Report submitted successfully"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@app.route('/resolve-issue/<int:index>', methods=['POST'])
def resolve_issue(index):
    try:
        if 0 <= index < len(maintenance_reports):
            # Remove images when resolving the issue
            report = maintenance_reports[index]
            for image in report.get('images', []):
                try:
                    image_path = os.path.join(app.config['UPLOAD_FOLDER'], image)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error removing image {image}: {e}")

            maintenance_reports.pop(index)
            return jsonify({"success": True})
        return jsonify({"success": False, "message": "Issue not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500