import os
import sys
from scripts.scil_frf_ssst import main as scil_frf_ssst_main
from scripts.scil_fodf_ssst import main as scil_fodf_ssst_main
from scripts.scil_dti_metrics import main as scil_dti_metrics_main
from scripts.scil_fodf_metrics import main as scil_fodf_metrics_main

class GenerateFODF:
    def __init__(self, subjectName, diffusionPath, whiteMaskPath, bvalPath, bvecPath, outputFolderPath):
        self.whiteMaskPath: str = whiteMaskPath
        self.diffusionPath: str = diffusionPath
        self.bvalPath: str = bvalPath
        self.bvecPath: str = bvecPath
        self.fodfPath: str = None
        self.outputFolderPath: str = outputFolderPath
        self.subjectName: str = subjectName

    def generateFodf(self):
        try:
            # Ensure output directory exists
            os.makedirs(self.outputFolderPath, exist_ok=True)

            # Step 2: Estimate response function using SSST
            frf_file = os.path.join(self.outputFolderPath, f"{self.subjectName}_frf.txt")
            frf_args = [
                "scil_frf_ssst.py", self.diffusionPath, self.bvalPath, self.bvecPath, frf_file,
                "--mask_wm", self.whiteMaskPath, "-f", "-v"
            ]
            sys.argv = frf_args
            scil_frf_ssst_main()
            print("Response function estimated successfully.")

            # Step 3: Generate FODF using SSST
            fodf_file = os.path.join(self.outputFolderPath, f"{self.subjectName}_fodf.nii.gz")
            fodf_args = [
                "scil_fodf_ssst.py", self.diffusionPath, self.bvalPath, self.bvecPath, frf_file, fodf_file,
                "--processes", "8", "--sh_order", "6", "-f"
            ]
            sys.argv = fodf_args
            scil_fodf_ssst_main()
            print("FODF generated successfully.")

            # Compute DTI metrics
            dti_args = ["scil_dti_metrics.py", self.diffusionPath, self.bvalPath, self.bvecPath]
            sys.argv = dti_args
            scil_dti_metrics_main()
            print("DTI metrics computed successfully.")

            # Compute FODF metrics
            fodf_metrics_args = ["scil_fodf_metrics.py", fodf_file, "-f"]
            sys.argv = fodf_metrics_args
            scil_fodf_metrics_main()
            print("FODF metrics computed successfully.")

        except Exception as e:
            print(f"An error occurred: {e}")

        finally:
            # Reset sys.argv to avoid affecting other parts of the program
            sys.argv = ["main.py"]


if __name__ == "__main__":
    rootPath = "/scratch/mahirj.scee.iitmandi/Gagan/SlicerTracto/Fodf/Output"
    generateFODF = GenerateFODF(subjectName="sample", diffusionPath=f"{rootPath}/sample_dwi.nii", whiteMaskPath=f"{rootPath}/sample_wm.nii", bvalPath=f"{rootPath}/sample.bval", bvecPath=f"{rootPath}/sample.bvec")