import csv
import time
import pandas as pd
from datetime import datetime
from Netio import Netio
import pyipmi
import psutil
import pyipmi.interfaces
import os
from src.util import config, logger

# TODO: Fix that shit!
# Run with:
# python -c 'from src.measure import write_labels; print(write_labels([], "sequential", "2025-04-30_14-42-03"));'
def write_labels(label_times, filename, timestamp):
    df = pd.read_csv(f"results/{timestamp}/{filename}.csv")
    df["label"] = df["timestamp"].apply(lambda x: "create" if x < label_times[0] else "destroy")
    df.to_csv(f"results/{timestamp}/{filename}.csv", index=False)

# Run with:
# sudo -E python3 -c 'from src.measure import measure; measure(None, "test", "test");'
def measure(stop_event, filename, timestamp):
    csv_file = f"results/{timestamp}/{filename}.csv"

    num_cpu = psutil.cpu_count(logical=True)
    rapl_sockets = len([name for name in os.listdir('/sys/class/powercap') if name.startswith('intel-rapl') and ':' in name and name.count(':') == 1])
    
    headers = [
        "timestamp",
        # PDU data
        "PDU-L_Current", "PDU-L_PowerFactor", "PDU-L_Load", "PDU-L_Energy",
        "PDU-R_Current", "PDU-R_PowerFactor", "PDU-R_Load", "PDU-R_Energy",
        # IPMI data
        "IPMI_Current", "IPMI_State", 
        # Memory data
        "Memory_Usage"
    ]
    # INTEL-RAPL data
    for i in range(rapl_sockets):
        headers.append(f"INTEL-RAPL{i}_CPU")
        headers.append(f"INTEL-RAPL{i}_MEM")
    # CPU data
    headers += [f"CPU{i+1}" for i in range(num_cpu)]

    poll_interval = 0.1

    PDU_L, PDU_R = setup_PDU()
    ipmi = setup_IPMI()

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(headers)

        while not stop_event.is_set():
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            data_PDU = read_PDU(PDU_L, PDU_R)
            data_IPMI = read_IPMI(ipmi)
            data_MEM = psutil.virtual_memory()
            data_CPU = psutil.cpu_percent(interval=poll_interval, percpu=True)
            data_RAPL = read_rapl(rapl_sockets)
            if data_PDU is None or data_IPMI is None or data_RAPL is None:
                continue
            row = [
                timestamp,
                # PDU data
                data_PDU['PDU-L_Current'], data_PDU['PDU-L_PowerFactor'], data_PDU['PDU-L_Load'], data_PDU['PDU-L_Energy'],
                data_PDU['PDU-R_Current'], data_PDU['PDU-R_PowerFactor'], data_PDU['PDU-R_Load'], data_PDU['PDU-R_Energy'],
                # IPMI data
                data_IPMI['current'], data_IPMI['state'], 
                # Memory, battery, and CPU data
                data_MEM.percent
            ]
            # INTEL-RAPL data
            row.extend(data_RAPL)
            # CPU data
            row.extend(data_CPU)
            writer.writerow(row)
            f.flush()
            
def read_rapl(sockets):
    data_rapl = []
    for socket in range(sockets):
        socket_paths = [f"/sys/class/powercap/intel-rapl:{socket}/energy_uj",
                        f"/sys/class/powercap/intel-rapl:{socket}:0/energy_uj"]
        try:
            with open(socket_paths[0], 'r') as file:
                data_rapl.append(int(file.read().strip()))
            with open(socket_paths[1], 'r') as file:
                data_rapl.append(int(file.read().strip()))
        except Exception as e:
            logger.error(f"Error reading RAPL data from {socket}: {e}")
            return None
    return data_rapl


def setup_PDU():
    PDU_L = Netio(config['host']['NETIO_IP_L'], auth_rw=config['host']['NETIO_AUTH'])
    PDU_R = Netio(config['host']['NETIO_IP_R'], auth_rw=config['host']['NETIO_AUTH'])
    return PDU_L, PDU_R

# Run with:
# python -c 'from src.measure import setup_PDU, read_PDU; PDU_L, PDU_R = setup_PDU(); print(read_PDU(PDU_L, PDU_R));'
def read_PDU(PDU_L, PDU_R):
    
    output_L = PDU_L.get_output(int(config['host']['PDU_NODE_ID']))
    output_R = PDU_R.get_output(int(config['host']['PDU_NODE_ID']))

    return {
        'PDU-L_Current': output_L.Current,            # In mA
        'PDU-L_PowerFactor': output_L.PowerFactor,    # True Power Factor
        'PDU-L_Load': output_L.Load,                  # In Watts
        'PDU-L_Energy': output_L.Energy,              # In Wh
        'PDU-R_Current': output_R.Current,            # In In mA
        'PDU-R_PowerFactor': output_R.PowerFactor,    # True Power Factor
        'PDU-R_Load': output_R.Load,                  # In Watts
        'PDU-R_Energy': output_R.Energy               # In Wh
    }

def setup_IPMI():
    interface = pyipmi.interfaces.create_interface('ipmitool', interface_type='lan')

    ipmi = pyipmi.create_connection(interface)
    
    ipmi.target = pyipmi.Target(ipmb_address=0x20)
    ipmi.session.set_session_type_rmcp(config['host']['IPMI_IP'])
    ipmi.session.set_auth_type_user(config['host']['IPMI_AUTH'][0], config['host']['IPMI_AUTH'][1])
    ipmi.session.establish()
    return ipmi

# Run with:
# python -c 'from src.measure import read_IPMI, setup_IPMI; ipmi = setup_IPMI(); print(read_IPMI(ipmi));'
# Allowed IPMI commands:
# ipmitool -H 192.168.1.209 sensor -U atlstudent -P 56iPmIuSeR -L USER
# ipmitool -H 192.168.1.203 dcmi power reading -U atlstudent -P 56iPmIuSeR -L ADMINISTRATOR
def read_IPMI(ipmi):
    try:
        power_reading = ipmi.get_power_reading(1)
    except Exception as e:
        logger.error(f"Error reading IPMI power data: {e}")
        return None

    return {
        'current': power_reading.current_power, # In Watts
        'minimum': power_reading.minimum_power, # In Watts
        'maximum': power_reading.maximum_power, # In Watts
        'average': power_reading.average_power, # In Watts
        'timestamp': datetime.fromtimestamp(power_reading.timestamp),
        'period': round(power_reading.period / 86400000, 2), # Convert ms to days
        'state': power_reading.reading_state
    }