from SSHManager.SSHManager import SSHManager
from LocalManager.LocalManager import LocalManager

class ComputationManager:
    def __init__(self):
        self.local_middleware = LocalManager()
        self.ssh_middleware = SSHManager()


    def route_request(self, subjectName, method, algo, approxMaskPathFilePath, fodfFilePath):
        if method == "Local":
            self.local_middleware.execute(subjectName=subjectName, algo=algo, approxMaskPathFilePath=approxMaskPathFilePath, fodfFilePath=fodfFilePath)
        elif method == "SSH":
            self.ssh_middleware.execute(subjectName=subjectName, algo=algo, approxMaskPathFilePath=approxMaskPathFilePath, fodfFilePath=fodfFilePath)