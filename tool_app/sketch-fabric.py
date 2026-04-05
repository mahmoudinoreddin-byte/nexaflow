from flask import Flask, render_template, request, jsonify
import json
import base64
from datetime import datetime
import os

app = Flask(__name__)

# Configure upload folder
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    """Serve the main drawing page"""
    return render_template('index.html')

@app.route('/save_drawing', methods=['POST'])
def save_drawing():
    """Save the drawing as JSON and optionally as image"""
    try:
        data = request.json
        canvas_data = data.get('canvasData')
        image_data = data.get('imageData')
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save canvas state as JSON
        json_filename = f'drawing_{timestamp}.json'
        json_path = os.path.join(app.config['UPLOAD_FOLDER'], json_filename)
        
        with open(json_path, 'w') as f:
            json.dump(canvas_data, f, indent=2)
        
        # Save as PNG if image data is provided
        if image_data:
            # Remove the data:image/png;base64 prefix
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            png_filename = f'drawing_{timestamp}.png'
            png_path = os.path.join(app.config['UPLOAD_FOLDER'], png_filename)
            
            with open(png_path, 'wb') as f:
                f.write(base64.b64decode(image_data))
            
            return jsonify({
                'success': True,
                'json_file': json_filename,
                'png_file': png_filename,
                'message': 'Drawing saved successfully!'
            })
        
        return jsonify({
            'success': True,
            'json_file': json_filename,
            'message': 'Drawing state saved successfully!'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/load_drawing', methods=['POST'])
def load_drawing():
    """Load a previously saved drawing"""
    try:
        filename = request.json.get('filename')
        if not filename:
            return jsonify({'success': False, 'error': 'No filename provided'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        with open(filepath, 'r') as f:
            canvas_data = json.load(f)
        
        return jsonify({
            'success': True,
            'canvasData': canvas_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/list_drawings', methods=['GET'])
def list_drawings():
    """List all saved drawings"""
    try:
        drawings = []
        for file in os.listdir(app.config['UPLOAD_FOLDER']):
            if file.endswith('.json'):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file)
                stat = os.stat(filepath)
                drawings.append({
                    'filename': file,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by modified time, newest first
        drawings.sort(key=lambda x: x['modified'], reverse=True)
        
        return jsonify({
            'success': True,
            'drawings': drawings
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
