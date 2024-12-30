#%%
# PFT on sub-1006 PYT_R:-
#%%
import subprocess
import os
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


interactive = False
OUTPUT_FOLDER_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "Output")
SEEDING_MASK_FOLDER_PATH: str = os.path.join(OUTPUT_FOLDER_PATH, "SeedingMask")
TRKS_FOLDER_PATH: str = os.path.join(OUTPUT_FOLDER_PATH, "TRKS")







def run(subjectName, hardi_fname, hardi_bval_fname,hardi_bvec_fname,  f_pve_csf, f_pve_wm, f_pve_gm, bundle_mask):
    trk_file_path = os.path.join(TRKS_FOLDER_PATH, f"{subjectName}_trk.trk")
    seeding_mask_path = os.path.join(SEEDING_MASK_FOLDER_PATH, f"{subjectName}_seeding_mask.nii.gz")
    data, affine, hardi_img = load_nifti(hardi_fname, return_img=True)
    # hardi_bval_fname = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.bval'
    # hardi_bvec_fname = '/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/dwi/sub-1006__dwi.bvec'
    bvals, bvecs = read_bvals_bvecs(hardi_bval_fname, hardi_bvec_fname)
    gtab = gradient_table(bvals, bvecs)


    pve_csf_data = load_nifti_data(f_pve_csf)
    pve_gm_data = load_nifti_data(f_pve_gm)
    pve_wm_data, _, voxel_size = load_nifti(f_pve_wm, return_voxsize=True)


    

    shape = data.shape[:-1]

    response, ratio = auto_response_ssst(gtab, data, roi_radii=10, fa_thr=0.7)
    csd_model = ConstrainedSphericalDeconvModel(gtab, response)
    csd_fit = csd_model.fit(data, mask=pve_wm_data)

    dg = ProbabilisticDirectionGetter.from_shcoeff(csd_fit.shm_coeff,
                                                max_angle=20.,
                                                sphere=default_sphere)
                                                #sh_to_pmf=True)

    
    # bundle_mask = '/datasets/TractoInferno-ds003900/pop_avg-aligned-masks/PYT_L/sub-1006_aligned.nii.gz'
    seed_mask0 = load_nifti_data(bundle_mask)
    seed_mask = (seed_mask0 > 0)
    seed_mask[pve_wm_data < 0.5] = 0
    

    seeds = utils.seeds_from_mask(seed_mask, affine, density=2)

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
    save_trk(sft, trk_file_path)
    


    if has_fury:
        scene = window.Scene()
        scene.add(actor.line(streamlines, colormap.line_colors(streamlines)))
        window.record(scene, out_path='pyt_l_pft.png',
                    size=(800, 800))
        if interactive:
            window.show(scene)


    streamlines_gt = nib.streamlines.load('/datasets/TractoInferno-ds003900/derivatives/testset/sub-1006/tractography/sub-1006__PYT_L.trk').streamlines

    if has_fury:
        scene = window.Scene()
        scene.add(actor.line(streamlines_gt, colormap.line_colors(streamlines)))
        window.record(scene, out_path='pyt_gt1006_pft.png',
                    size=(800, 800))
        if interactive:
            window.show(scene)
    
    streamlines_gt = nib.streamlines.load('/datasets/TractoInferno-ds003900/atlas/rbx_atlas/pop_average/PYT_L.trk').streamlines

    if has_fury:
        scene = window.Scene()
        scene.add(actor.line(streamlines_gt, colormap.line_colors(streamlines)))
        window.record(scene, out_path='pyt_pop.png',
                    size=(800, 800))
        if interactive:
            window.show(scene)
    
    seed_mask

    

    sub_affine = hardi_img.affine
    nifti_img = nib.Nifti1Image(seed_mask.astype(np.float32), sub_affine)
    
    nib.save(nifti_img, seeding_mask_path)
