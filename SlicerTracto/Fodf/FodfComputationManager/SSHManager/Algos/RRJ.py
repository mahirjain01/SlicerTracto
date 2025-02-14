import os
import time
import paramiko
from pathlib import Path
from scp import SCPClient
from select import select


# DEFAULT_REMOTE_SCRIPT = "/neuro/DL_Code_1/process_script.py"
DEFAULT_LOCAL_INPUT_DIR = "./local_input/"
DEFAULT_LOCAL_OUTPUT_DIR = "./local_output/"
# DEFAULT_REMOTE_INPUT_DIR = "/neuro/DL_Code_1/Input/"
# DEFAULT_REMOTE_OUTPUT_DIR = "/neuro/DL_Code_1/Pred_data/"

class RemoteProcessing:
    def __init__(self):
        self.ssh = None
        self.scp = None

        # SSH Configuration (should be moved to config file in production)
        self.ssh_config = {
            'hostname': '172.18.40.12',
            'username': 'turing',
            'key_filename': os.path.expanduser('~/.ssh/id_rsa'),  
            'timeout': 30
        }
        self.remote_workspace = '/neuro/DL_Code_1'
        self.conda_env = 'project_3_7'
        self.local_results = Path('./results')

    def _initialize_parameters(self):
        """Initialize all input parameters with default empty values"""
        self.parameters = {
            'dwiSH1K': '',
            'brain_mask': '',
            'output_dir': ''
        }

    def setDwiPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['dwiSH1K'] = str(path)

    def setBrainMaskPath(self, path):
        if self._validate_path(path, ['.nii', '.nii.gz']):
            self.parameters['brain_mask'] = str(path)
    
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
            self.execute()
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

    def transfer_files(self):
        """Transfer all required input files to the remote server"""
        remote_input_dir = f'{self.remote_workspace}/input'

        # Create remote directories
        self.execute_command(f'mkdir -p {remote_input_dir}')
        self.execute_command(f'mkdir -p {self.remote_workspace}/output')

        # Transfer each relevant file, but **skip empty paths**
        for key in [
            'dwiSH1K', 'brain_mask'
        ]:
            local_path = self.parameters[key]

            if not local_path:  # **SKIP EMPTY PATHS**
                continue

            remote_path = f'{remote_input_dir}/{os.path.basename(local_path)}'
            self.scp.put(local_path, remote_path)
    
    def execute(self):
        """Execute the tracking command on the remote server"""

        # Generate unique output filename
        timestamp = int(time.time())
        self.output_filename = f'trk_trlf_{timestamp}.trk'

        # Build base command
        cmd = (
            f'source ~/anaconda3/etc/profile.d/conda.sh && '
            f'conda activate {self.conda_env} && '
            f"cd {self.remote_workspace} && "
            f"python generation.py "
            f'--trlf_model_load_path input/{os.path.basename(self.parameters["trlf_model_load_path"])} '
            f'--input_fodf_signal input/{os.path.basename(self.parameters["input_fodf_signal"])} '
            f'--seeding_mask input/{os.path.basename(self.parameters["seeding_mask"])} '
            f'--tracking_mask input/{os.path.basename(self.parameters["tracking_mask"])} '
            f'--bundle_mask input/{os.path.basename(self.parameters["bundle_mask"])} '
            f'--peaks input/{os.path.basename(self.parameters["peaks"])} '
            f'--reference_file_fa input/{os.path.basename(self.parameters["reference_file_fa"])} '
            f'--save_trk_path output/{self.output_filename}'
        )

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
    
    def close_connection(self):
        if self.scp:
            self.scp.close()
        if self.ssh:
            self.ssh.close()
    
    def execute_pipeline(self):
        try:
            self.connect()
            self.transfer_files()
            self.run_remote_script()
            self.retrieve_files()
            self.clean_remote()
        finally:
            self.close_connection()



if __name__ == "__main__":
    processor = RemoteProcessing()
    processor.execute_pipeline()
