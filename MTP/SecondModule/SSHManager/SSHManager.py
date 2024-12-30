import paramiko
import os
import logging
from SSHManager import configuration
from SSHManager.Algos import algo1
from FileManager.FileManager import FileManager
from scp import SCPClient
from paramiko import SFTPClient
import time

class SSHManager:
    def __init__(self):
        """Establish the SSH connection."""
        self.hostname = configuration.hostname
        self.port = configuration.port
        self.username = configuration.username
        self.private_key_path = configuration.private_key_path  # Add private key folder path from config
        self.private_key = None
        self.client = None
        self.ssh_status = False
        self.fileManager = FileManager()
        self.algoFolderPath = os.path.join(os.path.dirname(__file__), "Algos")
        self.remoteFolder = "/scratch/mahirj.scee.iitmandi/Gagan/SlicerTracto"
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
            print(f"[SLICER TRACTO]Hostname: {self.hostname}")
            print(f"[SLICER TRACTO]Port: {self.port}")
            print(f"[SLICER TRACTO]username: {self.username}")

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

    def execute(self, subjectName, algo, approxMaskPathFilePath, fodfFilePath):
        start_time = time.time()  # Start the timer at the beginning of the function
        self.connect()

        # Remote paths
        remoteFodfFilePath = self.remoteInputFolder + "/sample_fodf.nii"
        remoteApproxMaskPathFilePath = self.remoteInputFolder + "/sample_approx_mask.nii"

        # Upload FODF file
        print("Uploading FODF file...")
        upload_start_time = time.time()
        # self.upload_file(local_path=fodfFilePath, remote_path=remoteFodfFilePath)
        upload_end_time = time.time()
        print(f"Time taken to upload FODF file: {upload_end_time - upload_start_time:.2f} seconds")

        # Upload Approximate Mask file
        print("Uploading Approximate Mask file...")
        upload_start_time = time.time()
        # self.upload_file(local_path=approxMaskPathFilePath, remote_path=remoteApproxMaskPathFilePath)
        upload_end_time = time.time()
        print(f"Time taken to upload Approximate Mask file: {upload_end_time - upload_start_time:.2f} seconds")

        # Execute algorithm if 'algo1' is selected
        if algo == 'algo1':
            localAlgoPath = os.path.join(self.algoFolderPath, "algo1.py")
            remoteAlgoPath = self.remoteScriptsFolder + "/script.py"
            
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
        localSeddingMaskPath = os.path.join(self.localOutputFolder, "SeedingMask", f"{subjectName}_seeding_mask.nii")
        localTrkPath = os.path.join(self.localOutputFolder, "SeedingMask", f"{subjectName}_trk.trk")
        remoteSeddingMaskPath = self.remoteOutputFolder + "/sample_seeding_mask.nii"
        remoteTrkPath = self.remoteOutputFolder + "/sample_trk.trk"

        # Download Seeding Mask
        print("Downloading Seeding Mask...")
        download_start_time = time.time()
        self.download_file(local_path=localSeddingMaskPath, remote_path=remoteSeddingMaskPath)
        download_end_time = time.time()
        print(f"Time taken to download Seeding Mask: {download_end_time - download_start_time:.2f} seconds")

        # Download TRK file
        print("Downloading TRK file...")
        download_start_time = time.time()
        self.download_file(local_path=localTrkPath, remote_path=remoteTrkPath)
        download_end_time = time.time()
        print(f"Time taken to download TRK file: {download_end_time - download_start_time:.2f} seconds")

        # Print total time taken for the entire process
        end_time = time.time()
        print(f"Total time taken: {end_time - start_time:.2f} seconds")


    # def execute(self, subjectName, algo, approxMaskPathFilePath, fodfFilePath):
    #     self.connect()
    #     remoteFodfFilePath = self.remoteInputFolder+"/sample_fodf.nii"
    #     remoteApproxMaskPathFilePath = self.remoteInputFolder+"/sample_approx_mask.nii"

    #     self.upload_file(local_path=fodfFilePath, remote_path=remoteFodfFilePath)
    #     self.upload_file(local_path=approxMaskPathFilePath, remote_path=remoteApproxMaskPathFilePath)
    #     if algo == 'algo1':
    #         localAlgoPath = os.path.join(self.algoFolderPath, "algo1.py")
    #         remoteAlgoPath = self.remoteScriptsFolder+"/script.py"
    #         self.upload_file(local_path=localAlgoPath, remote_path=remoteAlgoPath)
    #         self.run_file(remote_path=remoteAlgoPath)

    #     localSeddingMaskPath = os.path.join(self.localOutputFolder, "SeedingMask", "{subjectName}_seeding_mask.nii")
    #     localTrkPath = os.path.join(self.localOutputFolder, "SeedingMask", "{subjectName}_trk.trk")
    #     remoteSeddingMaskPath = self.remoteOutputFolder+"/sample_seeding_mask.nii"
    #     remoteTrkPath = self.remoteOutputFolder+"/sample_trk.nii"

    #     self.download_file(local_path=localSeddingMaskPath, remote_path=remoteSeddingMaskPath)
    #     self.download_file(local_path=localTrkPath, remote_path=remoteTrkPath)
