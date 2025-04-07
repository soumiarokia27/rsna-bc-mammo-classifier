import torch
import torch.nn.functional as F
import timm
import logging
import os
from collections import OrderedDict
from typing import Optional

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

def load_prediction_model(model_name: str, num_classes: int, model_path: str) -> Optional[torch.nn.Module]:
    """
    Loads a pre-trained model for prediction.

    Args:
        model_name (str): Name of the model architecture (e.g., 'resnet50', 'efficientnet_b0').
        num_classes (int): Number of output classes for the model.
        model_path (str): Path to the saved model state dictionary (.pth file).

    Returns:
        torch.nn.Module | None: Loaded PyTorch model in evaluation mode, or None if error.
    """
    if not os.path.exists(model_path):
        logging.error(f"Model file not found at: {model_path}")
        return None
    try:
        # Create model structure without pre-trained weights initially
        # `pretrained=False` is important here as we load our own weights
        model = timm.create_model(model_name, pretrained=False, num_classes=num_classes)

        logging.info(f"Loading state_dict from {model_path}")
        state_dict = torch.load(model_path, map_location=DEVICE)

        # Handle potential 'module.' prefix if saved using DataParallel
        if next(iter(state_dict)).startswith('module.'):
            logging.info("Adjusting state_dict keys (removing 'module.' prefix).")
            new_state_dict = OrderedDict()
            for k, v in state_dict.items():
                name = k[7:] # remove `module.`
                new_state_dict[name] = v
            model.load_state_dict(new_state_dict)
        else:
            model.load_state_dict(state_dict)

        model = model.to(DEVICE)
        model.eval() # Set to evaluation mode
        logging.info(f"Model '{model_name}' loaded successfully from '{model_path}' to {DEVICE}.")
        return model
    except Exception as e:
        logging.error(f"Error loading model '{model_name}' from '{model_path}': {e}", exc_info=True)
        return None

def run_prediction(model: torch.nn.Module, image_tensor: torch.Tensor) -> Optional[tuple[int, float, torch.Tensor]]:
    """
    Runs inference on a preprocessed image tensor.

    Args:
        model (torch.nn.Module): Loaded PyTorch model in eval mode.
        image_tensor (torch.Tensor): Preprocessed image tensor (BCHW format).

    Returns:
        tuple[int, float, torch.Tensor] | None: A tuple containing:
            - Predicted class index (int).
            - Confidence score (float).
            - Raw probability/logit tensor (torch.Tensor).
         Returns None if prediction fails.
    """
    if model is None or image_tensor is None:
        logging.error("Prediction requires a valid model and image tensor.")
        return None

    try:
        image_tensor = image_tensor.to(DEVICE)
        with torch.no_grad(): # Disable gradient calculation for inference
            outputs = model(image_tensor)

            # Assuming classification: apply softmax for probabilities
            probabilities = F.softmax(outputs, dim=1)
            confidence, predicted_idx = torch.max(probabilities, 1)

            return predicted_idx.item(), confidence.item(), probabilities.cpu() # Return cpu tensor

    except Exception as e:
        logging.error(f"Error during model prediction: {e}", exc_info=True)
        return None
