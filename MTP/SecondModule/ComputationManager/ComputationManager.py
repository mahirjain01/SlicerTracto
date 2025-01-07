from SSHManager.SSHManager import SSHManager
from LocalManager.LocalManager import LocalManager

class ComputationManager:
    def __init__(self):
        self.local_middleware = LocalManager()
        self.ssh_middleware = SSHManager()


    def route_request(self, subjectName, method, algo, folderPath):
        if method == "Local":
            self.local_middleware.execute(subjectName=subjectName, algo=algo, folderPath = folderPath)
        elif method == "SSH":
            self.ssh_middleware.execute(subjectName=subjectName, algo=algo, folderPath = folderPath)