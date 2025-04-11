
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from flask import send_from_directory
from flask import send_file, abort

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tasks.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d'),
            'completed_at': self.completed_at.strftime('%Y-%m-%d') if self.completed_at else None
        }

@app.route('/')
def index():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return render_template('index.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task():
    title = request.form['title']
    description = request.form.get('description')
    new_task = Task(title=title, description=description)
    db.session.add(new_task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/download-db')
def download_db():
    try:
        # Use the directory of the current Python file (more reliable than os.getcwd())
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, 'instance', 'task.db')

        print(f"[DEBUG] DB path resolved to: {db_path}")  # Will show in Render logs

        if not os.path.exists(db_path):
            return f"Error: Database not found at {db_path}", 404

        return send_file(db_path, as_attachment=True)

    except Exception as e:
        return f"Internal Server Error: {str(e)}", 500

@app.route('/complete/<int:id>')
def complete_task(id):
    task = Task.query.get_or_404(id)
    task.status = 'Completed'
    task.completed_at = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:id>')
def delete_task(id):
    task = Task.query.get_or_404(id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/reports')
def reports():
    tasks = Task.query.all()
    return render_template('reports.html', tasks=tasks)

@app.route('/chart-data')
def chart_data():
    total = Task.query.count()
    completed = Task.query.filter_by(status='Completed').count()
    pending = total - completed
    return jsonify({
        'labels': ['Completed', 'Pending'],
        'data': [completed, pending]
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
