import os
import vtk
import paramiko
import time
from scp import SCPClient
from pathlib import Path
from select import select
import slicer
from vtk import vtkPolyDataReader
from dipy.io.stateful_tractogram import Space
from dipy.io.streamline import load_tractogram, save_vtk
from dipy.io.streamline import load_tractogram

DEFAULT_VTK_FILE_NAME = "result.vtk"
DEFAULT_DIR = "/Users/mahir/Desktop/MTP/TractRLFormer/Output"

class Tract_RLFormer:
    def __init__(self):
        self.outputConsole = None
        self._initialize_parameters()
        self.ssh = None
        self.scp = None
        self.output_filename = None
        self._running = False
        
        self.output_trk_path = None  # Track generated TRK file
        self.trkPath = None

        # SSH Configuration (should be moved to config file in production)
        self.ssh_config = {
            'hostname': '172.18.40.12',
            'username': 'turing',
            'key_filename': os.path.expanduser('~/.ssh/id_rsa'),  
            'timeout': 30
        }
        self.remote_workspace = '/home/turing/tracking_workspace'
        self.conda_env = 'project_3_7'
        self.local_results = Path('/Users/mahir/Desktop/MTP/SlicerTracto/SlicerTracto/Tracts/Output')

    def _initialize_parameters(self):
        """Initialize all input parameters with default empty values"""
        self.parameters = {
            'trlf_model_load_path': '',
            'offline_trajectories': '',
            'input_fodf_signal': '',
            'seeding_mask': '',
            'tracking_mask': '',
            'bundle_mask': '',
            'peaks': '',
            'reference_file_fa': '',
            'output_dir': ''
        }

    # -------------------------------------------------------------------------
    # Parameter setters
    # -------------------------------------------------------------------------
    def setTrlfModelPath(self, path):
        if self._validate_path(path, ['.pt']):
            self.parameters['trlf_model_load_path'] = str(path)

    def setOfflineTrajectoriesPath(self, path):
        if self._validate_path(path, ['.pkl']):
            self.parameters['offline_trajectories'] = str(path)

    def setFodfPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['input_fodf_signal'] = str(path)

    def setSeedingMaskPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['seeding_mask'] = str(path)

    def setTrackingMaskPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['tracking_mask'] = str(path)

    def setBundleMaskPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['bundle_mask'] = str(path)

    def setPeaksPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['peaks'] = str(path)

    def setReferenceFAPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['reference_file_fa'] = str(path)

    def setOutputDirPath(self, path):
        self.local_results.mkdir(exist_ok=True)
        # if Path(path).is_dir():
        #     self.parameters['output_dir'] = str(path)
        #     self.local_results = Path(path)
        # else:
        #     self._log_error(f"Invalid output directory: {path}")

    # -------------------------------------------------------------------------
    # Main function triggered by UI
    # -------------------------------------------------------------------------
    def runTracking(self):
        """
        Main entry point to run the pipeline from the Slicer UI button.
        1. Validate parameters
        2. SSH connect
        3. Upload input data
        4. Execute tracking script on remote
        5. Download results
        6. Cleanup remote
        """
        if not self._validate_all_paths():
            self._log_error("Aborting due to invalid parameters")
            return

        try:

            self._log("Starting remote tracking pipeline...")
            self._running = True

            self.connect()
            self.transfer_files()
            self.execute_tracking()
            result_path = self.retrieve_results()

            self._log(f"Tracking complete! Results saved to:\n{result_path}")

        except Exception as e:
            self._log_error(f"Pipeline failed: {str(e)}")

        finally:
            self.cleanup()
            if self.scp:
                self.scp.close()
            if self.ssh:
                self.ssh.close()
            self._running = False

    def cancelTracking(self):
        """Cancel ongoing tracking operation"""
        if self._running:
            self._log("Cancelling tracking operation...")
            self._running = False
            self.cleanup()  # optionally also close ssh/scp

    # -------------------------------------------------------------------------
    # Validation methods
    # -------------------------------------------------------------------------
    def _validate_path(self, path, valid_extensions=None):
        """Validate that the file path exists and extension is allowed."""
        if not path:  # Ignore empty paths (fixes the issue)
            return True

        path_obj = Path(path)

        if not path_obj.exists():
            self._log_error(f"Path does not exist: {path}")
            return False

        if valid_extensions and not any(path.endswith(ext) for ext in valid_extensions):
            self._log_error(f"Invalid file extension for: {path}")
            return False

        return True


    def _validate_all_paths(self):
        """Validate all required input parameters before execution"""
        required = [
            ('trlf_model_load_path', ['.pt']),
            # ('offline_trajectories', ['.pkl']),
            ('input_fodf_signal', ['.nii', '.nii.gz']),
            ('seeding_mask', ['.nii', '.nii.gz']),
            ('tracking_mask', ['.nii', '.nii.gz']),
            ('bundle_mask', ['.nii', '.nii.gz']),
            ('peaks', ['.nii', '.nii.gz']),
            ('reference_file_fa', ['.nii', '.nii.gz'])
        ]

        return all(
            self._validate_path(self.parameters[key], exts)
            for key, exts in required
            if key in self.parameters
        )

    # -------------------------------------------------------------------------
    # Logging helpers
    # -------------------------------------------------------------------------
    def _log(self, message):
        """Add info message to console output"""
        if self.outputConsole:
            self.outputConsole.append(f"[INFO] {message}")
        else:
            print(f"[INFO] {message}")

    def _log_error(self, message):
        """Add error message to console output"""
        if self.outputConsole:
            self.outputConsole.append(f"[ERROR] {message}")
        else:
            print(f"[ERROR] {message}")
  # -------------------------------------------------------------------------
    # SSH / SCP methods
    # -------------------------------------------------------------------------
    
    def connect(self):
        """Establish SSH connection with explicit key format"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            private_key_path = os.path.expanduser("~/.ssh/filename")
            
            # Load the key explicitly
            pkey = paramiko.RSAKey(filename=private_key_path)

            self.ssh.connect(
                hostname=self.ssh_config['hostname'],
                username=self.ssh_config['username'],
                pkey=pkey,  
                timeout=self.ssh_config['timeout']
            )

            self.scp = SCPClient(self.ssh.get_transport())
            self._log("SSH connection established")

        except Exception as e:
            self._log_error(f"SSH connection failed: {str(e)}")
            raise

    def transfer_files(self):
        """Transfer all required input files to the remote server"""
        remote_input_dir = f'{self.remote_workspace}/input'

        # Create remote directories
        self.execute_command(f'mkdir -p {remote_input_dir}')
        self.execute_command(f'mkdir -p {self.remote_workspace}/output')

        # Transfer each relevant file, but **skip empty paths**
        for key in [
            'trlf_model_load_path', 'offline_trajectories',
            'input_fodf_signal', 'seeding_mask', 'tracking_mask',
            'bundle_mask', 'peaks', 'reference_file_fa'
        ]:
            local_path = self.parameters[key]

            if not local_path:  # **SKIP EMPTY PATHS**
                continue

            remote_path = f'{remote_input_dir}/{os.path.basename(local_path)}'
            self.scp.put(local_path, remote_path)

    def execute_tracking(self):
        """Execute the tracking command on the remote server"""

        # Generate unique output filename
        timestamp = int(time.time())
        self.output_filename = f'trk_trlf_{timestamp}.trk'

        # Build base command
        cmd = (
            f'source ~/anaconda3/etc/profile.d/conda.sh && '
            f'conda activate {self.conda_env} && '
            f"cd {self.remote_workspace} && "
            f"python inference_tracking.py "
            f'--trlf_model_load_path input/{os.path.basename(self.parameters["trlf_model_load_path"])} '
            f'--input_fodf_signal input/{os.path.basename(self.parameters["input_fodf_signal"])} '
            f'--seeding_mask input/{os.path.basename(self.parameters["seeding_mask"])} '
            f'--tracking_mask input/{os.path.basename(self.parameters["tracking_mask"])} '
            f'--bundle_mask input/{os.path.basename(self.parameters["bundle_mask"])} '
            f'--peaks input/{os.path.basename(self.parameters["peaks"])} '
            f'--reference_file_fa input/{os.path.basename(self.parameters["reference_file_fa"])} '
            f'--save_trk_path output/{self.output_filename}'
        )

        # **Only include offline_trajectories if it is NOT empty**
        if self.parameters.get("offline_trajectories"):
            cmd += f' --offline_trajectories input/{os.path.basename(self.parameters["offline_trajectories"])}'

        # Execute and monitor
        stdin, stdout, stderr = self.ssh.exec_command(cmd, get_pty=True)

        # Print real-time output
        while self.ssh.get_transport().is_active():
            if select([stdout.channel], [], [], 0.1)[0]:
                line = stdout.readline()
                if not line:
                    break
                print(line.strip())

        # Check exit status
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode()
            raise RuntimeError(f"Tracking failed with error: {error}")

    def retrieve_results(self):
        """Download the tracking result (.trk) from the remote server"""
        self.local_results.mkdir(exist_ok=True)
        remote_path = f'{self.remote_workspace}/output/{self.output_filename}'
        local_path = self.local_results / self.output_filename
        self.scp.get(remote_path, local_path=str(local_path))
        return local_path

    def cleanup(self):
        """Remove remote input/output files to keep HPC workspace clean"""
        if not self.ssh:
            return
        try:
            # Remove everything we uploaded
            remote_input_dir = f'{self.remote_workspace}/input'
            input_files = ' '.join(
                f'{remote_input_dir}/{os.path.basename(val)}'
                for val in self.parameters.values() if val
            )
            self.execute_command(f'rm -f {input_files}')

            # Remove the output .trk
            self.execute_command(
                f'rm -f {self.remote_workspace}/output/{self.output_filename}'
            )

        except Exception as e:
            self._log_error(f"Cleanup failed: {e}")

    def execute_command(self, command):
        """Helper to run a remote command and check for errors."""
        stdin, stdout, stderr = self.ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        if exit_status != 0:
            error = stderr.read().decode()
            raise RuntimeError(f"Command failed: {command}\nError: {error}")
        
    def visualizeTrk(self):
        """
        Convert a .trk file to .vtk format for visualization in Slicer 3D.
        
        Parameters:
            trk_path (str): Path to the input .trk file.
            output_dir (str): Directory to save the output .vtk file.
        
        Returns:
            output_vtk_path (str): Path of the converted .vtk file.
        """
        
        trk_path = "/Users/mahir/Desktop/MTP/TractRLFormer/Output/trk_trlf_1739181068.trk"

        # Check if input TRK file exists
        if not os.path.exists(trk_path):
            print(f"[ERROR] .trk file not found: {trk_path}")
            return None

        output_dir = self.parameters['output_dir']
        # Create output directory if not exists
        os.makedirs(output_dir, exist_ok=True)

        # Load the .trk file
        print(f"[INFO] Loading .trk file from: {trk_path}")
        try:
            tractogram = load_tractogram(trk_path, reference='same', bbox_valid_check=False, to_space=Space.RASMM)

            # Define output VTK file path
            output_vtk_path = os.path.join(output_dir, os.path.basename(trk_path).replace(".trk", ".vtk"))

            # Convert streamlines to VTK format
            self._saveStreamlinesVTK(tractogram.streamlines, output_vtk_path)

            # Load the VTK file into Slicer
            reader = vtkPolyDataReader()
            reader.SetFileName(output_vtk_path)
            reader.Update()

            polydata = reader.GetOutput()

            # Create visualization node
            streamline_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelNode")
            streamline_node.SetAndObservePolyData(polydata)

            display_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLModelDisplayNode")
            streamline_node.SetAndObserveDisplayNodeID(display_node.GetID())

            display_node.SetColor(0, 1, 0)  
            display_node.SetOpacity(1.0)

            slicer.app.applicationLogic().GetSelectionNode().SetReferenceActiveVolumeID(streamline_node.GetID())
            slicer.app.applicationLogic().PropagateVolumeSelection()
            slicer.app.layoutManager().resetThreeDViews()

            print(f"[INFO] Visualization complete. VTK saved at: {output_vtk_path}")

            return output_vtk_path

        except Exception as e:
            print(f"[ERROR] Conversion failed: {e}")
            return None

    def _saveStreamlinesVTK(self, streamlines, output_vtk_path):
        """
        Save streamlines in .vtk format.
        """

        polydata = vtk.vtkPolyData()
        lines = vtk.vtkCellArray()
        points = vtk.vtkPoints()

        ptCtr = 0

        for i, streamline in enumerate(streamlines):
            if (i % 10000) == 0:
                print(f"Processing streamline {i}/{len(streamlines)}")

            line = vtk.vtkLine()
            line.GetPointIds().SetNumberOfIds(len(streamline))

            for j, point in enumerate(streamline):
                points.InsertNextPoint(point)
                line.GetPointIds().SetId(j, ptCtr)
                ptCtr += 1

            lines.InsertNextCell(line)

        polydata.SetLines(lines)
        polydata.SetPoints(points)

        writer = vtk.vtkPolyDataWriter()
        writer.SetFileName(output_vtk_path)
        writer.SetInputData(polydata)
        writer.Write()

        print(f"[INFO] Wrote streamlines to: {output_vtk_path}")