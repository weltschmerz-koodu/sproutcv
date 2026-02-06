"""
Calibration data loading and validation
"""

import os
import logging
import pandas as pd
from typing import Optional

from sproutcv.config import ValidationConfig
from sproutcv.exceptions import CalibrationError, FileOperationError

logger = logging.getLogger('sproutcv.calibration')


def load_calibration_data(csv_path: str) -> pd.DataFrame:
    """
    Load and validate calibration CSV file
    
    Args:
        csv_path: Path to calibration CSV
    
    Returns:
        pd.DataFrame: DataFrame with calibration data containing columns:
            - file_name: Image filename without extension
            - pixel: Pixel distance measurement
            - distance: Real-world distance measurement
    
    Raises:
        FileOperationError: If CSV doesn't exist or cannot be read
        CalibrationError: If CSV is invalid or malformed
    """
    # Check file exists
    if not os.path.exists(csv_path):
        logger.error(f"CSV file not found: {csv_path}")
        raise FileOperationError(f"CSV file not found: {csv_path}")
    
    if not os.path.isfile(csv_path):
        logger.error(f"Path is not a file: {csv_path}")
        raise FileOperationError(f"Path is not a file: {csv_path}")
    
    try:
        # Load CSV
        logger.debug(f"Loading calibration CSV: {csv_path}")
        df = pd.read_csv(csv_path)
        
        # Trim whitespace from column names
        df.columns = [c.strip() for c in df.columns]
        
        # Validate required columns
        required = ValidationConfig.REQUIRED_CSV_COLUMNS
        found = set(df.columns)
        
        if not required.issubset(found):
            missing = required - found
            logger.error(f"CSV missing required columns: {missing}")
            raise CalibrationError(
                f"CSV missing required columns: {missing}. "
                f"Required: {required}, Found: {list(df.columns)}"
            )
        
        # Trim whitespace from file_name column
        df['file_name'] = df['file_name'].astype(str).str.strip()
        
        logger.info(f"Loaded calibration for {len(df)} images")
        return df
    
    except pd.errors.EmptyDataError:
        logger.error(f"CSV file is empty: {csv_path}")
        raise CalibrationError(f"CSV file is empty: {csv_path}")
    
    except pd.errors.ParserError as e:
        logger.error(f"CSV parse error: {str(e)}")
        raise CalibrationError(f"CSV parse error: {str(e)}")
    
    except PermissionError:
        logger.error(f"Permission denied reading CSV: {csv_path}")
        raise FileOperationError(f"Permission denied reading CSV: {csv_path}")


def get_mm_to_pixel_ratio(calibration_data: pd.DataFrame, 
                          image_name: str) -> Optional[float]:
    """
    Get mm-to-pixel conversion ratio for an image
    
    Args:
        calibration_data: DataFrame from load_calibration_data
        image_name: Image filename without extension
    
    Returns:
        float or None: Conversion ratio (mm/pixel) if found, None if not found
    
    Raises:
        CalibrationError: If calibration data is invalid
    """
    # Find matching row
    row = calibration_data[calibration_data['file_name'] == image_name]
    
    if row.empty:
        logger.debug(f"No calibration found for image: {image_name}")
        return None
    
    # Get values
    pixel = row.iloc[0]['pixel']
    distance = row.iloc[0]['distance']
    
    # Validate
    if pd.isna(pixel) or pd.isna(distance):
        logger.error(f"Missing calibration data for '{image_name}'")
        raise CalibrationError(
            f"Missing calibration data for '{image_name}': "
            f"pixel={pixel}, distance={distance}"
        )
    
    try:
        pixel = float(pixel)
        distance = float(distance)
    except (ValueError, TypeError):
        logger.error(f"Non-numeric calibration data for '{image_name}'")
        raise CalibrationError(
            f"Non-numeric calibration data for '{image_name}': "
            f"pixel={pixel}, distance={distance}"
        )
    
    if pixel <= 0 or distance <= 0:
        logger.error(f"Invalid calibration data for '{image_name}'")
        raise CalibrationError(
            f"Invalid calibration data for '{image_name}': "
            f"pixel={pixel}, distance={distance} (must be positive)"
        )
    
    ratio = distance / pixel
    logger.debug(f"Calibration ratio for '{image_name}': {ratio:.6f} mm/pixel")
    return ratio