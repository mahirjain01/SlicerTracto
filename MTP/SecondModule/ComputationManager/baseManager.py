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
    