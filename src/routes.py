import os
from flask import request, render_template, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from src.models import get_prediction
from src.preprocessing import preprocess_image, process_dicom, enhance_mammography_dicom
from src.utils import get_explanation, generate_denoised_image_src, resolve_file_path, get_temp_dicom_path
from src.config import allowed_file

def register_routes(app, model, upload_folder):
    @app.route('/')
    def home():
        return render_template('index.html')

    @app.route('/predict', methods=['POST'])
    def predict():
        if 'file' not in request.files:
            flash('No file uploaded')
            return redirect(url_for('home'))
        
        file = request.files['file']
        if not file or file.filename == '':
            flash('No file selected')
            return redirect(url_for('home'))
        
        if not allowed_file(file.filename):
            flash('Invalid file type')
            return redirect(url_for('home'))
        
        try:
            # Save and process file
            filename = secure_filename(file.filename)
            save_path = os.path.join(upload_folder, filename)
            file.save(save_path)
            
            # Verify model availability
            if model is None:
                flash('Model not loaded - please contact administrator')
                return redirect(url_for('home'))
            
            # Process and predict
            tensor, metadata, img_base64 = preprocess_image(save_path)
            pred_class, confidence = get_prediction(model, tensor)
            
            # Get explanation
            explanation = get_explanation(pred_class)
            
            # Use enhanced mammography denoising
            denoised_image = enhance_mammography_dicom(save_path)

            # Convert to base64 for HTML display
            denoised_image_src = generate_denoised_image_src(denoised_image)

            result = {
                    'predicted_class': pred_class,
                    'confidence': confidence * 100,  # Convert to percentage
                    'explanation': explanation,
                    'original_image_base64': img_base64,
                    'denoised_image': denoised_image_src,
                    'metadata': metadata,
                }
            
            return render_template('result.html', result=result)
            
        except Exception as e:
            flash(f'Error processing image: {str(e)}')
            return redirect(url_for('home'))

    @app.route('/dicom_preview', methods=['POST', 'GET'])
    def dicom_preview():
        """AJAX endpoint for DICOM previews"""
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['file']
            if not file.filename.lower().endswith('.dcm'):
                return jsonify({'error': 'Invalid DICOM file'}), 400
            
            try:
                # Temporary processing
                temp_path = get_temp_dicom_path(upload_folder)
                file.save(temp_path)
                _, _, img_base64 = process_dicom(temp_path)
                os.remove(temp_path)
                
                return jsonify({'preview': img_base64})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        elif request.method == 'GET':
            file_path = request.args.get('file')
            if not file_path or not file_path.lower().endswith('.dcm'):
                return jsonify({'error': 'Invalid or missing DICOM file path'}), 400
            
            try:
                # Resolve file path
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                file_path = resolve_file_path(file_path, base_dir)
                    
                # Check if file exists
                if not os.path.exists(file_path):
                    return jsonify({'error': f'File not found: {file_path}'}), 404
                    
                # Process the DICOM file from the provided path
                _, _, img_base64 = process_dicom(file_path)
                return jsonify({'preview': img_base64})
            
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    @app.route('/about')
    def about():
        """About page with application information"""
        return render_template('about.html')