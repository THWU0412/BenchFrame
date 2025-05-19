import paramiko
import threading
import time
from datetime import datetime
import os
from src.diagram import plot_diagrams, plot_avg_cpu_usage, plot_all_cpus, plot_memory_usage
from src.measure import measure, write_labels
import subprocess

# Configuration for remote host
REMOTE_HOST = "192.168.1.109"
REMOTE_USER = "twuttge"
REMOTE_SSH_KEY = "/home/twuttge/.ssh/atlarge"

# Configuration for VM
VM_HOST = "192.168.155.2"
VM_USER = "cloud_controller_twuttge"
VM_SSH_KEY = "/home/twuttge/.ssh/id_rsa_continuum"

# Run with:
# python -c 'from main import run_script; run_script("node9", "twuttge", "/home/twuttge/.ssh/atlarge", ["idle_benchmark"]);'
def run_script(run, host=None, username=None, key_path=None):
    if host and username and key_path:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
        ssh.connect(hostname=host, username=username, key_filename=key_path)
        script_path = f"/home/{username}/tmp/{run[0]}.sh"
        ssh.exec_command(f"chmod +x {script_path}")
        stdin, stdout, stderr = ssh.exec_command(f"bash {script_path}")
        stdout.channel.recv_exit_status()
        print("Finished remote shit")
        print("Output:", stdout.read().decode())
        print("Error:", stderr.read().decode())
        output = stdout.read().decode()
        times_str = [line for line in output.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')
        times_dt = [datetime.strptime(item.strip(), '%a %b %d %I:%M:%S %p %Z %Y') for item in times_str]
        ssh.close()
    else:
        print(f"Running {run[0]} on local host...")
        # Make the script executable
        script_path = f"/home/twuttge/thesis/benchmark/{run[1]}"
        os.chmod(script_path, 0o755)
        process = subprocess.Popen(['bash', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Started script with PID: {process.pid}")
        process.wait()
        stdout, stderr = process.communicate()
        times_str = [line for line in stdout.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')
        times_dt = [datetime.strptime(item.strip(), '%a %b %d %I:%M:%S %p %Z %Y') for item in times_str]
    return times_dt

def run_remote_vm_script(host, username, key_path, run):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, key_filename=key_path)

    script_path = f"/home/cloud_controller_twuttge/scripts/{run[0]}.sh"
    ssh.exec_command(f"chmod +x {script_path}")
    
    print(f"Running {run[0]} on remote host...")
    stdin, stdout, stderr = ssh.exec_command(f"bash {script_path}")
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    ssh.close()
    return [line for line in output.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')

# Run with:
# python -c 'from main import upload_scripts; upload_scripts()'
def upload_script(script_path):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=REMOTE_HOST, username=REMOTE_USER, key_filename=REMOTE_SSH_KEY)

    sftp = ssh.open_sftp()
    remote_dir = f'/home/{REMOTE_USER}/tmp/'

    try:
        sftp.mkdir(remote_dir)
    except IOError:
        print(f"Remote directory {remote_dir} already exists.")

    local_path = os.path.join('.', script_path)
    remote_path = os.path.join(remote_dir, script_path.split('/')[-1])
    if os.path.isfile(local_path):
        sftp.put(local_path, remote_path)
    
    sftp.close()
    ssh.close()
    
def generate_diagrams(results_dir):
    for csv_file in os.listdir(results_dir):
        if csv_file.endswith(".csv"):
            csv_path = os.path.join(results_dir, csv_file)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_power.png")
            plot_diagrams(csv_path, output_path)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_avg_cpu.png")
            plot_avg_cpu_usage(csv_path, output_path)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_total_cpu.png")
            plot_all_cpus(csv_path, output_path)
            output_path = os.path.join(results_dir, f"{os.path.splitext(csv_file)[0]}_mem.png")
            plot_memory_usage(csv_path, output_path)
            
def run_local_benchmark(run, timestamp):
    stop_event = threading.Event()
    logger_thread = threading.Thread(target=measure, args=(stop_event, run[0], timestamp))
    logger_thread.start()
    try:
        print("------- Start Run -------")
        print(f"Running host test {run[0]}...")
        # label_times = run_remote_vm_script(VM_HOST, VM_USER, VM_SSH_KEY, run)
        label_times = run_script(run)
    finally:
        stop_event.set()
        logger_thread.join()
        print(f"------- Finished Run -------")
        # write_labels(label_times, run[0], timestamp)
        time.sleep(5)

def run_remote_benchmark(run, timestamp):
    if "local" in run[0]:
        print(f"Running local test {run[0]}...")
        stop_event = threading.Event()
        logger_thread = threading.Thread(target=measure, args=(stop_event, run[0], timestamp))
        logger_thread.start()
        try:
            label_times = run_script(run)
        finally:
            stop_event.set()
            logger_thread.join()
            print(f"------- Finished Run -------")
            # write_labels(label_times, folder_item)
            time.sleep(5)

    elif "remote" in run[0]:
        print(f"Running remote test {run[0]}...")
        upload_script(run[1])
        
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(os.path.expanduser("~/.ssh/known_hosts"))
        ssh.connect(REMOTE_HOST, username=REMOTE_USER, key_filename=REMOTE_SSH_KEY)
        
        session_name = "measure"
        command = (
            f"tmux new-session -d -s {session_name} "
            f"'cd /home/twuttge/thesis/continuum_energy_benchmark && "
            f"sudo HOME=/home/twuttge/ VIRTUAL_ENV=\"/home/twuttge/continuum_energy_benchmark/venv\" "
            f"python3 -c \"from remote_src.measure import measure; measure(\\\"test\\\", \\\"test\\\")\"'"
        )

        stdin, stdout, stderr = ssh.exec_command(command)
        # print("Output:", stdout.read().decode())
        # print("Error:", stderr.read().decode())
        
        try:
            label_times = run_script(run, REMOTE_HOST, REMOTE_USER, REMOTE_SSH_KEY)
        finally:
            ssh.exec_command("tmux kill-session -t measure")
            ssh.close()
            # write_labels(label_times, folder_item)
            time.sleep(5)
    else:
        return

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = f"results/{timestamp}/"
    os.makedirs(results_dir, exist_ok=True)
    # upload_scripts()

    for folder_item in os.listdir('scripts/'):
        if folder_item.endswith(".sh"):
            run = (os.path.splitext(folder_item)[0], f"scripts/{folder_item}")
            run_local_benchmark(run, timestamp)
        elif os.path.isdir(os.path.join('scripts/', folder_item)):
            # TODO: Fix that shit!
            continue
            print("------- Start Connection Benchmark -------")
            runs = []
            for item in os.listdir(os.path.join('scripts/', folder_item)):
                if item.endswith(".sh"):
                    runs.append((os.path.splitext(item)[0], f"scripts/{folder_item}/{item}"))
                else:
                    continue
            runs.sort(key=lambda x: x[0])
            processes = []
            for run in runs:
                # Start each benchmark as a subprocess
                p = subprocess.Popen(
                    ["python3", "-c", f"from main import run_remote_benchmark; run_remote_benchmark({run!r}, '{timestamp}')"]
                )
                processes.append(p)
            # Wait for all subprocesses to finish
            for p in processes:
                p.wait()
            print("------- Finished Connection Benchmark -------")
        else:
            continue
    generate_diagrams(results_dir)