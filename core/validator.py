"""
Input validation for SproutCV pipeline
"""

import os
import logging
from typing import Callable, Optional, Dict, Any, List
import pandas as pd

from sproutcv.config import ValidationConfig
from sproutcv.io.image_io import get_image_files
from sproutcv.exceptions import ValidationError

logger = logging.getLogger('sproutcv.validator')


def validate_inputs(
    parent_folder: str,
    csv_path: str,
    log_callback: Optional[Callable[[str], None]] = None,
    verbose: bool = True
) -> Dict[str, List[str]]:
    """
    Validate all inputs before processing
    
    Args:
        parent_folder: Path to image folder
        csv_path: Path to calibration CSV
        log_callback: Optional logging function
        verbose: Show detailed messages
    
    Returns:
        dict: Dictionary containing validation results with keys:
            - 'fatal' (list): Fatal errors that prevent processing
            - 'warnings' (list): Non-critical issues to review
            - 'info' (list): Informational messages
    
    Raises:
        ValidationError: If critical validation setup fails
    """
    log = log_callback or logger.info
    
    fatal_errors = []
    warnings = []
    infos = []
    
    # ========================================
    # IMAGE FOLDER VALIDATION
    # ========================================
    
    if not os.path.exists(parent_folder):
        fatal_errors.append(f"Image folder does not exist: {parent_folder}")
        images = []
    elif not os.path.isdir(parent_folder):
        fatal_errors.append(f"Path is not a directory: {parent_folder}")
        images = []
    else:
        try:
            images = get_image_files(parent_folder)
            
            if not images:
                fatal_errors.append(
                    f"No images found in the selected folder. "
                    f"Please ensure the folder contains image files "
                    f"({', '.join(ValidationConfig.SUPPORTED_IMAGE_FORMATS)})"
                )
            else:
                infos.append(f"Found {len(images)} image(s) to process")
                
                # Check file sizes
                large_files = []
                for img in images:
                    path = os.path.join(parent_folder, img)
                    size_mb = os.path.getsize(path) / (1024 * 1024)
                    if size_mb > ValidationConfig.MAX_IMAGE_SIZE_MB:
                        large_files.append(f"{img} ({size_mb:.1f} MB)")
                
                if large_files:
                    warnings.append(
                        f"Large image files detected (>{ValidationConfig.MAX_IMAGE_SIZE_MB}MB): "
                        f"{', '.join(large_files[:3])}"
                        + ("..." if len(large_files) > 3 else "")
                    )
        
        except PermissionError:
            fatal_errors.append(f"Permission denied accessing folder: {parent_folder}")
            images = []
    
    # ========================================
    # CSV VALIDATION
    # ========================================
    
    if not os.path.exists(csv_path):
        fatal_errors.append(f"CSV file does not exist: {csv_path}")
        df = None
    elif not os.path.isfile(csv_path):
        fatal_errors.append(f"Path is not a file: {csv_path}")
        df = None
    else:
        try:
            # Check file size
            size_mb = os.path.getsize(csv_path) / (1024 * 1024)
            if size_mb > ValidationConfig.MAX_CSV_SIZE_MB:
                warnings.append(f"Large CSV file: {size_mb:.1f} MB")
            
            # Try to load CSV
            df = pd.read_csv(csv_path)
            infos.append("Calibration CSV loaded successfully")
            
            # Validate structure
            df.columns = [c.strip() for c in df.columns]
            found_cols = set(df.columns)
            required_cols = ValidationConfig.REQUIRED_CSV_COLUMNS
            
            if not required_cols.issubset(found_cols):
                missing = required_cols - found_cols
                fatal_errors.append(
                    f"CSV missing required columns: {missing}. "
                    f"Found: {list(df.columns)}"
                )
                df = None
            
        except pd.errors.EmptyDataError:
            fatal_errors.append("CSV file is empty")
            df = None
        except pd.errors.ParserError as e:
            fatal_errors.append(f"CSV parse error: {str(e)}")
            df = None
        except PermissionError:
            fatal_errors.append(f"Permission denied reading CSV: {csv_path}")
            df = None
        except Exception as e:
            fatal_errors.append(f"Error loading CSV: {str(e)}")
            df = None
    
    # ========================================
    # CROSS-VALIDATION (CSV vs Images)
    # ========================================
    
    if df is not None and images:
        image_names = {os.path.splitext(f)[0] for f in images}
        csv_names = set(df['file_name'].astype(str).str.strip())
        
        # Images without calibration
        missing_in_csv = sorted(image_names - csv_names)
        if missing_in_csv:
            fatal_errors.append(
                f"Missing calibration for {len(missing_in_csv)} image(s): "
                f"{missing_in_csv[:5]}"
                + ("..." if len(missing_in_csv) > 5 else "")
            )
        
        # CSV rows without images
        extra_in_csv = sorted(csv_names - image_names)
        if extra_in_csv:
            warnings.append(
                f"CSV has {len(extra_in_csv)} row(s) without matching images: "
                f"{extra_in_csv[:5]}"
                + ("..." if len(extra_in_csv) > 5 else "")
            )
        
        # Check for duplicates
        duplicates = df['file_name'][df['file_name'].duplicated()].tolist()
        if duplicates:
            fatal_errors.append(
                f"Duplicate calibration rows for: {duplicates}"
            )
        
        # Validate calibration values
        for idx, row in df.iterrows():
            name = row['file_name']
            
            # Check for missing values
            if pd.isna(row['pixel']) or pd.isna(row['distance']):
                fatal_errors.append(
                    f"Missing pixel/distance value for '{name}'"
                )
                continue
            
            # Check for valid numeric values
            try:
                pixel = float(row['pixel'])
                distance = float(row['distance'])
                
                # Check for positive values
                if pixel <= 0 or distance <= 0:
                    fatal_errors.append(
                        f"Non-positive calibration for '{name}': "
                        f"pixel={pixel}, distance={distance}"
                    )
                
                # Check for reasonable values
                if pixel < 1 or pixel > 10000:
                    warnings.append(
                        f"Unusual pixel value for '{name}': {pixel}"
                    )
                
                if distance < 0.1 or distance > 1000:
                    warnings.append(
                        f"Unusual distance value for '{name}': {distance}"
                    )
            
            except (ValueError, TypeError):
                fatal_errors.append(
                    f"Non-numeric calibration for '{name}': "
                    f"pixel={row['pixel']}, distance={row['distance']}"
                )
    
    # ========================================
    # SUMMARY
    # ========================================
    
    log("\n" + "="*50)
    log("VALIDATION SUMMARY")
    log("="*50)
    log(f"❌ Fatal errors: {len(fatal_errors)}")
    log(f"⚠️  Warnings: {len(warnings)}")
    log(f"ℹ️  Info: {len(infos)}")
    
    if verbose:
        if fatal_errors:
            log("\n❌ FATAL ERRORS (must be fixed):")
            for i, err in enumerate(fatal_errors, 1):
                log(f"  {i}. {err}")
        
        if warnings:
            log("\n⚠️  WARNINGS (review recommended):")
            for i, warn in enumerate(warnings, 1):
                log(f"  {i}. {warn}")
        
        if infos:
            log("\nℹ️  INFORMATION:")
            for i, info in enumerate(infos, 1):
                log(f"  {i}. {info}")
    
    # Log to standard logger as well
    if fatal_errors:
        for err in fatal_errors:
            logger.error(f"Validation error: {err}")
    if warnings:
        for warn in warnings:
            logger.warning(f"Validation warning: {warn}")
    
    return {
        'fatal': fatal_errors,
        'warnings': warnings,
        'info': infos
    }