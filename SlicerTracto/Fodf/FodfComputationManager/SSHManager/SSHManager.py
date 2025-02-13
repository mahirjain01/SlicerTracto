import paramiko
import os
import logging
from FodfComputationManager.SSHManager import configuration
from scp import SCPClient
from paramiko import SFTPClient
import time
from FodfComputationManager.baseManager import BaseManager

class SSHManager(BaseManager):
    def __init__(self):
        """Establish the SSH connection."""
        self.hostname = configuration.hostname
        self.port = configuration.port
        self.username = configuration.username
        self.private_key_path = configuration.private_key_path  # Add private key folder path from config
        self.private_key = None
        self.client = None
        self.ssh_status = False
        self.algoFolderPath = os.path.join(os.path.dirname(__file__), "Algos")
        self.remoteFolder = "/scratch/mahirj.scee.iitmandi/Gagan/SlicerTracto/Fodf"
        self.remoteScriptsFolder = self.remoteFolder+"/Scripts"
        self.remoteInputFolder = self.remoteFolder+"/Input"
        self.remoteOutputFolder = self.remoteFolder+"/Output"
        self.localOutputFolder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Output")
        self.conda_env = "slicer_env"
        # self.connect()  # Optionally, you can call connect here if needed

    def connect(self):
        """Establish the SSH connection."""
        try:
            # Create an SSH client
            self.ssh_client = paramiko.SSHClient()
            self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # Automatically accept unknown host keys

            # Load the private key for authentication
            private_key = paramiko.Ed25519Key.from_private_key_file(self.private_key_path)  # Replace with RSAKey if using RSA

            # Use private key authentication

            self.ssh_client.connect(self.hostname, port=self.port, username=self.username, pkey=private_key)

            self.ssh_status = True
            logging.info(f"SSH connection established to {self.hostname}")
            print(f"[SLICER TRACTO]SSH connection established to {self.hostname}")
        except Exception as e:
            self.ssh_status = False
            logging.error(f"Failed to connect to {self.hostname}: {e}")

    def get_connection_status(self):
        """Return the connection status."""
        return self.ssh_status

    def close(self):
        """Close the SSH connection."""
        if self.client:
            self.client.close()
            self.ssh_status = False
            logging.info(f"SSH connection to {self.hostname} closed.")
        else:
            logging.error("No active SSH connection to close.")

    def upload_file(self, local_path, remote_path):
        try:
            sftp = self.ssh_client.open_sftp()
            sftp.put(local_path, remote_path)
            sftp.close()
            print(f"[SLICER TRACTO]File uploaded successfully to {remote_path}")
        except Exception as e:
            print(f"[SLICER TRACTO]Error during upload: {e}")

    def download_file(self, local_path, remote_path):
        try:
            scp = SCPClient(self.ssh_client.get_transport())
            scp.get(remote_path, local_path)
            scp.close()
            print(f"[SLICER TRACTO]File downloaded successfully to {local_path}")
        except Exception as e:
            print(f"[SLICER TRACTO]Error during download: {e}")
    
    def run_file(self, remote_path):
        try:
            # Activate conda environment if specified
            conda_command = f"conda activate {self.conda_env} && " if self.conda_env else ""
            command = f"{conda_command}python3 {remote_path}"
            stdin, stdout, stderr = self.ssh_client.exec_command(command)

            # Print the output of the script execution
            for line in stdout:
                print("[SLICER TRACTO]" + line.strip())
            # Print any errors encountered during execution
            for line in stderr:
                print(f"[SLICER TRACTO]Error: {line.strip()}")
            # Ensure the script execution is complete
            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                print(f"[SLICER TRACTO]Script executed successfully.")
            else:
                print(f"[SLICER TRACTO]Script execution failed with exit status {exit_status}.")
        except Exception as e:
            print(f"[SLICER TRACTO]Error during script execution: {e}")

    def execute(self, subjectName, algo, inputFolderPath, outputFolderPath):
        start_time = time.time()  # Start the timer at the beginning of the function
        self.connect()
        # Remote paths
        # Execute algorithm if 'algo1' is selected
        if algo == 'Scilpy':
            
            diffusionPath, whiteMaskPath, bvalPath, bvecPath = self.getFodfInputs(folderPath=inputFolderPath)
            
            remoteDiffusionPath = self.remoteInputFolder + "/sample_dwi.nii"
            remoteWhiteMaskPath= self.remoteInputFolder + "/sample_wm.nii"
            remoteBvalPath= self.remoteInputFolder + "/sample.bval"
            remoteBvecPath= self.remoteInputFolder + "/sample.bvec"

            print("Uploading Diffusion File...")
            upload_start_time = time.time()
            self.upload_file(local_path=diffusionPath, remote_path=remoteDiffusionPath)
            upload_end_time = time.time()
            print(f"Time taken to upload Diffusion File: {upload_end_time - upload_start_time:.2f} seconds")
            
            print("Uploading White Matter Mask...")
            upload_start_time = time.time()
            self.upload_file(local_path=whiteMaskPath, remote_path=remoteWhiteMaskPath)
            upload_end_time = time.time()
            print(f"Time taken to upload White Matter Mask: {upload_end_time - upload_start_time:.2f} seconds")
            
            print("Uploading Bval File...")
            upload_start_time = time.time()
            self.upload_file(local_path=bvalPath, remote_path=remoteBvalPath)
            upload_end_time = time.time()
            print(f"Time taken to upload Bval File: {upload_end_time - upload_start_time:.2f} seconds")
            
            print("Uploading Bvec File...")
            upload_start_time = time.time()
            self.upload_file(local_path=bvecPath, remote_path=remoteBvecPath)
            upload_end_time = time.time()
            print(f"Time taken to upload Bvec File: {upload_end_time - upload_start_time:.2f} seconds")

            localAlgoPath = os.path.join(self.algoFolderPath, "generateFodf.py")
            remoteAlgoPath = self.remoteScriptsFolder + "/generateFodf.py"
            
            print("Uploading algorithm script...")
            upload_start_time = time.time()
            self.upload_file(local_path=localAlgoPath, remote_path=remoteAlgoPath)
            upload_end_time = time.time()
            print(f"Time taken to upload algorithm script: {upload_end_time - upload_start_time:.2f} seconds")

            print("Running algorithm script...")
            run_start_time = time.time()
            self.run_file(remote_path=remoteAlgoPath)
            run_end_time = time.time()
            print(f"Time taken to execute algorithm: {run_end_time - run_start_time:.2f} seconds")
        
        # Define paths for seeding mask and trk files
        localFodfFilePath = os.path.join(outputFolderPath, f"{subjectName}_fodf.nii")
        remoteFodfFilePath = self.remoteOutputFolder + "/sample_fodf.nii"

        # Download Seeding Mask
        print("Downloading FODF...")
        download_start_time = time.time()
        self.download_file(local_path=localFodfFilePath, remote_path=remoteFodfFilePath)
        download_end_time = time.time()
        print(f"Time taken to download FODF: {download_end_time - download_start_time:.2f} seconds")

        # Print total time taken for the entire process
        end_time = time.time()
        print(f"Total time taken: {end_time - start_time:.2f} seconds")
