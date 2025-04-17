import paramiko
import threading
import time
import csv
from datetime import datetime
from Netio import Netio
import os


def log_data(stop_event, filename):
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    csv_file = f"results/{filename}_{timestamp_str}.csv"

    n = Netio("http://192.168.1.78/netio.json", auth_rw=("admin", "password"))

    headers = [
        "timestamp",
        "Node3-1_Current", "Node3-1_PowerFactor", "Node3-1_Load", "Node3-1_Energy",
        "Node3-2_Current", "Node3-2_PowerFactor", "Node3-2_Load", "Node3-2_Energy"
    ]

    # This is every 100ms
    poll_interval = 0.1

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        if f.tell() == 0:
            writer.writerow(headers)

        while not stop_event.is_set():
            timestamp = datetime.now().isoformat()
            outputs = n.get_outputs()

            out1 = next((o for o in outputs if o.ID == 1), None)
            out2 = next((o for o in outputs if o.ID == 2), None)

            if out1 and out2:
                writer.writerow([
                    timestamp,
                    out1.Current, out1.PowerFactor, out1.Load, out1.Energy,
                    out2.Current, out2.PowerFactor, out2.Load, out2.Energy
                ])
                f.flush()

            time.sleep(poll_interval)


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
    remote_host = "192.168.155.2"
    remote_user = "cloud_controller_twuttge"
    ssh_key = "/home/twuttge/.ssh/id_rsa_continuum"

    test_runs = [("simultaneous", "scripts/simultaneous.sh"), ("sequential", "scripts/sequential.sh")]

    for run in test_runs:
        stop_event = threading.Event()
        logger_thread = threading.Thread(target=log_data, args=(stop_event, run[0]))
        logger_thread.start()
        try:
            print("------- Start Run -------")
            run_remote_script(remote_host, remote_user, ssh_key, run)
        finally:
            stop_event.set()
            logger_thread.join()
            print(f"------- Done running -------")
            time.sleep(5)
