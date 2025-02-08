from abc import ABC
import os
class BaseManager(ABC):
    def getFodfInputs(self, folderPath):
        diffusionPath = None
        whiteMaskPath = None
        bvalPath = None
        bvecPath = None

        for file_name in os.listdir(folderPath):
            file_path = os.path.join(folderPath, file_name)

            if file_name.endswith("dwi.nii"):
                diffusionPath = file_path
            elif file_name.endswith("wm.nii"):
                whiteMaskPath = file_path
            elif file_name.endswith(".bval"):
                bvalPath = file_path
            elif file_name.endswith(".bvec"):
                bvecPath = file_path

            if diffusionPath and whiteMaskPath and bvalPath and bvecPath:
                print("[SLICER TRACTO] FODF and MASK file found")
                break  

        return diffusionPath, whiteMaskPath, bvalPath, bvecPath
