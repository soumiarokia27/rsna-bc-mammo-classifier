import cv2
import numpy as np
import pydicom
import base64
import torch
from src.models import device, transform

def process_dicom(dicom_path):
    """Process DICOM file with enhanced error handling"""
    try:
        ds = pydicom.dcmread(dicom_path)
        img = ds.pixel_array
        
        # Handle various DICOM photometric interpretations
        if ds.PhotometricInterpretation == 'MONOCHROME1':
            img = np.amax(img) - img  # Invert if needed
        
        # Normalization with safety checks
        img = img.astype(np.float32)
        img = (img - np.min(img)) / (np.max(img) - np.min(img) + 1e-6) * 255
        img = img.astype(np.uint8)
        
        # Generate preview
        _, buffer = cv2.imencode('.png', img)
        img_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # Extract metadata
        metadata = {
            'PatientID': getattr(ds, 'PatientID', 'N/A'),
            'PatientAge': getattr(ds, 'PatientAge', 'N/A'),
            'StudyDate': getattr(ds, 'StudyDate', 'N/A'),
            'Modality': getattr(ds, 'Modality', 'N/A'),
            'BodyPart': getattr(ds, 'BodyPartExamined', 'N/A')
        }
        
        return img, metadata, img_base64
    
    except Exception as e:
        raise RuntimeError(f"DICOM processing failed: {str(e)}")

def preprocess_image(image_path):
    """Unified preprocessing for DICOM and regular images"""
    try:
        if image_path.lower().endswith('.dcm'):
            img, metadata, img_base64 = process_dicom(image_path)
        else:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            metadata = {}
            _, buffer = cv2.imencode('.png', img)
            img_base64 = base64.b64encode(buffer).decode('utf-8')

        # Convert to 3-channel RGB with CLAHE enhancement
        if len(img.shape) == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
            
        # Apply preprocessing pipeline
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        img = clahe.apply(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY))
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        
        # Apply transformations
        tensor = transform(img).unsqueeze(0).to(device)
        
        return tensor, metadata, img_base64
    
    except Exception as e:
        raise RuntimeError(f"Image processing failed: {str(e)}")

def enhance_mammography_dicom(dicom_path: str,
                         bilateral_d: int = 9,
                         bilateral_sigma_color: float = 75.0,
                         bilateral_sigma_space: float = 75.0,
                         clahe_clip_limit: float = 3.0,
                         clahe_grid_size: tuple = (8, 8),
                         unsharp_kernel_size: int = 5,
                         unsharp_sigma: float = 1.0,
                         unsharp_amount: float = 1.5,
                         unsharp_threshold: int = 5,
                         wavelet_threshold: float = 30.0) -> np.ndarray:
    
    # Read DICOM
    try:
        ds = pydicom.dcmread(dicom_path)
        img = ds.pixel_array.astype(np.float32)
        
        # Handle MONOCHROME1 (invert if needed)
        if getattr(ds, 'PhotometricInterpretation', '') == 'MONOCHROME1':
            img = np.max(img) - img
            
        # Normalize to 0-255 for processing
        img_norm = cv2.normalize(img, None, 0, 255, cv2.NORM_MINMAX)
        img_uint8 = np.uint8(img_norm)
        
        # SIMPLIFIED APPROACH WITHOUT WAVELETS - SKIP THE PROBLEMATIC PART
        
        # Start with bilateral filtering (preserves edges while removing noise)
        img_bilateral = cv2.bilateralFilter(img_uint8, bilateral_d, 
                                           bilateral_sigma_color, 
                                           bilateral_sigma_space)
        
        # Apply another denoising method that's more robust
        # Using Non-local Means Denoising with careful parameter tuning
        img_denoised = cv2.fastNlMeansDenoising(
            img_bilateral,
            None,
            h=15,  # Filtering strength
            templateWindowSize=7,
            searchWindowSize=21
        )
        
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=clahe_clip_limit, 
                               tileGridSize=clahe_grid_size)
        img_clahe = clahe.apply(img_denoised)
        
        # Gamma correction for better tissue differentiation
        gamma = 0.8
        inv_gamma = 1.0 / gamma
        table = np.array([((i / 255.0) ** inv_gamma) * 255 
                         for i in np.arange(0, 256)]).astype(np.uint8)
        img_gamma = cv2.LUT(img_clahe, table)
        
        # Unsharp masking to enhance edges (highlights tissue boundaries)
        gaussian = cv2.GaussianBlur(img_gamma, (unsharp_kernel_size, unsharp_kernel_size), 
                                   unsharp_sigma)
        img_unsharp = cv2.addWeighted(img_gamma, 1 + unsharp_amount, 
                                     gaussian, -unsharp_amount, 0)
        
        # Local contrast adjustment using morphological operations
        kernel = np.ones((5, 5), np.uint8)
        tophat = cv2.morphologyEx(img_unsharp, cv2.MORPH_TOPHAT, kernel)
        blackhat = cv2.morphologyEx(img_unsharp, cv2.MORPH_BLACKHAT, kernel)
        img_morph = cv2.add(img_unsharp, tophat)
        img_morph = cv2.subtract(img_morph, blackhat)
        
        # Adaptive brightness/contrast based on image statistics
        mean_val = np.mean(img_morph)
        std_val = np.std(img_morph)
        
        alpha = 1.2  # Contrast control (1.0-3.0)
        beta = 128 - alpha * mean_val  # Brightness control
        
        # Apply adaptive brightness/contrast adjustment
        img_final = cv2.convertScaleAbs(img_morph, alpha=alpha, beta=beta)
        
        # Final refinement with a simple Gaussian blur for smoothness if needed
        img_final = cv2.GaussianBlur(img_final, (3, 3), 0.5)
        
        return img_final
        
    except Exception as e:
        print(f"Error in mammography enhancement: {str(e)}")
        # Return original image if processing fails
        if 'img_uint8' in locals():
            return img_uint8
        raise RuntimeError(f"DICOM processing failed: {str(e)}")