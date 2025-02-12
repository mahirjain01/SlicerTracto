from ComputationManager.ComputationManager import ComputationManager
import slicer
import os
import time
from dipy.io.streamline import load_tractogram
from vtk import vtkPolyDataReader
import vtk
from dipy.io.stateful_tractogram import Space
import qt
import numpy as np

class TractographyUIManager:
    def __init__(self, ui, layout, uiWidget):
        self.inputFolder = None
        self.ui = ui
        self.uiWidget = uiWidget
        self.computationManager = ComputationManager()
        self.computationMethod = "Local"
        self.algo = "dipy"
        self.folderPath = None
        self.subjectName = None

        self.computationMethods = ["Local", "SSH"]
        self.algos = ["dipy", "PFT", "TRLF"]
        self.trkPathList = []
        self.trkPath = None
        self.vtkFolderPath = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Output', 'VTKS')
        self.visualizationCheckboxes = []
        self.display_nodes = []
        self.index= 0
        self.overlayFilePath = None
        

        # UI connections
        # Buttons
        self.ui.generateTrkButton.connect("clicked(bool)", self.generateTrk)
        self.ui.visualizeTrkButton.connect("clicked(bool)", self.visualizeTrk)
        self.ui.overlayButton.connect("clicked(bool)", self.displayOverlayFile)


        # Paths
        self.ui.InputFolderTractography.connect('currentPathChanged(QString)', self.setInputFolderPath)
        self.ui.overlayFileTractography.connect('currentPathChanged(QString)', self.setOverlayPath)

        # Text
        
        # #Combo Box
        self.ui.selectComputationMethod.currentIndexChanged.connect(self.setComputationMethod)
        self.ui.selectAlgorithmTractography.currentIndexChanged.connect(self.setAlgo)
        self.ui.selectTrks.currentIndexChanged.connect(self.setTrk)
        
        self._loadTrks()
    
    def generateTrk(self):
        if self.folderPath:
            print("[SLICER TRACTO]RUNNING...")
            self.computationManager.route_request(method=self.computationMethod, algo=self.algo, subjectName=self.subjectName, folderPath=self.folderPath)
            self._loadTrks()
        else:
            print("[SLICER TRACTO][ERROR]Cannot file FODF or MASK file")
    
    def setInputFolderPath(self, path:str):
        self.folderPath = path
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

    def _loadTrks(self):
        trkFolder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Output', "TRKS")
        trkList = []
        self.trkPathList = []
        for file in os.listdir(trkFolder):
            
            file_name, file_extension = os.path.splitext(file)
            if file_extension == ".trk":
                trkList.append(file)
                self.trkPathList.append(os.path.join(trkFolder, file))
        
        self.ui.selectTrks.clear()
        self.ui.selectTrks.addItems(trkList)
        print(f"[SLICER TRACTO]f{trkList} TRKS added.")

    def visualizeTrk(self):
        print(f"[SLICER TRACTO]Visualizing... {self.trkPath}")
        time.sleep(5)
        print(f"[SLICER TRACTO]Visualizing... {self.trkPath}")
        if self.trkPath == None:
            print("[SLICER TRACTO]Generate Trk First...")
            return
        tractogram = load_tractogram(self.trkPath, reference='same', bbox_valid_check=False, to_space=Space.RASMM)
        print(" Tractography Visualization...")
        vtk_file_name, ext = os.path.splitext(os.path.basename(self.trkPath)) 
        output_vtk_path = os.path.join(self.vtkFolderPath, vtk_file_name+"_vtk.vtk")
        
        
        self._saveStreamlinesVTK(tractogram.streamlines, output_vtk_path )
        reader = vtkPolyDataReader()
        reader.SetFileName(output_vtk_path)
        reader.Update()

        polydata = reader.GetOutput()

        streamline_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
        streamline_node.SetAndObservePolyData(polydata)

        display_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
        streamline_node.SetAndObserveDisplayNodeID(display_node.GetID())

        display_node.SetColor(0, 1, 0)  
        display_node.SetOpacity(1.0)  
        self.display_nodes.append(display_node)
        slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveVolumeID(streamline_node.GetID())
        slicer.app.applicationLogic().PropagateVolumeSelection()
        slicer.app.layoutManager().resetThreeDViews()   
        print("[SLICER TRACTO]Done Visualization")

        self._addCheckBox(self.index, vtk_file_name)
    
    def _addCheckBox(self, index:int, name:str):
        if name not in self.visualizationCheckboxes:
            new_checkbox = qt.QCheckBox(name)
            new_checkbox.setChecked(True)
            self.visualizationCheckboxes.append(name)
            self.uiWidget.verticalLayout.verticalLayout_2.addWidget(new_checkbox)
            new_checkbox.stateChanged.connect(lambda state: self.onCheckboxStateChanged(index=index, state=state))

    
    def onCheckboxStateChanged(self, index, state):
        if state == qt.Qt.Checked:
            # Show the model
            self.display_nodes[index].SetOpacity(1.0)
            print("[SLICER TRACTO] Model Visible")
        else:
            # Hide the model
            self.display_nodes[index].SetOpacity(0.0)
            print("[SLICER TRACTO] Model Hidden")

    def _saveStreamlinesVTK(self, streamlines, pStreamlines):
        
        polydata = vtk.vtkPolyData()

        lines = vtk.vtkCellArray()
        points = vtk.vtkPoints()

        ptCtr = 0

        for i, streamline in enumerate(streamlines):
            if (i % 10000) == 0:
                print(f"[SLICER TRACTO]{i}/{len(streamlines)}")
            
            line = vtk.vtkLine()
            line.GetPointIds().SetNumberOfIds(len(streamline))

            for j, point in enumerate(streamline):
                points.InsertNextPoint(point)
                line.GetPointIds().SetId(j, ptCtr)
                ptCtr += 1

            lines.InsertNextCell(line)

        polydata.SetLines(lines)
        polydata.SetPoints(points)

        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(pStreamlines)
        writer.SetInputData(polydata)
        writer.Write()

        print(f"[SLICER TRACTO]Wrote streamlines to {writer.GetFileName()}")
    

    def setOverlayPath(self, path:str):
        if not os.path.isfile(path):
            print("[SLICER TRACTO] Input path is not a file.")
            return
    
        valid_extensions = {".nii", ".nii.gz"}
        if any(path.endswith(ext) for ext in valid_extensions):
            self.overlayFilePath = path
            print(f"[SLICER TRACTO] overlay file path set to {path}")
        
        print("[SLICER TRACTO] Input file is not nifti.")

    def displayOverlayFile(self):
        if self.overlayFilePath == None:
            print("[SLICER TRACTO] Select File")
        # Load the NIfTI file as a volume
        volume_node = slicer.util.loadVolume(self.overlayFilePath)

        identity_matrix = np.eye(3)  # 3x3 Identity matrix for RAS

        # Convert the identity matrix to a vtk matrix
        vtk_matrix = slicer.vtkMatrix4x4()
        for i in range(3):
            for j in range(3):
                vtk_matrix.SetElement(i, j, identity_matrix[i][j])

        # Set the direction matrix to the identity matrix (for example, to fix RAS orientation)
        volume_node.SetIJKToRASDirections(vtk_matrix)

        # if volume_node is None:
        #     slicer.util.errorDisplay("Failed to load NIfTI file.")
        #     return

        # # Optionally, you can set the view to 3D
        # slicer.app.processEvents()  # Ensure the UI updates
        # slicer.app.viewers()[0].resetFocalPoint()

        # # You can also adjust display settings (like color map, etc.) here
        # # Example: changing the color map
        # volume_node.GetDisplayNode().SetAndObserveColorNodeID("vtkMRMLColorTableNodeGrey")

        # Add the volume to the scene if it's not already added
        slicer.mrmlScene.AddNode(volume_node)
        
        # Save the current view
        current_camera_position = slicer.app.layoutManager().threeDWidget(0).threeDView().cameraPosition()

        # Center the volume (reset camera)
        slicer.app.layoutManager().threeDWidget(0).threeDView().resetFocalPoint()

        # Optionally, restore the previous camera position to prevent models from aligning
        slicer.app.layoutManager().threeDWidget(0).threeDView().setCameraPosition(*current_camera_position)

        print(f"Successfully loaded NIfTI file: {self.overlayFilePath}")


