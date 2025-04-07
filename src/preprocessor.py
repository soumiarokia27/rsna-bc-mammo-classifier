import cv2
import numpy as np
import torch
import logging
from typing import Optional

def preprocess_image_for_model(
    image: np.ndarray,
    target_size: tuple[int, int] = (224, 224),
    normalization_mean: tuple[float, ...] = (0.485, 0.456, 0.406),
    normalization_std: tuple[float, ...] = (0.229, 0.224, 0.225),
    requires_3channel: bool = True
) -> Optional[torch.Tensor]:
    """
    Preprocesses a single image frame for deep learning model inference.

    Args:
        image (np.ndarray): Input image (expects uint8 grayscale, 0-255 range).
        target_size (tuple[int, int]): Target size (height, width) for resizing.
        normalization_mean (tuple[float, ...]): Mean for normalization (per channel).
        normalization_std (tuple[float, ...]): Standard deviation for normalization (per channel).
        requires_3channel (bool): Whether the model requires a 3-channel input.

    Returns:
        torch.Tensor | None: Preprocessed image as a PyTorch tensor (CHW format)
                             with batch dimension added (BCHW), or None if error.
    """
    try:
        # 1. Resize
        resized_image = cv2.resize(image, (target_size[1], target_size[0]), interpolation=cv2.INTER_LINEAR)

        # 2. Convert to float and normalize to [0, 1]
        image_float = resized_image.astype(np.float32) / 255.0

        # 3. Handle Channels
        if requires_3channel:
            if len(image_float.shape) == 2: # Grayscale to RGB
                image_rgb = cv2.cvtColor(image_float, cv2.COLOR_GRAY2RGB)
            elif len(image_float.shape) == 3 and image_float.shape[2] == 1: # Grayscale (H, W, 1) to RGB
                 image_rgb = cv2.cvtColor(image_float, cv2.COLOR_GRAY2RGB)
            elif len(image_float.shape) == 3 and image_float.shape[2] == 3: # Already RGB
                 image_rgb = image_float
            else:
                 logging.error(f"Unsupported number of channels: {image_float.shape}")
                 return None
            target_image = image_rgb
            if len(normalization_mean) != 3 or len(normalization_std) != 3:
                 logging.warning("Normalization stats length mismatch for 3-channel image. Using first value.")
                 norm_mean = (normalization_mean[0], normalization_mean[0], normalization_mean[0])
                 norm_std = (normalization_std[0], normalization_std[0], normalization_std[0])
            else:
                 norm_mean = normalization_mean
                 norm_std = normalization_std

        else: # Requires single channel
             if len(image_float.shape) == 3 and image_float.shape[2] == 3: # RGB to Grayscale
                  image_gray = cv2.cvtColor(image_float, cv2.COLOR_RGB2GRAY)
             elif len(image_float.shape) == 3 and image_float.shape[2] == 1: # Already (H, W, 1)
                   image_gray = image_float.squeeze(-1) # Make it (H, W)
             else: # Already grayscale (H, W)
                  image_gray = image_float
             target_image = image_gray[..., np.newaxis] # Add channel dim back -> (H, W, 1)
             if len(normalization_mean) != 1 or len(normalization_std) != 1:
                  logging.warning("Normalization stats length mismatch for 1-channel image. Using first value.")
                  norm_mean = (normalization_mean[0],)
                  norm_std = (normalization_std[0],)
             else:
                  norm_mean = normalization_mean
                  norm_std = normalization_std


        # 4. Normalize (Subtract mean, divide by std)
        mean = np.array(norm_mean, dtype=np.float32)
        std = np.array(norm_std, dtype=np.float32)
        normalized_image = (target_image - mean) / std

        # 5. Convert to PyTorch Tensor and transpose (HWC to CHW)
        # Ensure channel dimension is last before transpose
        if normalized_image.ndim == 2: # Add channel dim if missing (H, W) -> (H, W, 1)
            normalized_image = normalized_image[..., np.newaxis]

        tensor = torch.from_numpy(normalized_image.transpose((2, 0, 1))) # HWC -> CHW

        # 6. Add Batch Dimension (CHW -> BCHW)
        tensor = tensor.unsqueeze(0)

        return tensor.float()

    except Exception as e:
        logging.error(f"Error during preprocessing: {e}", exc_info=True)
        return None
