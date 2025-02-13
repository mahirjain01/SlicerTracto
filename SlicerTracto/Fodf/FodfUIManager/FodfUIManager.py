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
        self.algos = ["Scilpy"]
        
        # UI connections
        # Buttons
        self.ui.generateFodfButton.connect("clicked(bool)", self.generateFodf)
        self.ui.visualizeFodfButton.connect("clicked(bool)", self.visualizeFodf)

        # Paths
        self.ui.inputFolderPath.connect('currentPathChanged(QString)', self.setInputFolderPath)
        self.ui.fodfPath.connect('currentPathChanged(QString)', self.setOutputFolderPath)
        
        # #Combo Box
        self.ui.selectComputationMethod.currentIndexChanged.connect(self.setComputationMethod)
        self.ui.selectFodfGenerationAlgo.currentIndexChanged.connect(self.setAlgo)
        
    
    def generateFodf(self):
        if self.folderPath:
            print("[SLICER TRACTO]RUNNING...")
            self.computationManager.route_request(method=self.computationMethod, algo=self.algo, subjectName=self.subjectName, inputFolderPath=self.folderPath, outputFolderPath=self.outputFolderPath)
        else:
            print("[SLICER TRACTO][ERROR]Cannot file FODF or MASK file")
    
    def setInputFolderPath(self, path:str):
        self.inputFolderPath = path
        print(f"[SLICER TRACTO] Output Folder Path Set to f{self.outputFolderPath}")
    
    def setOutputFolderPath(self, path:str):
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
        if self.outputFolderPath == None:
            print("[SLICER TRACTO] Select Output Folder")
        for file in os.listdir(self.outputFolderPath):
            if file.endswith(".nii"):
                self.fodfFile = os.path.join(self.outputFolderPath, file)
                break
        
        if self.fodfFile == None:
            print("[SLICER TRACTO] No Fodf found")
        
        # Load the NIfTI file as a volume
        volume_node = slicer.util.loadVolume(self.fodfFile)

        identity_matrix = np.eye(3)  # 3x3 Identity matrix for RAS

        # Convert the identity matrix to a vtk matrix
        vtk_matrix = slicer.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                vtk_matrix.SetElement(i, j, identity_matrix[i][j])

        # Set the direction matrix to the identity matrix (for example, to fix RAS orientation)
        volume_node.SetIJKToRASDirections(vtk_matrix)
        slicer.mrmlScene.AddNode(volume_node)
        
        # Save the current view
        current_camera_position = slicer.app.layoutManager().threeDWidget(0).threeDView().cameraPosition()

        # Center the volume (reset camera)
        slicer.app.layoutManager().threeDWidget(0).threeDView().resetFocalPoint()

        # Optionally, restore the previous camera position to prevent models from aligning
        slicer.app.layoutManager().threeDWidget(0).threeDView().setCameraPosition(*current_camera_position)

        print(f"Successfully loaded NIfTI file: {self.overlayFilePath}")
      
