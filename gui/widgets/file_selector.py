"""
File/Folder selection widget with drag-and-drop support
"""

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QFileDialog
)
from PySide6.QtCore import Qt, Signal


class FileSelector(QWidget):
    """Widget for selecting files or folders"""
    
    path_changed = Signal(str)
    
    def __init__(self, label_text, is_folder=False, file_filter="", 
                 callback=None, optional=False):
        super().__init__()
        
        self.is_folder = is_folder
        self.file_filter = file_filter
        self.callback = callback
        self.optional = optional
        self.selected_path = None
        
        self._setup_ui(label_text)
        self.setAcceptDrops(True)
    
    def _setup_ui(self, label_text):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Label
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        # Horizontal layout for path display and browse button
        h_layout = QHBoxLayout()
        
        # Path display
        self.path_label = QLabel("No file selected" if not self.optional 
                                 else "Not set (using default)")
        self.path_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #bdc3c7;
                padding: 10px;
                border-radius: 5px;
                background-color: #ecf0f1;
            }
        """)
        self.path_label.setMinimumHeight(40)
        h_layout.addWidget(self.path_label, stretch=1)
        
        # Browse button
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setMinimumHeight(40)
        browse_btn.clicked.connect(self._browse)
        h_layout.addWidget(browse_btn)
        
        layout.addLayout(h_layout)
    
    def _browse(self):
        """Open file/folder browser dialog"""
        if self.is_folder:
            path = QFileDialog.getExistingDirectory(
                self,
                "Select Folder"
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Select File",
                "",
                self.file_filter
            )
        
        if path:
            self._set_path(path)
    
    def _set_path(self, path):
        """Set the selected path"""
        self.selected_path = path
        self.path_label.setText(path)
        self.path_label.setStyleSheet("""
            QLabel {
                border: 2px solid #27ae60;
                padding: 10px;
                border-radius: 5px;
                background-color: #d5f4e6;
            }
        """)
        
        self.path_changed.emit(path)
        
        if self.callback:
            self.callback(path)
    
    def get_path(self):
        """Get the selected path"""
        return self.selected_path
    
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dropEvent(self, event):
        """Handle drop event"""
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            
            # Validate that it's the right type
            import os
            if self.is_folder and os.path.isdir(path):
                self._set_path(path)
            elif not self.is_folder and os.path.isfile(path):
                self._set_path(path)
