import cv2
import numpy as np
import logging

# Optional: Try importing bm3d
try:
    import bm3d
    BM3D_AVAILABLE = True
except ImportError:
    logging.info("bm3d library not found. BM3D denoising disabled. Install with 'pip install bm3d'")
    BM3D_AVAILABLE = False

def denoise_image(image: np.ndarray, method: str = 'nlm', **kwargs) -> np.ndarray:
    """
    Applies a denoising algorithm to a grayscale image.

    Args:
        image (np.ndarray): Input grayscale image (should be uint8).
        method (str): Denoising method ('nlm', 'bm3d').
        **kwargs: Additional parameters for the denoising algorithm.
                  For NLM: h, templateWindowSize, searchWindowSize
                  For BM3D: sigma_psd

    Returns:
        np.ndarray: Denoised grayscale image (uint8).
    """
    if image.dtype != np.uint8:
        logging.warning("Input image for denoising is not uint8. Attempting conversion.")
        # Attempt to normalize and convert if not uint8
        if image.max() > 0:
             image = (image / image.max() * 255).astype(np.uint8)
        else:
             image = image.astype(np.uint8)


    logging.info(f"Applying denoising method: {method}")

    if method.lower() == 'nlm':
        # Parameters for Non-Local Means
        h = kwargs.get('h', 10) # Filter strength
        template_window_size = kwargs.get('templateWindowSize', 7) # Must be odd
        search_window_size = kwargs.get('searchWindowSize', 21) # Must be odd
        try:
            denoised_image = cv2.fastNlMeansDenoising(
                image,
                None, # Use default h value calculation if None, else use h parameter
                h=float(h),
                templateWindowSize=int(template_window_size),
                searchWindowSize=int(search_window_size)
            )
        except Exception as e:
             logging.error(f"Error during NLM denoising: {e}. Returning original image.")
             denoised_image = image

    elif method.lower() == 'bm3d':
        if not BM3D_AVAILABLE:
            logging.warning("BM3D denoising selected but library not available. Returning original image.")
            return image
        try:
            sigma_psd = kwargs.get('sigma_psd', 30.0 / 255.0) # Noise standard deviation estimate
            # BM3D typically works on float images [0, 1]
            img_float = image.astype(np.float32) / 255.0
            denoised_image_float = bm3d.bm3d(
                img_float,
                sigma_psd=float(sigma_psd),
                stage_arg=bm3d.BM3DStages.ALL_STAGES # Apply both stages
            )
            # Convert back to uint8
            denoised_image = (np.clip(denoised_image_float, 0, 1) * 255).astype(np.uint8)
        except Exception as e:
            logging.error(f"Error during BM3D denoising: {e}. Returning original image.")
            denoised_image = image

    # Placeholder for potential Deep Learning based denoising
    # elif method.lower() == 'dl_denoise':
    #     logging.warning("DL denoising method not implemented yet. Returning original image.")
    #     denoised_image = image

    else:
        logging.warning(f"Unknown denoising method '{method}'. Returning original image.")
        denoised_image = image

    return denoised_image
