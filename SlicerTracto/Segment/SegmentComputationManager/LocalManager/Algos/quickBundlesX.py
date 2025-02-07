from dipy.io.streamline import load_tractogram, save_tractogram
from dipy.segment.clustering import QuickBundlesX
from dipy.tracking.streamline import transform_streamlines
import vtk
import os
import slicer
import random
from dipy.io.stateful_tractogram import StatefulTractogram, Space
import numpy as np # Import numpy

DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX = 'segmentedTrk'
file_path = os.path.abspath(__file__)
DEFAULT_DIR = os.path.dirname(file_path)

class QuickBundlesXAlgo:
    def __init__(self, trkPath, segmentedTrkFolderPath):
        self.trkPath: str = trkPath
        self.segmentedTrkFolderPath: str = segmentedTrkFolderPath
        self.clusters = None
        self.thresholds = [40.0, 30.0, 20.0, 10.0]  # Distance threshold for clustering

    def run(self):
        print("Segmenting Trk using QuickBundlesX...")
        
        # Load tractogram
        tractogram = load_tractogram(self.trkPath, reference="same")
        streamlines = tractogram.streamlines

        # Initialize QuickBundlesX with threshold
        qb = QuickBundlesX(thresholds=self.thresholds)  # Pass the threshold to the constructor

        # Perform clustering (no threshold needed here, it's in the constructor)
        self.clusters = qb.cluster(streamlines)

        for i, cluster in enumerate(self.clusters):
            # Extract streamlines for the cluster
            #cluster_streamlines = cluster.centroids  # QuickBundlesX stores clusters as centroids
            cluster_streamlines = streamlines[cluster.indices]
            
            # Define file paths
            trkFileName = f"{DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX}-{i}.trk"
            vtkFileName = f"{DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX}-{i}.vtk"
            trkFilePath = os.path.join(self.segmentedTrkFolderPath, trkFileName)
            vtkFilePath = os.path.join(self.segmentedTrkFolderPath, vtkFileName)

            # Create a new tractogram with only the cluster's streamlines
            new_tractogram = StatefulTractogram(cluster_streamlines, tractogram.space_attributes, Space.RASMM)

            # Save the tractogram
            save_tractogram(new_tractogram, trkFilePath, bbox_valid_check=False)

            # Convert and save as VTK
            self._saveStreamlinesVTK(cluster_streamlines, vtkFilePath)

    def _saveStreamlinesVTK(self, streamlines, filePath):
        """Save streamlines as VTK PolyData."""
        polydata = vtk.vtkPolyData()
        lines = vtk.vtkCellArray()
        points = vtk.vtkPoints()

        ptCtr = 0
        for streamline in streamlines:
            line = vtk.vtkPolyLine()
            line.GetPointIds().SetNumberOfIds(len(streamline))

            for j, point in enumerate(streamline):
                points.InsertNextPoint(point)
                line.GetPointIds().SetId(j, ptCtr)
                ptCtr += 1

            lines.InsertNextCell(line)

        polydata.SetPoints(points)
        polydata.SetLines(lines)

        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(filePath)
        writer.SetInputData(polydata)
        writer.Write()

        print(f"Wrote streamlines to {filePath}")
