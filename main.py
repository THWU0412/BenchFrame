import paramiko
import threading
import time
from datetime import datetime
import os
from src.diagram import plot_diagrams, plot_avg_cpu_usage, plot_all_cpus
from src.measure import write_csv, write_labels

REMOTE_HOST = "192.168.155.2"
REMOTE_USER = "cloud_controller_twuttge"
SSH_KEY = "/home/twuttge/.ssh/id_rsa_continuum"

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
    output = stdout.read().decode()
    ssh.close()
    return [line for line in output.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')


if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = f"results/{timestamp}/"
    os.makedirs(results_dir, exist_ok=True)

    for file in os.listdir('scripts/'):
        if file.endswith(".sh"):
            run = (os.path.splitext(file)[0], f"scripts/{file}")
        stop_event = threading.Event()
        logger_thread = threading.Thread(target=write_csv, args=(stop_event, run[0], timestamp))
        logger_thread.start()
        try:
            print("------- Start Run -------")
            label_times = run_remote_script(REMOTE_HOST, REMOTE_USER, SSH_KEY, run)
        finally:
            stop_event.set()
            logger_thread.join()
            print(f"------- Finished Run -------")
            print(f"Label times: {label_times}")
            write_labels(label_times, run[0], timestamp)
            time.sleep(5)

    for csv_file in os.listdir(results_dir):
        if csv_file.endswith(".csv"):
            csv_path = os.path.join(results_dir, csv_file)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_diagrams.png")
            plot_diagrams(csv_path, output_path)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_avg_cpu_usage.png")
            plot_avg_cpu_usage(csv_path, output_path)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_total_cpu_usage.png")
            plot_all_cpus(csv_path, output_path)