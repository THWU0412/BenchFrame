import paramiko
import threading
import time
from datetime import datetime
import os
from src.diagram import plot_cleaned_data, generate_diagrams_thesis
from src.measure import measure, clean_results
import subprocess
from src.util import logger, config
from src.granularity import run_granularity_tests

def run_script(run, host=None, username=None, key_path=None):
    print(f"Running {run[0]} on local host...")
    logger.info(f"Running {run[0]} on local host...")
    # Make the script executable
    script_path = f"{config['host']['EXEC_PATH'].rstrip('/')}/{run[1]}"
    os.chmod(script_path, 0o755)
    args = [config['remote']['REMOTE_USER'], config['remote']['REMOTE_HOST'], config['remote']['REMOTE_SSH_KEY']]
    process = subprocess.Popen(['bash', script_path] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    print(f"Started script with PID: {process.pid}")
    logger.info(f"Started script with PID: {process.pid}")
    process.wait()
    stdout, stderr = process.communicate()
    logger.info(f"Script output: {stdout}")
    logger.error(f"Script error: {stderr}")

def generate_diagrams(results_dir):
    for file in os.listdir(os.path.join(results_dir, "cleaned/")):
        if file.endswith(".csv"):
            csv_path = os.path.join(results_dir, "cleaned/", file)
            output_path = os.path.join(results_dir, "cleaned/", f"{os.path.splitext(file)[0]}.pdf")
            print(f"Generating diagrams for {csv_path}...")
            plot_cleaned_data(csv_path, output_path)

def run_benchmark(run, timestamp):
    stop_event = threading.Event()
    logger_thread = threading.Thread(target=measure, args=(stop_event, run[0], timestamp))
    logger_thread.start()
    try:
        run_script(run)
    finally:
        stop_event.set()
        logger_thread.join()
        time.sleep(5)

if __name__ == "__main__":
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    results_dir = f"results/{timestamp}/"
    os.makedirs(results_dir, exist_ok=True)

    # Ensure tmp directory exists
    os.makedirs("tmp/", exist_ok=True)
    
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
            # time.sleep(10)
        else:
            continue
        
    clean_results(results_dir)
    generate_diagrams(results_dir)
    # generate_diagrams_thesis(results_dir)
    run_granularity_tests()
