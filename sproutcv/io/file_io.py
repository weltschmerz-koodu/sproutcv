import cv2
import os
import shutil
import pandas as pd

# ---------------- Calibration ---------------- #

def load_calibration_data(csv_path):
    return pd.read_csv(csv_path)


def move_image_to_folder(parent_folder, image_file, use_copy=True):

    image_name_no_ext = os.path.splitext(image_file)[0]
    image_path = os.path.join(parent_folder, image_file)

    image_folder = os.path.join(parent_folder, image_name_no_ext)
    os.makedirs(image_folder, exist_ok=True)

    new_image_path = os.path.join(image_folder, image_file)

    if use_copy:
        shutil.copy(image_path, new_image_path)
    else:
        shutil.move(image_path, new_image_path)

    return new_image_path, image_folder, image_name_no_ext


def get_mm_to_pixel_ratio(calibration_data, image_name_no_ext):

    row = calibration_data[calibration_data["file_name"] == image_name_no_ext]

    if not row.empty:
        return row.iloc[0]["distance"] / row.iloc[0]["pixel"]

    return None

# ---------------- Save ---------------- #

def save_results(image_folder, name, output_image, skeleton_image, sprout_data):

    cv2.imwrite(os.path.join(image_folder, f"skeletons_{name}.jpg"), skeleton_image)

    cv2.imwrite(
        os.path.join(image_folder, f"length_measurement_{name}.jpg"),
        output_image
    )

    pd.DataFrame(
        sprout_data,
        columns=["Sprout Number", "Pixels", "Millimeters"]
    ).to_csv(
        os.path.join(image_folder, f"sprout_lengths_{name}.csv"),
        index=False
    )
