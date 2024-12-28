import os
import sys
import logging

# Get the path to the scilpy folder and add to sys paths
sibling_folder_path = os.path.join(os.path.dirname(__file__),'scilpy')
if sibling_folder_path not in sys.path:
    sys.path.append(sibling_folder_path)

from scilpy.reconst.utils import (find_order_from_nb_coeff,
                                    get_maximas)
from scilpy.io.image import get_data_as_mask
from scilpy.tracking.utils import get_theta

from dipy.tracking.local_tracking import LocalTracking
from dipy.tracking.stopping_criterion import BinaryStoppingCriterion
from dipy.tracking.streamlinespeed import length
from dipy.tracking import utils as track_utils
from dipy.io.streamline import save_trk
from dipy.io.stateful_tractogram import StatefulTractogram, Space
from dipy.io.streamline import load_tractogram
from dipy.io.stateful_tractogram import Space
from dipy.io.utils import is_header_compatible
from dipy.io.streamline import load_tractogram
from dipy.io.image import load_nifti

from dipy.io.utils import (get_reference_info,
                           create_tractogram_header)
from dipy.reconst.shm import sph_harm_lookup
from dipy.direction.peaks import PeaksAndMetrics
from dipy.direction import (DeterministicMaximumDirectionGetter,
                            ProbabilisticDirectionGetter) 
from dipy.core.sphere import HemiSphere
from dipy.data import get_sphere
from vtk import vtkPolyDataReader
import numpy as np
import warnings
import nibabel as nib
from nibabel.streamlines.tractogram import LazyTractogram
from scripts.scil_frf_ssst import main as scil_frf_ssst_main
import vtk
import parser

# Constansts 
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
ALGO = "det"
STEP_SIZE = 0.5
OUTPUT_FOLDER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Output")
INPUT_FOLDER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Input")
SEEDING_MASK_FOLDER_PATH: str = os.path.join(OUTPUT_FOLDER_PATH)
TRKS_FOLDER_PATH: str = os.path.join(OUTPUT_FOLDER_PATH)
os.makedirs(SEEDING_MASK_FOLDER_PATH, exist_ok=True)
os.makedirs(TRKS_FOLDER_PATH, exist_ok=True)


def run(subjectName, approxMaskPathFilePath, fodfFilePath):
    print("[SLICER TRACTO] Generating SEEDING MASKS...")
    seeding_mask_file_path = _create_binary_mask(approxMaskPathFilePath, subjectName)
    print("[SLICER TRACTO] SEEDING MASKS GENERATED...")
    print("[SLICER TRACTO] Generating TRACKS MASKS...")

    mask_img = nib.load(seeding_mask_file_path)
    mask_data = get_data_as_mask(mask_img, dtype=bool)

    odf_sh_img = nib.load(fodfFilePath)
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
    vox_step_size = STEP_SIZE / voxel_size
    seed_img = nib.load(seeding_mask_file_path)
    seeds = track_utils.random_seeds_from_mask(
        seed_img.get_fdata(dtype=np.float32),
        np.eye(4),
        seeds_count=nb_seeds,
        seed_count_per_voxel=seed_per_vox,
        random_seed=None)

    max_steps = int(MAX_LENGTH / STEP_SIZE) + 1
    streamlines_generator = LocalTracking(
        _get_direction_getter(fodfFilePath),
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
    trkFileName = f"/{subjectName}_trk.trk"
    output_trk_path = os.path.join(OUTPUT_FOLDER_PATH+trkFileName)
    
    
    nib.streamlines.save(tractogram, output_trk_path, header=header)
    print("[SLICER TRACTO] TRK GENERATED...")

    # self.outputText.append(f'Trk Genererated Successfully \n (location: {self.output_trk_path}) \n')

def _get_direction_getter(fodfFilePath):
        odf_data = nib.load(fodfFilePath).get_fdata(dtype=np.float32)
        sphere = HemiSphere.from_sphere(get_sphere(SPHERE))
        theta = get_theta(THETA, ALGO)

        non_zeros_count = np.count_nonzero(np.sum(odf_data, axis=-1))
        non_first_val_count = np.count_nonzero(np.argmax(odf_data, axis=-1))

        if ALGO in ['det', 'prob']:
            if non_first_val_count / non_zeros_count > 0.5:
                logging.warning('Input detected as peaks. Input should be'
                                'fodf for det/prob, verify input just in case.')
            if ALGO == 'det':
                dg_class = DeterministicMaximumDirectionGetter
            else:
                dg_class = ProbabilisticDirectionGetter
            return dg_class.from_shcoeff(
                shcoeff=odf_data, max_angle=theta, sphere=sphere,
                basis_type=SH_BASIS,
                relative_peak_threshold=SF_THRESHOLD)
        elif ALGO == 'eudx':
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
                b_matrix = _get_b_matrix(
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
        
def _create_binary_mask(approxMaskPathFilePath, subjectName:str, threshold=0.5):
        # Load the image
        img = nib.load(approxMaskPathFilePath)

        # Get the image data
        data = img.get_fdata()

        # Threshold the data to create a binary mask
        mask_data = (data > threshold).astype(np.uint8)

        # Create a new nibabel image with the binary mask
        mask_img = nib.Nifti1Image(mask_data, img.affine, img.header)
        mask_img.set_data_dtype(np.uint8)
        seeding_mask_file_path = OUTPUT_FOLDER_PATH+f"/{subjectName}_seeding_mask.nii"
        # Save the new image
        nib.save(mask_img, seeding_mask_file_path)
        return seeding_mask_file_path

def _get_b_matrix(order, sphere, sh_basis_type, return_all=False):
    sh_basis = _honor_authorsnames_sh_basis(sh_basis_type)
    sph_harm_basis = sph_harm_lookup.get(sh_basis)
    if sph_harm_basis is None:
        raise ValueError("Invalid basis name.")
    b_matrix, m, n = sph_harm_basis(order, sphere.theta, sphere.phi)
    if return_all:
        return b_matrix, m, n
    return b_matrix

if __name__ == "__main__":
    subjectName="sample"
    approxMaskFilePath=os.path.join(INPUT_FOLDER_PATH, "sample_approx_mask.nii")
    fodfFilePath=os.path.join(INPUT_FOLDER_PATH, "sample_fodf.nii")
    run(subjectName=subjectName, approxMaskPathFilePath=approxMaskFilePath, fodfFilePath=fodfFilePath)