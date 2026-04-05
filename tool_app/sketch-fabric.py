import json
import os
import base64
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings

# Define upload directory relative to your Django project
UPLOAD_FOLDER = os.path.join(settings.BASE_DIR, 'static', 'uploads', 'sketch_fabric')

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@csrf_exempt
@require_http_methods(["POST"])
def save_drawing(request):
    """Save the drawing as JSON and optionally as image"""
    try:
        data = json.loads(request.body)
        canvas_data = data.get('canvasData')
        image_data = data.get('imageData')
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        
        # Save canvas state as JSON
        json_filename = f'drawing_{timestamp}.json'
        json_path = os.path.join(UPLOAD_FOLDER, json_filename)
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(canvas_data, f, indent=2)
        
        # Save as PNG if image data is provided
        saved_files = [json_filename]
        
        if image_data:
            # Remove the data:image/png;base64 prefix
            if ',' in image_data:
                image_data = image_data.split(',')[1]
            
            png_filename = f'drawing_{timestamp}.png'
            png_path = os.path.join(UPLOAD_FOLDER, png_filename)
            
            with open(png_path, 'wb') as f:
                f.write(base64.b64decode(image_data))
            
            saved_files.append(png_filename)
        
        return JsonResponse({
            'success': True,
            'files': saved_files,
            'message': f'Drawing saved successfully! Files: {", ".join(saved_files)}'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def load_drawing(request):
    """Load a previously saved drawing"""
    try:
        data = json.loads(request.body)
        filename = data.get('filename')
        
        if not filename:
            return JsonResponse({
                'success': False, 
                'error': 'No filename provided'
            }, status=400)
        
        # Security check: prevent directory traversal
        filename = os.path.basename(filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        if not os.path.exists(filepath):
            return JsonResponse({
                'success': False,
                'error': 'File not found'
            }, status=404)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            canvas_data = json.load(f)
        
        return JsonResponse({
            'success': True,
            'canvasData': canvas_data,
            'filename': filename
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["GET"])
def list_drawings(request):
    """List all saved drawings"""
    try:
        drawings = []
        for file in os.listdir(UPLOAD_FOLDER):
            if file.endswith('.json'):
                filepath = os.path.join(UPLOAD_FOLDER, file)
                stat = os.stat(filepath)
                drawings.append({
                    'filename': file,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
        
        # Sort by modified time, newest first
        drawings.sort(key=lambda x: x['modified'], reverse=True)
        
        return JsonResponse({
            'success': True,
            'drawings': drawings,
            'count': len(drawings)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@require_http_methods(["DELETE"])
def delete_drawing(request, filename):
    """Delete a saved drawing"""
    try:
        # Security check: prevent directory traversal
        filename = os.path.basename(filename)
        json_path = os.path.join(UPLOAD_FOLDER, filename)
        png_path = os.path.join(UPLOAD_FOLDER, filename.replace('.json', '.png'))
        
        deleted_files = []
        
        if os.path.exists(json_path):
            os.remove(json_path)
            deleted_files.append(filename)
        
        if os.path.exists(png_path):
            os.remove(png_path)
            deleted_files.append(filename.replace('.json', '.png'))
        
        if deleted_files:
            return JsonResponse({
                'success': True,
                'message': f'Deleted: {", ".join(deleted_files)}'
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'File not found'
            }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


# Helper function to get upload folder path (useful for debugging)
def get_upload_folder_info(request):
    """Get information about the upload folder (for debugging)"""
    return JsonResponse({
        'upload_folder': UPLOAD_FOLDER,
        'exists': os.path.exists(UPLOAD_FOLDER),
        'files_count': len([f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.json')]) if os.path.exists(UPLOAD_FOLDER) else 0
    })
