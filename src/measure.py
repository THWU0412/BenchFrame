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
import redfish

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
    rapl_path = '/sys/class/powercap'
    rapl_sockets = sum(
        1 for name in os.listdir(rapl_path)
        if name.startswith('intel-rapl') and name.count(':') == 1
    )
    
    headers = [
        "timestamp",
        # PDU data
        "PDU-L_Current", "PDU-L_PowerFactor", "PDU-L_Load", "PDU-L_Energy",
        "PDU-R_Current", "PDU-R_PowerFactor", "PDU-R_Load", "PDU-R_Energy",
        # IPMI data
        "IPMI_Current", "IPMI_State",
        # Redfish data
        "Redfish_PowerControl_Current", "Redfish_PowerSupplies1_InputWatts", "Redfish_PowerSupplies1_OutputWatts",
        "Redfish_PowerSupplies2_InputWatts", "Redfish_PowerSupplies2_OutputWatts",
        # Memory data
        "Memory_Usage"
    ]
    # INTEL-RAPL data
    for i in range(rapl_sockets):
        headers.append(f"INTEL-RAPL{i}_CPU")
        headers.append(f"INTEL-RAPL{i}_MEM")
    # CPU data
    headers += [f"CPU{i+1}" for i in range(num_cpu)]

    PDU_L, PDU_R = setup_PDU()
    ipmi = setup_IPMI()
    REDFISH_OBJ = setup_Redfish()

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(headers)

        while not stop_event.is_set():
            timestamp = time.strftime("%H:%M:%S", time.localtime())
            data_PDU = read_PDU(PDU_L, PDU_R)
            data_IPMI = read_IPMI(ipmi)
            data_REDFISH = read_Redfish(REDFISH_OBJ)
            data_MEM = psutil.virtual_memory()
            data_RAPL = read_rapl(rapl_sockets)
            data_CPU = psutil.cpu_percent(interval=float(config['host']['POLL_INTERVAL']), percpu=True)
            if data_PDU is None or data_IPMI is None or data_REDFISH is None or data_RAPL is None:
                continue
            row = [
                timestamp,
                # PDU data
                data_PDU['PDU-L_Current'], data_PDU['PDU-L_PowerFactor'], data_PDU['PDU-L_Load'], data_PDU['PDU-L_Energy'],
                data_PDU['PDU-R_Current'], data_PDU['PDU-R_PowerFactor'], data_PDU['PDU-R_Load'], data_PDU['PDU-R_Energy'],
                # IPMI data
                data_IPMI['current'], data_IPMI['state'],
                # Redfish data
                data_REDFISH['powerControl_current'],
                data_REDFISH['powerSupplies1_InputWatts'], data_REDFISH['powerSupplies1_OutputWatts'],
                data_REDFISH['powerSupplies2_InputWatts'], data_REDFISH['powerSupplies2_OutputWatts'],
                # Memory data
                data_MEM.percent
            ]
            # INTEL-RAPL data
            row.extend(data_RAPL)
            # CPU data
            row.extend(data_CPU)
            writer.writerow(row)
            f.flush()
            
        writer.writerow("-")
    
    REDFISH_OBJ.logout()
            
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
    credentials = tuple(part.strip() for part in config['host']['IPMI_AUTH'].strip("()").split(','))
    ipmi.session.set_auth_type_user(credentials[0], credentials[1])
    ipmi.session.establish()
    return ipmi

# Run with:
# python -c 'from src.measure import read_IPMI, setup_IPMI; ipmi = setup_IPMI(); print(read_IPMI(ipmi));'
# Allowed IPMI commands:
# ipmitool -H 192.168.1.209 sensor -U atlstudent -P 56iPmIuSeR -L USER
# ipmitool -H 192.168.1.209 dcmi power reading -U atlstudent -P 56iPmIuSeR -L ADMINISTRATOR
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
    
def setup_Redfish():
    credentials = tuple(part.strip() for part in config['host']['IPMI_AUTH'].strip("()").split(','))
    REDFISH_OBJ = redfish.redfish_client(base_url='https://' + config['host']['IPMI_IP'], username=credentials[0], password=credentials[1], default_prefix='/redfish/v1/')
    REDFISH_OBJ.login(auth="session")
    return REDFISH_OBJ
    
def read_Redfish(REDFISH_OBJ):
    response = REDFISH_OBJ.get("/redfish/v1/Chassis/1/Power")
    if response.status == 200:
        power_data = response.dict
        return {
            'powerControl_current': power_data['PowerControl'][0]['PowerConsumedWatts'],
            'powerSupplies1_InputWatts': power_data['PowerSupplies'][0]['PowerInputWatts'],
            'powerSupplies1_OutputWatts': power_data['PowerSupplies'][0]['PowerOutputWatts'],
            'powerSupplies2_InputWatts': power_data['PowerSupplies'][1]['PowerInputWatts'],
            'powerSupplies2_OutputWatts': power_data['PowerSupplies'][1]['PowerOutputWatts']
        }
    else:
        logger.error(f"Error reading Redfish power data: {response.status} - {response.text}")
        return None


# Run with:
# sudo -E python3 -c 'from src.measure import clean_results; clean_results("results/2025-06-11_19-33-53");'
def clean_results(results_dir):
    os.makedirs(os.path.join(results_dir, "cleaned/"), exist_ok=True)
    for folder_item in os.listdir(results_dir):
        if folder_item.endswith(".csv"):
            try:
                df = pd.read_csv(os.path.join(results_dir, folder_item))
                # Example cleaning: drop rows with any NaN values and remove rows with only '-'
                rep_set = []
                current = []
                for _, row in df.iterrows():
                    if str(row.iloc[0]).startswith('-'):
                        if current:
                            rep_set.append(pd.DataFrame(current, columns=df.columns))
                            current = []
                    else:
                        current.append(row)
                if current:
                    rep_set.append(pd.DataFrame(current, columns=df.columns))
                    
                cleaned = []
                for rep in rep_set:
                    # Convert timestamp to seconds (assume format HH:MM:SS)
                    rep['timestamp_sec'] = rep['timestamp'].apply(lambda x: sum(int(t) * 60 ** i for i, t in enumerate(reversed(str(x).split(":")))))
                    rep = rep.dropna()
                    # Group by second and average numeric columns
                    grouped = rep.groupby('timestamp_sec').mean(numeric_only=True).round(2)
                    # Reindex to fill missing seconds
                    idx = range(grouped.index.min(), grouped.index.max() + 1)
                    grouped = grouped.reindex(idx)
                    grouped = grouped.interpolate(method='linear').round(2)
                    grouped['timestamp'] = range(len(grouped))
                    grouped = grouped.reset_index(drop=True)
                    cleaned.append(grouped)
                # Save cleaned reps back to CSV
                cleaned_with_sep = []
                for rep in cleaned:
                    cleaned_with_sep.append(rep)
                    # Add a separator row with '-' for each column
                    sep_row = {col: '-' for col in rep.columns}
                    cleaned_with_sep.append(pd.DataFrame([sep_row]))
                cleaned_df = pd.concat(cleaned_with_sep, ignore_index=True)
                out_path = os.path.join(results_dir, "cleaned/", f"{folder_item[:-4]}_cleaned.csv")
                cleaned_df.to_csv(out_path, index=False)
                
                
            except Exception as e:
                print(f"Error processing {folder_item}: {e}")
                