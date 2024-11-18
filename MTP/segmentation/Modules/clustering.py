import os
import slicer
from dipy.io.streamline import load_tractogram
from dipy.tracking.streamline import Streamlines
from dipy.segment.clustering import QuickBundles
import vtk


class Segment:
    def __init__(self):
        self.trkPath: str = None
        self.clusters = None  # Store clustering results

    @staticmethod
    def isValidPath(path: str) -> bool:
        """Validate if the provided path exists and is a file."""
        return os.path.isfile(path)

    # Setter functions with validation
    def settrkPath(self, path: str):
        """Set the path for trk after validation."""
        if self.isValidPath(path):
            self.trkPath = path
            print(f"trk path set to: {self.trkPath}")
        else:
            raise ValueError(f"Invalid trk path: {path}")

    def segment(self):
        """Cluster streamlines using QuickBundles."""
        try:
            # Load streamlines from the .trk file
            print("Loading streamlines...")
            tractogram = load_tractogram(self.trkPath, reference="same", bbox_valid_check=False)
            streamlines = Streamlines(tractogram.streamlines)
            print(f"Loaded {len(streamlines)} streamlines from {self.trkPath}")

            # Initialize QuickBundles with desired threshold
            threshold = 10.0  # Example threshold, adjust as needed
            qb = QuickBundles(threshold=threshold)

            # Cluster streamlines
            print("Clustering streamlines...")
            self.clusters = qb.cluster(streamlines)

            # Display cluster results
            print(f"Number of clusters: {len(self.clusters)}")
            cluster_sizes = [len(cluster) for cluster in self.clusters]
            print(f"Cluster sizes: {cluster_sizes}")

            # Save cluster information
            self.saveFodf()

        except Exception as e:
            print(f"An error occurred during segmentation: {e}")

    def saveFodf(self):
        """Save clustering results to a file."""
        if not self.clusters:
            print("No clusters to save. Please run `segment` first.")
            return

        try:
            # Save cluster indices and sizes to a text file
            output_dir = os.path.dirname(self.trkPath)
            output_path = os.path.join(output_dir, "clusters.txt")
            with open(output_path, "w") as f:
                for i, cluster in enumerate(self.clusters):
                    f.write(f"Cluster {i}: {len(cluster)} streamlines\n")

            print(f"Cluster information saved to: {output_path}")

        except Exception as e:
            print(f"An error occurred while saving clusters: {e}")

    def visualizeFodf(self):
        """Visualize clustering results using VTK in Slicer3D."""
        if not self.clusters:
            print("No clusters to visualize. Please run `segment` first.")
            return

        try:
            colors = self._generateColors(len(self.clusters))

            for idx, cluster in enumerate(self.clusters):
                vtk_polydata = self._convertToVTK(cluster)

                # Create a new model node
                modelNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode", f"Cluster {idx + 1}")
                modelNode.SetAndObservePolyData(vtk_polydata)

                # Add a display node explicitly
                displayNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
                modelNode.SetAndObserveDisplayNodeID(displayNode.GetID())

                # Set color and scalar visibility
                displayNode.SetColor(colors[idx])
                displayNode.SetScalarVisibility(True)
                displayNode.SetActiveScalarName("ClusterIndex")
                displayNode.SetScalarRange(0, len(cluster))

                displayNode.SetVisibility(True)

            print("Clusters visualized successfully in Slicer3D.")

        except Exception as e:
            print(f"An error occurred during visualization: {e}")


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
    



    

