"""
YamGuard - Spectral Feature Extractor
Extracts features from hyperspectral data for machine learning classification
"""

import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from utils.constants import PCA_COMPONENTS, FEATURE_VECTOR_SIZE


class FeatureExtractor:
    """
    Extracts features from hyperspectral data for classification.
    Supports multiple feature types: statistical, spectral indices, shape, texture, and PCA.
    """
    
    def __init__(self, n_components: int = PCA_COMPONENTS):
        self.n_components = n_components
        self.pca = PCA(n_components=n_components)
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def extract_all_features(self, hyper_cube: np.ndarray, 
                            mask: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Extract comprehensive feature set from hyperspectral cube
        
        Args:
            hyper_cube: Hyperspectral data cube
            mask: Optional ROI mask
            
        Returns:
            Dictionary containing all feature types
        """
        features = {}
        
        # Statistical features
        features['statistical'] = self.extract_statistical_features(hyper_cube, mask)
        
        # Spectral features
        features['spectral'] = self.extract_spectral_features(hyper_cube, mask)
        
        # Shape features
        if mask is not None:
            features['shape'] = self.extract_shape_features(mask)
        
        # Texture features
        features['texture'] = self.extract_texture_features(hyper_cube, mask)
        
        # PCA features
        features['pca'] = self.extract_pca_features(hyper_cube, mask)
        
        # Combine into feature vector
        feature_vector = self._combine_features(features)
        features['feature_vector'] = feature_vector.tolist()
        
        return features
    
    def extract_statistical_features(self, hyper_cube: np.ndarray,
                                     mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Extract statistical features from hyperspectral data
        
        Args:
            hyper_cube: Hyperspectral cube
            mask: Optional ROI mask
            
        Returns:
            Dictionary of statistical features
        """
        if mask is not None:
            masked_data = hyper_cube[mask > 0, :]
        else:
            masked_data = hyper_cube.reshape(-1, hyper_cube.shape[-1])
        
        if len(masked_data) == 0:
            return self._empty_statistical_features()
        
        # Band-wise statistics
        band_means = np.mean(masked_data, axis=0)
        band_stds = np.std(masked_data, axis=0)
        band_mins = np.min(masked_data, axis=0)
        band_maxs = np.max(masked_data, axis=0)
        
        # Overall statistics
        features = {
            # Mean statistics across bands
            'mean_reflectance': float(np.mean(band_means)),
            'std_reflectance': float(np.mean(band_stds)),
            'min_reflectance': float(np.min(band_mins)),
            'max_reflectance': float(np.max(band_maxs)),
            
            # Coefficient of variation
            'cv_reflectance': float(np.mean(band_stds) / (np.mean(band_means) + 1e-6)),
            
            # Spectral range
            'spectral_range': float(np.max(band_maxs) - np.min(band_mins)),
            
            # Band ratios
            'blue_red_ratio': float(np.mean(band_means[:20]) / (np.mean(band_means[50:70]) + 1e-6)),
            'nir_red_ratio': float(np.mean(band_means[80:]) / (np.mean(band_means[50:70]) + 1e-6)),
            'green_red_ratio': float(np.mean(band_means[30:50]) / (np.mean(band_means[50:70]) + 1e-6)),
            
            # Moments
            'skewness': float(self._calculate_skewness(band_means)),
            'kurtosis': float(self._calculate_kurtosis(band_means)),
            
            # Entropy
            'spectral_entropy': float(self._calculate_entropy(band_means)),
        }
        
        return features
    
    def extract_spectral_features(self, hyper_cube: np.ndarray,
                                  mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Extract spectral index features
        
        Args:
            hyper_cube: Hyperspectral cube
            mask: Optional ROI mask
            
        Returns:
            Dictionary of spectral index features
        """
        if mask is not None:
            data = hyper_cube[mask > 0, :]
        else:
            data = hyper_cube.reshape(-1, hyper_cube.shape[-1])
        
        if len(data) == 0:
            return self._empty_spectral_features()
        
        n_bands = hyper_cube.shape[-1]
        
        # Approximate wavelength bands (assuming 400-1000nm range)
        blue_idx = int(n_bands * 0.1)   # ~440nm
        green_idx = int(n_bands * 0.25)  # ~550nm
        red_idx = int(n_bands * 0.45)    # ~670nm
        red_edge_idx = int(n_bands * 0.55)  # ~720nm
        nir_idx = int(n_bands * 0.65)    # ~800nm
        swir_idx = int(n_bands * 0.9)    # ~940nm
        
        mean_spectrum = np.mean(data, axis=0)
        
        # Vegetation indices
        ndvi = self._safe_divide(
            mean_spectrum[nir_idx] - mean_spectrum[red_idx],
            mean_spectrum[nir_idx] + mean_spectrum[red_idx]
        )
        
        gndvi = self._safe_divide(
            mean_spectrum[nir_idx] - mean_spectrum[green_idx],
            mean_spectrum[nir_idx] + mean_spectrum[green_idx]
        )
        
        savi = self._safe_divide(
            1.5 * (mean_spectrum[nir_idx] - mean_spectrum[red_idx]),
            mean_spectrum[nir_idx] + mean_spectrum[red_idx] + 0.5
        )
        
        # Water index
        ndwi = self._safe_divide(
            mean_spectrum[green_idx] - mean_spectrum[nir_idx],
            mean_spectrum[green_idx] + mean_spectrum[nir_idx]
        )
        
        # Red edge normalized difference vegetation index
        rendvi = self._safe_divide(
            mean_spectrum[nir_idx] - mean_spectrum[red_edge_idx],
            mean_spectrum[nir_idx] + mean_spectrum[red_edge_idx]
        )
        
        # Photochemical reflectance index
        pri = self._safe_divide(
            mean_spectrum[int(n_bands * 0.26)] - mean_spectrum[int(n_bands * 0.35)],
            mean_spectrum[int(n_bands * 0.26)] + mean_spectrum[int(n_bands * 0.35)]
        )
        
        # Structural indices
        si = mean_spectrum[nir_idx] / (mean_spectrum[green_idx] + 1e-6)
        
        features = {
            'NDVI': float(ndvi),
            'GNDVI': float(gndvi),
            'SAVI': float(savi),
            'NDWI': float(ndwi),
            'RENDVI': float(rendvi),
            'PRI': float(pri),
            'SI': float(si),
            'red_edge_position': float(self._find_red_edge_position(mean_spectrum)),
            'nir_plateau': float(np.mean(mean_spectrum[nir_idx:])),
            'blue_absorption_depth': float(1 - np.mean(mean_spectrum[:blue_idx + 10])),
            'red_absorption_depth': float(1 - mean_spectrum[red_idx]),
        }
        
        return features
    
    def extract_shape_features(self, mask: np.ndarray) -> Dict[str, float]:
        """
        Extract shape features from binary mask
        
        Args:
            mask: Binary segmentation mask
            
        Returns:
            Dictionary of shape features
        """
        contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return self._empty_shape_features()
        
        largest_contour = max(contours, key=cv2.contourArea)
        
        area = cv2.contourArea(largest_contour)
        perimeter = cv2.arcLength(largest_contour, True)
        
        # Bounding box
        x, y, w, h = cv2.boundingRect(largest_contour)
        
        # Ellipse fit
        if len(largest_contour) >= 5:
            ellipse = cv2.fitEllipse(largest_contour)
            major_axis = max(ellipse[1])
            minor_axis = min(ellipse[1])
            orientation = ellipse[2]
        else:
            major_axis = minor_axis = max(w, h)
            orientation = 0
        
        features = {
            'area': float(area),
            'perimeter': float(perimeter),
            'equivalent_diameter': float(np.sqrt(4 * area / np.pi)),
            'aspect_ratio': float(w / h) if h > 0 else 0,
            'extent': float(area / (w * h)) if w * h > 0 else 0,
            'solidity': float(area / cv2.contourArea(cv2.convexHull(largest_contour))) if cv2.contourArea(cv2.convexHull(largest_contour)) > 0 else 0,
            'compactness': float(4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0,
            'eccentricity': float(np.sqrt(1 - (minor_axis / major_axis) ** 2)) if major_axis > 0 else 0,
            'elongation': float(major_axis / minor_axis) if minor_axis > 0 else 0,
            'orientation': float(orientation),
            'circularity': float(4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0,
        }
        
        return features
    
    def extract_texture_features(self, hyper_cube: np.ndarray,
                                 mask: Optional[np.ndarray] = None) -> Dict[str, float]:
        """
        Extract texture features from key bands
        
        Args:
            hyper_cube: Hyperspectral cube
            mask: Optional ROI mask
            
        Returns:
            Dictionary of texture features
        """
        import cv2
        
        n_bands = hyper_cube.shape[-1]
        
        # Select key bands for texture analysis
        red_band = hyper_cube[:, :, int(n_bands * 0.45)]
        nir_band = hyper_cube[:, :, int(n_bands * 0.65)]
        
        if mask is not None:
            red_band = red_band * (mask > 0)
            nir_band = nir_band * (mask > 0)
        
        features = {}
        
        # GLCM features for red band
        red_glcm = self._compute_glcm(red_band)
        features['red_contrast'] = float(self._glcm_contrast(red_glcm))
        features['red_homogeneity'] = float(self._glcm_homogeneity(red_glcm))
        features['red_energy'] = float(self._glcm_energy(red_glcm))
        features['red_correlation'] = float(self._glcm_correlation(red_glcm))
        
        # GLCM features for NIR band
        nir_glcm = self._compute_glcm(nir_band)
        features['nir_contrast'] = float(self._glcm_contrast(nir_glcm))
        features['nir_homogeneity'] = float(self._glcm_homogeneity(nir_glcm))
        features['nir_energy'] = float(self._glcm_energy(nir_glcm))
        features['nir_correlation'] = float(self._glcm_correlation(nir_glcm))
        
        # Gabor filter features
        gabor_features = self._extract_gabor_features(red_band)
        features.update(gabor_features)
        
        # Local binary pattern features
        lbp_features = self._extract_lbp_features(red_band)
        features.update(lbp_features)
        
        return features
    
    def extract_pca_features(self, hyper_cube: np.ndarray,
                            mask: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Extract PCA features from hyperspectral data
        
        Args:
            hyper_cube: Hyperspectral cube
            mask: Optional ROI mask
            
        Returns:
            Dictionary of PCA features
        """
        if mask is not None:
            data = hyper_cube[mask > 0, :]
        else:
            data = hyper_cube.reshape(-1, hyper_cube.shape[-1])
        
        if len(data) == 0 or len(data) < self.n_components:
            return self._empty_pca_features()
        
        # Sample data for PCA if too large
        if len(data) > 10000:
            indices = np.random.choice(len(data), 10000, replace=False)
            sample_data = data[indices]
        else:
            sample_data = data
        
        # Scale data
        scaled_data = self.scaler.fit_transform(sample_data)
        
        # Fit PCA
        pca_data = self.pca.fit_transform(scaled_data)
        
        features = {
            'explained_variance_ratio': self.pca.explained_variance_ratio_.tolist(),
            'cumulative_variance': np.cumsum(self.pca.explained_variance_ratio_).tolist(),
            'pc1_mean': float(np.mean(pca_data[:, 0])),
            'pc2_mean': float(np.mean(pca_data[:, 1])) if pca_data.shape[1] > 1 else 0,
            'pc3_mean': float(np.mean(pca_data[:, 2])) if pca_data.shape[1] > 2 else 0,
            'pc1_std': float(np.std(pca_data[:, 0])),
            'pc2_std': float(np.std(pca_data[:, 1])) if pca_data.shape[1] > 1 else 0,
            'pc3_std': float(np.std(pca_data[:, 2])) if pca_data.shape[1] > 2 else 0,
        }
        
        # Store PCA components for visualization
        features['components'] = self.pca.components_.tolist()
        features['transformed_data'] = pca_data[:100].tolist()  # Sample for visualization
        
        return features
    
    def _combine_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        Combine all features into a single feature vector
        
        Args:
            features: Dictionary of all feature types
            
        Returns:
            Combined feature vector
        """
        feature_list = []
        
        # Add statistical features
        if 'statistical' in features:
            feature_list.extend(list(features['statistical'].values()))
        
        # Add spectral features
        if 'spectral' in features:
            feature_list.extend(list(features['spectral'].values()))
        
        # Add shape features
        if 'shape' in features:
            feature_list.extend(list(features['shape'].values()))
        
        # Add texture features
        if 'texture' in features:
            feature_list.extend(list(features['texture'].values()))
        
        # Add PCA features (select numerical ones)
        if 'pca' in features:
            pca_dict = features['pca']
            numerical_pca = [
                pca_dict.get('pc1_mean', 0),
                pca_dict.get('pc2_mean', 0),
                pca_dict.get('pc3_mean', 0),
                pca_dict.get('pc1_std', 0),
                pca_dict.get('pc2_std', 0),
                pca_dict.get('pc3_std', 0),
            ]
            feature_list.extend(numerical_pca)
        
        # Pad or truncate to fixed size
        feature_vector = np.array(feature_list, dtype=np.float32)
        
        if len(feature_vector) < FEATURE_VECTOR_SIZE:
            feature_vector = np.pad(feature_vector, 
                                  (0, FEATURE_VECTOR_SIZE - len(feature_vector)),
                                  mode='constant')
        elif len(feature_vector) > FEATURE_VECTOR_SIZE:
            feature_vector = feature_vector[:FEATURE_VECTOR_SIZE]
        
        # Normalize
        feature_vector = (feature_vector - np.mean(feature_vector)) / (np.std(feature_vector) + 1e-6)
        
        return feature_vector
    
    def _compute_glcm(self, image: np.ndarray, levels: int = 32) -> np.ndarray:
        """Compute Gray Level Co-occurrence Matrix"""
        # Quantize image
        quantized = (image * (levels - 1)).astype(np.uint8)
        
        glcm = np.zeros((levels, levels), dtype=np.float64)
        
        # Compute co-occurrences (horizontal)
        for i in range(quantized.shape[0]):
            for j in range(quantized.shape[1] - 1):
                glcm[quantized[i, j], quantized[i, j + 1]] += 1
        
        # Normalize
        glcm_sum = np.sum(glcm)
        if glcm_sum > 0:
            glcm /= glcm_sum
        
        return glcm
    
    def _glcm_contrast(self, glcm: np.ndarray) -> float:
        """GLCM contrast feature"""
        contrast = 0
        for i in range(glcm.shape[0]):
            for j in range(glcm.shape[1]):
                contrast += (i - j) ** 2 * glcm[i, j]
        return contrast
    
    def _glcm_homogeneity(self, glcm: np.ndarray) -> float:
        """GLCM homogeneity feature"""
        homogeneity = 0
        for i in range(glcm.shape[0]):
            for j in range(glcm.shape[1]):
                homogeneity += glcm[i, j] / (1 + abs(i - j))
        return homogeneity
    
    def _glcm_energy(self, glcm: np.ndarray) -> float:
        """GLCM energy/ASM feature"""
        return float(np.sum(glcm ** 2))
    
    def _glcm_correlation(self, glcm: np.ndarray) -> float:
        """GLCM correlation feature"""
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
        
        return float(correlation / (std_i * std_j))
    
    def _extract_gabor_features(self, image: np.ndarray) -> Dict[str, float]:
        """Extract Gabor filter features"""
        import cv2
        
        features = {}
        ksize = 15
        sigma = 5.0
        lambd = 10.0
        gamma = 0.5
        
        for theta_idx, theta in enumerate([0, np.pi/4, np.pi/2, 3*np.pi/4]):
            kernel = cv2.getGaborKernel((ksize, ksize), sigma, theta, lambd, gamma)
            filtered = cv2.filter2D((image * 255).astype(np.uint8), cv2.CV_32F, kernel)
            
            features[f'gabor_mean_{theta_idx}'] = float(np.mean(filtered))
            features[f'gabor_std_{theta_idx}'] = float(np.std(filtered))
        
        return features
    
    def _extract_lbp_features(self, image: np.ndarray, P: int = 8, R: int = 1) -> Dict[str, float]:
        """Extract Local Binary Pattern features"""
        from skimage.feature import local_binary_pattern
        
        lbp = local_binary_pattern((image * 255).astype(np.uint8), P, R, method='uniform')
        
        # Histogram of LBP
        n_bins = int(lbp.max() + 1)
        hist, _ = np.histogram(lbp, bins=n_bins, range=(0, n_bins), density=True)
        
        features = {
            'lbp_entropy': float(-np.sum(hist * np.log2(hist + 1e-7))),
            'lbp_energy': float(np.sum(hist ** 2)),
        }
        
        # Add histogram bins
        for i, val in enumerate(hist[:10]):
            features[f'lbp_hist_{i}'] = float(val)
        
        return features
    
    def _find_red_edge_position(self, spectrum: np.ndarray) -> float:
        """Find red edge inflection point"""
        # Red edge is where derivative is maximum in red-NIR region
        red_edge_region = spectrum[int(len(spectrum) * 0.4):int(len(spectrum) * 0.6)]
        if len(red_edge_region) < 2:
            return 0
        derivative = np.diff(red_edge_region)
        if len(derivative) == 0:
            return 0
        max_derivative_idx = np.argmax(derivative)
        return float(max_derivative_idx / len(derivative))
    
    def _calculate_skewness(self, data: np.ndarray) -> float:
        """Calculate skewness"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return float(np.mean(((data - mean) / std) ** 3))
    
    def _calculate_kurtosis(self, data: np.ndarray) -> float:
        """Calculate kurtosis"""
        mean = np.mean(data)
        std = np.std(data)
        if std == 0:
            return 0
        return float(np.mean(((data - mean) / std) ** 4) - 3)
    
    def _calculate_entropy(self, data: np.ndarray, bins: int = 32) -> float:
        """Calculate Shannon entropy"""
        hist, _ = np.histogram(data, bins=bins, density=True)
        hist = hist[hist > 0]
        return float(-np.sum(hist * np.log2(hist)))
    
    def _safe_divide(self, a: float, b: float) -> float:
        """Safe division avoiding division by zero"""
        return a / (b + 1e-6) if b != 0 else 0
    
    # Empty feature templates
    def _empty_statistical_features(self) -> Dict[str, float]:
        return {k: 0.0 for k in ['mean_reflectance', 'std_reflectance', 'min_reflectance',
                                  'max_reflectance', 'cv_reflectance', 'spectral_range',
                                  'blue_red_ratio', 'nir_red_ratio', 'green_red_ratio',
                                  'skewness', 'kurtosis', 'spectral_entropy']}
    
    def _empty_spectral_features(self) -> Dict[str, float]:
        return {k: 0.0 for k in ['NDVI', 'GNDVI', 'SAVI', 'NDWI', 'RENDVI', 'PRI', 'SI',
                                  'red_edge_position', 'nir_plateau', 'blue_absorption_depth',
                                  'red_absorption_depth']}
    
    def _empty_shape_features(self) -> Dict[str, float]:
        return {k: 0.0 for k in ['area', 'perimeter', 'equivalent_diameter', 'aspect_ratio',
                                  'extent', 'solidity', 'compactness', 'eccentricity',
                                  'elongation', 'orientation', 'circularity']}
    
    def _empty_pca_features(self) -> Dict[str, Any]:
        return {
            'explained_variance_ratio': [0] * self.n_components,
            'cumulative_variance': [0] * self.n_components,
            'pc1_mean': 0, 'pc2_mean': 0, 'pc3_mean': 0,
            'pc1_std': 0, 'pc2_std': 0, 'pc3_std': 0,
            'components': [],
            'transformed_data': [],
        }
