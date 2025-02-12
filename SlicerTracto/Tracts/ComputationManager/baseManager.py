from abc import ABC
import os
class BaseManager(ABC):
    def getDipyInputs(self, folderPath):
        fodf_path = None
        mask_path = None

        # Iterate through all files in the folder
        for file_name in os.listdir(folderPath):
            file_path = os.path.join(folderPath, file_name)

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
        
        return fodf_path, mask_path

    def getPFTInputs(self, folderPath):
        hardiFName = None
        hardiBvalFName = None
        hardiBvecFName = None
        FPveCsf = None
        FPveGm = None
        FPveWm = None
        BundleMask = None
        for file_name in os.listdir(folderPath):
                file_path = os.path.join(folderPath, file_name)

                # Check if the current file is a .nii file
                if file_name.endswith("__dwi.nii.gz"):
                    hardiFName = file_path
                elif file_name.endswith("__dwi.bval"):
                    hardiBvalFName = file_path
                elif file_name.endswith("__dwi.bvec"):
                    hardiBvecFName = file_path
                elif file_name.endswith("_pve_0.nii.gz"):
                    FPveCsf = file_path
                elif file_name.endswith("_pve_1.nii.gz"):
                    FPveGm = file_path
                elif file_name.endswith("_pve_2.nii.gz"):
                    FPveWm = file_path
                elif file_name.endswith("_aligned.nii.gz"):
                    BundleMask = file_path
            
        if hardiFName == None or hardiBvalFName == None or hardiBvecFName == None or FPveCsf == None or FPveGm == None or FPveWm == None or BundleMask == None:
            print("[SLICER TRACTO] one of the file not found")
        else:
            print("[SLICER TRACTO] Files Found")
        return hardiFName, hardiBvalFName, hardiBvecFName, FPveCsf, FPveGm, FPveWm, BundleMask  

    def getTRLFInputs(self, folderPath):
        trlf_model_load_path = None
        offline_trajectories = None
        input_fodf_signal = None
        seeding_mask = None
        tracking_mask = None
        bundle_mask = None
        peaks = None
        reference_file_fa = None
        for file_name in os.listdir(folderPath):
                file_path = os.path.join(folderPath, file_name)

                # Check if the current file is a .nii file
                if file_name.endswith("_fods.nii.gz"):
                    input_fodf_signal = file_path
                elif file_name.endswith("_peak.nii.gz"):
                    peaks = file_path
                elif file_name.endswith(".pt"):
                    trlf_model_load_path = file_path
                elif file_name.endswith("_fa.nii.gz"):
                    reference_file_fa = file_path
                elif file_name.endswith(".pkl"):
                    offline_trajectories = file_path
                elif file_name.endswith(".nii.gz"):
                    seeding_mask = file_path
                    tracking_mask = file_path
                    bundle_mask = file_path
            
        if input_fodf_signal == None or peaks == None or trlf_model_load_path == None or bundle_mask == None or seeding_mask == None or tracking_mask == None or reference_file_fa == None or offline_trajectories == None:
            print("[SLICER TRACTO] one of the file not found")
        else:
            print("[SLICER TRACTO] Files Found")
        return trlf_model_load_path, offline_trajectories, input_fodf_signal, seeding_mask, tracking_mask, bundle_mask, peaks, reference_file_fa 
    