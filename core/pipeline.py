"""
Enhanced pipeline for SproutCV with support for new overlay system
"""

import os
import logging
from typing import Callable, Optional, Dict, Any

import pandas as pd

from sproutcv.io.calibration import load_calibration_data, get_mm_to_pixel_ratio
from sproutcv.io.image_io import move_image_to_folder, get_image_files
from sproutcv.analysis.preprocessing import preprocess_image
from sproutcv.core.validator import validate_inputs
from sproutcv.exceptions import ProcessingError, ValidationError

logger = logging.getLogger('sproutcv.pipeline')


def run_pipeline(
    parent_folder: str,
    csv_path: str,
    output_root: Optional[str] = None,
    log_callback: Optional[Callable[[str], None]] = None,
    progress_callback: Optional[Callable[[float], None]] = None,
) -> None:
    """
    Run the complete sprout analysis pipeline
    
    Args:
        parent_folder: Path to folder containing sprout images
        csv_path: Path to calibration CSV file
        output_root: Optional custom output root directory
        log_callback: Optional function for logging messages
        progress_callback: Optional function for progress updates (0.0-1.0)
    
    Raises:
        ProcessingError: If pipeline execution fails
        ValidationError: If inputs are invalid
    """
    log = log_callback or logger.info
    
    from sproutcv.analysis.sprout_detector import analyze_sprouts
    from sproutcv.io.results_writer import save_results_with_overlays

    try:
        log("Loading calibration data...")
        calibration_data = load_calibration_data(csv_path)
        log(f"✓ Loaded calibration for {len(calibration_data)} images")

        image_files = get_image_files(parent_folder)
        total = len(image_files)

        if total == 0:
            raise ValidationError(f"No images found in {parent_folder}")

        log(f"Found {total} images to process")

        processed = 0
        skipped = []
        errors = []

        for i, image_file in enumerate(image_files):
            try:
                log(f"\nProcessing [{i+1}/{total}]: {image_file}")

                new_image_path, image_folder, name = move_image_to_folder(
                    parent_folder,
                    image_file,
                    output_root=output_root,
                )

                ratio = get_mm_to_pixel_ratio(calibration_data, name)

                if ratio is None:
                    log(f"⚠ Skipping {name} - no calibration data")
                    skipped.append(name)
                    continue

                image, cleaned, gray = preprocess_image(new_image_path)

                result = analyze_sprouts(image, cleaned, gray, ratio)
                if len(result) == 4:
                    output_image, skeleton_image, sprout_data, overlay_data = result
                else:
                    raise ProcessingError(
                        f"analyze_sprouts returned {len(result)} values, expected 4"
                    )
                
                save_results_with_overlays(
                    image_folder, name, image,
                    output_image, skeleton_image,
                    sprout_data, overlay_data
                )

                log(f"✓ Found {len(sprout_data)} sprouts")
                processed += 1

            except Exception as e:
                logger.error(f"Error processing {image_file}: {str(e)}")
                log(f"❌ Error processing {image_file}: {str(e)}")
                errors.append((image_file, str(e)))

            finally:
                if progress_callback:
                    try:
                        progress_callback((i + 1) / total)
                    except Exception as e:
                        logger.warning(f"Progress callback failed: {e}")

        log("\n" + "="*50)
        log("PROCESSING SUMMARY")
        log("="*50)
        log(f"Total images: {total}")
        log(f"Successfully processed: {processed}")
        log(f"Skipped (no calibration): {len(skipped)}")
        log(f"Errors: {len(errors)}")

        if skipped:
            log("\nSkipped files:")
            for name in skipped:
                log(f"  - {name}")

        if errors:
            log("\nErrors encountered:")
            for filename, error in errors:
                log(f"  - {filename}: {error}")

        if errors:
            raise ProcessingError(f"Pipeline completed with {len(errors)} error(s)")

        log("\n✅ Pipeline completed successfully!")
        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        log(f"\n❌ Pipeline failed: {str(e)}")
        raise


def dry_run_pipeline(
    parent_folder: str,
    csv_path: str,
    log_callback: Optional[Callable[[str], None]] = None,
    verbose: bool = True,
    return_report: bool = False,
) -> Optional[Dict[str, Any]]:
    """
    Validate inputs without running full analysis
    
    Args:
        parent_folder: Path to folder containing sprout images
        csv_path: Path to calibration CSV file
        log_callback: Optional function for logging messages
        verbose: If True, show detailed validation messages
        return_report: If True, return validation report dict
    
    Returns:
        dict or None: Validation report if return_report=True, containing:
            - 'fatal' (list): Fatal errors that must be fixed
            - 'warnings' (list): Warnings that should be reviewed
            - 'info' (list): Informational messages
        
    Raises:
        ValidationError: If validation fails with fatal errors
    """
    log = log_callback or logger.info
    
    log("🧪 Running validation...")
    
    try:
        # Run validation
        report = validate_inputs(
            parent_folder,
            csv_path,
            log_callback=log,
            verbose=verbose
        )
        
        # Check for fatal errors
        if report['fatal']:
            error_count = len(report['fatal'])
            raise ValidationError(
                f"Validation failed with {error_count} fatal error(s). "
                f"See log for details."
            )
        
        log("\n✅ Validation passed! Ready to process.")
        logger.info("Validation passed")
        
        if return_report:
            return report
            
    except Exception as e:
        logger.error(f"Validation failed: {str(e)}")
        log(f"\n❌ Validation failed: {str(e)}")
        raise