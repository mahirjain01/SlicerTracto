import os
from SegmentComputationManager.ComputationManager import ComputationManager
import qt
from vtk import vtkPolyDataReader
import vtk
import slicer
import random

class SegmentUIManager:
    def __init__(self, ui, uiWidget):
        self.ui = ui
        self.uiWidget = uiWidget
        self.computationMethods = ["Local", "SSH"]
        self.algos = ["QuickBundles", "QuickBundlesX"]
        self.computationMethod = "Local"
        self.algo = "QuickBundles"
        self.trkPath = None
        self.segmentedTrkFolderPath = None
        self.computationManager = ComputationManager()
        self.visualizationCheckboxes = []
        self.display_nodes = []

        self.ui.segmentationButton_Segmentation.connect("clicked(bool)", self.segmentTrk)
        self.ui.visualizeTrks_Segmentation.connect("clicked(bool)", self.visualizeTrk)

        self.ui.trkPath_Segmentation.connect('currentPathChanged(QString)', self.setTrkPath)
        self.ui.segmentedTrkFolderPath_Segmentation.connect('currentPathChanged(QString)', self.setSegmentedTrkFolderPath)

        # #Combo Box
        self.ui.selectComputationMethod.currentIndexChanged.connect(self.setComputationMethod)
        self.ui.selectAlgorithmTractography.currentIndexChanged.connect(self.setAlgo)
        self.index= 0

    def setComputationMethod(self, index:int):
        self.computationMethod = self.computationMethods[index]
        print(f"[SLICER TRACTO]Computation set to: {self.computationMethod}")
    
    def setAlgo(self, index:int):
        self.algo = self.algos[index]
        print(f"[SLICER TRACTO]Algorithm set to: {self.algo}")


    def generate_random_rgb(self):
        """Generate a random RGB color with values between 0 and 1."""
        r = random.uniform(0, 1)
        g = random.uniform(0, 1)
        b = random.uniform(0, 1)
        return (r, g, b)

    def visualizeTrk(self):
        for file_name in os.listdir(self.segmentedTrkFolderPath):

            if not file_name.lower().endswith('.vtk'):
                continue

            reader = vtkPolyDataReader()
            reader.SetFileName(os.path.join(self.segmentedTrkFolderPath,file_name))
            reader.Update()

            polydata = reader.GetOutput()

            streamline_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            streamline_node.SetAndObservePolyData(polydata)

            display_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
            streamline_node.SetAndObserveDisplayNodeID(display_node.GetID())

            display_node.SetColor(self.generate_random_rgb())  
            display_node.SetOpacity(1.0)  
            self.display_nodes.append(display_node)
            slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveVolumeID(streamline_node.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection()
            slicer.app.layoutManager().resetThreeDViews()   
            print("[SLICER TRACTO]Done Visualization")

            self._addCheckBox(self.index, file_name)
            self.index+=1

    @staticmethod
    def _isValidPath(path: str) -> bool:
        return os.path.isfile(path) or os.path.isdir(path)

    def setTrkPath(self, path: str):
        if self._isValidPath(path):
            self.trkPath = path
            print(f"Trk path set to: {self.trkPath}")
        else:
            raise FileNotFoundError(f"Invalid trk path: {path}")
    
    def setSegmentedTrkFolderPath(self, path: str):
        if self._isValidPath(path):
            self.segmentedTrkFolderPath = path
            print(f"Trks Folder path set to: {self.segmentedTrkFolderPath}")
        else:
            raise FileNotFoundError(f"Trks Folder path: {path}")
        
    def segmentTrk(self):
        if self.trkPath and self.segmentedTrkFolderPath:
            print("[SLICER TRACTO]RUNNING...")
            self.computationManager.route_request(method=self.computationMethod, algo=self.algo, trkPath=self.trkPath, segmentedTrkFolderPath=self.segmentedTrkFolderPath)
        else:
            print("[SLICER TRACTO][ERROR]Cannot file Trk path or Folder Path")
    
    def _addCheckBox(self, index:int, name:str):
        if name not in self.visualizationCheckboxes:
            new_checkbox = qt.QCheckBox(name)
            new_checkbox.setChecked(True)
            self.visualizationCheckboxes.append(name)
            self.uiWidget.verticalLayout.addWidget(new_checkbox)
            new_checkbox.stateChanged.connect(lambda state: self.onCheckboxStateChanged(index=index, state=state))

    
    def onCheckboxStateChanged(self, index, state):
        print("[SLICER TRACTO] State changed")
        if state == qt.Qt.Checked:
            # Show the model
            self.display_nodes[index].SetOpacity(1.0)
            print("[SLICER TRACTO] Model Visible")
        else:
            # Hide the model
            self.display_nodes[index].SetOpacity(0.0)
            print("[SLICER TRACTO] Model Hidden")