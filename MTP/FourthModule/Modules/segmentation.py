
from dipy.io.streamline import load_tractogram
from dipy.segment.clustering import QuickBundles
from dipy.io.streamline import save_trk
from dipy.tracking.streamline import transform_streamlines
from dipy.io.streamline import load_tractogram
from dipy.io.streamline import save_tractogram
import vtk
import os
import slicer
import random

DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX = 'segmentedTrk'
THRESHOLD : float = 10.0
file_path = os.path.abspath(__file__)
DEFAULT_DIR = os.path.dirname(file_path)

class Segmentation:
    def _init_(self):
        self.trkPath: str = None
        self.segmentedTrkFolderPath : str = DEFAULT_DIR
        self.outputText = None
    
    @staticmethod
    def _isValidPath(path: str) -> bool:
        """Validate if the provided path exists and is a file."""
        return os.path.isfile(path) or os.path.isdir(path)

    def set_trkPath(self, path: str):
        """Set the path for the FODF file after validation."""
        if self._isValidPath(path):
            self.trkPath = path
            print(f"Trk path set to: {self.trkPath}")
        else:
            raise FileNotFoundError(f"Invalid trk path: {path}")

    def set_segmentedTrkFolderPath(self, path: str):
            """Set the path for the FODF file after validation."""
            if self._isValidPath(path):
                self.segmentedTrkFolderPath = path
                print(f"Trks Folder path set to: {self.segmentedTrkFolderPath}")
            else:
                raise FileNotFoundError(f"Trks Folder path: {path}")
    
    def segmentTrk(self):
        print("Segmenting Trk...")
        tractogram = load_tractogram(self.trkPath, reference="same")
        streamlines = tractogram.streamlines
        # Define the threshold for clustering (in mm)
          # Adjust based on desired clustering sensitivity

        # Initialize QuickBundles
        qb = QuickBundles(threshold=THRESHOLD)

        # Perform clustering
        clusters = qb.cluster(streamlines)

        self.outputText.append(f"Segmentation Completed... \n No. of Clusters = {len(clusters)} \n")

        for i, cluster in enumerate(clusters):
            self.outputText.append(f"Cluster {i}: {len(cluster)} streamlines \n")
            # Extract streamlines for the cluster
            cluster_streamlines = [streamlines[idx] for idx in cluster.indices]
            
            # Save the cluster to a new .trk file
            trkFileName = DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX + f"-{i}.trk"
            vtkFileName = DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX + f"-{i}.vtk"

            trkFilePath = os.path.join(self.segmentedTrkFolderPath, trkFileName)
            vtkFilePath = os.path.join(self.segmentedTrkFolderPath, vtkFileName)

            save_tractogram(tractogram, trkFilePath)
            tractogram = load_tractogram(trkFilePath, reference="same")
            self._saveStreamlinesVTK(tractogram.streamlines, vtkFilePath )
            self.outputText.append(f'Cluster {i} saved in file {trkFileName} \n\n')

    def visualizeSegmentation(self):
        """
        Load and visualize multiple .vtk files from a directory in 3D Slicer,
        assigning a random color to each file.

        Args:
            vtk_files_directory (str): Path to the directory containing .vtk files.
        """
        # Check if the directory exists
        vtk_files_directory = self.segmentedTrkFolderPath
        if not os.path.exists(vtk_files_directory):
            print(f"Directory not found: {vtk_files_directory}")
            return
        
        # List all .vtk files in the directory
        vtk_files = [f for f in os.listdir(vtk_files_directory) if f.endswith('.vtk')]
        if not vtk_files:
            print("No .vtk files found in the directory.")
            return
        
        print(f"Found {len(vtk_files)} .vtk files. Loading with random colors...")

        for vtk_file in vtk_files:
            # Create the full file path
            file_path = os.path.join(vtk_files_directory, vtk_file)
            
            # Load the .vtk file as a model
            loaded_node = slicer.util.loadModel(file_path)
            
            if loaded_node:
                print(f"Loaded: {vtk_file}")
                
                # Generate a random color (RGB values between 0 and 1)
                random_color = [random.random(), random.random(), random.random()]
                
                # Set the color of the model
                display_node = loaded_node.GetDisplayNode()
                if display_node:
                    display_node.SetColor(random_color)
                    print(f"Assigned color {random_color} to {vtk_file}")
            else:
                print(f"Failed to load: {vtk_file}")
    
    def _saveStreamlinesVTK(self, streamlines, pStreamlines):
        
        polydata = vtk.vtkPolyData()

        lines = vtk.vtkCellArray()
        points = vtk.vtkPoints()

        ptCtr = 0

        for i, streamline in enumerate(streamlines):
            if (i % 10000) == 0:
                print(f"{i}/{len(streamlines)}")
            
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

        print(f"Wrote streamlines to {writer.GetFileName()}")
            


        
