"""
QThread worker for running the processing pipeline
"""

from PySide6.QtCore import QThread, Signal

from sproutcv.core.pipeline import run_pipeline, dry_run_pipeline


class PipelineWorker(QThread):
    """
    Worker thread for running the sprout analysis pipeline
    
    Signals:
        log_signal: Emitted with log messages (str)
        progress_signal: Emitted with progress value 0.0-1.0 (float)
        finished_signal: Emitted when processing completes successfully
        error_signal: Emitted with error message if processing fails (str)
    """
    
    log_signal = Signal(str)
    progress_signal = Signal(float)
    finished_signal = Signal()
    error_signal = Signal(str)
    
    def __init__(self, folder, csv_path, output_root=None, 
                 dry_run=False, verbose=False):
        """
        Initialize the worker
        
        Args:
            folder: Path to image folder
            csv_path: Path to calibration CSV
            output_root: Optional output folder path
            dry_run: If True, only validate inputs without processing
            verbose: If True, show detailed validation messages
        """
        super().__init__()
        self._is_cancelled = False

        self.folder = folder
        self.csv_path = csv_path
        self.output_root = output_root
        self.dry_run = dry_run
        self.verbose = verbose
    
    def cancel(self):
        """Request cancellation of processing"""
        self._is_cancelled = True    
    
    def run(self):
        """Execute the pipeline (runs in separate thread)"""
        try:
            if self.dry_run:
                # Check cancellation periodically
                if self._is_cancelled:
                    return
                
                # Validation only
                dry_run_pipeline(
                    parent_folder=self.folder,
                    csv_path=self.csv_path,
                    log_callback=self.log_signal.emit,
                    verbose=self.verbose
                )
            else:
                # Full processing
                run_pipeline(
                    parent_folder=self.folder,
                    csv_path=self.csv_path,
                    output_root=self.output_root,
                    log_callback=self.log_signal.emit,
                    progress_callback=self.progress_signal.emit
                )
            
            self.finished_signal.emit()
            
        except Exception as e:
            self.error_signal.emit(str(e))
