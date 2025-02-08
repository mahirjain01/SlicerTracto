from FodfComputationManager.SSHManager.SSHManager import SSHManager
from FodfComputationManager.LocalManager.LocalManager import LocalManager

class FodfComputationManager:
    def __init__(self):
        self.local_middleware = LocalManager()
        self.ssh_middleware = SSHManager()


    def route_request(self, subjectName, method, algo, inputFolderPath, outputFolderPath):
        if method == "Local":
            self.local_middleware.execute(subjectName=subjectName, algo=algo, inputFolderPath=inputFolderPath, outputFolderPath=outputFolderPath)
        elif method == "SSH":
            self.ssh_middleware.execute(subjectName=subjectName, algo=algo, inputFolderPath=inputFolderPath, outputFolderPath=outputFolderPath)