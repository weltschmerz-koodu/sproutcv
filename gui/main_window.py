"""
Enhanced main application window for SproutCV with tabbed interface
"""

import os
import sys
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QMessageBox,
    QGroupBox, QProgressBar, QTabWidget
)
from PySide6.QtCore import Qt

from sproutcv.gui.widgets.file_selector import FileSelector
from sproutcv.gui.widgets.log_viewer import LogViewer
from sproutcv.gui.widgets.results_viewer import ResultsViewer
from sproutcv.gui.workers.pipeline_worker import PipelineWorker
from sproutcv.config import LoggingConfig

logger = logging.getLogger('sproutcv.gui')


class MainWindow(QMainWindow):
    """Enhanced main application window with tabbed interface"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("SproutCV")
        self.setMinimumSize(1400, 800)
        
        # State variables
        self.image_folder = None
        self.csv_file = None
        self.output_folder = None
        self.worker = None
        
        self._setup_ui()
        self._setup_connections()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the user interface with tabs"""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Header
        header = QLabel("SproutCV - Sprout Length Measurement through Computer Vision")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #ecf0f1;
                border: 2px solid #bdc3c7;
                border-bottom: none;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                padding: 10px 20px;
                margin-right: 2px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid white;
            }
            QTabBar::tab:hover {
                background-color: #d5dbdb;
            }
        """)
        
        # Tab 1: Input & Control
        self.input_tab = self._create_input_tab()
        self.tab_widget.addTab(self.input_tab, "Input & Control")
        
        # Tab 2: Results Viewer
        self.viewer_tab = self._create_viewer_tab()
        self.tab_widget.addTab(self.viewer_tab, "Results Viewer")
        
        # Tab 3: Processing Log
        self.log_tab = self._create_log_tab()
        self.tab_widget.addTab(self.log_tab, "Process Logs")
        
        main_layout.addWidget(self.tab_widget)
    
    def _create_input_tab(self):
        """Create input and control tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Input section
        input_group = self._create_input_section()
        layout.addWidget(input_group)
        
        # Control buttons
        control_group = self._create_control_section()
        layout.addWidget(control_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(30)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #27ae60;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Status message
        self.status_label = QLabel("Ready to process images")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
                font-size: 11px;
            }
        """)
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add stretch to push everything to top
        layout.addStretch()
        
        return tab
    
    def _create_viewer_tab(self):
        """Create results viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Results viewer
        self.results_viewer = ResultsViewer()
        layout.addWidget(self.results_viewer)
        
        return tab
    
    def _create_log_tab(self):
        """Create processing log tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Log viewer
        log_group = QGroupBox("Processing Messages")
        log_layout = QVBoxLayout()
        self.log_viewer = LogViewer()
        log_layout.addWidget(self.log_viewer)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Clear button
        clear_btn = QPushButton("🗑️ Clear Log")
        clear_btn.setMinimumHeight(35)
        clear_btn.clicked.connect(self.log_viewer.clear)
        layout.addWidget(clear_btn)
        
        return tab
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait(5000)  # Wait up to 5 seconds
        logger.info("Application closing")
        event.accept()
    
    def _create_input_section(self):
        """Create input file selection section"""
        group = QGroupBox("Input Files")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout()
        
        # Image folder selector
        self.image_selector = FileSelector(
            "Image Folder:",
            is_folder=True,
            callback=self._on_image_folder_selected
        )
        layout.addWidget(self.image_selector)
        
        # CSV file selector
        self.csv_selector = FileSelector(
            "Calibration CSV:",
            is_folder=False,
            file_filter="CSV Files (*.csv)",
            callback=self._on_csv_selected
        )
        layout.addWidget(self.csv_selector)
        
        # Output folder selector (optional)
        self.output_selector = FileSelector(
            "Output Folder (optional):",
            is_folder=True,
            callback=self._on_output_folder_selected,
            optional=True
        )
        layout.addWidget(self.output_selector)
        
        group.setLayout(layout)
        return group
    
    def _create_control_section(self):
        """Create control buttons section"""
        group = QGroupBox("Actions")
        group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        layout = QVBoxLayout()
        
        # First row of buttons
        row1 = QHBoxLayout()
        
        # Validate button
        self.validate_btn = QPushButton("Validate Inputs")
        self.validate_btn.setEnabled(False)
        self.validate_btn.setMinimumHeight(45)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        row1.addWidget(self.validate_btn)
        
        # Process button
        self.process_btn = QPushButton("Process Images")
        self.process_btn.setEnabled(False)
        self.process_btn.setMinimumHeight(45)
        self.process_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        row1.addWidget(self.process_btn)
        
        layout.addLayout(row1)
        
        # Second row - Load results button
        self.load_results_btn = QPushButton("📂 Load Results Folder")
        self.load_results_btn.setMinimumHeight(40)
        self.load_results_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
        """)
        layout.addWidget(self.load_results_btn)
        
        group.setLayout(layout)
        return group
    
    def _setup_connections(self):
        """Setup signal-slot connections"""
        self.validate_btn.clicked.connect(self._validate_inputs)
        self.process_btn.clicked.connect(self._process_images)
        self.load_results_btn.clicked.connect(self._load_results_folder)
    
    def _on_image_folder_selected(self, folder):
        """Handle image folder selection"""
        self.image_folder = folder
        self.log_viewer.log(f"✓ Image folder selected: {folder}")
        self.status_label.setText(f"Image folder: {os.path.basename(folder)}")
        self._update_button_states()
        logger.info(f"Image folder selected: {folder}")
    
    def _on_csv_selected(self, file):
        """Handle CSV file selection"""
        self.csv_file = file
        self.log_viewer.log(f"✓ Calibration CSV selected: {file}")
        self.status_label.setText(f"CSV file: {os.path.basename(file)}")
        self._update_button_states()
        logger.info(f"Calibration CSV selected: {file}")
    
    def _on_output_folder_selected(self, folder):
        """Handle output folder selection"""
        self.output_folder = folder
        if folder:
            self.log_viewer.log(f"✓ Output folder selected: {folder}")
            logger.info(f"Output folder selected: {folder}")
        else:
            self.log_viewer.log("ℹ Using default output location")
    
    def _update_button_states(self):
        """Update button enabled states based on inputs"""
        has_image = self.image_selector.get_path() is not None
        has_csv = self.csv_selector.get_path() is not None
        has_inputs = has_image and has_csv
        
        self.validate_btn.setEnabled(has_inputs)
        self.process_btn.setEnabled(has_inputs)
        
        if has_inputs:
            self.status_label.setText("Ready to process")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #d5f4e6;
                    border-radius: 5px;
                    font-size: 11px;
                    color: #27ae60;
                    font-weight: bold;
                }
            """)
    
    def _validate_inputs(self):
        """Run validation in dry-run mode"""
        self.log_viewer.log("\n" + "="*50)
        self.log_viewer.log("Starting validation...")
        self.log_viewer.log("="*50)
        
        # Switch to log tab
        self.tab_widget.setCurrentIndex(2)
        
        self._run_pipeline(dry_run=True, verbose=True)
    
    def _process_images(self):
        """Run full image processing pipeline"""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            'Confirm Processing',
            'Start processing images? This may take several minutes.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        self.log_viewer.log("\n" + "="*50)
        self.log_viewer.log("Starting image processing...")
        self.log_viewer.log("="*50)
        
        # Switch to log tab
        self.tab_widget.setCurrentIndex(2)
        
        # Clear previous results
        self.results_viewer.clear_images()
        
        self._run_pipeline(dry_run=False)
    
    def _run_pipeline(self, dry_run=False, verbose=False):
        """Execute the pipeline in a worker thread"""
        # Disable controls during processing
        self._set_controls_enabled(False)
        self.progress_bar.setVisible(not dry_run)
        self.progress_bar.setValue(0)
        
        if dry_run:
            self.status_label.setText("Validating inputs...")
        else:
            self.status_label.setText("Processing images...")
        
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #fff3cd;
                border-radius: 5px;
                font-size: 11px;
                color: #856404;
                font-weight: bold;
            }
        """)
        
        # Create and configure worker
        self.worker = PipelineWorker(
            folder=self.image_folder,
            csv_path=self.csv_file,
            output_root=self.output_folder,
            dry_run=dry_run,
            verbose=verbose
        )
        
        # Connect signals
        self.worker.log_signal.connect(self.log_viewer.log)
        self.worker.progress_signal.connect(self._update_progress)
        self.worker.finished_signal.connect(
            lambda: self._on_processing_finished(dry_run)
        )
        self.worker.error_signal.connect(self._on_processing_error)
        
        # Start processing
        self.worker.start()
        logger.info(f"Started {'validation' if dry_run else 'processing'}")
    
    def _update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(int(value * 100))
    
    def _on_processing_finished(self, was_dry_run):
        """Handle successful completion"""
        if not was_dry_run:
            self.log_viewer.log("\n✅ Processing completed successfully!")
            self._auto_load_results()
            self.status_label.setText("Processing complete!")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #d5f4e6;
                    border-radius: 5px;
                    font-size: 11px;
                    color: #27ae60;
                    font-weight: bold;
                }
            """)
            # Switch to viewer tab
            self.tab_widget.setCurrentIndex(1)
        else:
            self.log_viewer.log("\n✅ Validation completed successfully!")
            self.status_label.setText("Validation passed!")
            self.status_label.setStyleSheet("""
                QLabel {
                    padding: 10px;
                    background-color: #d5f4e6;
                    border-radius: 5px;
                    font-size: 11px;
                    color: #27ae60;
                    font-weight: bold;
                }
            """)
        
        self._set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        if not was_dry_run:
            QMessageBox.information(
                self,
                'Success',
                'Processing completed successfully!\nResults loaded in viewer.'
            )
        
        logger.info(f"{'Validation' if was_dry_run else 'Processing'} completed successfully")
    
    def _on_processing_error(self, error_msg):
        """Handle processing errors"""
        self.log_viewer.log(f"\n❌ ERROR: {error_msg}")
        self._set_controls_enabled(True)
        self.progress_bar.setVisible(False)
        
        self.status_label.setText("Processing failed!")
        self.status_label.setStyleSheet("""
            QLabel {
                padding: 10px;
                background-color: #f8d7da;
                border-radius: 5px;
                font-size: 11px;
                color: #721c24;
                font-weight: bold;
            }
        """)
        
        # Switch to log tab to show error
        self.tab_widget.setCurrentIndex(2)
        
        QMessageBox.critical(
            self,
            'Error',
            f'Processing failed:\n\n{error_msg}'
        )
        
        logger.error(f"Processing error: {error_msg}")
    
    def _auto_load_results(self):
        """Automatically load results after processing"""
        # Determine output folder
        if self.output_folder:
            base_folder = self.output_folder
        else:
            base_folder = self.image_folder
        
        # Find all subfolders (each image creates its own folder)
        try:
            items = os.listdir(base_folder)
            for item in items:
                item_path = os.path.join(base_folder, item)
                if os.path.isdir(item_path):
                    # Check if it contains output files
                    files = os.listdir(item_path)
                    has_skeleton = any(f.startswith("skeletons_") for f in files)
                    has_measurement = any(f.startswith("length_measurement_") for f in files)
                    
                    if has_skeleton and has_measurement:
                        self.results_viewer.add_processed_image(item, item_path)
            
            self.log_viewer.log(f"📊 Loaded {len(self.results_viewer.processed_images)} results into viewer")
            logger.info(f"Auto-loaded {len(self.results_viewer.processed_images)} results")
            
        except Exception as e:
            self.log_viewer.log(f"⚠️ Could not auto-load results: {str(e)}")
            logger.warning(f"Auto-load failed: {str(e)}")
    
    def _load_results_folder(self):
        """Manually load a folder containing processed results"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Results Folder",
            self.image_folder if self.image_folder else ""
        )
        
        if not folder:
            return
        
        self.results_viewer.clear_images()
        
        # Find all subfolders
        try:
            items = os.listdir(folder)
            count = 0
            
            for item in items:
                item_path = os.path.join(folder, item)
                if os.path.isdir(item_path):
                    # Check if it contains output files
                    files = os.listdir(item_path)
                    has_skeleton = any(f.startswith("skeletons_") for f in files)
                    has_measurement = any(f.startswith("length_measurement_") for f in files)
                    
                    if has_skeleton and has_measurement:
                        self.results_viewer.add_processed_image(item, item_path)
                        count += 1
            
            if count > 0:
                self.log_viewer.log(f"✓ Loaded {count} processed images from {folder}")
                # Switch to viewer tab
                self.tab_widget.setCurrentIndex(1)
                QMessageBox.information(
                    self,
                    'Results Loaded',
                    f'Successfully loaded {count} processed images.'
                )
                logger.info(f"Manually loaded {count} results from {folder}")
            else:
                self.log_viewer.log(f"⚠️ No processed images found in {folder}")
                QMessageBox.warning(
                    self,
                    'No Results Found',
                    'No processed images found in selected folder.'
                )
                logger.warning(f"No results found in {folder}")
        
        except Exception as e:
            self.log_viewer.log(f"❌ Error loading results: {str(e)}")
            QMessageBox.critical(
                self,
                'Error',
                f'Failed to load results:\n\n{str(e)}'
            )
            logger.error(f"Error loading results: {str(e)}")
    
    def _set_controls_enabled(self, enabled):
        """Enable/disable controls during processing"""
        self.image_selector.setEnabled(enabled)
        self.csv_selector.setEnabled(enabled)
        self.output_selector.setEnabled(enabled)
        
        if enabled:        
            self._update_button_states()
        else:
            self.validate_btn.setEnabled(False)
            self.process_btn.setEnabled(False)
        
        self.load_results_btn.setEnabled(enabled)