"""
YamGuard - Tuber Classification Engine
Machine learning classifier for yam tuber fungal infection detection
Architecture supports future integration with TensorFlow Lite, ONNX Mobile, PyTorch Mobile
"""

import os
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum

from utils.constants import (
    CLASSIFICATION_PROBABILITIES,
    CONFIDENCE_THRESHOLD,
    FEATURE_VECTOR_SIZE,
)
from utils.helpers import get_recommendation, get_severity_info


class ClassificationResult:
    """Classification result container"""
    
    def __init__(self, classification: str, confidence: float, 
                 severity: str, recommendation: str,
                 probabilities: Dict[str, float] = None,
                 feature_importance: Dict[str, float] = None):
        self.classification = classification
        self.confidence = confidence
        self.severity = severity
        self.recommendation = recommendation
        self.probabilities = probabilities or {}
        self.feature_importance = feature_importance or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        return {
            "classification": self.classification,
            "severity": self.severity,
            "confidence": round(self.confidence, 1),
            "recommendation": self.recommendation,
            "probabilities": self.probabilities,
            "feature_importance": self.feature_importance,
            "is_healthy": self.classification == "Healthy",
            "needs_attention": self.confidence < CONFIDENCE_THRESHOLD,
        }


class TuberClassifier:
    """
    Yam Tuber Fungal Infection Classifier
    
    Current: Simulation-based classification with realistic probability distributions
    Future: TensorFlow Lite / ONNX Mobile / PyTorch Mobile integration
    """
    
    def __init__(self):
        self.is_trained = False
        self.model_type = "simulation"  # Options: "simulation", "tflite", "onnx", "pytorch"
        self.class_names = list(CLASSIFICATION_PROBABILITIES.keys())
        self.class_weights = list(CLASSIFICATION_PROBABILITIES.values())
        
        # Feature importance weights for simulation
        self.feature_weights = self._initialize_feature_weights()
        
        # Confidence calibration parameters
        self.confidence_calibration = {
            "Healthy": (85.0, 99.5),
            "Level 1 - Early Infection": (70.0, 89.0),
            "Level 2 - Moderate Infection": (65.0, 85.0),
        }
    
    def _initialize_feature_weights(self) -> Dict[str, float]:
        """Initialize feature weights for classification"""
        return {
            # Vegetation indices (high importance)
            "NDVI": 0.15,
            "GNDVI": 0.12,
            "SAVI": 0.10,
            "RENDVI": 0.10,
            "PRI": 0.08,
            
            # Spectral features
            "red_edge_position": 0.08,
            "nir_plateau": 0.07,
            "red_absorption_depth": 0.06,
            "blue_absorption_depth": 0.05,
            
            # Statistical features
            "mean_reflectance": 0.05,
            "spectral_entropy": 0.04,
            "cv_reflectance": 0.03,
            
            # Shape and texture (lower importance for spectral classification)
            "compactness": 0.02,
            "roughness": 0.02,
            "contrast": 0.01,
            "homogeneity": 0.01,
            "energy": 0.01,
        }
    
    def analyze_tuber(self, features: Dict[str, Any], 
                      spectral_indices: Dict[str, float] = None) -> ClassificationResult:
        """
        Analyze tuber and classify fungal infection
        
        Args:
            features: Extracted features dictionary
            spectral_indices: Spectral vegetation indices
            
        Returns:
            ClassificationResult with classification, confidence, and recommendation
        """
        if self.model_type == "simulation":
            return self._simulate_classification(features, spectral_indices)
        elif self.model_type == "tflite":
            return self._classify_tflite(features)
        elif self.model_type == "onnx":
            return self._classify_onnx(features)
        elif self.model_type == "pytorch":
            return self._classify_pytorch(features)
        else:
            return self._simulate_classification(features, spectral_indices)
    
    def _simulate_classification(self, features: Dict[str, Any],
                                  spectral_indices: Dict[str, float] = None) -> ClassificationResult:
        """
        Simulate classification with realistic behavior
        
        Uses spectral indices and features to determine classification
        with weighted random selection biased by feature values.
        """
        # Calculate feature-based scores for each class
        scores = self._calculate_class_scores(features, spectral_indices)
        
        # Normalize scores to probabilities
        total_score = sum(scores.values())
        if total_score > 0:
            probabilities = {k: v / total_score for k, v in scores.items()}
        else:
            probabilities = CLASSIFICATION_PROBABILITIES.copy()
        
        # Select class based on probabilities
        class_names = list(probabilities.keys())
        class_probs = list(probabilities.values())
        
        selected_idx = np.random.choice(len(class_names), p=class_probs)
        selected_class = class_names[selected_idx]
        
        # Calculate confidence based on class
        confidence_range = self.confidence_calibration[selected_class]
        confidence = np.random.uniform(confidence_range[0], confidence_range[1])
        
        # Adjust confidence based on feature strength
        if spectral_indices:
            ndvi = spectral_indices.get("NDVI", 0.5)
            if selected_class == "Healthy" and ndvi > 0.7:
                confidence = min(99.5, confidence + 5)
            elif selected_class != "Healthy" and ndvi < 0.5:
                confidence = min(99.5, confidence + 3)
        
        # Generate feature importance
        feature_importance = self._calculate_feature_importance(features)
        
        return ClassificationResult(
            classification=selected_class,
            confidence=round(confidence, 1),
            severity=selected_class,
            recommendation=get_recommendation(selected_class),
            probabilities={k: round(v * 100, 1) for k, v in probabilities.items()},
            feature_importance=feature_importance,
        )
    
    def _calculate_class_scores(self, features: Dict[str, Any],
                                spectral_indices: Dict[str, float] = None) -> Dict[str, float]:
        """Calculate class scores based on features"""
        scores = {name: weight for name, weight in CLASSIFICATION_PROBABILITIES.items()}
        
        if spectral_indices:
            ndvi = spectral_indices.get("NDVI", 0.5)
            
            # NDVI-based adjustments
            if ndvi > 0.7:
                scores["Healthy"] *= 1.5
                scores["Level 1 - Early Infection"] *= 0.8
                scores["Level 2 - Moderate Infection"] *= 0.5
            elif ndvi > 0.5:
                scores["Healthy"] *= 1.2
                scores["Level 1 - Early Infection"] *= 1.1
            elif ndvi > 0.3:
                scores["Healthy"] *= 0.7
                scores["Level 1 - Early Infection"] *= 1.3
                scores["Level 2 - Moderate Infection"] *= 1.2
            else:
                scores["Healthy"] *= 0.4
                scores["Level 1 - Early Infection"] *= 1.1
                scores["Level 2 - Moderate Infection"] *= 1.4
            
            # PRI-based adjustments
            pri = spectral_indices.get("PRI", 0)
            if pri < -0.1:
                scores["Healthy"] *= 0.8
                scores["Level 1 - Early Infection"] *= 1.2
        
        # Feature-based adjustments
        if features:
            spectral_features = features.get("spectral", {})
            statistical_features = features.get("statistical", {})
            
            # Spectral entropy (higher = more complex = more likely infected)
            entropy = statistical_features.get("spectral_entropy", 3.0)
            if entropy > 4.0:
                scores["Healthy"] *= 0.8
                scores["Level 2 - Moderate Infection"] *= 1.2
            
            # Red absorption depth
            red_depth = spectral_features.get("red_absorption_depth", 0.5)
            if red_depth < 0.3:
                scores["Healthy"] *= 0.7
                scores["Level 1 - Early Infection"] *= 1.3
        
        # Ensure minimum scores
        scores = {k: max(v, 0.05) for k, v in scores.items()}
        
        return scores
    
    def _calculate_feature_importance(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate relative feature importance"""
        importance = {}
        
        # Spectral features importance
        if "spectral" in features:
            for key, weight in self.feature_weights.items():
                if key in features["spectral"]:
                    value = features["spectral"][key]
                    importance[key] = round(abs(value) * weight * 100, 2)
        
        # Sort by importance
        importance = dict(sorted(importance.items(), 
                                key=lambda x: x[1], reverse=True)[:10])
        
        return importance
    
    def _classify_tflite(self, features: Dict[str, Any]) -> ClassificationResult:
        """
        Classify using TensorFlow Lite model
        Placeholder for future TFLite integration
        """
        # TODO: Implement TensorFlow Lite inference
        # interpreter = tf.lite.Interpreter(model_path="model.tflite")
        # interpreter.allocate_tensors()
        # ...
        return self._simulate_classification(features)
    
    def _classify_onnx(self, features: Dict[str, Any]) -> ClassificationResult:
        """
        Classify using ONNX Mobile model
        Placeholder for future ONNX integration
        """
        # TODO: Implement ONNX inference
        return self._simulate_classification(features)
    
    def _classify_pytorch(self, features: Dict[str, Any]) -> ClassificationResult:
        """
        Classify using PyTorch Mobile model
        Placeholder for future PyTorch Mobile integration
        """
        # TODO: Implement PyTorch Mobile inference
        return self._simulate_classification(features)
    
    def load_model(self, model_path: str, model_type: str = "tflite") -> bool:
        """
        Load a trained model for inference
        
        Args:
            model_path: Path to model file
            model_type: Model framework type
            
        Returns:
            True if model loaded successfully
        """
        if not os.path.exists(model_path):
            return False
        
        self.model_type = model_type
        
        if model_type == "tflite":
            # TODO: Load TFLite model
            pass
        elif model_type == "onnx":
            # TODO: Load ONNX model
            pass
        elif model_type == "pytorch":
            # TODO: Load PyTorch Mobile model
            pass
        
        self.is_trained = True
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get current model information"""
        return {
            "model_type": self.model_type,
            "is_trained": self.is_trained,
            "class_names": self.class_names,
            "input_size": FEATURE_VECTOR_SIZE,
            "confidence_threshold": CONFIDENCE_THRESHOLD,
            "supported_frameworks": ["simulation", "tflite", "onnx", "pytorch"],
        }
    
    def calibrate_confidence(self, raw_confidence: float, 
                            class_name: str) -> float:
        """
        Calibrate confidence score for better reliability
        
        Args:
            raw_confidence: Raw confidence from model
            class_name: Predicted class name
            
        Returns:
            Calibrated confidence score
        """
        # Apply temperature scaling
        temperature = 1.5
        calibrated = raw_confidence / temperature
        
        # Ensure within valid range
        return round(max(50.0, min(99.9, calibrated)), 1)
    
    def generate_explanation(self, result: ClassificationResult,
                            features: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation for classification
        
        Args:
            result: Classification result
            features: Extracted features
            
        Returns:
            Explanation text
        """
        explanations = []
        
        if result.classification == "Healthy":
            explanations.append("The tuber shows normal spectral characteristics with strong vegetation indices.")
            if features.get("spectral", {}).get("NDVI", 0) > 0.7:
                explanations.append("High NDVI value indicates healthy chlorophyll content.")
        elif "Level 1" in result.classification:
            explanations.append("Early signs of stress detected in spectral signature.")
            explanations.append("Minor deviations in red edge and NIR regions suggest initial infection.")
        elif "Level 2" in result.classification:
            explanations.append("Moderate infection indicated by significant spectral changes.")
            explanations.append("Reduced chlorophyll absorption and altered NIR reflectance observed.")
        
        # Add feature-based explanation
        if result.feature_importance:
            top_feature = list(result.feature_importance.keys())[0]
            explanations.append(f"Key indicator: {top_feature} shows significant deviation.")
        
        return " ".join(explanations)


# Singleton classifier instance
_classifier = None

def get_classifier() -> TuberClassifier:
    """Get singleton classifier instance"""
    global _classifier
    if _classifier is None:
        _classifier = TuberClassifier()
    return _classifier
