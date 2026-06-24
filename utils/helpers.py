"""
YamGuard - Helper Utilities
Common helper functions for the application
"""

import os
import re
import random
import string
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Tuple

from utils.constants import (
    UPLOADS_DIR, EXPORTS_DIR, SEVERITY_LEVELS,
    SPECTRAL_RANGE_START, SPECTRAL_RANGE_END, SPECTRAL_BANDS,
    CLASSIFICATION_PROBABILITIES
)


def generate_tuber_id() -> str:
    """Generate a unique tuber scan ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"YG-{timestamp}-{random_suffix}"


def generate_filename(prefix: str = "scan", extension: str = "jpg") -> str:
    """Generate a unique filename for captured images"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{timestamp}.{extension}"


def ensure_directories():
    """Ensure all required directories exist"""
    for directory in [UPLOADS_DIR, EXPORTS_DIR]:
        os.makedirs(directory, exist_ok=True)


def format_datetime(dt: Optional[datetime] = None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime object to string"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime(fmt)


def format_date(dt: Optional[datetime] = None) -> str:
    """Format date only"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%Y-%m-%d")


def format_time(dt: Optional[datetime] = None) -> str:
    """Format time only"""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%H:%M:%S")


def get_timestamp() -> str:
    """Get current timestamp string"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def parse_datetime(date_string: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime string to object"""
    try:
        return datetime.strptime(date_string, fmt)
    except (ValueError, TypeError):
        return None


def get_date_range(days: int = 30) -> Tuple[str, str]:
    """Get date range for filtering"""
    end = datetime.now()
    start = end - timedelta(days=days)
    return format_date(start), format_date(end)


def calculate_infection_rate(total: int, infected: int) -> float:
    """Calculate infection rate percentage"""
    if total == 0:
        return 0.0
    return round((infected / total) * 100, 2)


def get_severity_info(classification: str) -> Dict[str, Any]:
    """Get severity level information"""
    return SEVERITY_LEVELS.get(classification, SEVERITY_LEVELS["Healthy"])


def get_recommendation(classification: str) -> str:
    """Get recommendation based on classification"""
    recommendations = {
        "Healthy": "Approved for Storage and Sale",
        "Level 1 - Early Infection": "Monitor closely. Quarantine for 48 hours and re-scan. Early treatment recommended.",
        "Level 2 - Moderate Infection": "Not approved for storage. Immediate treatment required. Consult agricultural extension officer.",
        "Level 3 - Severe Infection": "Reject for storage. Destroy infected tubers to prevent spread. Full treatment protocol required.",
        "Level 4 - Critical": "Immediate disposal required. High risk of contamination. Quarantine entire batch.",
    }
    return recommendations.get(classification, "Consult an expert for further analysis.")


def generate_spectral_signature(
    base_reflectance: float = 0.5,
    noise_level: float = 0.02,
    infection_type: Optional[str] = None
) -> Tuple[List[float], List[float]]:
    """Generate synthetic spectral signature data"""
    import numpy as np
    
    wavelengths = np.linspace(SPECTRAL_RANGE_START, SPECTRAL_RANGE_END, SPECTRAL_BANDS)
    
    # Base vegetation curve (simplified)
    reflectance = base_reflectance * np.ones_like(wavelengths)
    
    # Add chlorophyll absorption features
    # Blue absorption (450nm)
    reflectance -= 0.15 * np.exp(-((wavelengths - 450)**2) / (2 * 30**2))
    # Red absorption (675nm)
    reflectance -= 0.25 * np.exp(-((wavelengths - 675)**2) / (2 * 25**2))
    # Red edge rise (720nm)
    reflectance += 0.20 * (1 / (1 + np.exp(-(wavelengths - 720) / 15)))
    # NIR plateau
    reflectance += 0.30 * (1 / (1 + np.exp(-(wavelengths - 750) / 20)))
    # Water absorption (970nm)
    reflectance -= 0.10 * np.exp(-((wavelengths - 970)**2) / (2 * 40**2))
    
    # Add infection-specific modifications
    if infection_type and "Level" in infection_type:
        severity = int(infection_type.split(" ")[1]) if "Level" in infection_type else 0
        
        # Reduced chlorophyll absorption with infection
        reflectance += (0.05 * severity) * np.exp(-((wavelengths - 675)**2) / (2 * 25**2))
        
        # Reduced NIR reflectance
        reflectance -= (0.05 * severity) * (1 / (1 + np.exp(-(wavelengths - 750) / 20)))
        
        # Shifted red edge
        reflectance -= (0.03 * severity) * np.exp(-((wavelengths - (720 + 10 * severity))**2) / (2 * 20**2))
    
    # Add noise
    noise = np.random.normal(0, noise_level, len(wavelengths))
    reflectance += noise
    
    # Clip to valid range
    reflectance = np.clip(reflectance, 0.0, 1.0)
    
    return wavelengths.tolist(), reflectance.tolist()


def simulate_classification() -> Dict[str, Any]:
    """Simulate classification result with weighted random selection"""
    import numpy as np
    
    classifications = list(CLASSIFICATION_PROBABILITIES.keys())
    probabilities = list(CLASSIFICATION_PROBABILITIES.values())
    
    selected = np.random.choice(classifications, p=probabilities)
    
    # Generate confidence based on classification
    if selected == "Healthy":
        confidence = random.uniform(85.0, 99.5)
    elif selected == "Level 1 - Early Infection":
        confidence = random.uniform(70.0, 89.0)
    else:
        confidence = random.uniform(65.0, 85.0)
    
    return {
        "classification": selected,
        "confidence": round(confidence, 1),
        "severity": selected,
        "recommendation": get_recommendation(selected),
    }


def get_file_size(file_path: str) -> str:
    """Get human-readable file size"""
    if not os.path.exists(file_path):
        return "0 B"
    
    size_bytes = os.path.getsize(file_path)
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def hash_password(password: str) -> str:
    """Hash password using SHA-256 (for demo - use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed


def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem usage"""
    filename = re.sub(r'[^\w\-. ]', '_', filename)
    return filename.strip()


def get_status_color(status: str) -> str:
    """Get color hex for a status string"""
    status_colors = {
        "healthy": "#22C55E",
        "infected": "#DC2626",
        "warning": "#F59E0B",
        "info": "#3B82F6",
        "pending": "#94A3B8",
    }
    return status_colors.get(status.lower(), "#64748B")


def format_confidence(confidence: float) -> str:
    """Format confidence as percentage string"""
    return f"{confidence:.1f}%"


def get_initials(name: str) -> str:
    """Get initials from full name"""
    parts = name.split()
    if len(parts) >= 2:
        return f"{parts[0][0]}{parts[-1][0]}".upper()
    return name[:2].upper() if name else "YG"
