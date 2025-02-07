
from dipy.segment.clustering import QuickBundles
from dipy.io.streamline import save_trk
from dipy.tracking.streamline import transform_streamlines
from dipy.io.streamline import load_tractogram
from dipy.io.streamline import save_tractogram
from dipy.io.stateful_tractogram import StatefulTractogram, Space
import vtk
import os
import slicer
import random

DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX = 'segmentedTrk'
file_path = os.path.abspath(__file__)
DEFAULT_DIR = os.path.dirname(file_path)

class QuickBundlesAlgo:
    def __init__(self, trkPath, segmentedTrkFolderPath):
        self.trkPath: str = trkPath
        self.segmentedTrkFolderPath : str = segmentedTrkFolderPath
        self.clusters = None
        self.threshold : float = 10.0


    def run(self):
        print("Segmenting Trk...")
        tractogram = load_tractogram(self.trkPath, reference="same")
        streamlines = tractogram.streamlines
        # Define the threshold for clustering (in mm)
          # Adjust based on desired clustering sensitivity

        # Initialize QuickBundles
        qb = QuickBundles(threshold=self.threshold)

        # Perform clustering
        self.clusters = qb.cluster(streamlines)


        for i, cluster in enumerate(self.clusters):
            cluster_streamlines = [streamlines[idx] for idx in cluster.indices]

            trkFilePath = os.path.join(self.segmentedTrkFolderPath, f"{DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX}-{i}.trk")
            vtkFilePath = os.path.join(self.segmentedTrkFolderPath, f"{DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX}-{i}.vtk")

            new_tractogram = StatefulTractogram(cluster_streamlines, tractogram, Space.RASMM)
            save_tractogram(new_tractogram, trkFilePath)

            self._saveStreamlinesVTK(cluster_streamlines, vtkFilePath)

    def _convertToVTK(self, cluster):
        """Convert a cluster of streamlines to VTK polydata with per-cluster coloring."""
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        scalars = vtk.vtkFloatArray()
        scalars.SetName("ClusterIndex")

        for streamline in cluster:
            line = vtk.vtkPolyLine()
            line.GetPointIds().SetNumberOfIds(len(streamline))

            for i, point in enumerate(streamline):
                pointId = points.InsertNextPoint(point)
                line.GetPointIds().SetId(i, pointId)
                scalars.InsertNextValue(i)  # Assign scalar value (index)

            lines.InsertNextCell(line)

        polydata = vtk.vtkPolyData()
        polydata.SetPoints(points)
        polydata.SetLines(lines)
        polydata.GetPointData().SetScalars(scalars)  # Add scalars for coloring

        return polydata


    def _generateColors(self, numClusters):
        """Generate distinct colors for each cluster."""
        colors = []
        colormap = vtk.vtkNamedColors()
        predefinedColors = list(colormap.GetColorNames())
        for i in range(numClusters):
            colorName = predefinedColors[i % len(predefinedColors)]
            colors.append(colormap.GetColor3d(colorName))
        return colors
    
    def _saveStreamlinesVTK(self, streamlines, pStreamlines):
        polydata = vtk.vtkPolyData()
        lines = vtk.vtkCellArray()
        points = vtk.vtkPoints()

        ptCtr = 0

        for i, streamline in enumerate(streamlines):
            if (i % 10000) == 0:
                print(f"{i}/{len(streamlines)}")

            line = vtk.vtkPolyLine()  # Corrected from vtkLine
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

                


            
