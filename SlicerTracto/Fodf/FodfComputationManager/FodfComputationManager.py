import os
import sys
# Get the path to the scilpy folder and add to sys paths
sibling_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scilpy'))
if sibling_folder_path not in sys.path:
    sys.path.append(sibling_folder_path)

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