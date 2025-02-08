from FodfComputationManager.FodfComputationManager import FodfComputationManager
import slicer
import os
import time
from dipy.io.streamline import load_tractogram
from vtk import vtkPolyDataReader
import vtk
from dipy.io.stateful_tractogram import Space
import qt
import numpy as np

class FodfUIManager:
    def __init__(self, ui, uiWidget):
        self.inputFolder = None
        self.ui = ui
        self.uiWidget = uiWidget
        self.computationManager = FodfComputationManager()
        self.computationMethod = "Local"
        self.algo = "Scilpy Fodf Generation"
        self.subjectName = None
        self.outputFolderPath = None
        self.inputFolderPath = None

        self.computationMethods = ["Local", "SSH"]
        self.algos = ["scilpy Fodf Generation"]
        self.vtkFolderPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Output', 'VTKS')
        
        

        # UI connections
        # Buttons
        self.ui.generateFodfButton.connect("clicked(bool)", self.generateTrk)
        self.ui.visualizeFodfButton.connect("clicked(bool)", self.visualizeFodf)

        # Paths
        self.ui.inputFolderPath.connect('currentPathChanged(QString)', self.setInputFolderPath)
        self.ui.fodfPath.connect('currentPathChanged(QString)', self.setOutputFolderPath)
        
        # #Combo Box
        self.ui.selectComputationMethod.currentIndexChanged.connect(self.setComputationMethod)
        self.ui.selectAlgorithmFodf.currentIndexChanged.connect(self.setAlgo)
        
    
    def generateFodf(self):
        if self.folderPath:
            print("[SLICER TRACTO]RUNNING...")
            self.computationManager.route_request(method=self.computationMethod, algo=self.algo, subjectName=self.subjectName, folderPath=self.folderPath)
        else:
            print("[SLICER TRACTO][ERROR]Cannot file FODF or MASK file")
    
    def setInputFolderPath(self, path:str):
        self.outputFolderPath = path
        print(f"[SLICER TRACTO] Output Folder Path Set to f{self.outputFolderPath}")
    
    def setInputFolderPath(self, path:str):
        self.inputFolderPath = path
        self.subjectName = os.path.basename(path)
        print(f"[SLICER TRACTO]Folder Path Set And Subject Name Set to f{self.subjectName}")
        
    
    def setComputationMethod(self, index:int):
        self.computationMethod = self.computationMethods[index]
        print(f"[SLICER TRACTO]Computation set to: {self.computationMethod}")
    
    def setAlgo(self, index:int):
        self.algo = self.algos[index]
        print(f"[SLICER TRACTO]Algorithm set to: {self.algo}")
    
    def setTrk(self, index:int):
        self.trkPath = self.trkPathList[index]
        print(f"[SLICER TRACTO]TRK set to: {self.trkPath}")

    def visualizeFodf(self):
        pass
      
