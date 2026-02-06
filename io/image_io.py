"""
Image file operations
"""

import os
import shutil
import logging
from typing import List, Tuple

from sproutcv.config import ValidationConfig
from sproutcv.exceptions import FileOperationError

logger = logging.getLogger('sproutcv.image_io')


def get_image_files(folder: str) -> List[str]:
    """
    Get list of supported image files in folder
    
    Args:
        folder: Path to folder
    
    Returns:
        list: List of image filenames (strings)
    
    Raises:
        FileOperationError: If folder doesn't exist or is inaccessible
    """
    if not os.path.exists(folder):
        logger.error(f"Folder does not exist: {folder}")
        raise FileOperationError(f"Folder does not exist: {folder}")
    
    if not os.path.isdir(folder):
        logger.error(f"Path is not a directory: {folder}")
        raise FileOperationError(f"Path is not a directory: {folder}")
    
    try:
        all_files = os.listdir(folder)
    except PermissionError:
        logger.error(f"Permission denied accessing folder: {folder}")
        raise FileOperationError(f"Permission denied accessing folder: {folder}")
    
    # Filter for supported image formats
    image_files = [
        f for f in all_files
        if f.lower().endswith(ValidationConfig.SUPPORTED_IMAGE_FORMATS)
    ]
    
    logger.debug(f"Found {len(image_files)} image files in {folder}")
    return sorted(image_files)


def move_image_to_folder(parent_folder: str, 
                         image_file: str,
                         output_root: str = None,
                         use_copy: bool = True) -> Tuple[str, str, str]:
    """
    Move or copy image to its own output folder
    
    Args:
        parent_folder: Source folder containing image
        image_file: Image filename
        output_root: Optional custom output root directory
        use_copy: If True, copy instead of move
    
    Returns:
        tuple: (new_image_path, image_folder, image_name_no_ext) where:
            - new_image_path (str): Full path to image in output folder
            - image_folder (str): Path to output folder
            - image_name_no_ext (str): Image name without extension
    
    Raises:
        FileOperationError: If source image doesn't exist or operation fails
    """
    # Get image name without extension
    image_name_no_ext = os.path.splitext(image_file)[0]
    
    # Source path
    source_path = os.path.join(parent_folder, image_file)
    
    if not os.path.exists(source_path):
        logger.error(f"Image not found: {source_path}")
        raise FileOperationError(f"Image not found: {source_path}")
    
    # Determine output folder
    if output_root:
        image_folder = os.path.join(output_root, image_name_no_ext)
    else:
        image_folder = os.path.join(parent_folder, image_name_no_ext)
    
    # Create output folder
    try:
        os.makedirs(image_folder, exist_ok=True)
        logger.debug(f"Created output folder: {image_folder}")
    except PermissionError:
        logger.error(f"Cannot create folder: {image_folder}")
        raise FileOperationError(f"Cannot create folder: {image_folder}")
    
    # Destination path
    dest_path = os.path.join(image_folder, image_file)
    
    # Copy or move
    try:
        if use_copy:
            shutil.copy2(source_path, dest_path)
            logger.debug(f"Copied image to: {dest_path}")
        else:
            shutil.move(source_path, dest_path)
            logger.debug(f"Moved image to: {dest_path}")
    except PermissionError:
        logger.error(f"Cannot {'copy' if use_copy else 'move'} file: {source_path}")
        raise FileOperationError(
            f"Cannot {'copy' if use_copy else 'move'} file: {source_path}"
        )
    
    return dest_path, image_folder, image_name_no_ext