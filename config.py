"""
Configuration constants for SproutCV application
All magic numbers and thresholds are defined here
"""


class ImageProcessingConfig:
    """Image processing parameters"""
    
    # Preprocessing
    MEAN_SHIFT_SP = 20  # Spatial window radius
    MEAN_SHIFT_SR = 40  # Color window radius
    GAUSSIAN_BLUR_KERNEL = (5, 5)  # Gaussian blur kernel size
    GAUSSIAN_BLUR_SIGMA = 0  # Auto-calculate sigma
    
    # Morphological operations
    MORPHOLOGY_KERNEL_SIZE = (3, 3)
    MORPHOLOGY_SHAPE = 'ELLIPSE'  # RECT, ELLIPSE, or CROSS
    
    # Contour filtering
    MIN_CONTOUR_AREA = 300  # Minimum pixels for valid contour
    
    # Row grouping
    ROW_TOLERANCE_RATIO = 0.08  # Fraction of image height for row grouping


class GraphConfig:
    """Graph analysis parameters"""
    
    # Path simplification
    PATH_SIMPLIFICATION_TOLERANCE = 2.0  # Pixels
    
    # Skeleton connectivity (8-connected neighborhood)
    NEIGHBORS = [
        (-1, 0), (1, 0), (0, -1), (0, 1),  # 4-connected
        (-1, -1), (-1, 1), (1, -1), (1, 1)  # Diagonals
    ]


class VisualizationConfig:
    """Visualization and display parameters"""
    
    # Font scaling
    MIN_FONT_SCALE = 0.45
    FONT_SCALE_DIVISOR = 1500
    MIN_THICKNESS = 1
    THICKNESS_MULTIPLIER = 3
    
    # Colors (BGR format for OpenCV)
    CONTOUR_COLOR = (255, 0, 0)  # Blue
    SKELETON_COLOR = (0, 0, 255)  # Red
    TEXT_OUTLINE_COLOR = (0, 0, 0)  # Black
    TEXT_COLOR = (255, 255, 255)  # White
    
    # Label placement
    LABEL_OFFSET_Y = 30  # Pixels above/below contour center
    LABEL_MARGIN = 8  # Margin from image edges
    LABEL_ADJUSTMENT_STEP = 22  # Step size for label repositioning


class ValidationConfig:
    """Input validation parameters"""
    
    # Required CSV columns
    REQUIRED_CSV_COLUMNS = {'file_name', 'pixel', 'distance'}
    
    # Supported image formats
    SUPPORTED_IMAGE_FORMATS = ('.jpg', '.jpeg', '.png', '.bmp', '.tiff')
    
    # File size limits (in MB)
    MAX_IMAGE_SIZE_MB = 50
    MAX_CSV_SIZE_MB = 10


class OutputConfig:
    """Output file naming and formats"""
    
    SKELETON_PREFIX = "skeletons_"
    MEASUREMENT_PREFIX = "length_measurement_"
    CSV_PREFIX = "sprout_lengths_"
    
    # Output image format
    OUTPUT_IMAGE_FORMAT = ".jpg"
    OUTPUT_IMAGE_QUALITY = 95  # For JPEG (0-100)


class ViewerConfig:
    """Results viewer default settings"""

    # Colors (BGR for OpenCV)
    DEFAULT_SKELETON_COLOR = (0, 0, 255)      # Red
    DEFAULT_CONTOUR_COLOR = (255, 0, 0)       # Blue
    DEFAULT_LABEL_COLOR = (255, 255, 255)     # White
    DEFAULT_LABEL_BG_COLOR = (0, 0, 0)        # Black

    # Thickness & font
    DEFAULT_SKELETON_THICKNESS = 2
    DEFAULT_CONTOUR_THICKNESS = 2
    DEFAULT_LABEL_FONT_SCALE = 0.6
    DEFAULT_LABEL_THICKNESS = 2

    # Label background
    DEFAULT_LABEL_BG_OPACITY = 0.7
    DEFAULT_USE_LABEL_BG = False


class LoggingConfig:
    """Logging configuration"""
    
    # Log levels
    DEFAULT_LEVEL = 'INFO'
    FILE_LEVEL = 'DEBUG'
    
    # Log format
    CONSOLE_FORMAT = '%(levelname)s: %(message)s'
    FILE_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Log file
    LOG_DIR = 'logs'
    LOG_FILE = 'sproutcv.log'