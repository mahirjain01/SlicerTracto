# Slicer Extension: Advanced White Matter Analysis

This Slicer extension provides tools for advanced white matter analysis using diffusion MRI data. It includes three modules designed for FODF generation, tractography, and metric analysis of white matter fiber tracks.

![Extension Screenshot](images/Screenshot-Extension.png)
---

## Features

1. **Generate FODF (First Module)**  
   Responsible for generating Fiber Orientation Distribution Functions (FODFs) from diffusion MRI data.

   **Inputs:**
   - **White Mask**: Binary mask for white matter regions.
   - **Diffusion NIfTI**: Diffusion-weighted image file.
   - **BVALS**: File containing b-values (`.bvals`).
   - **BVECS**: File containing b-vectors (`.bvecs`).

   ![Generate FODF Module Screenshot](images/Screenshot-GenerateFoDFs.png)

---

2. **Tractography (Second Module)**  
   Generates white matter fiber tracts using seeding masks and FODF data. Tracks can be visualized directly in 3D Slicer.  

   **Inputs:**
   - **Approximate Mask**: Binary mask approximating regions of interest for tractography.
   - **FODF**: Fiber Orientation Distribution Function file generated from the first module.
   - **Step Size**: Step size for tractography.
   - **Algorithm**: Choice of tractography algorithm (`deterministic` or `probabilistic`).

   **Outputs:**
   - **.trk file**: Generated track file containing white matter fiber tracts.
   - **.vtk file**: Visualization-ready track file for rendering in Slicer.

   **Key Features:**
   - Automatically generates a seeding mask from the approximate mask.
   - Converts `.trk` files to `.vtk` for 3D visualization in Slicer.

   ![Tractography Module Screenshot](images/Screenshot-Tractography.png)

---

3. **Metric Analysis (Third Module)**  
   Computes metrics between two `.trk` files to quantify overlap, overreach, and agreement.

   **Metrics:**
   - **Dice Score**: Measures spatial agreement between tracks.
   - **Overreach Score**: Quantifies tracks extending beyond the target area.
   - **Overlap Score**: Measures the shared region between two tractographies.

   ![Metric Analysis Module Screenshot](images/Screenshot-MetricAnalysis.png)

---

## Installation

1. Clone the repository or download the source code:
   ```bash
   git clone https://github.com/yourusername/white-matter-analysis-extension.git

2. Clone the scilpy library inside each module directory:
    ```bash
    cd MTP
    git clone https://github.com/scilus/scilpy.git FirstModule/scilpy
    git clone https://github.com/scilus/scilpy.git SecondModule/scilpy
    git clone https://github.com/scilus/scilpy.git ThirdModule/scilpy

The scilpy library provides essential tools for diffusion MRI processing and tractography.

3. Open 3D Slicer and navigate to the Extensions Manager.

4. Install the extension manually by adding the repository directory to Slicer's module paths:
    - Go to Edit > Application Settings > Modules > Additional Module Paths.
    - Add the path to the downloaded repository.

5.  Restart Slicer to load the extension.

