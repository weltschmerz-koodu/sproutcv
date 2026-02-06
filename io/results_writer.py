"""
Enhanced results file writing with separate overlay data
"""

import os
import cv2
import pandas as pd
import json
import numpy as np
import logging
from typing import List, Dict, Any

from sproutcv.config import OutputConfig
from sproutcv.exceptions import FileOperationError

logger = logging.getLogger('sproutcv.results_writer')


def save_results_with_overlays(
    image_folder: str,
    image_name: str,
    original_image,
    output_image,
    skeleton_image,
    sprout_data: List,
    overlay_data: Dict[str, Any]
) -> None:
    """
    Save processing results with separate overlay data for interactive viewing
    
    Args:
        image_folder: Output folder path
        image_name: Image name without extension
        original_image: Original BGR image
        output_image: Annotated output image
        skeleton_image: Binary skeleton image
        sprout_data: List of [index, pixels, mm] measurements
        overlay_data: Dictionary containing overlay information
    
    Raises:
        FileOperationError: If file writing fails
    """
    logger.debug(f"Saving results for {image_name}")

    if not os.path.exists(image_folder):
        logger.error(f"Output folder does not exist: {image_folder}")
        raise FileOperationError(f"Output folder does not exist: {image_folder}")

    if not os.path.isdir(image_folder):
        logger.error(f"Path is not a directory: {image_folder}")
        raise FileOperationError(f"Path is not a directory: {image_folder}")

    # Validate sprout_data
    if not isinstance(sprout_data, list):
        raise FileOperationError("sprout_data must be a list")

    if sprout_data and not all(isinstance(row, (list, tuple)) and len(row) == 3 for row in sprout_data):
        raise FileOperationError("All sprout_data rows must have 3 values [index, pixels, mm]")

    # Save original image copy
    original_path = os.path.join(image_folder, f"{image_name}.jpg")
    try:
        success = cv2.imwrite(
            original_path,
            original_image,
            [cv2.IMWRITE_JPEG_QUALITY, OutputConfig.OUTPUT_IMAGE_QUALITY]
        )
        if not success:
            raise FileOperationError(f"Failed to write original image: {original_path}")
        logger.debug(f"Saved original image: {original_path}")
    except Exception as e:
        logger.error(f"Cannot write original image: {str(e)}")
        raise FileOperationError(f"Cannot write original image: {str(e)}")

    # Save skeleton-only mask
    skeleton_mask_path = os.path.join(
        image_folder,
        f"mask_skeleton_{image_name}.png"
    )
    try:
        success = cv2.imwrite(skeleton_mask_path, skeleton_image)
        if not success:
            raise FileOperationError(f"Failed to write skeleton mask: {skeleton_mask_path}")
        logger.debug(f"Saved skeleton mask: {skeleton_mask_path}")
    except Exception as e:
        logger.error(f"Cannot write skeleton mask: {str(e)}")
        raise FileOperationError(f"Cannot write skeleton mask: {str(e)}")

    # Save contour-only mask
    if 'contour_mask' in overlay_data:
        contour_mask_path = os.path.join(
            image_folder,
            f"mask_contour_{image_name}.png"
        )
        try:
            success = cv2.imwrite(contour_mask_path, overlay_data['contour_mask'])
            if not success:
                raise FileOperationError(f"Failed to write contour mask: {contour_mask_path}")
            logger.debug(f"Saved contour mask: {contour_mask_path}")
        except Exception as e:
            logger.error(f"Cannot write contour mask: {str(e)}")
            raise FileOperationError(f"Cannot write contour mask: {str(e)}")

    # Save overlay metadata (contours, labels, skeleton paths)
    metadata_path = os.path.join(
        image_folder,
        f"overlay_data_{image_name}.json"
    )
    try:
        serializable_data = {}

        if 'contours' in overlay_data:
            serializable_data['contours'] = [
                {
                    'points': contour.reshape(-1, 2).tolist() if isinstance(contour, np.ndarray) else contour,
                    'index': idx
                }
                for idx, contour in enumerate(overlay_data['contours'])
            ]

        if 'skeleton_paths' in overlay_data:
            serializable_data['skeleton_paths'] = overlay_data['skeleton_paths']
        
        # NEW: Save skeleton points
        if 'skeleton_points' in overlay_data:
            serializable_data['skeleton_points'] = overlay_data['skeleton_points']

        if 'labels' in overlay_data:
            serializable_data['labels'] = overlay_data['labels']

        with open(metadata_path, 'w') as f:
            json.dump(serializable_data, f, indent=2)
        logger.debug(f"Saved overlay metadata: {metadata_path}")

    except Exception as e:
        logger.error(f"Cannot write overlay metadata: {str(e)}")
        raise FileOperationError(f"Cannot write overlay metadata: {str(e)}")

    # Save traditional outputs for backward compatibility

    skeleton_viz_path = os.path.join(
        image_folder,
        f"{OutputConfig.SKELETON_PREFIX}{image_name}{OutputConfig.OUTPUT_IMAGE_FORMAT}"
    )
    try:
        success = cv2.imwrite(
            skeleton_viz_path,
            skeleton_image,
            [cv2.IMWRITE_JPEG_QUALITY, OutputConfig.OUTPUT_IMAGE_QUALITY]
        )
        if not success:
            raise FileOperationError(f"Failed to write skeleton image: {skeleton_viz_path}")
        logger.debug(f"Saved skeleton visualization: {skeleton_viz_path}")
    except Exception as e:
        logger.error(f"Cannot write skeleton image: {str(e)}")
        raise FileOperationError(f"Cannot write skeleton image: {str(e)}")

    measurement_path = os.path.join(
        image_folder,
        f"{OutputConfig.MEASUREMENT_PREFIX}{image_name}{OutputConfig.OUTPUT_IMAGE_FORMAT}"
    )
    try:
        success = cv2.imwrite(
            measurement_path,
            output_image,
            [cv2.IMWRITE_JPEG_QUALITY, OutputConfig.OUTPUT_IMAGE_QUALITY]
        )
        if not success:
            raise FileOperationError(f"Failed to write measurement image: {measurement_path}")
        logger.debug(f"Saved measurement image: {measurement_path}")
    except Exception as e:
        logger.error(f"Cannot write measurement image: {str(e)}")
        raise FileOperationError(f"Cannot write measurement image: {str(e)}")

    # Save CSV
    csv_path = os.path.join(
        image_folder,
        f"{OutputConfig.CSV_PREFIX}{image_name}.csv"
    )
    try:
        df = pd.DataFrame(
            sprout_data,
            columns=["Sprout Number", "Pixels", "Millimeters"]
        )
        df.to_csv(csv_path, index=False)
        logger.debug(f"Saved CSV data: {csv_path}")
    except Exception as e:
        logger.error(f"Cannot write CSV file: {str(e)}")
        raise FileOperationError(f"Cannot write CSV file: {str(e)}")
    
    logger.info(f"Successfully saved all results for {image_name}")