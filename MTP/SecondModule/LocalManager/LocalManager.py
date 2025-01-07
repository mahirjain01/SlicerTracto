from LocalManager.Algos import pftAlgo, dipyAlgo
import os


class LocalManager:
    def __init__(self):
        pass

    def execute(self, subjectName, algo, folderPath):
        if algo == 'dipy':
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
            
            dipyAlgo.run(subjectName=subjectName, approxMaskPathFilePath=mask_path, fodfFilePath=fodf_path)
        elif algo == 'PFT':
            print("[SLICER TRACTO] Running PFT Algo")
            # hardiFName = None
            # hardiBvalFName = None
            # hardiBvecFName = None
            # FPveCsf = None
            # FPveGm = None
            # FPveWm = None
            # BundleMask = None
            # for file_name in os.listdir(folderPath):
            #         file_path = os.path.join(folderPath, file_name)

            #         # Check if the current file is a .nii file
            #         if file_name.endswith("__dwi.nii.gz"):
            #             hardiFName = file_path
            #         elif file_name.endswith("__dwi.bval"):
            #             hardiBvalFName = file_path
            #         elif file_name.endswith("__dwi.bvec"):
            #             hardiBvecFName = file_path
            #         elif file_name.endswith("_pve_0.nii.gz"):
            #             FPveCsf = file_path
            #         elif file_name.endswith("_pve_1.nii.gz"):
            #             FPveGm = file_path
            #         elif file_name.endswith("_pve_2.nii.gz"):
            #             FPveWm = file_path
            #         elif file_name.endswith("_aligned.nii.gz"):
            #             BundleMask = file_path
                
            # if hardiFName == None or hardiBvalFName == None or hardiBvecFName == None or FPveCsf == None or FPveGm == None or FPveWm == None or BundleMask == None:
            #     print("[SLICER TRACTO] one of the file not found")
            # else:
            #     print("[SLICER TRACTO] Files Found")
            # pftAlgo.run(HARDI_FNAME=hardiFName, HARDI_BVAL_FNAME=hardiBvalFName, HARDI_BVEC_FNAME=hardiBvecFName, F_PVE_CSF=FPveCsf, F_PVE_GM=FPveGm, F_PVE_WM=FPveWm, BUNDLE_MASK=BundleMask, subjectName=subjectName)
            