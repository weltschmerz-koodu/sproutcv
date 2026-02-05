import cv2
import numpy as np
import networkx as nx
import os
import shutil
import pandas as pd
from skimage.morphology import skeletonize
from shapely.geometry import LineString

from sproutcv.io.file_io import (
    load_calibration_data,
    move_image_to_folder,
    save_results,
    get_mm_to_pixel_ratio
)

from sproutcv.core.sprout_analysis import (
    preprocess_image,
    analyze_sprouts
)

# ---------------- GUI Pipeline ---------------- #

def run_pipeline(parent_folder, csv_path,
                 log_callback=None,
                 progress_callback=None):

    calibration_data = load_calibration_data(csv_path)

    image_files = [
        f for f in os.listdir(parent_folder)
        if f.lower().endswith((".jpg", ".png", ".jpeg"))
    ]

    total = len(image_files)

    for i, image_file in enumerate(image_files):

        if log_callback:
            log_callback(f"Processing {image_file}")

        new_image_path, image_folder, name = move_image_to_folder(
            parent_folder, image_file
        )

        ratio = get_mm_to_pixel_ratio(calibration_data, name)

        if ratio is None:
            if log_callback:
                log_callback(f"Skipping {name} (no calibration)")
            continue

        image, cleaned, gray = preprocess_image(new_image_path)

        out, skel, data = analyze_sprouts(
            image, cleaned, gray, ratio
        )

        save_results(image_folder, name, out, skel, data)

        if progress_callback:
            progress_callback((i + 1) / total)
