import os
import cv2
import base64
import uuid

def get_explanation(pred_class):
    """Generate explanation based on prediction class"""
    explanations = {
        'B': {
            'title': 'Category B - Scattered Fibroglandular',
            'content': 'Mostly fatty tissue with some scattered fibroglandular densities',
            'recommendation': 'Regular screening recommended'
        },
        'C': {
            'title': 'Category C - Heterogeneously Dense',
            'content': 'Dense tissue that may obscure small masses',
            'recommendation': 'Consider supplemental screening methods'
        }
    }
    return explanations[pred_class]

def generate_denoised_image_src(denoised_image):
    """Convert OpenCV image to base64 data URL for HTML display"""
    _, buffer = cv2.imencode('.png', denoised_image)
    denoised_base64 = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/png;base64,{denoised_base64}"

def resolve_file_path(file_path, base_dir):
    """Resolve various file path formats to absolute paths"""
    print(f"Original requested path: {file_path}")
    
    # Handle both relative and absolute paths
    if file_path.startswith('app/') or file_path.startswith('/app/'):
        # Convert relative path to absolute path
        relative_path = file_path.replace('app/', '', 1).replace('/app/', '', 1)
        file_path = os.path.join(base_dir, relative_path)
    elif file_path.startswith('static/'):
        # Handle paths relative to static folder
        file_path = os.path.join(base_dir, file_path)
    elif not os.path.isabs(file_path):
        # If it's another relative path format, try to resolve it
        file_path = os.path.join(base_dir, file_path)
    
    print(f"Resolved path: {file_path}")
    print(f"Current directory: {base_dir}")
    print(f"File exists: {os.path.exists(file_path)}")
    
    return file_path

def get_temp_dicom_path(upload_folder):
    """Generate temporary path for DICOM preview"""
    return os.path.join(upload_folder, f"preview_{uuid.uuid4().hex}.dcm")