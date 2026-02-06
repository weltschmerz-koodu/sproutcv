"""
Enhanced sprout detection with separate overlay data export
"""

import cv2
import numpy as np
import networkx as nx
import logging
from skimage.morphology import skeletonize
from typing import Dict, Any, List, Tuple

from sproutcv.config import ImageProcessingConfig, VisualizationConfig
from sproutcv.exceptions import ProcessingError
from sproutcv.utils.graph_utils import (
    build_graph_from_skeleton,
    simplify_path,
    reconnect_path,
    find_farthest_nodes
)

logger = logging.getLogger('sproutcv.detector')


def analyze_sprouts(image, cleaned, gray, mm_to_pixel_ratio):
    """
    Detect and measure sprouts with enhanced overlay data export
    
    Args:
        image: Original BGR image
        cleaned: Binary image after preprocessing
        gray: Grayscale image
        mm_to_pixel_ratio: Conversion ratio from pixels to millimeters
    
    Returns:
        tuple: (annotated_image, skeleton_image, sprout_data_list, overlay_data_dict)
            - annotated_image (np.ndarray): Image with annotations drawn
            - skeleton_image (np.ndarray): Binary skeleton image
            - sprout_data_list (list): List of [index, pixel_length, mm_length]
            - overlay_data_dict (dict): Overlay data for interactive viewing
    
    Raises:
        ProcessingError: If detection fails
    """
    try:
        h, w = image.shape[:2]
        
        # Calculate font parameters based on image size
        font_scale = max(
            VisualizationConfig.MIN_FONT_SCALE,
            min(h, w) / VisualizationConfig.FONT_SCALE_DIVISOR
        )
        thickness = max(
            VisualizationConfig.MIN_THICKNESS,
            int(font_scale * VisualizationConfig.THICKNESS_MULTIPLIER)
        )
        
        # Find and group contours
        logger.debug("Detecting and grouping contours")
        contour_groups = detect_and_group_contours(cleaned, h)
        logger.info(f"Found {sum(len(row) for row in contour_groups)} contours in {len(contour_groups)} rows")
        
        # Prepare outputs
        output_image = image.copy()
        skeleton_image = np.zeros_like(gray)
        sprout_data = []
        
        # Enhanced: separate overlay data
        overlay_data = {
            'contours': [],
            'skeleton_paths': [],
            'skeleton_points': [],  # NEW: Store actual skeleton points
            'labels': [],
            'contour_mask': np.zeros_like(gray)
        }
        
        used_label_boxes = []
        sprout_index = 1
        
        # Process each row of sprouts
        for row in contour_groups:
            # Sort left to right within row
            row.sort(key=lambda x: x[1])  # Sort by cx
            
            for i, (contour, cx, cy) in enumerate(row):
                try:
                    # Analyze single sprout
                    result = analyze_single_sprout_enhanced(
                        contour, cx, cy,
                        gray, output_image, skeleton_image,
                        mm_to_pixel_ratio, sprout_index,
                        font_scale, thickness,
                        used_label_boxes, i, h, w,
                        overlay_data
                    )
                    
                    if result:
                        sprout_data.append(result)
                        sprout_index += 1
                
                except Exception as e:
                    logger.warning(f"Failed to process sprout at ({cx}, {cy}): {e}")
                    continue
        
        logger.info(f"Successfully analyzed {len(sprout_data)} sprouts")
        return output_image, skeleton_image, sprout_data, overlay_data
        
    except Exception as e:
        logger.error(f"Sprout analysis failed: {str(e)}")
        raise ProcessingError(f"Sprout analysis failed: {str(e)}")


def detect_and_group_contours(binary_image, image_height):
    """
    Find contours and group them into rows
    
    Args:
        binary_image: Binary image
        image_height: Height of image for row tolerance
    
    Returns:
        list: List of rows, each containing list of (contour, cx, cy) tuples
    """
    contours, _ = cv2.findContours(
        binary_image,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )
    
    # Filter and extract centroids
    valid_contours = []
    
    for contour in contours:
        # Filter by minimum area
        if cv2.contourArea(contour) < ImageProcessingConfig.MIN_CONTOUR_AREA:
            continue
        
        # Calculate centroid
        M = cv2.moments(contour)
        if M["m00"] == 0:
            continue
        
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        
        valid_contours.append((contour, cx, cy))
    
    # Group into rows
    row_tolerance = int(image_height * ImageProcessingConfig.ROW_TOLERANCE_RATIO)
    
    # Sort by y-coordinate
    valid_contours.sort(key=lambda x: x[2])
    
    rows = []
    for contour_data in valid_contours:
        _, _, cy = contour_data
        
        # Try to add to existing row
        added = False
        for row in rows:
            _, _, row_cy = row[0]
            
            if abs(row_cy - cy) < row_tolerance:
                row.append(contour_data)
                added = True
                break
        
        # Create new row if needed
        if not added:
            rows.append([contour_data])
    
    return rows


def analyze_single_sprout_enhanced(
    contour, cx, cy, gray, output_image, skeleton_image,
    mm_to_pixel_ratio, index, font_scale, thickness,
    used_boxes, row_position, img_h, img_w,
    overlay_data
):
    """
    Analyze a single sprout and save overlay data
    
    Args:
        contour: OpenCV contour
        cx, cy: Centroid coordinates
        gray: Grayscale image
        output_image: Output image to draw on
        skeleton_image: Skeleton accumulator image
        mm_to_pixel_ratio: Pixel to mm conversion
        index: Sprout number
        font_scale, thickness: Text rendering parameters
        used_boxes: List of used label bounding boxes
        row_position: Position in row (for label placement)
        img_h, img_w: Image dimensions
        overlay_data: Dictionary to store overlay information
    
    Returns:
        list or None: [index, pixel_length, mm_length] if successful, None otherwise
    """
    # Draw contour on output image (for traditional view)
    cv2.drawContours(
        output_image,
        [contour],
        -1,
        VisualizationConfig.CONTOUR_COLOR,
        2
    )
    
    # Draw contour on separate mask
    cv2.drawContours(
        overlay_data['contour_mask'],
        [contour],
        -1,
        255,
        2
    )
    
    # Store contour data
    overlay_data['contours'].append(contour)
    
    # Create mask for this contour
    mask = np.zeros_like(gray)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    
    # Skeletonize
    skeleton = skeletonize(mask > 0).astype(np.uint8) * 255
    skeleton_image[:] = cv2.bitwise_or(skeleton_image, skeleton)
    
    # NEW: Store skeleton points for this sprout
    skeleton_points = np.column_stack(np.where(skeleton > 0))
    overlay_data['skeleton_points'].append({
        'index': index,
        'points': skeleton_points.tolist()
    })
    
    # Build graph
    G = build_graph_from_skeleton(skeleton)
    
    if len(G.nodes) < 2:
        return None
    
    # Find endpoints and path
    try:
        n1, n2 = find_farthest_nodes(G)
        path = nx.shortest_path(G, n1, n2)
        
        # Simplify and measure path
        simplified_path = simplify_path(path)
        pixel_length = reconnect_path(G, simplified_path)
        mm_length = pixel_length * mm_to_pixel_ratio
        
    except (nx.NetworkXNoPath, nx.NetworkXError, ValueError) as e:
        logger.debug(f"Graph analysis failed for sprout at ({cx}, {cy}): {e}")
        return None
    
    # Store skeleton path
    overlay_data['skeleton_paths'].append({
        'index': index,
        'path': simplified_path
    })
    
    # Draw skeleton path on output
    for i in range(len(simplified_path) - 1):
        p1 = (int(simplified_path[i][1]), int(simplified_path[i][0]))
        p2 = (int(simplified_path[i+1][1]), int(simplified_path[i+1][0]))
        
        cv2.line(
            output_image,
            p1,
            p2,
            VisualizationConfig.SKELETON_COLOR,
            2
        )
    
    # Prepare label data
    label_text = f"{index}: {mm_length:.2f} mm"
    
    # Calculate label position
    text_size, _ = cv2.getTextSize(
        label_text,
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        thickness
    )
    text_width, text_height = text_size
    
    # Calculate position
    x = cx - text_width // 2
    if row_position % 2 == 0:
        y = cy - VisualizationConfig.LABEL_OFFSET_Y
    else:
        y = cy + VisualizationConfig.LABEL_OFFSET_Y
    
    # Keep inside image bounds
    margin = VisualizationConfig.LABEL_MARGIN
    x = max(margin, min(x, img_w - text_width - margin))
    y = max(text_height + margin, min(y, img_h - margin))
    
    # Avoid overlap (simplified)
    max_attempts = 12
    for attempt in range(max_attempts):
        box = (x, y - text_height, x + text_width, y)
        
        overlaps = False
        for used_box in used_boxes:
            if not (box[2] < used_box[0] or box[0] > used_box[2] or
                   box[3] < used_box[1] or box[1] > used_box[3]):
                overlaps = True
                break
        
        if not overlaps:
            break
        
        step = VisualizationConfig.LABEL_ADJUSTMENT_STEP
        if row_position % 2 == 0:
            y += step
        else:
            y -= step
        
        y = max(text_height + margin, min(y, img_h - margin))
    
    used_boxes.append((x, y - text_height, x + text_width, y))
    
    # Store label data
    overlay_data['labels'].append({
        'text': label_text,
        'position': (x, y),
        'index': index,
        'font_scale': font_scale,
        'thickness': thickness
    })
    
    # Draw label on output (traditional)
    cv2.putText(
        output_image,
        label_text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        VisualizationConfig.TEXT_OUTLINE_COLOR,
        thickness + 2,
        cv2.LINE_AA
    )
    
    cv2.putText(
        output_image,
        label_text,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        VisualizationConfig.TEXT_COLOR,
        thickness,
        cv2.LINE_AA
    )
    
    return [index, pixel_length, mm_length]