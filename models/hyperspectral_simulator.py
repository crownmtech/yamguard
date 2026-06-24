"""
YamGuard - Hyperspectral Imaging Simulator
Simulates hyperspectral image acquisition from smartphone camera images
Generates synthetic spectral signatures from 400nm to 1000nm
"""

import numpy as np
from typing import List, Tuple, Dict, Any, Optional
import cv2

from utils.constants import (
    SPECTRAL_RANGE_START, SPECTRAL_RANGE_END, SPECTRAL_BANDS,
    KEY_WAVELENGTHS
)


class HyperspectralSimulator:
    """
    Simulates hyperspectral imaging system for yam tuber analysis.
    Converts RGB images to synthetic hyperspectral cubes and extracts spectral signatures.
    """
    
    def __init__(self, bands: int = SPECTRAL_BANDS):
        self.bands = bands
        self.wavelengths = np.linspace(SPECTRAL_RANGE_START, SPECTRAL_RANGE_END, bands)
        self.key_wavelengths = KEY_WAVELENGTHS
        
        # Spectral response curves for RGB channels (simplified)
        self._init_spectral_response()
    
    def _init_spectral_response(self):
        """Initialize spectral response functions for RGB to hyperspectral conversion"""
        # Red channel response (peaks around 600-650nm)
        self.red_response = np.exp(-((self.wavelengths - 625)**2) / (2 * 40**2))
        self.red_response += 0.3 * np.exp(-((self.wavelengths - 700)**2) / (2 * 50**2))
        
        # Green channel response (peaks around 530-570nm)
        self.green_response = np.exp(-((self.wavelengths - 550)**2) / (2 * 35**2))
        
        # Blue channel response (peaks around 440-480nm)
        self.blue_response = np.exp(-((self.wavelengths - 460)**2) / (2 * 30**2))
        
        # Normalize responses
        max_response = max(
            np.max(self.red_response),
            np.max(self.green_response),
            np.max(self.blue_response)
        )
        self.red_response /= max_response
        self.green_response /= max_response
        self.blue_response /= max_response
    
    def simulate_bands(self, image: np.ndarray) -> np.ndarray:
        """
        Simulate hyperspectral bands from RGB image
        
        Args:
            image: RGB image as numpy array (H, W, 3)
            
        Returns:
            hyperspectral_cube: Simulated hyperspectral cube (H, W, bands)
        """
        if image is None or image.size == 0:
            raise ValueError("Invalid input image")
        
        # Ensure image is float32
        if image.dtype != np.float32:
            image = image.astype(np.float32) / 255.0
        
        height, width = image.shape[:2]
        
        # Initialize hyperspectral cube
        hyper_cube = np.zeros((height, width, self.bands), dtype=np.float32)
        
        # Extract RGB channels
        if len(image.shape) == 3 and image.shape[2] >= 3:
            red = image[:, :, 0]
            green = image[:, :, 1]
            blue = image[:, :, 2]
        else:
            # Grayscale image
            red = green = blue = image[:, :, 0] if len(image.shape) == 3 else image
        
        # Generate synthetic hyperspectral bands using spectral response curves
        for i in range(self.bands):
            band_value = (
                red * self.red_response[i] +
                green * self.green_response[i] +
                blue * self.blue_response[i]
            )
            
            # Add vegetation spectral features based on pixel characteristics
            band_value = self._add_vegetation_features(
                band_value, red, green, blue, self.wavelengths[i]
            )
            
            hyper_cube[:, :, i] = band_value
        
        # Add realistic noise
        hyper_cube = self._add_realistic_noise(hyper_cube)
        
        return np.clip(hyper_cube, 0.0, 1.0)
    
    def _add_vegetation_features(self, band_value: np.ndarray, 
                                  red: np.ndarray, green: np.ndarray,
                                  blue: np.ndarray, wavelength: float) -> np.ndarray:
        """Add vegetation-specific spectral features"""
        # Calculate vegetation index proxy
        vegetation_proxy = (green - red) / (green + red + 1e-6)
        
        # Chlorophyll absorption at 675nm and 650nm
        if 640 <= wavelength <= 690:
            absorption_strength = np.exp(-((wavelength - 675)**2) / (2 * 15**2))
            band_value -= 0.2 * absorption_strength * vegetation_proxy
        
        # Red edge (700-750nm)
        if 700 <= wavelength <= 750:
            red_edge = (wavelength - 700) / 50.0
            band_value += 0.15 * red_edge * vegetation_proxy
        
        # NIR plateau (750-900nm)
        if 750 <= wavelength <= 900:
            nir_strength = 1.0 - 0.3 * (wavelength - 750) / 150.0
            band_value += 0.25 * nir_strength * vegetation_proxy
        
        # Water absorption at 970nm
        if 950 <= wavelength <= 990:
            water_absorption = np.exp(-((wavelength - 970)**2) / (2 * 20**2))
            band_value -= 0.15 * water_absorption
        
        # Carotenoid absorption at 470nm
        if 450 <= wavelength <= 490:
            carotenoid_absorption = np.exp(-((wavelength - 470)**2) / (2 * 20**2))
            band_value -= 0.1 * carotenoid_absorption
        
        return np.clip(band_value, 0.0, 1.0)
    
    def _add_realistic_noise(self, hyper_cube: np.ndarray) -> np.ndarray:
        """Add realistic sensor noise to hyperspectral cube"""
        # Photon shot noise (Poisson-like)
        shot_noise = np.random.normal(0, 0.005, hyper_cube.shape)
        
        # Read noise (Gaussian)
        read_noise = np.random.normal(0, 0.002, hyper_cube.shape)
        
        # Band-to-band variation
        band_noise = np.random.normal(1.0, 0.01, self.bands)
        
        noisy_cube = hyper_cube * band_noise[np.newaxis, np.newaxis, :]
        noisy_cube += shot_noise + read_noise
        
        return noisy_cube
    
    def generate_signature(self, hyper_cube: np.ndarray, 
                          mask: Optional[np.ndarray] = None) -> Tuple[List[float], List[float]]:
        """
        Generate average spectral signature from hyperspectral cube
        
        Args:
            hyper_cube: Hyperspectral cube (H, W, bands)
            mask: Optional binary mask for ROI (H, W)
            
        Returns:
            (wavelengths, reflectance): Lists of wavelengths and reflectance values
        """
        if mask is not None:
            # Use masked region
            masked_cube = hyper_cube[mask > 0, :]
            if masked_cube.size == 0:
                signature = np.mean(hyper_cube.reshape(-1, self.bands), axis=0)
            else:
                signature = np.mean(masked_cube, axis=0)
        else:
            # Use entire image
            signature = np.mean(hyper_cube.reshape(-1, self.bands), axis=0)
        
        # Smooth the signature
        signature = self._smooth_signature(signature)
        
        return self.wavelengths.tolist(), signature.tolist()
    
    def extract_reflectance(self, hyper_cube: np.ndarray, 
                           wavelength_nm: float) -> np.ndarray:
        """
        Extract reflectance image at specific wavelength
        
        Args:
            hyper_cube: Hyperspectral cube
            wavelength_nm: Target wavelength in nanometers
            
        Returns:
            Reflectance image at specified wavelength
        """
        # Find closest band
        band_idx = np.argmin(np.abs(self.wavelengths - wavelength_nm))
        return hyper_cube[:, :, band_idx]
    
    def get_band_images(self, hyper_cube: np.ndarray, 
                       band_indices: Optional[List[int]] = None) -> Dict[str, np.ndarray]:
        """
        Extract key band images for visualization
        
        Args:
            hyper_cube: Hyperspectral cube
            band_indices: Optional list of band indices to extract
            
        Returns:
            Dictionary of band images
        """
        if band_indices is None:
            # Extract key wavelength bands
            band_indices = []
            for name, wavelength in self.key_wavelengths.items():
                idx = np.argmin(np.abs(self.wavelengths - wavelength))
                band_indices.append((name, idx))
        
        band_images = {}
        for name, idx in band_indices:
            if isinstance(name, str):
                band_images[name] = hyper_cube[:, :, idx]
            else:
                band_images[f"band_{idx}"] = hyper_cube[:, :, idx]
        
        # Add false color composite (NIR, Red, Green)
        nir_idx = np.argmin(np.abs(self.wavelengths - 800))
        red_idx = np.argmin(np.abs(self.wavelengths - 650))
        green_idx = np.argmin(np.abs(self.wavelengths - 550))
        
        false_color = np.stack([
            hyper_cube[:, :, nir_idx],
            hyper_cube[:, :, red_idx],
            hyper_cube[:, :, green_idx]
        ], axis=-1)
        false_color = np.clip(false_color * 2.0, 0, 1)  # Enhance contrast
        
        band_images['false_color'] = false_color
        
        return band_images
    
    def calculate_ndvi(self, hyper_cube: np.ndarray) -> np.ndarray:
        """Calculate NDVI from hyperspectral cube"""
        nir_idx = np.argmin(np.abs(self.wavelengths - 800))
        red_idx = np.argmin(np.abs(self.wavelengths - 650))
        
        nir = hyper_cube[:, :, nir_idx]
        red = hyper_cube[:, :, red_idx]
        
        ndvi = (nir - red) / (nir + red + 1e-6)
        return np.clip(ndvi, -1, 1)
    
    def calculate_pri(self, hyper_cube: np.ndarray) -> np.ndarray:
        """Calculate Photochemical Reflectance Index"""
        # PRI = (R531 - R570) / (R531 + R570)
        idx_531 = np.argmin(np.abs(self.wavelengths - 531))
        idx_570 = np.argmin(np.abs(self.wavelengths - 570))
        
        r531 = hyper_cube[:, :, idx_531]
        r570 = hyper_cube[:, :, idx_570]
        
        pri = (r531 - r570) / (r531 + r570 + 1e-6)
        return np.clip(pri, -1, 1)
    
    def calculate_ari(self, hyper_cube: np.ndarray) -> np.ndarray:
        """Calculate Anthocyanin Reflectance Index"""
        # ARI = (1/R550) - (1/R700)
        idx_550 = np.argmin(np.abs(self.wavelengths - 550))
        idx_700 = np.argmin(np.abs(self.wavelengths - 700))
        
        r550 = hyper_cube[:, :, idx_550]
        r700 = hyper_cube[:, :, idx_700]
        
        ari = (1.0 / (r550 + 1e-6)) - (1.0 / (r700 + 1e-6))
        return ari
    
    def _smooth_signature(self, signature: np.ndarray, 
                         window_size: int = 5) -> np.ndarray:
        """Apply Savitzky-Golay-like smoothing to spectral signature"""
        if window_size < 3:
            return signature
        
        half_window = window_size // 2
        smoothed = np.copy(signature)
        
        for i in range(half_window, len(signature) - half_window):
            smoothed[i] = np.mean(signature[i - half_window:i + half_window + 1])
        
        return smoothed
    
    def generate_infected_signature(self, base_signature: List[float],
                                    severity: int = 1) -> List[float]:
        """
        Generate infected spectral signature by modifying base signature
        
        Args:
            base_signature: Healthy spectral signature
            severity: Infection severity (1-4)
            
        Returns:
            Modified spectral signature showing infection characteristics
        """
        signature = np.array(base_signature)
        
        # Reduce chlorophyll absorption with infection
        chlorophyll_region = (self.wavelengths >= 650) & (self.wavelengths <= 700)
        signature[chlorophyll_region] += 0.05 * severity * np.random.random(np.sum(chlorophyll_region))
        
        # Reduce NIR reflectance
        nir_region = self.wavelengths >= 750
        signature[nir_region] -= 0.04 * severity * np.random.random(np.sum(nir_region))
        
        # Shift red edge to longer wavelengths
        red_edge_region = (self.wavelengths >= 700) & (self.wavelengths <= 750)
        signature[red_edge_region] -= 0.03 * severity
        
        # Increase visible light reflectance (yellowing)
        visible_region = self.wavelengths < 650
        signature[visible_region] += 0.02 * severity * np.random.random(np.sum(visible_region))
        
        return np.clip(signature, 0.0, 1.0).tolist()
    
    def get_spectral_indices(self, hyper_cube: np.ndarray) -> Dict[str, float]:
        """Calculate key spectral vegetation indices"""
        ndvi = self.calculate_ndvi(hyper_cube)
        pri = self.calculate_pri(hyper_cube)
        ari = self.calculate_ari(hyper_cube)
        
        return {
            "NDVI": round(float(np.mean(ndvi)), 4),
            "PRI": round(float(np.mean(pri)), 4),
            "ARI": round(float(np.mean(ari)), 4),
            "NDVI_std": round(float(np.std(ndvi)), 4),
            "mean_reflectance_680": round(float(
                np.mean(self.extract_reflectance(hyper_cube, 680))
            ), 4),
            "mean_reflectance_800": round(float(
                np.mean(self.extract_reflectance(hyper_cube, 800))
            ), 4),
        }
