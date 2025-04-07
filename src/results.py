from typing import Optional
import torch

DEFAULT_CLASS_NAMES = {0: 'Class 0', 1: 'Class 1'} # Example

def format_prediction_results(
    predicted_idx: int,
    confidence: float,
    probabilities: Optional[torch.Tensor],
    class_names: Optional[dict]
) -> dict:
    """
    Formats the prediction output into a human-readable dictionary.

    Args:
        predicted_idx (int): The index of the predicted class.
        confidence (float): The confidence score for the prediction.
        probabilities (torch.Tensor | None): Tensor of probabilities for all classes (optional).
        class_names (dict | None): Dictionary mapping class indices to names.

    Returns:
        dict: A dictionary containing formatted results.
    """
    if class_names is None:
        class_names = DEFAULT_CLASS_NAMES

    predicted_class_name = class_names.get(predicted_idx, f"Unknown Class ({predicted_idx})")

    result = {
        "predicted_class_index": predicted_idx,
        "predicted_class_name": predicted_class_name,
        "confidence": f"{confidence:.4f}"
    }

    if probabilities is not None:
        probs_list = probabilities.squeeze().tolist() # Remove batch dim and convert to list
        result["all_probabilities"] = {
            class_names.get(i, f"Unknown Class ({i})"): f"{p:.4f}"
            for i, p in enumerate(probs_list)
        }

    return result

