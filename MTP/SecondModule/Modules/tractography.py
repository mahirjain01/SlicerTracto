import os
import sys
import logging
# Get the path to the sibling folder
sibling_folder_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scilpy'))

# Add it to sys.path
if sibling_folder_path not in sys.path:
    sys.path.append(sibling_folder_path)

from scilpy.reconst.utils import (find_order_from_nb_coeff,
                                    get_maximas)
from scilpy.io.image import get_data_as_mask
from scilpy.tracking.utils import get_theta


from dipy.io.image import load_nifti
from dipy.core.sphere import HemiSphere
from dipy.io.streamline import load_tractogram
from dipy.data import get_sphere

from dipy.direction import (DeterministicMaximumDirectionGetter,
                            ProbabilisticDirectionGetter)
from dipy.io.utils import (get_reference_info,
                           create_tractogram_header)
from dipy.direction.peaks import PeaksAndMetrics
from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.streamlinespeed import length
from dipy.io.streamline import save_trk
from dipy.tracking import utils as track_utils
from vtk import vtkPolyDataReader
import numpy as np
import warnings
from dipy.io.stateful_tractogram import StatefulTractogram, Space
from dipy.reconst.shm import sph_harm_lookup
import nibabel as nib
from nibabel.streamlines.tractogram import LazyTractogram


from scripts.scil_frf_ssst import main as scil_frf_ssst_main




NPV = None
NT = None
MIN_LENGTH : float = 10.0
MAX_LENGTH : float = 200.0
SPHERE : str = 'symmetric724'
THETA : float = 45.0
SH_BASIS : str = 'tournier07'  
SF_THRESHOLD : float = 0.1
SEED = None
SAVE_SEEDS = False
FILETYPE = nib.streamlines.TrkFile
COMPRESS : float = 0.0
OUTPUT_TRK_FILE_PATH: str = "C:/Users/HP/Documents/MTP/Slicer-Task/Final Modules/Results/trk_1061_mrm_detT.trk"
SEEDING_MASK_FILE_PATH: str = "C:/Users/HP/Documents/MTP/Slicer-Task/Final Modules/Results/sub_1061_seeding_mask.nii"
RESULT_VTK:str = "C:/Users/HP/Documents/MTP/Slicer-Task/Final Modules/Results/result.vtk"

class Tractography:
    def __init__(self):
        self.approxMaskPath: str = None
        self.fodfPath: str = None
        self.stepSize: float = 0.2
        self.algo: str = "det"
        self.trkPath : str = None
        self.seedingMaskPath = SEEDING_MASK_FILE_PATH

    @staticmethod
    def isValidPath(path: str) -> bool:
        """Validate if the provided path exists and is a file."""
        return os.path.isfile(path)

    # Updated setter methods with validation
    def set_approxMaskPath(self, path: str):
        """Set the path for the approximate mask after validation."""
        if self.isValidPath(path):
            self.approxMaskPath = path
            print(f"Approximate mask path set to: {self.approxMaskPath}")
        else:
            raise FileNotFoundError(f"Invalid approximate mask path: {path}")

    def set_fodfPath(self, path: str):
        """Set the path for the FODF file after validation."""
        if self.isValidPath(path):
            self.fodfPath = path
            print(f"FODF path set to: {self.fodfPath}")
        else:
            raise FileNotFoundError(f"Invalid FODF path: {path}")

    def set_trkPath(self, path: str):
        """Set the path for the FODF file after validation."""
        if self.isValidPath(path):
            self.trkPath = path
            print(f"Trk path set to: {self.trkPath}")
        else:
            raise FileNotFoundError(f"Invalid trk path: {path}")

    def set_stepSize(self, step: float):
        """Set the step size with validation."""
        step = float(step)
        if isinstance(step, (int, float)) and step > 0:
            self.stepSize = float(step)
            print(f"Step size set to: {self.stepSize}")
        # else:
        #     raise ValueError("stepSize must be a positive numeric value.")

    def set_algo(self, algorithm: str):
        """Set the tracking algorithm with validation."""
        self.algo = self.comboBox.itemText(index)
        slicer.util.showStatusMessage(f"Selected: {self.algo}", 2000)
        print(f"Algorithm set to: {self.algo}")

    def get_b_matrix(self, order, sphere, sh_basis_type, return_all=False):
        sh_basis = self._honor_authorsnames_sh_basis(sh_basis_type)
        sph_harm_basis = sph_harm_lookup.get(sh_basis)
        if sph_harm_basis is None:
            raise ValueError("Invalid basis name.")
        b_matrix, m, n = sph_harm_basis(order, sphere.theta, sphere.phi)
        if return_all:
            return b_matrix, m, n
        return b_matrix

    def create_binary_mask(self, threshold=0.5):
        # Load the image
        img = nib.load(self.approxMaskPath)

        # Get the image data
        data = img.get_fdata()

        # Threshold the data to create a binary mask
        mask_data = (data > threshold).astype(np.uint8)

        # Create a new nibabel image with the binary mask
        mask_img = nib.Nifti1Image(mask_data, img.affine, img.header)
        mask_img.set_data_dtype(np.uint8)
        # Save the new image
        nib.save(mask_img, SEEDING_MASK_FILE_PATH)

    

    def _get_direction_getter(self):
        odf_data = nib.load(self.fodfPath).get_fdata(dtype=np.float32)
        sphere = HemiSphere.from_sphere(get_sphere(SPHERE))
        theta = get_theta(THETA, self.algo)

        non_zeros_count = np.count_nonzero(np.sum(odf_data, axis=-1))
        non_first_val_count = np.count_nonzero(np.argmax(odf_data, axis=-1))

        if self.algo in ['det', 'prob']:
            if non_first_val_count / non_zeros_count > 0.5:
                logging.warning('Input detected as peaks. Input should be'
                                'fodf for det/prob, verify input just in case.')
            if self.algo == 'det':
                dg_class = DeterministicMaximumDirectionGetter
            else:
                dg_class = ProbabilisticDirectionGetter
            return dg_class.from_shcoeff(
                shcoeff=odf_data, max_angle=theta, sphere=sphere,
                basis_type=SH_BASIS,
                relative_peak_threshold=SF_THRESHOLD)
        elif self.algo == 'eudx':
            # Code for type EUDX. We don't use peaks_from_model
            # because we want the peaks from the provided sh.
            odf_shape_3d = odf_data.shape[:-1]
            dg = PeaksAndMetrics()
            dg.sphere = sphere
            dg.ang_thr = theta
            dg.qa_thr = SF_THRESHOLD

            # Heuristic to find out if the input are peaks or fodf
            # fodf are always around 0.15 and peaks around 0.75
            if non_first_val_count / non_zeros_count > 0.5:
                logging.info('Input detected as peaks.')
                nb_peaks = odf_data.shape[-1] // 3
                slices = np.arange(0, 15+1, 3)
                peak_values = np.zeros(odf_shape_3d+(nb_peaks,))
                peak_indices = np.zeros(odf_shape_3d+(nb_peaks,))

                for idx in np.argwhere(np.sum(odf_data, axis=-1)):
                    idx = tuple(idx)
                    for i in range(nb_peaks):
                        peak_values[idx][i] = np.linalg.norm(
                            odf_data[idx][slices[i]:slices[i+1]], axis=-1)
                        peak_indices[idx][i] = sphere.find_closest(
                            odf_data[idx][slices[i]:slices[i+1]])

                dg.peak_dirs = odf_data
            else:
                logging.info('Input detected as fodf.')
                npeaks = 5
                peak_dirs = np.zeros((odf_shape_3d + (npeaks, 3)))
                peak_values = np.zeros((odf_shape_3d + (npeaks, )))
                peak_indices = np.full((odf_shape_3d + (npeaks, )), -1, dtype='int')
                b_matrix = get_b_matrix(
                    find_order_from_nb_coeff(odf_data), sphere, SH_BASIS)

                for idx in np.argwhere(np.sum(odf_data, axis=-1)):
                    idx = tuple(idx)
                    directions, values, indices = get_maximas(odf_data[idx],
                                                            sphere, b_matrix,
                                                            SF_THRESHOLD, 0)
                    if values.shape[0] != 0:
                        n = min(npeaks, values.shape[0])
                        peak_dirs[idx][:n] = directions[:n]
                        peak_values[idx][:n] = values[:n]
                        peak_indices[idx][:n] = indices[:n]

                dg.peak_dirs = peak_dirs

            dg.peak_values = peak_values
            dg.peak_indices = peak_indices

            return dg
    
    # Placeholder for generate, save, and visualize methods
    def generateTrk(self):
        self.create_binary_mask()
        mask_img = nib.load(self.seedingMaskPath)
        mask_data = get_data_as_mask(mask_img, dtype=bool)

        odf_sh_img = nib.load(self.fodfPath)
        if not np.allclose(np.mean(odf_sh_img.header.get_zooms()[:3]),
                        odf_sh_img.header.get_zooms()[0], atol=1e-03):
            parser.error(
                'ODF SH file is not isotropic. Tracking cannot be ran robustly.')

        if NPV:
            nb_seeds = NPV
            seed_per_vox = True
        elif NT:
            nb_seeds = NT
            seed_per_vox = False
        else:
            nb_seeds = 1
            seed_per_vox = True

        voxel_size = odf_sh_img.header.get_zooms()[0]
        vox_step_size = self.stepSize / voxel_size
        seed_img = nib.load(self.seedingMaskPath)
        seeds = track_utils.random_seeds_from_mask(
            seed_img.get_fdata(dtype=np.float32),
            np.eye(4),
            seeds_count=nb_seeds,
            seed_count_per_voxel=seed_per_vox,
            random_seed=None)

        max_steps = int(MAX_LENGTH / self.stepSize) + 1
        streamlines_generator = LocalTracking(
            self._get_direction_getter(),
            BinaryStoppingCriterion(mask_data),
            seeds, np.eye(4),
            step_size=vox_step_size, max_cross=1,
            maxlen=max_steps,
            fixedstep=True, return_all=True,
            random_seed=SEED,
            save_seeds=SAVE_SEEDS)
        
        scaled_min_length = MIN_LENGTH / voxel_size
        scaled_max_length = MAX_LENGTH / voxel_size

        if SAVE_SEEDS:
            filtered_streamlines, seeds = \
                zip(*((s, p) for s, p in streamlines_generator
                    if scaled_min_length <= length(s) <= scaled_max_length))
            data_per_streamlines = {'seeds': lambda: seeds}
        else:
            filtered_streamlines = \
                (s for s in streamlines_generator
                if scaled_min_length <= length(s) <= scaled_max_length)
            data_per_streamlines = {}

        if COMPRESS:
            filtered_streamlines = (
                compress_streamlines(s, COMPRESS)
                for s in filtered_streamlines)

        tractogram = LazyTractogram(lambda: filtered_streamlines,
                                    data_per_streamlines,
                                    affine_to_rasmm=seed_img.affine)

        
        reference = get_reference_info(seed_img)
        header = create_tractogram_header(FILETYPE, *reference)

        # Use generator to save the streamlines on-the-fly
        nib.streamlines.save(tractogram, OUTPUT_TRK_FILE_PATH, header=header)

    def saveTrk(self):
        """Placeholder method for saving tractography."""
        print("Saving tractography...")

    def visualizeTrk(self):
        """Placeholder method for visualizing tractography."""
        print("Visualizing tractography...")
    

    def __repr__(self):
        return (f"Tractography(approxMaskPath={self.approxMaskPath}, "
                f"fodfPath={self.fodfPath}, stepSize={self.stepSize}, algo={self.algo})")
    
    def readFODFNIfTI(self, mvNode, niftiFilePath):
        """Read a 4D NIfTI file containing spherical harmonics as multivolume."""

        # Use VTK's NIfTI reader to load the 4D NIfTI file
        reader = vtk.vtkNIFTIImageReader()
        reader.SetFileName(niftiFilePath)
        reader.SetTimeAsVector(True)  # Use the 4th dimension
        reader.Update()
        
        nFrames = reader.GetTimeDimension()

    
        print(f"Successfully read {nFrames} spherical harmonics frames from the FODF NIfTI file.")

        # Display message with the number of frames (SH coefficients)
        mvNode.SetName(f"{nFrames} frames NIfTI MultiVolume")

        # Process and store the FODF data
        mvImage = reader.GetOutputDataObject(0)

        # Create and configure the MultiVolume display node
        mvDisplayNode = slicer.mrmlScene.CreateNodeByClass('vtkMRMLMultiVolumeDisplayNode')
        mvDisplayNode.SetScene(slicer.mrmlScene)
        slicer.mrmlScene.AddNode(mvDisplayNode)
        mvDisplayNode.SetDefaultColorMap()

        # Set the image data and display node for the multivolume node
        mvNode.SetAndObserveImageData(mvImage)
        mvNode.SetAndObserveDisplayNodeID(mvDisplayNode.GetID())
        mvNode.SetNumberOfFrames(nFrames)

        print(f"Output node configured with {nFrames} frames.")

        # Optionally, you can add the logic to handle frame labels or SH-specific attributes

        # Return the number of frames (spherical harmonics coefficients)
        return nFrames

        
        