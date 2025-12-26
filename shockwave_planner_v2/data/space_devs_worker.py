from PyQt6.QtCore import QThread, pyqtSignal
from data.space_devs import SpaceDevsClient


class SyncWorker(QThread):
    """Background worker for Space Devs sync"""
    finished = pyqtSignal(dict)
    progress = pyqtSignal(str)
    
    def __init__(self, sync_type='upcoming', limit=100):
        super().__init__()
        
        self.sync_type = sync_type
        self.limit = limit
    
    def run(self):
        try:
            api = SpaceDevsClient()
            
            if self.sync_type == 'upcoming':
                self.progress.emit("Fetching upcoming launches...")
                result = api.sync_upcoming_launches(limit=self.limit)
            elif self.sync_type == 'previous':
                self.progress.emit("Fetching previous launches...")
                result = api.sync_previous_launches(limit=self.limit)
            elif self.sync_type == 'rockets':
                self.progress.emit("Updating rocket details...")
                result = api.sync_rocket_details()
            else:
                result = {'added': 0, 'updated': 0, 'errors': []}
                       
            self.finished.emit(result)
        except Exception as e:
            self.finished.emit({'added': 0, 'updated': 0, 'errors': [str(e)]})