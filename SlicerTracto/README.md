# Tractography and FODF Computation Codebase

This codebase is designed for processing diffusion MRI data, specifically focusing on tractography and Fiber Orientation Distribution Function (FODF) computations. It includes various algorithms and scripts for data processing, SSH management, and remote execution of tasks.

## Code Structure

- **Tracts/ComputationManager/SSHManager/Algos**: Contains algorithms for tractography, including `trlfAlgo.py` and `pftAlgo.py`.
- **Fodf/FodfComputationManager/LocalManager/Algos**: Contains local algorithms for FODF computation, such as `generateFodf.py`.
- **Fodf/FodfComputationManager/SSHManager/Algos**: Contains scripts for remote execution.
- **Segment/SegmentComputationManager/SSHManager**: Manages SSH connections for segmentation tasks.

## Key Components

### Tract_RLFormer Class
Located in `trlfAlgo.py`, this class handles the initialization and execution of tractography algorithms using SSH for remote processing.

## How to Run

1. **Setup Environment**: Ensure all dependencies are installed. This includes Python packages like `paramiko`, `scp`, and `dipy`.

2. **Configure SSH**: Update SSH configurations in the respective classes to match your server details. This includes hostname, username, and key file paths.

3. **Run Local Algorithms**: Execute local scripts directly from the command line. For example, to generate FODF:
   ```bash
   python Fodf/FodfComputationManager/LocalManager/Algos/generateFodf.py
   ```

4. **Run Remote Algorithms**: Use the SSHManager classes to connect and execute scripts on remote servers. Ensure SSH keys are correctly configured.

5. **Data Input/Output**: Ensure input data paths are correctly set in the scripts. Output directories will be created if they do not exist.

## Notes

- **SSH Configuration**: SSH details are hardcoded for demonstration purposes. For production, consider moving these to a configuration file.
- **Error Handling**: Ensure proper error handling is in place for network operations and file I/O.

For more detailed information on each script and its parameters, refer to the docstrings within the code files.