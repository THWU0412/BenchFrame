import paramiko
import threading
import time
from datetime import datetime
import os
from src.diagram import plot_cleaned_data, plot_diagrams, plot_avg_cpu_usage, plot_all_cpus, plot_memory_usage, plot_rapl, plot_redfish
from src.measure import measure, clean_results
import subprocess
from src.util import logger, config

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
        
        # DEBUG SHIT
        print("Finished remote shit")
        print("Output:", stdout.read().decode())
        print("Error:", stderr.read().decode())
        
        output = stdout.read().decode()
        
        # TODO: Fix that shit!
        # times_str = [line for line in output.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')
        # times_dt = [datetime.strptime(item.strip(), '%a %b %d %I:%M:%S %p %Z %Y') for item in times_str]
        ssh.close()
    else:
        print(f"Running {run[0]} on local host...")
        logger.info(f"Running {run[0]} on local host...")
        # Make the script executable
        script_path = f"/home/twuttge/thesis/continuum_energy_benchmark/{run[1]}"
        os.chmod(script_path, 0o755)
        process = subprocess.Popen(['bash', script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print(f"Started script with PID: {process.pid}")
        logger.info(f"Started script with PID: {process.pid}")
        process.wait()
        stdout, stderr = process.communicate()
        # TODO: Fix that shit!
        # times_str = [line for line in stdout.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')
        # times_dt = [datetime.strptime(item.strip(), '%a %b %d %I:%M:%S %p %Z %Y') for item in times_str]
    # return times_dt

def run_remote_vm_script(host, username, key_path, run):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=host, username=username, key_filename=key_path)

    script_path = f"/home/cloud_controller_twuttge/scripts/{run[0]}.sh"
    ssh.exec_command(f"chmod +x {script_path}")
    
    print(f"Running {run[0]} on remote host...")
    logger.info(f"Running {run[0]} on remote host...")
    stdin, stdout, stderr = ssh.exec_command(f"bash {script_path}")
    stdout.channel.recv_exit_status()
    output = stdout.read().decode()
    ssh.close()
    return [line for line in output.split('\n') if line.startswith('MEASUREMENT_TIMES:')][0].split('(')[1].split(')')[0].split(',')
    
# Run with:
# sudo -E python3 -c 'from main import generate_all_diagrams; generate_all_diagrams("results/2025-08-04_12-46-05/")'
def generate_all_diagrams(results_dir):
    for csv_file in os.listdir(results_dir):
        if csv_file.endswith(".csv"):
            csv_path = os.path.join(results_dir, csv_file)
            output_path = os.path.join(results_dir, "/diagrams/", f"{os.path.splitext(csv_file)[0]}_power.png")
            plot_diagrams(csv_path, output_path)
            output_path = os.path.join(results_dir, "/diagrams/", f"{os.path.splitext(csv_file)[0]}_avg_cpu.png")
            plot_avg_cpu_usage(csv_path, output_path)
            output_path = os.path.join(results_dir, "/diagrams/", f"{os.path.splitext(csv_file)[0]}_total_cpu.png")
            plot_all_cpus(csv_path, output_path)
            output_path = os.path.join(results_dir, "/diagrams/", f"{os.path.splitext(csv_file)[0]}_mem.png")
            plot_memory_usage(csv_path, output_path)
            output_path = os.path.join(results_dir, "/diagrams/", f"{os.path.splitext(csv_file)[0]}_rapl.png")
            plot_rapl(csv_path, output_path)
            output_path = os.path.join(results_dir, "/diagrams/", f"{os.path.splitext(csv_file)[0]}_redfish.png")
            plot_redfish(csv_path, output_path)

# sudo -E python3 -c 'from main import clean_data_and_generate_diagrams; clean_data_and_generate_diagrams("results/2025-08-04_12-46-05/")'
def clean_data_and_generate_diagrams(results_dir):
    clean_results(results_dir)
    for file in os.listdir(os.path.join(results_dir, "cleaned/")):
        if file.endswith(".csv"):
            csv_path = os.path.join(results_dir, "cleaned/", file)
            output_path = os.path.join(results_dir, "cleaned/", f"{os.path.splitext(file)[0]}.png")
            print(f"Generating diagrams for {csv_path}...")
            plot_cleaned_data(csv_path, output_path)
            
def run_benchmark(run, timestamp):
    stop_event = threading.Event()
    logger_thread = threading.Thread(target=measure, args=(stop_event, run[0], timestamp))
    logger_thread.start()
    try:
        # label_times = run_remote_vm_script(config['vm']['VM_HOST'], config['vm']['VM_USER'], config['vm']['VM_SSH_KEY'], run)
        run_script(run)
    finally:
        stop_event.set()
        logger_thread.join()
        # write_labels(label_times, run[0], timestamp)
        time.sleep(5)

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = f"results/{timestamp}/"
    os.makedirs(results_dir, exist_ok=True)
    
    test_counter = 0

    for folder_item in os.listdir('scripts/'):
        if folder_item.endswith(".sh"):
            print(f"------- Start Run ({test_counter+1}/{len([f for f in os.listdir('scripts/') if f.endswith('.sh')])}) -------")
            logger.info(f"------- Start Run ({test_counter+1}/{len([f for f in os.listdir('scripts/') if f.endswith('.sh')])}) -------")
            
            run = (os.path.splitext(folder_item)[0], f"scripts/{folder_item}")
            
            print(f"Running host test {run[0]}...")
            logger.info(f"Running host test {run[0]}...")

            for i in range(int(config['host']['RUN_REPETITIONS'])):
                print(f"Iteration {i+1} of {config['host']['RUN_REPETITIONS']} for {run[0]}")
                logger.info(f"Iteration {i+1} of {config['host']['RUN_REPETITIONS']} for {run[0]}")
                run_benchmark(run, timestamp)
            
            
            print(f"------- Finished Run {test_counter+1} -------")
            logger.info(f"------- Finished Run {test_counter+1} -------")
            
            test_counter += 1
            time.sleep(10)
        else:
            continue
        
    clean_data_and_generate_diagrams(results_dir)
