import csv
import time
import pandas as pd
from datetime import datetime
from Netio import Netio
import pyipmi
import psutil
import pyipmi.interfaces

NETIO_IP_L = "http://192.168.1.78/netio.json"
NETIO_IP_R = "http://192.168.1.79/netio.json"
NETIO_AUTH = ("admin", "password")

IPMI_IP = "192.168.1.203"
IPMI_AUTH = ("atlstudent", "56iPmIuSeR")

# Run with:
# python -c 'from src.measure import write_labels; print(write_labels([], "sequential", "2025-04-30_14-42-03"));'
def write_labels(label_times, filename, timestamp):
    df = pd.read_csv(f"results/{timestamp}/{filename}.csv")
    df["label"] = df["timestamp"].apply(lambda x: "create" if x < label_times[0] else "destroy")
    df.to_csv(f"results/{timestamp}/{filename}.csv", index=False)

# Run with:
# python -c 'from src.measure import write_csv; write_csv(None, "sequential", "2025-04-30_14-42-03");'
def write_csv(stop_event, filename, timestamp):
    csv_file = f"results/{timestamp}/{filename}.csv"

    headers = [
        "timestamp",
        # PDU data
        "Node3-L_Current", "Node3-L_PowerFactor", "Node3-L_Load", "Node3-L_Energy",
        "Node3-R_Current", "Node3-R_PowerFactor", "Node3-R_Load", "Node3-R_Energy",
        # IPMI data
        "IPMI_Timestamp", "IPMI_Current", "IPMI_State", 
        # CPU and Memory data
        "Memory_Usage",
        "CPU1", "CPU2", "CPU3", "CPU4", "CPU5", "CPU6", "CPU7", "CPU8",
        "CPU9", "CPU10", "CPU11", "CPU12", "CPU13", "CPU14", "CPU15", "CPU16", 
        "CPU17", "CPU18", "CPU19", "CPU20"
    ]

    poll_interval = 0.1

    PDU_L, PDU_R = setup_PDU()
    ipmi = setup_IPMI()

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        if f.tell() == 0:
            writer.writerow(headers)

        while not stop_event.is_set():
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            data_PDU = read_PDU(PDU_L, PDU_R)
            data_IPMI = read_IPMI(ipmi)
            data_MEM = psutil.virtual_memory()
            data_CPU = psutil.cpu_percent(interval=poll_interval, percpu=True)
            if data_PDU is None or data_IPMI is None:
                continue
            row = [
                timestamp,
                data_PDU['Node3-L_Current'], data_PDU['Node3-L_PowerFactor'], data_PDU['Node3-L_Load'], data_PDU['Node3-L_Energy'],
                data_PDU['Node3-R_Current'], data_PDU['Node3-R_PowerFactor'], data_PDU['Node3-R_Load'], data_PDU['Node3-R_Energy'],
                data_IPMI['timestamp'], data_IPMI['current'], data_IPMI['state'], data_MEM.percent
            ]
            row.extend(data_CPU)
            writer.writerow(row)
            f.flush()


def setup_PDU():
    PDU_L = Netio(NETIO_IP_L, auth_rw=NETIO_AUTH)
    PDU_R = Netio(NETIO_IP_R, auth_rw=NETIO_AUTH)
    return PDU_L, PDU_R

# Run with:
# python -c 'from src.measure import setup_PDU, read_PDU; PDU_L, PDU_R = setup_PDU(); print(read_PDU(PDU_L, PDU_R));'
def read_PDU(PDU_L, PDU_R):
    
    output_L = PDU_L.get_output(1)
    output_R = PDU_R.get_output(1)

    return {
        'Node3-L_Current': output_L.Current,            # In mA
        'Node3-L_PowerFactor': output_L.PowerFactor,    # True Power Factor
        'Node3-L_Load': output_L.Load,                  # In Watts
        'Node3-L_Energy': output_L.Energy,              # In Wh
        'Node3-R_Current': output_R.Current,            # In In mA
        'Node3-R_PowerFactor': output_R.PowerFactor,    # True Power Factor
        'Node3-R_Load': output_R.Load,                  # In Watts
        'Node3-R_Energy': output_R.Energy               # In Wh
    }

def setup_IPMI():
    interface = pyipmi.interfaces.create_interface('ipmitool', interface_type='lan')

    ipmi = pyipmi.create_connection(interface)
    
    ipmi.target = pyipmi.Target(ipmb_address=0x20)
    ipmi.session.set_session_type_rmcp(IPMI_IP)
    ipmi.session.set_auth_type_user(IPMI_AUTH[0], IPMI_AUTH[1])
    ipmi.session.establish()
    return ipmi

# Run with:
# python -c 'from src.measure import read_IPMI, setup_IPMI; ipmi = setup_IPMI(); print(read_IPMI(ipmi));'
# Allowed IPMI commands:
# ipmitool -H 192.168.1.203 sensor -U atlstudent -P 56iPmIuSeR -L USER
# ipmitool -H 192.168.1.203 dcmi power reading -U atlstudent -P 56iPmIuSeR -L ADMINISTRATOR
def read_IPMI(ipmi):
    try:
        power_reading = ipmi.get_power_reading(1)
    except Exception as e:
        print(f"Error reading IPMI power data: {e}")
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