from ComputationManager.ComputationManager import ComputationManager
import slicer
import os

class TractographyUIManager:
    def __init__(self, ui):
        self.inputFolder = None
        self.ui = ui
        self.computationManager = ComputationManager()
        self.computationMethod = "Local"
        self.algo = "algo1"
        self.fodf_path = None
        self.mask_path = None
        self.subjectName = None

        self.computationMethods = ["Local", "SSH"]
        self.algos = ["algo1", "algo2"]
        

        # UI connections
        # Buttons
        self.ui.generateTrkButton.connect("clicked(bool)", self.generateTrk)
        # self.ui.visualizeTrkButton.connect("clicked(bool)", self._tractographyParams.visualizeTrk)
        # self.ui.visualizeTrkButton.connect("clicked(bool)", self._tractographyParams.visualizeTrk)

        # Paths
        self.ui.InputFolderTractography.connect('currentPathChanged(QString)', self.setInputFolderPath)

        # Text
        
        # #Combo Box
        self.ui.selectComputationMethod.currentIndexChanged.connect(self.setComputationMethod)
        self.ui.selectAlgorithmTractography.currentIndexChanged.connect(self.setAlgo)
        # self.ui.selectTrks.currentIndexChanged.connect(self._tractographyParams.set_algo)

        
        #Output Box
        # self._tractographyParams.outputText = self.ui.outputTextTractography
    
    def generateTrk(self):
        if self.fodf_path and self.mask_path:
            print("[SLICER TRACTO]RUNNING...")
            self.computationManager.route_request(method=self.computationMethod, algo=self.algo, subjectName=self.subjectName, approxMaskPathFilePath=self.mask_path, fodfFilePath=self.fodf_path)
        else:
            print("[SLICER TRACTO][ERROR]Cannot file FODF or MASK file")
    
    def setInputFolderPath(self, path:str):
        fodf_path = None
        mask_path = None

        # Iterate through all files in the folder
        for file_name in os.listdir(path):
            file_path = os.path.join(path, file_name)

            # Check if the current file is a .nii file
            if file_name.endswith("fodf.nii"):
                fodf_path = file_path
            elif file_name.endswith("approximated_mask.nii"):
                mask_path = file_path

            # Stop searching if both files are found
            if fodf_path and mask_path:
                break
        if fodf_path and mask_path:
            print("[SLICER TRACTO] FODF and MASK file found")
        self.fodf_path = fodf_path
        self.mask_path = mask_path
        self.subjectName = os.path.basename(path)
    
    def setComputationMethod(self, index:int):
        self.computationMethod = self.computationMethods[index]
        print(f"[SLICER TRACTO]Computation set to: {self.computationMethod}")
    
    def setAlgo(self, index:int):
        self.algo = self.algos[index]
        print(f"[SLICER TRACTO]Algorithm set to: {self.algo}")