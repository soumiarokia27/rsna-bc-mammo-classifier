import pydicom
import numpy as np
import logging
import cv2
from pydicom.pixel_data_handlers.util import apply_voi_lut

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def apply_windowing(image: np.ndarray, center: float, width: float) -> np.ndarray:
    """Applies window center and width to image array."""
    image_min = center - width // 2
    image_max = center + width // 2
    windowed_image = np.clip(image, image_min, image_max)
    return windowed_image

def normalize_to_uint8(image: np.ndarray) -> np.ndarray:
    """Normalizes an image array to 0-255 uint8 range."""
    if image.dtype != np.uint8:
        if image.max() == image.min():
             # Avoid division by zero if image is flat
             logging.warning("Image has uniform intensity.")
             return np.zeros_like(image, dtype=np.uint8)

        # Scale to 0-1 first, then to 0-255
        img_norm = (image - np.min(image)) / (np.max(image) - np.min(image))
        img_uint8 = (img_norm * 255.0).astype(np.uint8)
        return img_uint8
    return image

from typing import Optional

def load_dicom_image(file_path: str, apply_window: bool = True) -> Optional[list[tuple[np.ndarray, dict]]]:
    """
    Loads a DICOM file, extracts pixel data and metadata for each frame.

    Args:
        file_path (str): Path to the DICOM file.
        apply_window (bool): Whether to apply Window Center/Width or VOI LUT.

    Returns:
        List[Tuple[np.ndarray, dict]] | None: A list where each tuple contains:
            - The processed image frame as a NumPy array (uint8, 0-255).
            - A dictionary containing relevant metadata (e.g., PatientID, StudyInstanceUID, frame_index).
        Returns None if loading fails or pixel data is missing.
    """
    try:
        ds = pydicom.dcmread(file_path)
    except Exception as e:
        logging.error(f"Error reading DICOM file '{file_path}': {e}")
        return None

    if 'PixelData' not in ds:
        logging.error(f"No PixelData found in DICOM file: {file_path}")
        return None

    try:
        pixel_array = ds.pixel_array
    except Exception as e:
        logging.error(f"Error accessing pixel_array in '{file_path}': {e}")
        return None

    # Handle multi-frame DICOMs
    num_frames = getattr(ds, 'NumberOfFrames', 1)
    if num_frames is None: num_frames = 1 # Handle case where NumberOfFrames is None

    frames_data = []
    base_metadata = {
        'PatientID': getattr(ds, 'PatientID', 'Unknown'),
        'StudyInstanceUID': getattr(ds, 'StudyInstanceUID', 'Unknown'),
        'SeriesInstanceUID': getattr(ds, 'SeriesInstanceUID', 'Unknown'),
        'SOPInstanceUID': getattr(ds, 'SOPInstanceUID', 'Unknown'),
        'FilePath': file_path
    }

    photometric_interpretation = getattr(ds, 'PhotometricInterpretation', 'MONOCHROME2')

    for i in range(num_frames):
        try:
            if num_frames > 1:
                frame_image = pixel_array[i]
                frame_metadata = base_metadata.copy()
                frame_metadata['FrameIndex'] = i
            else:
                frame_image = pixel_array
                frame_metadata = base_metadata.copy()
                frame_metadata['FrameIndex'] = 0

            processed_image = frame_image.astype(np.float32)

            # Apply Window Center/Width or VOI LUT if requested
            if apply_window:
                try:
                    # Prefer VOI LUT if available
                    processed_image = apply_voi_lut(processed_image, ds)
                    logging.debug(f"Applied VOI LUT for frame {i} in {file_path}")
                except Exception as voi_e:
                     # Fallback to Window Center/Width if VOI LUT fails or isn't present
                    wc = getattr(ds, 'WindowCenter', None)
                    ww = getattr(ds, 'WindowWidth', None)
                    if isinstance(wc, pydicom.multival.MultiValue): wc = wc[0] # Handle multi-values
                    if isinstance(ww, pydicom.multival.MultiValue): ww = ww[0]
                    if wc is not None and ww is not None:
                         processed_image = apply_windowing(processed_image, float(wc), float(ww))
                         logging.debug(f"Applied WC/WW ({wc}/{ww}) for frame {i} in {file_path}")
                    else:
                         logging.warning(f"No VOI LUT or WC/WW found/applicable for frame {i} in {file_path}. Using raw pixel range.")
                         # Normalize raw pixel range if no windowing applied
                         processed_image = normalize_to_uint8(processed_image).astype(np.float32)


            # Normalize to 0-255 uint8 AFTER windowing
            processed_image_uint8 = normalize_to_uint8(processed_image)

            # Handle MONOCHROME1 (inverted)
            if photometric_interpretation == 'MONOCHROME1':
                processed_image_uint8 = 255 - processed_image_uint8

            frames_data.append((processed_image_uint8, frame_metadata))

        except Exception as frame_e:
            logging.error(f"Error processing frame {i} in '{file_path}': {frame_e}")
            continue # Skip problematic frame

    if not frames_data:
        logging.warning(f"No frames successfully processed for '{file_path}'.")
        return None

    return frames_data
