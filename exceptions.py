"""
Custom exception classes for SproutCV
"""


class SproutCVError(Exception):
    """Base exception for SproutCV"""
    pass


class ImageLoadError(SproutCVError):
    """Raised when image cannot be loaded"""
    pass


class CalibrationError(SproutCVError):
    """Raised when calibration data is invalid"""
    pass


class ProcessingError(SproutCVError):
    """Raised when image processing fails"""
    pass


class ValidationError(SproutCVError):
    """Raised when input validation fails"""
    pass


class FileOperationError(SproutCVError):
    """Raised when file operations fail"""
    pass