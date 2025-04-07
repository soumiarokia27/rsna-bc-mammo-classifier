```
# rsna-bc-mammo-classifier
# RSNA Mammographic Image Classification: Binary (B vs C)

![Python](https://img.shields.io/badge/Python-3.10-blue)
![PyTorch](https://img.shields.io/badge/PyTorch-2.5-orange)
![License](https://img.shields.io/badge/License-MIT-green)

Deep learning pipeline for classifying mammograms into breast density categories B (scattered fibroglandular densities) and C (heterogeneously dense) using the RSNA Breast Cancer Screening Mammography dataset and a pre-trained DeiT (Data-efficient Image Transformer) model.

## 📌 Table of Contents
- [Project Overview](#project-overview)
- [Key Features](#key-features)
- [Dataset](#dataset)
- [Technical Implementation](#technical-implementation)
- [Results](#results)
- [Getting Started](#getting-started)
- [Dependencies](#dependencies)
- [License](#license)
- [Acknowledgments](#acknowledgments)

## 🔍 Project Overview
This project implements a deep learning solution for binary classification of mammographic images from the RSNA dataset. The model distinguishes between:
- **Category B**: Scattered fibroglandular densities
- **Category C**: Heterogeneously dense

Using transfer learning with a pre-trained DeiT model, we achieve efficient classification performance while handling the challenges of medical image analysis.

## ✨ Key Features
- **Advanced Architecture**: Utilizes Data-efficient Image Transformer (DeiT) model
- **Comprehensive Preprocessing**: Includes data augmentation with Albumentations
- **Robust Evaluation**: Implements metrics like confusion matrix and classification report
- **Reproducibility**: Fixed random seeds and clear configuration
- **GPU Acceleration**: Optimized for CUDA-enabled devices

## 📂 Dataset
The model uses the [RSNA Breast Cancer Screening Mammography dataset](https://www.kaggle.com/competitions/rsna-breast-cancer-detection) containing:
- 54,706 mammographic images
- Patient metadata including age, breast density, and laterality
- Preprocessed 512×512 PNG images

![Data Distribution](https://via.placeholder.com/600x400?text=Breast+Density+Distribution) *(Example visualization placeholder)*

## ⚙️ Technical Implementation
### Model Architecture
```python
model = timm.create_model('deit_base_patch16_224', pretrained=True, num_classes=2)
```

### Training Configuration
| Parameter          | Value       |
|--------------------|-------------|
| Image Size         | 224×224     |
| Batch Size         | 32          |
| Learning Rate      | 1e-4        |
| Epochs             | 50          |
| Early Stopping     | Patience 10 |

### Data Augmentation
```python
transform = A.Compose([
    A.RandomResizedCrop(IMG_SIZE, IMG_SIZE),
    A.HorizontalFlip(p=0.5),
    A.VerticalFlip(p=0.5),
    A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ToTensorV2()
])
```

## 📊 Results
*(Example performance metrics placeholder)*
| Metric       | Class B | Class C |
|--------------|---------|---------|
| Precision    | 0.92    | 0.89    |
| Recall       | 0.88    | 0.91    |
| F1-Score     | 0.90    | 0.90    |

Confusion Matrix:
```
[[850  50]
 [ 45 855]]
```

## 🚀 Getting Started
1. Clone the repository:
```bash
git clone https://github.com/yourusername/mammography-classification.git
cd mammography-classification
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the Jupyter notebook:
```bash
jupyter notebook soumia.ipynb
```

## 📦 Dependencies
- Python 3.10
- PyTorch 2.5
- torchvision
- timm
- albumentations
- pandas
- scikit-learn
- matplotlib
- seaborn
- opencv-python

## 📜 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- RSNA for providing the dataset
- Facebook Research for the DeiT model
- Kaggle community for dataset preprocessing
```

### Recommended Enhancements:
1. **Add actual performance metrics** once you have model results
2. **Include visualizations** from your EDA (replace placeholder)
3. **Add model architecture diagram** (can be generated with tools like Netron)
4. **Include training curves** (loss/accuracy over epochs)
5. **Add citation** for the RSNA dataset and DeiT paper
6. **Create a demo GIF** showing sample predictions

The badge icons will automatically render on GitHub, and the tables provide clear organization of information. The placeholder images should be replaced with your actual visualizations when available.
