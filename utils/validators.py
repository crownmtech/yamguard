"""
YamGuard - Input Validators
Form validation utilities for the application
"""

import re
from typing import Optional, Tuple


class ValidationResult:
    """Validation result container"""
    
    def __init__(self, is_valid: bool = True, message: str = ""):
        self.is_valid = is_valid
        self.message = message
    
    def __bool__(self):
        return self.is_valid


class Validator:
    """Base validator class"""
    
    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email format"""
        if not email or not email.strip():
            return ValidationResult(False, "Email is required")
        
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email.strip()):
            return ValidationResult(False, "Invalid email format")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_password(password: str) -> ValidationResult:
        """Validate password strength"""
        if not password:
            return ValidationResult(False, "Password is required")
        
        if len(password) < 6:
            return ValidationResult(False, "Password must be at least 6 characters")
        
        if len(password) > 128:
            return ValidationResult(False, "Password too long")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_fullname(name: str) -> ValidationResult:
        """Validate full name"""
        if not name or not name.strip():
            return ValidationResult(False, "Full name is required")
        
        if len(name.strip()) < 2:
            return ValidationResult(False, "Name too short")
        
        if len(name) > 100:
            return ValidationResult(False, "Name too long")
        
        if not re.match(r'^[a-zA-Z\s\-\'.]+$', name.strip()):
            return ValidationResult(False, "Name contains invalid characters")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_required(value: str, field_name: str = "Field") -> ValidationResult:
        """Validate that a field is not empty"""
        if not value or not value.strip():
            return ValidationResult(False, f"{field_name} is required")
        return ValidationResult(True)
    
    @staticmethod
    def validate_date_range(date_from: str, date_to: str) -> ValidationResult:
        """Validate date range"""
        if not date_from or not date_to:
            return ValidationResult(False, "Both dates are required")
        
        # Simple validation - can be enhanced with actual date parsing
        if date_from > date_to:
            return ValidationResult(False, "Start date must be before end date")
        
        return ValidationResult(True)
    
    @staticmethod
    def validate_report_title(title: str) -> ValidationResult:
        """Validate report title"""
        if not title or not title.strip():
            return ValidationResult(False, "Report title is required")
        
        if len(title.strip()) < 3:
            return ValidationResult(False, "Title too short")
        
        if len(title) > 200:
            return ValidationResult(False, "Title too long (max 200 characters)")
        
        return ValidationResult(True)


class FormValidator:
    """Form-level validator"""
    
    def __init__(self):
        self.errors: dict = {}
        self.validator = Validator()
    
    def validate_login(self, email: str, password: str) -> bool:
        """Validate login form"""
        self.errors = {}
        
        email_result = self.validator.validate_email(email)
        if not email_result:
            self.errors['email'] = email_result.message
        
        password_result = self.validator.validate_password(password)
        if not password_result:
            self.errors['password'] = password_result.message
        
        return len(self.errors) == 0
    
    def validate_registration(self, fullname: str, email: str, password: str, 
                             confirm_password: str, role: str = "") -> bool:
        """Validate registration form"""
        self.errors = {}
        
        name_result = self.validator.validate_fullname(fullname)
        if not name_result:
            self.errors['fullname'] = name_result.message
        
        email_result = self.validator.validate_email(email)
        if not email_result:
            self.errors['email'] = email_result.message
        
        password_result = self.validator.validate_password(password)
        if not password_result:
            self.errors['password'] = password_result.message
        
        if password != confirm_password:
            self.errors['confirm_password'] = "Passwords do not match"
        
        if not role:
            self.errors['role'] = "Please select a role"
        
        return len(self.errors) == 0
    
    def validate_report_form(self, title: str, date_from: str, date_to: str) -> bool:
        """Validate report generation form"""
        self.errors = {}
        
        title_result = self.validator.validate_report_title(title)
        if not title_result:
            self.errors['title'] = title_result.message
        
        date_result = self.validator.validate_date_range(date_from, date_to)
        if not date_result:
            self.errors['date_range'] = date_result.message
        
        return len(self.errors) == 0
    
    def get_error(self, field: str) -> str:
        """Get error message for a field"""
        return self.errors.get(field, "")
    
    def has_error(self, field: str) -> bool:
        """Check if a field has an error"""
        return field in self.errors


def format_validation_errors(errors: dict) -> str:
    """Format validation errors for display"""
    if not errors:
        return ""
    
    messages = []
    for field, message in errors.items():
        messages.append(f"• {message}")
    
    return "\n".join(messages)
