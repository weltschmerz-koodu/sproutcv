"""
Enhanced Interactive Results Viewer with True Overlay Rendering
Properly handles separate skeleton, contour, and label overlays
"""

import os
import cv2
import json
import numpy as np
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QComboBox, QCheckBox, QPushButton, QSpinBox, QDoubleSpinBox,
    QColorDialog, QGroupBox, QScrollArea, QTabWidget,
    QSizePolicy, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPixmap, QColor
from typing import Dict, Any, List, Tuple

from sproutcv.config import ViewerConfig



class ResultsViewer(QWidget):
    """Enhanced interactive viewer with proper overlay rendering"""
    
    def __init__(self):
        super().__init__()
        
        # State
        self.processed_images = []  # List of (name, folder_path) tuples
        self.current_image_name = None
        self.current_folder = None
        
        # Images and data
        self.original_image = None
        self.skeleton_mask = None
        self.contour_mask = None
        self.overlay_metadata = None  # JSON data with paths and labels
        
        # Overlay settings
        self.show_skeleton = True
        self.show_contours = True
        self.show_labels = True
        
        self.skeleton_color = ViewerConfig.DEFAULT_SKELETON_COLOR
        self.contour_color = ViewerConfig.DEFAULT_CONTOUR_COLOR
        self.label_color = ViewerConfig.DEFAULT_LABEL_COLOR
        self.label_bg_color = ViewerConfig.DEFAULT_LABEL_BG_COLOR
        self.use_label_bg = ViewerConfig.DEFAULT_USE_LABEL_BG
        self.label_bg_opacity = ViewerConfig.DEFAULT_LABEL_BG_OPACITY

        self.skeleton_thickness = ViewerConfig.DEFAULT_SKELETON_THICKNESS
        self.contour_thickness = ViewerConfig.DEFAULT_CONTOUR_THICKNESS
        self.label_font_scale = ViewerConfig.DEFAULT_LABEL_FONT_SCALE
        self.label_thickness = ViewerConfig.DEFAULT_LABEL_THICKNESS
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the user interface with tabs"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Image selector at top
        selector_layout = QHBoxLayout()
        selector_layout.addWidget(QLabel("<b>Select Image:</b>"))
        
        self.image_combo = QComboBox()
        self.image_combo.currentTextChanged.connect(self._on_image_selected)
        selector_layout.addWidget(self.image_combo, stretch=1)
        
        # Refresh button
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._refresh_current_image)
        selector_layout.addWidget(refresh_btn)
        
        layout.addLayout(selector_layout)
        
        # Create tab widget
        self.tabs = QTabWidget()
        
        # Tab 1: Viewer
        viewer_tab = self._create_viewer_tab()
        self.tabs.addTab(viewer_tab, "📊 Image Viewer")
        
        # Tab 2: Overlay Controls
        controls_tab = self._create_controls_tab()
        self.tabs.addTab(controls_tab, "🎨 Overlay Controls")
        
        # Tab 3: Data Table (placeholder for future)
        data_tab = self._create_data_tab()
        self.tabs.addTab(data_tab, "📋 Measurements")
        
        layout.addWidget(self.tabs)
    
    def _create_viewer_tab(self):
        """Create the main image viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Quick toggle controls
        quick_controls = QHBoxLayout()
        
        self.skeleton_check = QCheckBox("Show Skeleton")
        self.skeleton_check.setChecked(self.show_skeleton)
        self.skeleton_check.stateChanged.connect(self._update_display)
        quick_controls.addWidget(self.skeleton_check)
        
        self.contour_check = QCheckBox("Show Contours")
        self.contour_check.setChecked(self.show_contours)
        self.contour_check.stateChanged.connect(self._update_display)
        quick_controls.addWidget(self.contour_check)
        
        self.labels_check = QCheckBox("Show Labels")
        self.labels_check.setChecked(self.show_labels)
        self.labels_check.stateChanged.connect(self._update_display)
        quick_controls.addWidget(self.labels_check)
        
        quick_controls.addStretch()
        
        # Export button in quick controls
        export_btn = QPushButton("💾 Export Current View")
        export_btn.clicked.connect(self._export_current_view)
        quick_controls.addWidget(export_btn)
        
        layout.addLayout(quick_controls)
        
        # Image display area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("""
            QLabel {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 20px;
                min-height: 500px;
            }
        """)
        self.image_label.setMinimumSize(800, 500)
        
        scroll_area.setWidget(self.image_label)
        layout.addWidget(scroll_area)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        layout.addWidget(self.status_label)
        
        return tab
    
    def _create_controls_tab(self):
        """Create the overlay customization controls tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Skeleton controls
        skeleton_group = self._create_skeleton_controls()
        layout.addWidget(skeleton_group)
        
        # Contour controls
        contour_group = self._create_contour_controls()
        layout.addWidget(contour_group)
        
        # Label controls
        label_group = self._create_label_controls()
        layout.addWidget(label_group)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 Reset to Defaults")
        reset_btn.clicked.connect(self._reset_to_defaults)
        button_layout.addWidget(reset_btn)
        
        apply_btn = QPushButton("✓ Apply Changes")
        apply_btn.clicked.connect(self._update_display)
        apply_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(apply_btn)
        
        layout.addLayout(button_layout)
        layout.addStretch()
        
        return tab
    
    def _create_data_tab(self):
        """Create the data/measurements tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_label = QLabel("<h3>Measurement Data</h3>")
        layout.addWidget(info_label)
        
        # Table will be populated when image is loaded
        self.data_display = QLabel("No data loaded")
        self.data_display.setWordWrap(True)
        self.data_display.setStyleSheet("""
            QLabel {
                background-color: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                font-family: 'Courier New', monospace;
            }
        """)
        
        scroll = QScrollArea()
        scroll.setWidget(self.data_display)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        return tab
    
    def _create_skeleton_controls(self):
        """Create skeleton customization controls"""
        group = QGroupBox("Skeleton Settings")
        layout = QVBoxLayout()
        
        # Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.skeleton_color_btn = QPushButton()
        self.skeleton_color_btn.setFixedSize(80, 30)
        self._update_color_button(self.skeleton_color_btn, self.skeleton_color)
        self.skeleton_color_btn.clicked.connect(
            lambda: self._pick_color('skeleton')
        )
        color_layout.addWidget(self.skeleton_color_btn)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # Thickness
        thick_layout = QHBoxLayout()
        thick_layout.addWidget(QLabel("Line Thickness:"))
        
        self.skeleton_thick_spin = QSpinBox()
        self.skeleton_thick_spin.setRange(1, 15)
        self.skeleton_thick_spin.setValue(self.skeleton_thickness)
        self.skeleton_thick_spin.setSuffix(" px")
        thick_layout.addWidget(self.skeleton_thick_spin)
        thick_layout.addStretch()
        
        layout.addLayout(thick_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_contour_controls(self):
        """Create contour customization controls"""
        group = QGroupBox("Contour Settings")
        layout = QVBoxLayout()
        
        # Color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Color:"))
        
        self.contour_color_btn = QPushButton()
        self.contour_color_btn.setFixedSize(80, 30)
        self._update_color_button(self.contour_color_btn, self.contour_color)
        self.contour_color_btn.clicked.connect(
            lambda: self._pick_color('contour')
        )
        color_layout.addWidget(self.contour_color_btn)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # Thickness
        thick_layout = QHBoxLayout()
        thick_layout.addWidget(QLabel("Line Thickness:"))
        
        self.contour_thick_spin = QSpinBox()
        self.contour_thick_spin.setRange(1, 15)
        self.contour_thick_spin.setValue(self.contour_thickness)
        self.contour_thick_spin.setSuffix(" px")
        thick_layout.addWidget(self.contour_thick_spin)
        thick_layout.addStretch()
        
        layout.addLayout(thick_layout)
        
        group.setLayout(layout)
        return group
    
    def _create_label_controls(self):
        """Create label customization controls"""
        group = QGroupBox("Label Settings")
        layout = QVBoxLayout()
        
        # Text color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Text Color:"))
        
        self.label_color_btn = QPushButton()
        self.label_color_btn.setFixedSize(80, 30)
        self._update_color_button(self.label_color_btn, self.label_color)
        self.label_color_btn.clicked.connect(
            lambda: self._pick_color('label')
        )
        color_layout.addWidget(self.label_color_btn)
        color_layout.addStretch()
        
        layout.addLayout(color_layout)
        
        # Background
        bg_layout = QHBoxLayout()
        
        self.label_bg_check = QCheckBox("Background:")
        self.label_bg_check.setChecked(self.use_label_bg)
        bg_layout.addWidget(self.label_bg_check)
        
        self.label_bg_color_btn = QPushButton()
        self.label_bg_color_btn.setFixedSize(80, 30)
        self._update_color_button(self.label_bg_color_btn, self.label_bg_color)
        self.label_bg_color_btn.clicked.connect(
            lambda: self._pick_color('label_bg')
        )
        bg_layout.addWidget(self.label_bg_color_btn)
        
        bg_layout.addWidget(QLabel("Opacity:"))
        self.label_bg_opacity_spin = QDoubleSpinBox()
        self.label_bg_opacity_spin.setRange(0.0, 1.0)
        self.label_bg_opacity_spin.setSingleStep(0.1)
        self.label_bg_opacity_spin.setValue(self.label_bg_opacity)
        bg_layout.addWidget(self.label_bg_opacity_spin)
        
        bg_layout.addStretch()
        layout.addLayout(bg_layout)
        
        # Font scale
        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Font Scale:"))
        
        self.label_font_spin = QDoubleSpinBox()
        self.label_font_spin.setRange(0.1, 3.0)
        self.label_font_spin.setSingleStep(0.1)
        self.label_font_spin.setValue(self.label_font_scale)
        font_layout.addWidget(self.label_font_spin)
        font_layout.addStretch()
        
        layout.addLayout(font_layout)
        
        # Thickness
        thick_layout = QHBoxLayout()
        thick_layout.addWidget(QLabel("Text Thickness:"))
        
        self.label_thick_spin = QSpinBox()
        self.label_thick_spin.setRange(1, 10)
        self.label_thick_spin.setValue(self.label_thickness)
        self.label_thick_spin.setSuffix(" px")
        thick_layout.addWidget(self.label_thick_spin)
        thick_layout.addStretch()
        
        layout.addLayout(thick_layout)
        
        group.setLayout(layout)
        return group
    
    def _update_color_button(self, button, bgr_color):
        """Update button background to show selected color (BGR input)"""
        # Convert BGR to RGB for display
        if isinstance(bgr_color, tuple):
            b, g, r = bgr_color
        else:
            # It's a QColor
            r, g, b = bgr_color.red(), bgr_color.green(), bgr_color.blue()
        
        button.setStyleSheet(
            f"background-color: rgb({r}, {g}, {b}); border: 1px solid #000;"
        )
    
    def _pick_color(self, color_type):
        """Open color picker dialog"""
        # Convert current BGR to QColor for picker
        if color_type == 'skeleton':
            b, g, r = self.skeleton_color
        elif color_type == 'contour':
            b, g, r = self.contour_color
        elif color_type == 'label':
            b, g, r = self.label_color
        elif color_type == 'label_bg':
            b, g, r = self.label_bg_color
        
        current_qcolor = QColor(r, g, b)
        color = QColorDialog.getColor(current_qcolor, self, "Select Color")
        
        if color.isValid():
            # Convert QColor RGB back to BGR for OpenCV
            bgr_color = (color.blue(), color.green(), color.red())
            
            if color_type == 'skeleton':
                self.skeleton_color = bgr_color
                self._update_color_button(self.skeleton_color_btn, bgr_color)
            elif color_type == 'contour':
                self.contour_color = bgr_color
                self._update_color_button(self.contour_color_btn, bgr_color)
            elif color_type == 'label':
                self.label_color = bgr_color
                self._update_color_button(self.label_color_btn, bgr_color)
            elif color_type == 'label_bg':
                self.label_bg_color = bgr_color
                self._update_color_button(self.label_bg_color_btn, bgr_color)
            
            self._update_display()
    
    def add_processed_image(self, image_name, folder_path):
        """Add a processed image to the viewer"""
        self.processed_images.append((image_name, folder_path))
        self.image_combo.addItem(image_name)
    
    def clear_images(self):
        """Clear all loaded images"""
        self.processed_images.clear()
        self.image_combo.clear()
        self.original_image = None
        self.skeleton_mask = None
        self.contour_mask = None
        self.overlay_metadata = None
        self.image_label.setText("No image loaded")
        self.data_display.setText("No data loaded")
        self.status_label.setText("Ready")
    
    def _on_image_selected(self, image_name):
        """Handle image selection from dropdown"""
        if not image_name:
            return
        
        # Find folder for selected image
        folder = None
        for name, path in self.processed_images:
            if name == image_name:
                folder = path
                break
        
        if not folder:
            return
        
        self.current_image_name = image_name
        self.current_folder = folder
        
        # Load images and data
        self._load_images()
        self._load_measurement_data()
        self._update_display()
    
    def _load_images(self):
        """Load original image and overlay masks with size + path validation"""

        # ✅ Release old images first (prevents stale UI state)
        self.original_image = None
        self.skeleton_mask = None
        self.contour_mask = None
        self.overlay_metadata = None

        if not self.current_folder or not self.current_image_name:
            return

        self.status_label.setText("Loading images...")

        # ✅ Sanitize base folder path
        self.current_folder = os.path.abspath(self.current_folder)

        # Load original image (multi-extension)
        extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']
        original_path = None

        for ext in extensions:
            potential_path = os.path.abspath(os.path.join(
                self.current_folder,
                f"{self.current_image_name}{ext}"
            ))

            # ✅ Ensure file is inside expected directory (path traversal protection)
            if not potential_path.startswith(self.current_folder + os.sep):
                self.status_label.setText("⚠️ Invalid file path detected")
                return

            if os.path.exists(potential_path):
                original_path = potential_path
                break

        if not original_path:
            self.status_label.setText("⚠️ Original image not found")
            return

        try:
            # ✅ Size validation before loading
            size_mb = os.path.getsize(original_path) / (1024 * 1024)
            if size_mb > 100:  # 100 MB safety limit
                self.status_label.setText(f"⚠️ Image too large: {size_mb:.1f} MB")
                return

            self.original_image = cv2.imread(original_path)

            if self.original_image is None:
                self.status_label.setText("⚠️ Failed to read image (cv2.imread returned None)")
                return

            self.status_label.setText(f"Loaded original: {os.path.basename(original_path)}")

        except Exception as e:
            self.status_label.setText(f"⚠️ Failed to load image: {e}")
            return

        # Load skeleton mask
        skeleton_mask_path = os.path.join(
            self.current_folder,
            f"mask_skeleton_{self.current_image_name}.png"
        )
        if os.path.exists(skeleton_mask_path):
            self.skeleton_mask = cv2.imread(skeleton_mask_path, cv2.IMREAD_GRAYSCALE)
        else:
            skeleton_path = os.path.join(
                self.current_folder,
                f"skeletons_{self.current_image_name}.jpg"
            )
            if os.path.exists(skeleton_path):
                self.skeleton_mask = cv2.imread(skeleton_path, cv2.IMREAD_GRAYSCALE)

        # Load contour mask
        contour_mask_path = os.path.join(
            self.current_folder,
            f"mask_contour_{self.current_image_name}.png"
        )
        if os.path.exists(contour_mask_path):
            self.contour_mask = cv2.imread(contour_mask_path, cv2.IMREAD_GRAYSCALE)

        # Load overlay metadata (JSON)
        metadata_path = os.path.join(
            self.current_folder,
            f"overlay_data_{self.current_image_name}.json"
        )
        if os.path.exists(metadata_path):
            try:
                with open(metadata_path, 'r') as f:
                    self.overlay_metadata = json.load(f)
            except Exception as e:
                print(f"Warning: Could not load overlay metadata: {e}")

        self.status_label.setText("✓ Images loaded")


    
    def _load_measurement_data(self):
        """Load and display measurement CSV data"""
        if not self.current_folder:
            return
        
        csv_path = os.path.join(
            self.current_folder,
            f"sprout_lengths_{self.current_image_name}.csv"
        )
        
        if os.path.exists(csv_path):
            try:
                import pandas as pd
                df = pd.read_csv(csv_path)
                
                # Format data for display
                html = "<table style='width:100%; border-collapse: collapse;'>"
                html += "<tr style='background-color: #3498db; color: white;'>"
                html += "<th style='padding: 8px; border: 1px solid #ddd;'>Sprout #</th>"
                html += "<th style='padding: 8px; border: 1px solid #ddd;'>Pixels</th>"
                html += "<th style='padding: 8px; border: 1px solid #ddd;'>Millimeters</th>"
                html += "</tr>"
                
                for _, row in df.iterrows():
                    html += "<tr style='background-color: white;'>"
                    html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: center;'>{int(row['Sprout Number'])}</td>"
                    html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{row['Pixels']:.2f}</td>"
                    html += f"<td style='padding: 8px; border: 1px solid #ddd; text-align: right;'>{row['Millimeters']:.2f}</td>"
                    html += "</tr>"
                
                html += "</table>"
                
                # Add summary statistics
                html += f"<p style='margin-top: 15px;'><b>Summary:</b></p>"
                html += f"<p>Total Sprouts: {len(df)}</p>"
                html += f"<p>Average Length: {df['Millimeters'].mean():.2f} mm</p>"
                html += f"<p>Min Length: {df['Millimeters'].min():.2f} mm</p>"
                html += f"<p>Max Length: {df['Millimeters'].max():.2f} mm</p>"
                
                self.data_display.setText(html)
                self.data_display.setTextFormat(Qt.TextFormat.RichText)
                
            except Exception as e:
                self.data_display.setText(f"Error loading CSV: {str(e)}")
        else:
            self.data_display.setText("No measurement data found")
    
    def _update_display(self):
        """Render and display the image with current overlay settings"""
        if self.original_image is None:
            return
        
        self.status_label.setText("Rendering...")
        
        # Get current settings
        self.show_skeleton = self.skeleton_check.isChecked()
        self.show_contours = self.contour_check.isChecked()
        self.show_labels = self.labels_check.isChecked()
        
        self.skeleton_thickness = self.skeleton_thick_spin.value()
        self.contour_thickness = self.contour_thick_spin.value()
        self.label_font_scale = self.label_font_spin.value()
        self.label_thickness = self.label_thick_spin.value()
        self.use_label_bg = self.label_bg_check.isChecked()
        self.label_bg_opacity = self.label_bg_opacity_spin.value()
        
        # Start with original image
        display_image = self.original_image.copy()
        
        # Apply skeleton overlay
        if self.show_skeleton and self.skeleton_mask is not None:
            display_image = self._apply_skeleton_overlay(display_image)
        
        # Apply contour overlay
        if self.show_contours and self.contour_mask is not None:
            display_image = self._apply_contour_overlay(display_image)
        
        # Apply label overlay
        if self.show_labels and self.overlay_metadata is not None:
            display_image = self._apply_label_overlay(display_image)
        
        # Convert to QPixmap and display
        self._display_cv_image(display_image)
        self.status_label.setText("✓ Rendered")
    
    def _apply_skeleton_overlay(self, image):
        """Apply skeleton overlay with custom color and thickness"""
        result = image.copy()
        
        # Create colored skeleton
        mask = self.skeleton_mask > 0
        
        if self.skeleton_thickness > 1:
            # Dilate mask for thickness
            kernel = np.ones((self.skeleton_thickness, self.skeleton_thickness), np.uint8)
            mask = cv2.dilate(mask.astype(np.uint8), kernel).astype(bool)
        
        # Apply color
        result[mask] = self.skeleton_color
        
        return result
    
    def _apply_contour_overlay(self, image):
        """Apply contour overlay with custom color and thickness"""
        result = image.copy()
        
        # Create colored contour
        mask = self.contour_mask > 0
        
        if self.contour_thickness > 1:
            # Dilate mask for thickness
            kernel = np.ones((self.contour_thickness, self.contour_thickness), np.uint8)
            mask = cv2.dilate(mask.astype(np.uint8), kernel).astype(bool)
        
        # Apply color
        result[mask] = self.contour_color
        
        return result
    
    def _apply_label_overlay(self, image):
        """Apply label overlay with custom settings"""
        result = image.copy()
        
        if 'labels' not in self.overlay_metadata:
            return result
        
        for label_info in self.overlay_metadata['labels']:
            text = label_info['text']
            x, y = label_info['position']
            
            # Use custom font scale and thickness
            font_scale = self.label_font_scale
            thickness = self.label_thickness
            
            # Calculate text size
            (text_width, text_height), baseline = cv2.getTextSize(
                text,
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                thickness
            )
            
            # Draw background if enabled
            if self.use_label_bg:
                # Create semi-transparent background
                overlay = result.copy()
                padding = 4
                cv2.rectangle(
                    overlay,
                    (x - padding, y - text_height - padding),
                    (x + text_width + padding, y + baseline + padding),
                    self.label_bg_color,
                    -1
                )
                # Blend with opacity
                cv2.addWeighted(overlay, self.label_bg_opacity, result, 1 - self.label_bg_opacity, 0, result)
            
            # Draw text outline (black)
            cv2.putText(
                result,
                text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                (0, 0, 0),  # Black outline
                thickness + 2,
                cv2.LINE_AA
            )
            
            # Draw text
            cv2.putText(
                result,
                text,
                (x, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                font_scale,
                self.label_color,
                thickness,
                cv2.LINE_AA
            )
        
        return result
    
    def _display_cv_image(self, cv_image):
        """Convert OpenCV image to QPixmap and display"""
        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)
        
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        
        qt_image = QImage(
            rgb_image.data, 
            w, h, 
            bytes_per_line, 
            QImage.Format.Format_RGB888
        )
        
        pixmap = QPixmap.fromImage(qt_image)
        
        # Scale to fit while maintaining aspect ratio
        scaled_pixmap = pixmap.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.image_label.setPixmap(scaled_pixmap)
    
    def _refresh_current_image(self):
        """Refresh the current image"""
        if self.current_image_name:
            self._load_images()
            self._load_measurement_data()
            self._update_display()
    
    def _export_current_view(self):
        """Export the current view to a file"""
        if self.original_image is None:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Image",
            f"{self.current_image_name}_custom.jpg",
            "JPEG Images (*.jpg);;PNG Images (*.png);;All Files (*)"
        )
        
        if file_path:
            # Render current view
            display_image = self.original_image.copy()
            
            if self.show_skeleton and self.skeleton_mask is not None:
                display_image = self._apply_skeleton_overlay(display_image)
            
            if self.show_contours and self.contour_mask is not None:
                display_image = self._apply_contour_overlay(display_image)
            
            if self.show_labels and self.overlay_metadata is not None:
                display_image = self._apply_label_overlay(display_image)
            
            cv2.imwrite(file_path, display_image)
            self.status_label.setText(f"✓ Exported to {os.path.basename(file_path)}")
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults"""
        self.skeleton_color = ViewerConfig.DEFAULT_SKELETON_COLOR
        self.contour_color = ViewerConfig.DEFAULT_CONTOUR_COLOR
        self.label_color = ViewerConfig.DEFAULT_LABEL_COLOR
        self.label_bg_color = ViewerConfig.DEFAULT_LABEL_BG_COLOR
        self.use_label_bg = ViewerConfig.DEFAULT_USE_LABEL_BG
        self.label_bg_opacity = ViewerConfig.DEFAULT_LABEL_BG_OPACITY

        self.skeleton_thickness = ViewerConfig.DEFAULT_SKELETON_THICKNESS
        self.contour_thickness = ViewerConfig.DEFAULT_CONTOUR_THICKNESS
        self.label_font_scale = ViewerConfig.DEFAULT_LABEL_FONT_SCALE
        self.label_thickness = ViewerConfig.DEFAULT_LABEL_THICKNESS
        
        # Update UI
        self._update_color_button(self.skeleton_color_btn, self.skeleton_color)
        self._update_color_button(self.contour_color_btn, self.contour_color)
        self._update_color_button(self.label_color_btn, self.label_color)
        self._update_color_button(self.label_bg_color_btn, self.label_bg_color)
        
        self.skeleton_thick_spin.setValue(self.skeleton_thickness)
        self.contour_thick_spin.setValue(self.contour_thickness)
        self.label_font_spin.setValue(self.label_font_scale)
        self.label_thick_spin.setValue(self.label_thickness)
        self.label_bg_check.setChecked(self.use_label_bg)
        self.label_bg_opacity_spin.setValue(self.label_bg_opacity)
        
        self._update_display()
        self.status_label.setText("✓ Reset to defaults")