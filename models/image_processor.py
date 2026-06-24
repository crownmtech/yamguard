"""
YamGuard - Image Processing Engine
Handles image capture, preprocessing, segmentation, and enhancement
"""

import os
import cv2
import numpy as np
from typing import Tuple, Optional, Dict, Any, List
from PIL import Image as PILImage

from utils.constants import UPLOADS_DIR, PROCESSING_RESOLUTION, CAPTURE_RESOLUTION
from utils.helpers import generate_filename, ensure_directories


class ImageProcessor:
    """
    Image processing pipeline for yam tuber analysis.
    Handles all image operations from capture through analysis preparation.
    """
    
    def __init__(self):
        self.target_size = PROCESSING_RESOLUTION
        self.capture_size = CAPTURE_RESOLUTION
        ensure_directories()
    
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """
        Load image from file path
        
        Args:
            image_path: Path to image file
            
        Returns:
            Image as numpy array or None if failed
        """
        if not os.path.exists(image_path):
            return None
        
        try:
            # Load with OpenCV
            image = cv2.imread(image_path)
            if image is None:
                # Try with PIL
                pil_image = PILImage.open(image_path)
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return image
        except Exception as e:
            print(f"Error loading image: {e}")
            return None
    
    def save_image(self, image: np.ndarray, filename: Optional[str] = None,
                   directory: str = UPLOADS_DIR) -> str:
        """
        Save image to file
        
        Args:
            image: Image array to save
            filename: Optional filename (auto-generated if None)
            directory: Target directory
            
        Returns:
            Path to saved file
        """
        os.makedirs(directory, exist_ok=True)
        
        if filename is None:
            filename = generate_filename("capture", "jpg")
        
        file_path = os.path.join(directory, filename)
        cv2.imwrite(file_path, image, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return file_path
    
    def resize_image(self, image: np.ndarray, 
                    size: Tuple[int, int] = None) -> np.ndarray:
        """
        Resize image to target dimensions
        
        Args:
            image: Input image
            size: Target size (width, height)
            
        Returns:
            Resized image
        """
        if size is None:
            size = self.target_size
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        Full preprocessing pipeline
        
        Args:
            image: Raw captured image
            
        Returns:
            Preprocessed image ready for analysis
        """
        # Resize for processing efficiency
        processed = self.resize_image(image)
        
        # Denoise
        processed = self.denoise(processed)
        
        # White balance
        processed = self.white_balance(processed)
        
        # Enhance contrast
        processed = self.enhance_contrast(processed)
        
        # Normalize
        processed = self.normalize(processed)
        
        return processed
    
    def denoise(self, image: np.ndarray, strength: int = 10) -> np.ndarray:
        """
        Apply noise reduction
        
        Args:
            image: Input image
            strength: Denoising strength
            
        Returns:
            Denoised image
        """
        if len(image.shape) == 3:
            return cv2.fastNlMeansDenoisingColored(image, None, strength, strength, 7, 21)
        else:
            return cv2.fastNlMeansDenoising(image, None, strength, 7, 21)
    
    def white_balance(self, image: np.ndarray) -> np.ndarray:
        """
        Apply automatic white balance
        
        Args:
            image: Input image
            
        Returns:
            White-balanced image
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Calculate mean values for a and b channels
        a_mean = np.mean(a)
        b_mean = np.mean(b)
        
        # Shift channels to neutral gray
        a = a - a_mean + 128
        b = b - b_mean + 128
        
        # Merge channels back
        balanced = cv2.merge([l, a.astype(np.uint8), b.astype(np.uint8)])
        
        # Convert back to BGR
        return cv2.cvtColor(balanced, cv2.COLOR_LAB2BGR)
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast using CLAHE
        
        Args:
            image: Input image
            
        Returns:
            Contrast-enhanced image
        """
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        enhanced = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    def normalize(self, image: np.ndarray) -> np.ndarray:
        """
        Normalize image pixel values to [0, 1]
        
        Args:
            image: Input image
            
        Returns:
            Normalized float image
        """
        if image.dtype == np.uint8:
            return image.astype(np.float32) / 255.0
        return image.astype(np.float32)
    
    def segment_tuber(self, image: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Segment yam tuber from background
        
        Args:
            image: Preprocessed image
            
        Returns:
            (segmented_image, mask): Segmented tuber and binary mask
        """
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        else:
            gray = (image * 255).astype(np.uint8)
        
        # Gaussian blur
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Otsu's thresholding
        _, binary = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological operations to clean up
        kernel = np.ones((5, 5), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Find largest contour (assumed to be tuber)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        mask = np.zeros_like(gray)
        if contours:
            # Select largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            
            # Draw filled contour
            cv2.drawContours(mask, [largest_contour], -1, 255, -1)
            
            # Refine edges
            mask = cv2.GaussianBlur(mask, (5, 5), 0)
            _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
        
        # Apply mask to image
        if len(image.shape) == 3:
            mask_3ch = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            segmented = image * mask_3ch
        else:
            segmented = image * (mask / 255.0)
        
        return segmented, mask
    
    def detect_texture_features(self, image: np.ndarray) -> Dict[str, float]:
        """
        Extract texture features from tuber surface
        
        Args:
            image: Segmented tuber image
            
        Returns:
            Dictionary of texture features
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        else:
            gray = (image * 255).astype(np.uint8)
        
        # Remove background
        gray = gray[gray > 0]
        
        if len(gray) == 0:
            return {"contrast": 0, "homogeneity": 0, "energy": 0, "correlation": 0}
        
        # GLCM-based features
        glcm = self._compute_glcm(gray)
        
        return {
            "contrast": float(self._glcm_contrast(glcm)),
            "homogeneity": float(self._glcm_homogeneity(glcm)),
            "energy": float(self._glcm_energy(glcm)),
            "correlation": float(self._glcm_correlation(glcm)),
            "roughness": float(np.std(gray)),
            "mean_intensity": float(np.mean(gray)),
        }
    
    def _compute_glcm(self, gray: np.ndarray, 
                     distances: List[int] = [1],
                     angles: List[float] = [0, np.pi/4, np.pi/2, 3*np.pi/4]) -> np.ndarray:
        """Compute Gray Level Co-occurrence Matrix"""
        # Quantize to 32 levels
        quantized = (gray / 8).astype(np.uint8)
        quantized = np.clip(quantized, 0, 31)
        
        glcm = np.zeros((32, 32), dtype=np.float64)
        
        for d in distances:
            for angle in angles:
                dx = int(round(d * np.cos(angle)))
                dy = int(round(d * np.sin(angle)))
                
                for i in range(max(0, -dy), min(quantized.shape[0] - dy, quantized.shape[0])):
                    for j in range(max(0, -dx), min(quantized.shape[1] - dx, quantized.shape[1]) if len(quantized.shape) > 1 else 1):
                        if len(quantized.shape) > 1:
                            row, col = quantized[i, j], quantized[i + dy, j + dx]
                        else:
                            idx = i * quantized.shape[1] + j if len(quantized.shape) > 1 else i
                            if idx + dx < len(quantized):
                                row, col = quantized.flat[idx], quantized.flat[idx + dx]
                            else:
                                continue
                        glcm[row, col] += 1
        
        # Normalize
        glcm_sum = np.sum(glcm)
        if glcm_sum > 0:
            glcm /= glcm_sum
        
        return glcm
    
    def _glcm_contrast(self, glcm: np.ndarray) -> float:
        """Calculate contrast from GLCM"""
        contrast = 0
        for i in range(glcm.shape[0]):
            for j in range(glcm.shape[1]):
                contrast += (i - j) ** 2 * glcm[i, j]
        return contrast
    
    def _glcm_homogeneity(self, glcm: np.ndarray) -> float:
        """Calculate homogeneity from GLCM"""
        homogeneity = 0
        for i in range(glcm.shape[0]):
            for j in range(glcm.shape[1]):
                homogeneity += glcm[i, j] / (1 + abs(i - j))
        return homogeneity
    
    def _glcm_energy(self, glcm: np.ndarray) -> float:
        """Calculate energy (ASM) from GLCM"""
        return np.sum(glcm ** 2)
    
    def _glcm_correlation(self, glcm: np.ndarray) -> float:
        """Calculate correlation from GLCM"""
        mean_i = np.sum(np.arange(glcm.shape[0]) * np.sum(glcm, axis=1))
        mean_j = np.sum(np.arange(glcm.shape[1]) * np.sum(glcm, axis=0))
        
        std_i = np.sqrt(np.sum(((np.arange(glcm.shape[0]) - mean_i) ** 2) * np.sum(glcm, axis=1)))
        std_j = np.sqrt(np.sum(((np.arange(glcm.shape[1]) - mean_j) ** 2) * np.sum(glcm, axis=0)))
        
        if std_i == 0 or std_j == 0:
            return 0
        
        correlation = 0
        for i in range(glcm.shape[0]):
            for j in range(glcm.shape[1]):
                correlation += (i - mean_i) * (j - mean_j) * glcm[i, j]
        
        return correlation / (std_i * std_j)
    
    def create_thumbnail(self, image: np.ndarray, 
                        size: Tuple[int, int] = (200, 200)) -> np.ndarray:
        """
        Create thumbnail of image
        
        Args:
            image: Input image
            size: Thumbnail dimensions
            
        Returns:
            Thumbnail image
        """
        return cv2.resize(image, size, interpolation=cv2.INTER_AREA)
    
    def get_image_quality_score(self, image: np.ndarray) -> float:
        """
        Calculate image quality score
        
        Args:
            image: Input image
            
        Returns:
            Quality score (0-100)
        """
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Laplacian variance (sharpness)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        sharpness = min(100, laplacian_var / 10)
        
        # Brightness
        mean_brightness = np.mean(gray)
        brightness_score = 100 - abs(mean_brightness - 128) / 1.28
        
        # Contrast
        contrast = np.std(gray)
        contrast_score = min(100, contrast * 2)
        
        # Overall quality
        quality = (sharpness * 0.4 + brightness_score * 0.3 + contrast_score * 0.3)
        
        return round(max(0, min(100, quality)), 1)
    
    def detect_defects(self, image: np.ndarray, 
                      mask: np.ndarray) -> List[Dict[str, Any]]:
        """
        Detect visual defects on tuber surface
        
        Args:
            image: Segmented image
            mask: Binary mask
            
        Returns:
            List of detected defects with positions and types
        """
        defects = []
        
        if len(image.shape) == 3:
            gray = cv2.cvtColor((image * 255).astype(np.uint8), cv2.COLOR_BGR2GRAY)
        else:
            gray = (image * 255).astype(np.uint8)
        
        # Dark spot detection
        _, dark_spots = cv2.threshold(gray, 60, 255, cv2.THRESH_BINARY_INV)
        dark_spots = cv2.bitwise_and(dark_spots, mask)
        
        contours, _ = cv2.findContours(dark_spots, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 50:  # Filter small noise
                x, y, w, h = cv2.boundingRect(contour)
                defects.append({
                    "type": "dark_spot",
                    "area": float(area),
                    "position": (x, y, w, h),
                    "severity": "high" if area > 500 else "medium" if area > 200 else "low"
                })
        
        # Texture anomaly detection
        local_std = cv2.blur(gray.astype(np.float32) ** 2, (15, 15)) - cv2.blur(gray.astype(np.float32), (15, 15)) ** 2
        local_std = np.sqrt(np.abs(local_std))
        
        _, anomalies = cv2.threshold(local_std.astype(np.uint8), 30, 255, cv2.THRESH_BINARY)
        anomalies = cv2.bitwise_and(anomalies, mask)
        
        anomaly_contours, _ = cv2.findContours(anomalies, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in anomaly_contours:
            area = cv2.contourArea(contour)
            if area > 100:
                x, y, w, h = cv2.boundingRect(contour)
                defects.append({
                    "type": "texture_anomaly",
                    "area": float(area),
                    "position": (x, y, w, h),
                    "severity": "medium"
                })
        
        return defects
