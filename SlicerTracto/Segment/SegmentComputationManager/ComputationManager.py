from SegmentComputationManager.SSHManager.SSHManager import SSHManager
from SegmentComputationManager.LocalManager.LocalManager import LocalManager

class ComputationManager:
    def __init__(self):
        self.local_middleware = LocalManager()
        self.ssh_middleware = SSHManager()


    def route_request(self, method, algo, trkPath, segmentedTrkFolderPath):
        if method == "Local":
            self.local_middleware.execute(algo=algo, trkPath=trkPath, segmentedTrkFolderPath=segmentedTrkFolderPath)
        elif method == "SSH":
            self.ssh_middleware.execute(algo=algo, trkPath=trkPath, segmentedTrkFolderPath=segmentedTrkFolderPath)