import csv
import time
from datetime import datetime
from Netio import Netio
import pyipmi
import pyipmi.interfaces

NETIO_IP_L = "http://192.168.1.78/netio.json"
NETIO_IP_R = "http://192.168.1.79/netio.json"
NETIO_AUTH = ("admin", "password")

IPMI_IP = "192.168.1.203"
IPMI_AUTH = ("atlstudent", "56iPmIuSeR")

def write_csv(stop_event, filename, timestamp):
    csv_file = f"results/{timestamp}/{filename}.csv"

    headers = [
        "timestamp",
        "Node3-L_Current", "Node3-L_PowerFactor", "Node3-L_Load", "Node3-L_Energy",
        "Node3-R_Current", "Node3-R_PowerFactor", "Node3-R_Load", "Node3-R_Energy",
        "IPMI_Timestamp", "IPMI_Current", "IPMI_State"
    ]

    poll_interval = 0.1

    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        if f.tell() == 0:
            writer.writerow(headers)

        while not stop_event.is_set():
            timestamp = datetime.now().isoformat()
            data_PDU = read_PDU()
            data_IPMI = read_IPMI()
            writer.writerow([
                timestamp,
                data_PDU['Node3-L_Current'], data_PDU['Node3-L_PowerFactor'], data_PDU['Node3-L_Load'], data_PDU['Node3-L_Energy'],
                data_PDU['Node3-R_Current'], data_PDU['Node3-R_PowerFactor'], data_PDU['Node3-R_Load'], data_PDU['Node3-R_Energy'],
                data_IPMI['timestamp'], data_IPMI['current'], data_IPMI['state']
            ])
            f.flush()
            time.sleep(poll_interval)

# Run with:
# python -c 'from src.measure import read_PDU; print(read_PDU())'
def read_PDU():

    PDU_L = Netio(NETIO_IP_L, auth_rw=NETIO_AUTH)
    PDU_R = Netio(NETIO_IP_R, auth_rw=NETIO_AUTH)
    
    output_L = PDU_L.get_outputs()
    output_R = PDU_R.get_outputs()

    out1 = next((o for o in output_L if o.ID == 1), None)
    out2 = next((o for o in output_R if o.ID == 1), None)

    return {
        'Node3-L_Current': out1.Current,
        'Node3-L_PowerFactor': out1.PowerFactor,
        'Node3-L_Load': out1.Load,
        'Node3-L_Energy': out1.Energy,
        'Node3-R_Current': out2.Current,
        'Node3-R_PowerFactor': out2.PowerFactor,
        'Node3-R_Load': out2.Load,
        'Node3-R_Energy': out2.Energy
    }

# Run with:
# python -c 'from src.measure import read_IPMI; print(read_IPMI());'
def read_IPMI():
    interface = pyipmi.interfaces.create_interface('ipmitool', interface_type='lan')

    ipmi = pyipmi.create_connection(interface)
    
    ipmi.target = pyipmi.Target(ipmb_address=0x20)
    ipmi.session.set_session_type_rmcp(IPMI_IP)
    ipmi.session.set_auth_type_user(IPMI_AUTH[0], IPMI_AUTH[1])
    ipmi.session.establish()

    power_reading = ipmi.get_power_reading(1)

    return {
        'timestamp': datetime.fromtimestamp(power_reading.timestamp),
        'current': power_reading.current_power,
        'minimum': power_reading.minimum_power,
        'maximum': power_reading.maximum_power,
        'average': power_reading.average_power,
        'period': power_reading.period,
        'state': power_reading.reading_state
    }