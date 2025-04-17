import torch
import torchvision.transforms as transforms
from timm.models import create_model

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

# Image transformations (3-channel compatible)
transform = transforms.Compose([
    transforms.ToPILImage(),
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],  # ImageNet stats
                         std=[0.229, 0.224, 0.225])
])

def load_model(model_path):
    """Load the DeiT model for mammography classification"""
    try:
        # Create model with updated name format and proper parameters
        model = create_model(
            'deit_base_patch16_224.fb_in1k',  # Correct model identifier
            pretrained=False,
            num_classes=2,
            img_size=224,
            in_chans=3
        )
        
        # Load checkpoint with proper state dict handling
        checkpoint = torch.load(model_path, map_location=device)
        state_dict = checkpoint.get('state_dict', checkpoint)
        
        # Remove DataParallel wrapping prefixes if present
        if list(state_dict.keys())[0].startswith('module.'):
            state_dict = {k[7:]: v for k, v in state_dict.items()}
        
        model.load_state_dict(state_dict)
        model.to(device)
        model.eval()
        print(f"Successfully loaded model from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None

def get_prediction(model, tensor):
    """Get class prediction with confidence"""
    with torch.no_grad():
        outputs = model(tensor)
        probabilities = torch.nn.functional.softmax(outputs, dim=1)
        conf, pred_idx = torch.max(probabilities, 1)
    
    return 'C' if pred_idx.item() == 1 else 'B', conf.item()