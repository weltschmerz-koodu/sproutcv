"""
Log viewer widget for displaying processing messages
"""

from PySide6.QtWidgets import QTextEdit
from PySide6.QtGui import QTextCursor, QFont


class LogViewer(QTextEdit):
    """Widget for displaying log messages"""
    
    def __init__(self):
        super().__init__()
        
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 9))
        
        # Styling
        self.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                border-radius: 5px;
                padding: 10px;
            }
        """)
    
    def log(self, message):
        """Add a log message with auto-scroll"""
        # Color code based on message type
        if message.startswith("✅") or message.startswith("✓"):
            color = "#2ecc71"  # Green
        elif message.startswith("❌") or message.startswith("ERROR"):
            color = "#e74c3c"  # Red
        elif message.startswith("⚠") or message.startswith("WARNING"):
            color = "#f39c12"  # Orange
        elif message.startswith("ℹ") or message.startswith("INFO"):
            color = "#3498db"  # Blue
        else:
            color = "#ecf0f1"  # Default white
        
        # Append with color
        self.setTextColor(color)
        self.append(message)
        
        # Auto-scroll to bottom
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.setTextCursor(cursor)
