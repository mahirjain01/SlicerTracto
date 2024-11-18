
from dipy.io.streamline import load_tractogram
from dipy.segment.quickbundles import QuickBundles
from dipy.io.streamline import save_trk
from dipy.tracking.streamline import transform_streamlines
from dipy.io.streamline import load_tractogram
from dipy.segment.quickbundles import QuickBundles
from dipy.io.streamline import save_tractogram

import os


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
            fileName = DEFAULT_SEGMENTED_TRK_FILE_NAME_PREFIX + f"-{i}.trk"
            filePath = os.path.join(self.segmentedTrkFolderPath, fileName)
            save_tractogram(tractogram, filePath, streamlines=cluster_streamlines)
            self.outputText.append(f'Cluster {i} saved in file {filePath} \n\n')

    def visualizeSegmentation(self):
        pass
        


        
