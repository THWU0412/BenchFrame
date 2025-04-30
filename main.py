import paramiko
import threading
import time
from datetime import datetime
import os
from src.diagram import plot_diagrams
from src.measure import write_csv

def run_remote_script(host, username, key_path, run):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, key_filename=key_path)

    sftp = ssh.open_sftp()

    print(f"Uploading {run[0]} to remote host...")
    script_path = f"/home/cloud_controller_twuttge/{run[0]}.sh"
    sftp.put(os.path.abspath(run[1]), script_path)
    sftp.close()
    
    ssh.exec_command(f"chmod +x {script_path}")
    
    print(f"Running {run[0]} on remote host...")
    stdin, stdout, stderr = ssh.exec_command(f"bash {script_path}")
    stdout.channel.recv_exit_status()
    print(stdout.read().decode())
    ssh.close()


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = f"results/{timestamp}/"
    os.makedirs(results_dir, exist_ok=True)

    remote_host = "192.168.155.2"
    remote_user = "cloud_controller_twuttge"
    ssh_key = "/home/twuttge/.ssh/id_rsa_continuum"

    test_runs = [("simultaneous", "scripts/simultaneous.sh"), ("sequential", "scripts/sequential.sh")]

    for run in test_runs:
        stop_event = threading.Event()
        logger_thread = threading.Thread(target=write_csv, args=(stop_event, run[0], timestamp))
        logger_thread.start()
        try:
            print("------- Start Run -------")
            run_remote_script(remote_host, remote_user, ssh_key, run)
        finally:
            stop_event.set()
            logger_thread.join()
            print(f"------- Done running -------")
            time.sleep(5)

    for csv_file in os.listdir(results_dir):
        if csv_file.endswith(".csv"):
            csv_path = os.path.join(results_dir, csv_file)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_diagrams.png")
            plot_diagrams(csv_path, output_path)
