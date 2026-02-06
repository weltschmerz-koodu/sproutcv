# SproutCV - Automated Sprout Length Measurement

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![OpenCV](https://img.shields.io/badge/opencv-4.8+-red.svg)

SproutCV is a desktop application for automated measurement of sprout lengths from images using computer vision techniques. It provides a user-friendly graphical interface for batch processing sprout images with calibrated measurements.

## Features

- **Automated Sprout Detection**: Detects and measures individual sprouts from images
- **Batch Processing**: Process multiple images in a single run
- **Calibration Support**: Uses pixel-to-millimeter calibration data from CSV files
- **Interactive Results Viewer**: View and customize visualization of detected sprouts
- **Comprehensive Validation**: Pre-flight checks to ensure data integrity
- **Detailed Logging**: Track processing progress and debug issues
- **Export Options**: Outputs measurements, skeleton visualizations, and overlay data

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Guide](#usage-guide)
- [Input Requirements](#input-requirements)
- [Output Files](#output-files)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Architecture](#architecture)
- [Contributing](#contributing)

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install Dependencies

```bash
# Clone or download the repository
cd sproutcv

# Install required packages
pip install -r requirements.txt
```

### Dependencies

The application requires the following packages:

- **PySide6** (6.6.1): GUI framework
- **opencv-python** (4.8.1.78): Computer vision operations
- **scikit-image** (0.22.0): Image processing and skeletonization
- **numpy** (1.24.4): Numerical computations
- **pandas** (2.1.4): Data handling
- **networkx** (3.2.1): Graph analysis for skeleton paths
- **shapely** (2.0.2): Geometric operations

## Quick Start

1. **Launch the application**:
   ```bash
   python main.py
   ```

2. **Select your image folder**: Browse to the folder containing sprout images

3. **Select calibration CSV**: Choose the CSV file with calibration data

4. **Validate inputs**: Click "Validate" to check for issues before processing

5. **Process images**: Click "Process" to start batch analysis

6. **View results**: Use the Results Viewer to examine outputs

## Usage Guide

### Step 1: Prepare Your Data

#### Image Requirements
- Supported formats: `.jpg`, `.jpeg`, `.png`, `.bmp`, `.tiff`
- Images should clearly show sprouts against a contrasting background
- Recommended resolution: 1000x1000 pixels or higher

#### Calibration CSV Format

Create a CSV file with the following columns:

| file_name | pixel | distance |
|-----------|-------|----------|
| image1    | 250   | 10       |
| image2    | 240   | 10       |
| image3    | 255   | 10       |

- **file_name**: Image filename without extension
- **pixel**: Number of pixels in reference measurement
- **distance**: Real-world distance in millimeters

**Example calibration.csv**:
```csv
file_name,pixel,distance
sprout_001,245,10
sprout_002,250,10
sprout_003,248,10
```

### Step 2: Run Validation

Before processing, use the **Validate** button to check:
- ✓ All images have matching calibration data
- ✓ CSV file is properly formatted
- ✓ File paths are accessible
- ✓ No duplicate entries

The validation report will show:
- **Fatal Errors**: Must be fixed before processing
- **Warnings**: Should be reviewed but won't prevent processing
- **Info**: General information about your dataset

### Step 3: Process Images

Click **Process** to begin batch analysis. The application will:

1. Load each image and its calibration data
2. Preprocess the image (filtering, thresholding, morphology)
3. Detect sprout contours
4. Generate skeleton representations
5. Calculate path lengths in pixels and millimeters
6. Save results and visualizations

Progress is shown in real-time with a progress bar and detailed log messages.

### Step 4: Review Results

Use the **Results Viewer** to:
- Browse processed images
- Toggle visibility of overlays (contours, skeletons, labels)
- Customize colors and styles
- Export modified visualizations

## Input Requirements

### Image Folder Structure

```
parent_folder/
├── sprout_001.jpg
├── sprout_002.jpg
├── sprout_003.jpg
└── ...
```

### Calibration CSV Requirements

- Must contain columns: `file_name`, `pixel`, `distance`
- Each image must have exactly one calibration row
- Values must be positive numbers
- File names must match image names (without extension)

## Output Files

For each processed image, SproutCV creates an output folder containing:

### Directory Structure

```
parent_folder/
└── sprout_001/
    ├── sprout_001.jpg                           # Original image copy
    ├── length_measurement_sprout_001.jpg        # Annotated image with measurements
    ├── skeletons_sprout_001.jpg                 # Skeleton visualization
    ├── mask_skeleton_sprout_001.png             # Binary skeleton mask
    ├── mask_contour_sprout_001.png              # Binary contour mask
    ├── overlay_data_sprout_001.json             # Overlay metadata for interactive viewing
    └── sprout_lengths_sprout_001.csv            # Measurement data
```

### File Descriptions

#### `sprout_lengths_[name].csv`
Measurement data in CSV format:

| Sprout Number | Pixels | Millimeters |
|---------------|--------|-------------|
| 1             | 245.3  | 9.81        |
| 2             | 312.7  | 12.51       |

#### `overlay_data_[name].json`
Interactive overlay metadata containing:
- Contour coordinates
- Skeleton path points
- Label positions and text
- Font scales and styling information

#### `length_measurement_[name].jpg`
Annotated image showing:
- Detected contours (blue)
- Skeleton paths (red)
- Measurement labels (white text with black outline)

#### `mask_skeleton_[name].png` & `mask_contour_[name].png`
Binary masks for skeleton and contour overlays, useful for custom visualizations.

## Configuration

### Adjusting Processing Parameters

Edit `config.py` to customize processing behavior:

#### Image Processing

```python
class ImageProcessingConfig:
    MEAN_SHIFT_SP = 20              # Spatial window radius
    MEAN_SHIFT_SR = 40              # Color window radius
    GAUSSIAN_BLUR_KERNEL = (5, 5)   # Blur kernel size
    MIN_CONTOUR_AREA = 300          # Minimum sprout area (pixels)
    ROW_TOLERANCE_RATIO = 0.08      # Row grouping tolerance
```

#### Visualization

```python
class VisualizationConfig:
    CONTOUR_COLOR = (255, 0, 0)     # Blue (BGR)
    SKELETON_COLOR = (0, 0, 255)    # Red (BGR)
    TEXT_COLOR = (255, 255, 255)    # White (BGR)
    LABEL_OFFSET_Y = 30             # Label positioning
```

#### Validation

```python
class ValidationConfig:
    MAX_IMAGE_SIZE_MB = 50          # Maximum image file size
    MAX_CSV_SIZE_MB = 10            # Maximum CSV file size
```

### Logging Configuration

Logs are saved to `logs/sproutcv.log`. Adjust logging levels in `config.py`:

```python
class LoggingConfig:
    DEFAULT_LEVEL = 'INFO'          # Console log level
    FILE_LEVEL = 'DEBUG'            # File log level
```

## Troubleshooting

### Common Issues

#### "No calibration data found"
- **Cause**: Image filename doesn't match any `file_name` in CSV
- **Solution**: Ensure CSV `file_name` values match image filenames (without extension)

#### "Image has invalid dimensions"
- **Cause**: Corrupted or empty image file
- **Solution**: Re-export the image or check file integrity

#### "Failed to detect sprouts"
- **Cause**: Image contrast too low or sprouts too small
- **Solution**: 
  - Improve image lighting/contrast
  - Adjust `MIN_CONTOUR_AREA` in config
  - Check image preprocessing parameters

#### "Permission denied"
- **Cause**: Insufficient file system permissions
- **Solution**: Run with appropriate permissions or choose a different output location

#### Large Files Warning
- **Cause**: Images larger than 50MB
- **Solution**: Resize images or adjust `MAX_IMAGE_SIZE_MB` in config

### Debug Mode

For detailed debugging information, check `logs/sproutcv.log`. The log file contains:
- Processing steps for each image
- Error stack traces
- Performance metrics
- Validation results

## Architecture

### Project Structure

```
sproutcv/
├── main.py                    # Application entry point
├── config.py                  # Configuration constants
├── exceptions.py              # Custom exception classes
│
├── gui/                       # Graphical interface
│   ├── main_window.py         # Main application window
│   ├── widgets/               # Reusable UI components
│   └── workers/               # Background processing threads
│
├── core/                      # Core pipeline logic
│   ├── pipeline.py            # Main processing pipeline
│   └── validator.py           # Input validation
│
├── analysis/                  # Image analysis
│   ├── preprocessing.py       # Image preprocessing
│   └── sprout_detector.py     # Sprout detection and measurement
│
├── io/                        # Input/output operations
│   ├── calibration.py         # Calibration data loading
│   ├── image_io.py            # Image file operations
│   └── results_writer.py      # Results export
│
└── utils/                     # Utility functions
    └── graph_utils.py         # Graph/skeleton analysis
```

### Processing Pipeline

```
Input Image → Preprocessing → Contour Detection → Skeletonization
     ↓              ↓                ↓                  ↓
Validation    Mean Shift      Find Contours      Skeleton Graph
     ↓         Gaussian Blur   Filter by Area     Find Endpoints
Calibration   Thresholding    Group by Rows      Shortest Path
     ↓         Morphology           ↓                  ↓
Results ← Measurement ← Path Simplification ← Length Calculation
```

### Key Algorithms

1. **Preprocessing**: Mean shift filtering → Gaussian blur → Otsu's thresholding → Morphological operations
2. **Detection**: Contour detection → Centroid calculation → Row grouping
3. **Skeletonization**: Binary thinning to single-pixel width representation
4. **Measurement**: Graph-based path finding → Douglas-Peucker simplification → Length calculation

## Advanced Usage

### Programmatic Access

You can use SproutCV as a library:

```python
from sproutcv.core.pipeline import run_pipeline

def my_log_callback(message):
    print(message)

def my_progress_callback(progress):
    print(f"Progress: {progress * 100:.1f}%")

run_pipeline(
    parent_folder="/path/to/images",
    csv_path="/path/to/calibration.csv",
    output_root="/path/to/output",  # Optional
    log_callback=my_log_callback,
    progress_callback=my_progress_callback
)
```

### Validation Only (Dry Run)

```python
from sproutcv.core.pipeline import dry_run_pipeline

report = dry_run_pipeline(
    parent_folder="/path/to/images",
    csv_path="/path/to/calibration.csv",
    verbose=True,
    return_report=True
)

print(f"Fatal errors: {len(report['fatal'])}")
print(f"Warnings: {len(report['warnings'])}")
```

## Contributing

Contributions are welcome! Areas for improvement:

- Additional preprocessing filters
- Machine learning-based detection
- Support for more image formats
- Batch calibration tools
- Statistical analysis features
- Export to additional formats

## License

This project is licensed under the MIT License.

## Acknowledgments

- Built with OpenCV for computer vision operations
- Uses scikit-image for morphological operations
- NetworkX for graph-based skeleton analysis
- PySide6 for the graphical interface

## Contact & Support

For issues, questions, or suggestions, please open an issue on the project repository.

---

**Version**: 1.0.0  
**Last Updated**: February 2026
