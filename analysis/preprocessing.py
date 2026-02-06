"""
Image preprocessing for sprout analysis
"""

import os
import cv2
import numpy as np
import logging

from sproutcv.config import ImageProcessingConfig
from sproutcv.exceptions import ImageLoadError, ProcessingError

logger = logging.getLogger('sproutcv.preprocessing')


def preprocess_image(image_path: str) -> tuple:
    """
    Preprocess image for sprout detection
    
    Args:
        image_path: Path to input image
    
    Returns:
        tuple: (original_image, binary_image, grayscale_image)
            - original_image (np.ndarray): Original BGR image
            - binary_image (np.ndarray): Binary thresholded image
            - grayscale_image (np.ndarray): Grayscale image
    
    Raises:
        ImageLoadError: If image doesn't exist or cannot be loaded
        ProcessingError: If preprocessing fails
    """
    # Validate file exists
    if not os.path.exists(image_path):
        logger.error(f"Image not found: {image_path}")
        raise ImageLoadError(f"Image not found: {image_path}")
    
    # Load image
    logger.debug(f"Loading image: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        logger.error(f"Failed to load image: {image_path}")
        raise ImageLoadError(f"Failed to load image: {image_path}")
    
    if image.size == 0 or image.shape[0] == 0 or image.shape[1] == 0:
        logger.error(f"Image has invalid dimensions: {image_path}")
        raise ImageLoadError(f"Image has invalid dimensions: {image_path}")
    
    try:
        # Apply mean shift filtering for noise reduction
        logger.debug("Applying mean shift filtering")
        shifted = cv2.pyrMeanShiftFiltering(
            image,
            sp=ImageProcessingConfig.MEAN_SHIFT_SP,
            sr=ImageProcessingConfig.MEAN_SHIFT_SR
        )
        
        # Convert to grayscale
        logger.debug("Converting to grayscale")
        gray = cv2.cvtColor(shifted, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur
        logger.debug("Applying Gaussian blur")
        blurred = cv2.GaussianBlur(
            gray,
            ImageProcessingConfig.GAUSSIAN_BLUR_KERNEL,
            ImageProcessingConfig.GAUSSIAN_BLUR_SIGMA
        )
        
        # Otsu's thresholding
        logger.debug("Applying Otsu's thresholding")
        _, binary = cv2.threshold(
            blurred,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )
        
        # Morphological operations to clean up
        kernel_size = ImageProcessingConfig.MORPHOLOGY_KERNEL_SIZE
        
        valid_shapes = {'ELLIPSE', 'RECT', 'CROSS'}
        shape = ImageProcessingConfig.MORPHOLOGY_SHAPE

        if shape not in valid_shapes:
            raise ProcessingError(
                f"Invalid MORPHOLOGY_SHAPE: {shape}. Must be one of {valid_shapes}"
            )

        if shape == 'ELLIPSE':
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, kernel_size)
        elif shape == 'RECT':
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, kernel_size)
        else:  # CROSS
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, kernel_size)
        
        # Close gaps
        logger.debug("Applying morphological closing")
        cleaned = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Remove small noise
        logger.debug("Applying morphological opening")
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        logger.info("Preprocessing completed successfully")
        return image, cleaned, gray
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        raise ProcessingError(f"Preprocessing failed: {str(e)}")