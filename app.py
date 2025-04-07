import os
import argparse
import logging
import json
from typing import Optional
import uuid
import io
import base64

import numpy as np
import torch
import cv2 # For image encoding
from flask import Flask, request, render_template, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

# Import pipeline components (assuming they are in the same directory or accessible)
from src.dicom_loader import load_dicom_image
from src.denoising import denoise_image
from src.preprocessor import preprocess_image_for_model
from src.prediction import load_prediction_model, run_prediction
from src.results import format_prediction_results

# --- Configuration ---
load_dotenv() # Load environment variables from .env file

# Flask specific config
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
ALLOWED_EXTENSIONS = {'dcm', ''} # Allow .dcm and files with no extension
SECRET_KEY = os.environ.get('SECRET_KEY', 'N7x@Gz!vL9#qWpB8^u3T$Zr1MjKfXeA2') # CHANGE THIS!

# Model specific parameters (Load from env or keep defaults - ensure consistency)
MODEL_PATH = os.environ.get('MODEL_PATH', 'models/best_deit_base_patch16_224_binary_BC.pth') # IMPORTANT: Set via .env or default
MODEL_NAME = os.environ.get('MODEL_NAME', 'deit_base_patch16_224')
NUM_CLASSES = int(os.environ.get('NUM_CLASSES', '2'))
# Parse IMG_SIZE from env if needed, e.g., "256,256"
img_size_str = os.environ.get('MODEL_INPUT_SIZE', '224,224')
try:
    MODEL_INPUT_SIZE = tuple(map(int, img_size_str.split(',')))
except:
    MODEL_INPUT_SIZE = (224, 224) # Fallback
MODEL_REQUIRES_3CHANNEL = os.environ.get('MODEL_REQUIRES_3CHANNEL', 'True').lower() == 'true'
# Parse normalization params if needed
NORMALIZATION_MEAN = tuple(map(float, os.environ.get('NORMALIZATION_MEAN', '0.485,0.456,0.406').split(',')))
NORMALIZATION_STD = tuple(map(float, os.environ.get('NORMALIZATION_STD', '0.229,0.224,0.225').split(',')))
# Load class names from env (e.g., "0:Density B,1:Density C") or keep default
class_names_str = os.environ.get('CLASS_NAMES', '0:Density B,1:Density C')
try:
    CLASS_NAMES = {int(k): v for k, v in (item.split(':') for item in class_names_str.split(','))}
except:
    CLASS_NAMES = {0: 'Density B', 1: 'Density C'} # Fallback

# --- Flask App Initialization ---
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # 32 MB max upload size for DICOM
app.config['SECRET_KEY'] = SECRET_KEY

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Ensure upload folder exists ---
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# --- Load Model Globally ---
logger.info("Loading prediction model...")
model = load_prediction_model(
    model_name=MODEL_NAME,
    num_classes=NUM_CLASSES,
    model_path=MODEL_PATH
)
if model is None:
    logger.error(f"FATAL: Could not load model from {MODEL_PATH}. The application may not function.")
    # Optionally, exit or prevent app run
else:
    logger.info("Prediction model loaded successfully.")


# --- Utility Functions ---
def allowed_file(filename):
    """Checks if the file extension is allowed (or no extension)."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS \
           or '.' not in filename # Allow files with no extension

def encode_image_base64(image_array: np.ndarray) -> Optional[str]:
     """Encodes a NumPy image array to a base64 string for HTML display."""
     try:
          # Ensure uint8 for PNG encoding
          if image_array.dtype != np.uint8:
               # Attempt normalization if not uint8 (e.g., after denoising)
               if image_array.max() > 0 :
                    img_norm = (image_array - image_array.min()) / (image_array.max() - image_array.min())
                    image_array = (img_norm * 255).astype(np.uint8)
               else:
                    image_array = image_array.astype(np.uint8) # Handle flat images

          is_success, buffer = cv2.imencode(".png", image_array)
          if is_success:
               return f"data:image/png;base64,{base64.b64encode(buffer).decode('utf-8')}"
          else:
               logger.error("Failed to encode image to PNG.")
               return None
     except Exception as e:
          logger.error(f"Error encoding image to base64: {e}", exc_info=True)
          return None


# --- Flask Routes ---
@app.route('/', methods=['GET'])
def index():
    """Renders the main upload page."""
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_dicom_upload():
    """Handles DICOM file upload, processing, and displays results."""
    if model is None:
        flash('Model is not loaded. Cannot process files.', 'danger')
        return redirect(url_for('index'))

    if 'dicom_file' not in request.files:
        flash('No file part selected.', 'warning')
        return redirect(url_for('index'))

    file = request.files['dicom_file']
    if file.filename == '':
        flash('No file selected.', 'warning')
        return redirect(url_for('index'))

    # Denoising option from form
    denoise_method = request.form.get('denoise_method', 'none') # 'nlm', 'bm3d', 'none'
    if denoise_method == 'none':
        denoise_method = None
    denoise_params = {} # Add params if needed, e.g., from advanced options form fields
    if denoise_method == 'nlm':
         # Example: Get 'h' from form if available, else use default
         try:
             denoise_params['h'] = float(request.form.get('denoise_h', 10))
         except ValueError:
             denoise_params['h'] = 10
    elif denoise_method == 'bm3d':
         try:
             denoise_params['sigma_psd'] = float(request.form.get('denoise_sigma', 0.117)) # Default 30/255
         except ValueError:
             denoise_params['sigma_psd'] = 0.117


    if file and (allowed_file(file.filename) or file.filename == ''): # Allow empty filename if needed
        # Use a unique filename to avoid conflicts if saving temporarily
        filename = secure_filename(f"{uuid.uuid4()}_{file.filename or 'dicomfile.dcm'}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)
            logger.info(f"File saved temporarily to: {file_path}")

            # --- Start Processing Pipeline ---
            results_list = []
            processing_error = False

            # 1. Load DICOM (can return multiple frames)
            loaded_frames_data = load_dicom_image(file_path) # Returns list of (image_array, metadata)

            if loaded_frames_data is None:
                flash(f"Failed to load or parse DICOM file: {file.filename}", 'danger')
                processing_error = True
            else:
                logger.info(f"Loaded {len(loaded_frames_data)} frame(s) from {file.filename}")
                for image_array, metadata in loaded_frames_data:
                    frame_results = metadata.copy() # Start results dict with metadata
                    current_image = image_array
                    processed_image_base64 = None # For visualization

                    # 2. Denoise (Optional)
                    if denoise_method:
                        logger.info(f"Applying denoising ({denoise_method}) to frame {metadata.get('FrameIndex', 0)}")
                        denoised_image = denoise_image(current_image, method=denoise_method, **denoise_params)
                        processed_image_base64 = encode_image_base64(denoised_image) # Encode denoised image
                        current_image = denoised_image
                    else:
                        logger.info(f"Skipping denoising for frame {metadata.get('FrameIndex', 0)}")
                        processed_image_base64 = encode_image_base64(current_image) # Encode original image


                    # 3. Preprocess for Model
                    preprocessed_tensor = preprocess_image_for_model(
                        current_image,
                        target_size=MODEL_INPUT_SIZE,
                        normalization_mean=NORMALIZATION_MEAN,
                        normalization_std=NORMALIZATION_STD,
                        requires_3channel=MODEL_REQUIRES_3CHANNEL
                    )

                    if preprocessed_tensor is None:
                        logger.error(f"Preprocessing failed for frame {metadata.get('FrameIndex', 0)}")
                        frame_results['prediction_status'] = 'Preprocessing Error'
                        processing_error = True
                    else:
                        # 4. Run Prediction
                        prediction_output = run_prediction(model, preprocessed_tensor)
                        if prediction_output is None:
                            logger.error(f"Prediction failed for frame {metadata.get('FrameIndex', 0)}")
                            frame_results['prediction_status'] = 'Prediction Error'
                            processing_error = True
                        else:
                            pred_idx, conf, probs = prediction_output
                            # 5. Format Results
                            formatted_res = format_prediction_results(pred_idx, conf, probs, CLASS_NAMES)
                            frame_results.update(formatted_res) # Add prediction results
                            frame_results['prediction_status'] = 'Success'

                    frame_results['processed_image_base64'] = processed_image_base64 # Add image for display
                    results_list.append(frame_results)
            # --- End Processing Pipeline ---

        except Exception as e:
            logger.error(f"An error occurred during processing: {e}", exc_info=True)
            flash(f"An unexpected error occurred: {e}", 'danger')
            processing_error = True
        finally:
            # Clean up the uploaded file
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Removed temporary file: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing temporary file {file_path}: {e}")

        if not processing_error and results_list:
            # Pass results to the results template
            return render_template('results.html', results=results_list, filename=file.filename)
        elif not results_list and not processing_error:
             flash('No frames could be processed from the DICOM file.', 'warning')
             return redirect(url_for('index'))
        else:
             # Error occurred, redirect back to index where flash message will show
             return redirect(url_for('index'))

    else:
        flash('Invalid file type or filename.', 'warning')
        return redirect(url_for('index'))

# Optional: Route to serve uploaded files if needed (e.g., for direct download link)
# Be cautious with this in production - ensure proper access control
# @app.route('/uploads/<filename>')
# def uploaded_file(filename):
#     return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# --- Main Execution ---
if __name__ == '__main__':
    # Use environment variable for port or default to 5001 (to avoid conflicts)
    port = int(os.environ.get('PORT', 5001))
    # Run the app (set debug=False in production)
    # Use host='0.0.0.0' to make it accessible on the network
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true')
