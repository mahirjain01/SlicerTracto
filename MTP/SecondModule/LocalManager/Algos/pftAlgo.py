
# PFT on sub-1006 PYT_R:-

import subprocess
from dipy.tracking.stopping_criterion import CmcStoppingCriterion
import numpy as np

from dipy.core.gradients import gradient_table
from dipy.data import get_fnames, default_sphere
from dipy.direction import ProbabilisticDirectionGetter
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, load_nifti_data
from dipy.io.stateful_tractogram import Space, StatefulTractogram
from dipy.io.streamline import save_trk
from dipy.reconst.csdeconv import (ConstrainedSphericalDeconvModel,
                                   auto_response_ssst)
from dipy.tracking.local_tracking import (LocalTracking,
                                          ParticleFilteringTracking)
from dipy.tracking.streamline import Streamlines
from dipy.tracking import utils
from dipy.viz import window, actor, colormap, has_fury
import nibabel as nib
import os
OUTPUT_FOLDER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Output")
SEEDING_MASK_FOLDER_PATH: str = os.path.join(OUTPUT_FOLDER_PATH, "SeedingMask")
TRKS_FOLDER_PATH: str = os.path.join(OUTPUT_FOLDER_PATH, "TRKS")
os.makedirs(SEEDING_MASK_FOLDER_PATH, exist_ok=True)
os.makedirs(TRKS_FOLDER_PATH, exist_ok=True)



interactive = False
    # HARDI_FNAME = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.nii.gz'
    # HARDI_BVAL_FNAME = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.bval'
    # HARDI_BVEC_FNAME = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.bvec'



    # F_PVE_CSF = '/datasets/pft/pve/sub-1006/bet_pve_0.nii.gz'
    # F_PVE_GM = '/datasets/pft/pve/sub-1006/bet_pve_1.nii.gz'
    # F_PVE_WM = '/datasets/pft/pve/sub-1006/bet_pve_2.nii.gz'

    # BUNDLE_MASK = '/datasets/TractoInferno-ds003900/pop_avg-aligned-masks/PYT_L/sub-1006_aligned.nii.gz'
# output_trk_path = "pyt_l_pft.trk"


def run(HARDI_FNAME, HARDI_BVAL_FNAME, HARDI_BVEC_FNAME, F_PVE_CSF, F_PVE_GM, F_PVE_WM, BUNDLE_MASK, subjectName):

    trkFileName = subjectName + "_trk.trk"
    output_trk_path = os.path.join(TRKS_FOLDER_PATH, trkFileName)

    seeding_mask_file_path = os.path.join(SEEDING_MASK_FOLDER_PATH, subjectName+"_seeding_mask.nii")
    
    data, affine, hardi_img = load_nifti(HARDI_FNAME, return_img=True)
    bvals, bvecs = read_bvals_bvecs(HARDI_BVAL_FNAME, HARDI_BVEC_FNAME)
    gtab = gradient_table(bvals, bvecs)


    pve_csf_data = load_nifti_data(F_PVE_CSF)
    pve_gm_data = load_nifti_data(F_PVE_GM)
    pve_wm_data, _, voxel_size = load_nifti(F_PVE_WM, return_voxsize=True)




    shape = data.shape[:-1]

    response, ratio = auto_response_ssst(gtab, data, roi_radii=10, fa_thr=0.7)
    csd_model = ConstrainedSphericalDeconvModel(gtab, response)
    csd_fit = csd_model.fit(data, mask=pve_wm_data)

    dg = ProbabilisticDirectionGetter.from_shcoeff(csd_fit.shm_coeff,
                                                max_angle=20.,
                                                sphere=default_sphere)



    seed_mask0 = load_nifti_data(BUNDLE_MASK)
    seed_mask = (seed_mask0 > 0)
    seed_mask[pve_wm_data < 0.5] = 0


    seeds = utils.seeds_from_mask(seed_mask, affine, density=2)




    # ACT uses a fixed threshold on the PVE maps. Both stopping criterion can be used in conjunction with PFT. In this example, we used CMC.

    voxel_size = np.average(voxel_size[1:4])
    step_size = 0.375

    cmc_criterion = CmcStoppingCriterion.from_pve(pve_wm_data,
                                                pve_gm_data,
                                                pve_csf_data,
                                                step_size=step_size,
                                                average_voxel_size=voxel_size)








    pft_streamline_gen = ParticleFilteringTracking(dg,
                                                cmc_criterion,
                                                seeds,
                                                affine,
                                                max_cross=1,
                                                step_size=step_size,
                                                maxlen=1000,
                                                pft_back_tracking_dist=2,
                                                pft_front_tracking_dist=1,
                                                particle_count=15,
                                                return_all=False)
                                                #    min_wm_pve_before_stopping=1)
    streamlines = Streamlines(pft_streamline_gen)
    sft = StatefulTractogram(streamlines, hardi_img, Space.RASMM)
    save_trk(sft, output_trk_path)



    # if has_fury:
    #     scene = window.Scene()
    #     scene.add(actor.line(streamlines, colormap.line_colors(streamlines)))
    #     window.record(scene, out_path='pyt_l_pft.png',
    #                 size=(800, 800))
    #     if interactive:
    #         window.show(scene)


    # streamlines_gt = nib.streamlines.load(output_trk_path).streamlines

    # if has_fury:
    #     scene = window.Scene()
    #     scene.add(actor.line(streamlines_gt, colormap.line_colors(streamlines)))
    #     window.record(scene, out_path='pyt_gt1006_pft.png',
    #                 size=(800, 800))
    #     if interactive:
    #         window.show(scene)

    # streamlines_gt = nib.streamlines.load('/datasets/TractoInferno-ds003900/atlas/rbx_atlas/pop_average/PYT_L.trk').streamlines

    # if has_fury:
    #     scene = window.Scene()
    #     scene.add(actor.line(streamlines_gt, colormap.line_colors(streamlines)))
    #     window.record(scene, out_path='pyt_pop.png',
    #                 size=(800, 800))
    #     if interactive:
    #         window.show(scene)

    seed_mask



    sub_affine = hardi_img.affine
    nifti_img = nib.Nifti1Image(seed_mask.astype(np.float32), sub_affine)
    nib.save(nifti_img, seeding_mask_file_path)




# HARDI_FNAME = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.nii.gz'
    # HARDI_BVAL_FNAME = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.bval'
    # HARDI_BVEC_FNAME = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.bvec'



    # F_PVE_CSF = '/datasets/pft/pve/sub-1006/bet_pve_0.nii.gz'
    # F_PVE_GM = '/datasets/pft/pve/sub-1006/bet_pve_1.nii.gz'
    # F_PVE_WM = '/datasets/pft/pve/sub-1006/bet_pve_2.nii.gz'

    # BUNDLE_MASK = '/datasets/TractoInferno-ds003900/pop_avg-aligned-masks/PYT_L/sub-1006_aligned.nii.gz'
