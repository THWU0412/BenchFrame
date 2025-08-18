import csv
import os
from src.measure import read_PDU, setup_PDU, read_rapl, read_Redfish, setup_Redfish
from time import sleep
from datetime import datetime
import numpy as np
from src.util import logger

granularity_values = [0, 0.001, 0.01, 0.05, 0.1]

def test_pdu_granularity(granularity):
    PDU_L, PDU_R = setup_PDU()
    now = datetime.now()

    measurements_counter = 0
    error_counter = 0
    
    while measurements_counter < 100:
        measurements_counter += 1
        try:
            read_PDU(PDU_L, PDU_R)
        except:
            error_counter += 1
        sleep(granularity)
    duration = (datetime.now() - now).total_seconds()
    print(f"Executed granularity test for PDU with granularity: {granularity}, errors: {error_counter}, duration: {duration}")
    logger.info(f"Executed granularity test for PDU with granularity: {granularity}, errors: {error_counter}, duration: {duration}")
    return duration

def test_redfish_granularity(granularity):
    REDFISH_OBJ = setup_Redfish()
    now = datetime.now()

    measurements_counter = 0
    error_counter = 0
    
    while measurements_counter < 100:
        measurements_counter += 1
        try:
            read_Redfish(REDFISH_OBJ)
        except:
            error_counter += 1
        sleep(granularity)
    duration = (datetime.now() - now).total_seconds()
    print(f"Executed granularity test for Redfish with granularity: {granularity}, errors: {error_counter}, duration: {duration}")
    logger.info(f"Executed granularity test for Redfish with granularity: {granularity}, errors: {error_counter}, duration: {duration}")
    REDFISH_OBJ.logout()
    return duration

def test_rapl_granularity(granularity):
    rapl_sockets = len([name for name in os.listdir('/sys/class/powercap') if name.startswith('intel-rapl') and ':' in name and name.count(':') == 1])
    now = datetime.now()

    measurements_counter = 0
    error_counter = 0
    
    while measurements_counter < 100:
        measurements_counter += 1
        try:
            data_RAPL = read_rapl(rapl_sockets)
        except:
            error_counter += 1
        sleep(granularity)
    duration = (datetime.now() - now).total_seconds()
    print(f"Executed granularity test for RAPL with granularity: {granularity}, errors: {error_counter}, duration: {duration}")
    logger.info(f"Executed granularity test for RAPL with granularity: {granularity}, errors: {error_counter}, duration: {duration}")
    return duration

def test_none_granularity(granularity):
    now = datetime.now()

    measurements_counter = 0
    
    while measurements_counter < 100:
        measurements_counter += 1
        sleep(granularity)
    duration = (datetime.now() - now).total_seconds()
    print(f"Executed granularity test for NONE with granularity: {granularity}, duration: {duration}")
    logger.info(f"Executed granularity test for NONE with granularity: {granularity}, duration: {duration}")
    return duration

def store_results(results_dir, granularity, durations_pdu, durations_redfish, durations_rapl, durations_none):
    csv_file = os.path.join(results_dir, "granularity.csv")
    with open(csv_file, mode='a', newline='') as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(["GRANULARITY", "NONE", "PDU_DURATION", "Redfish_DURATION", "RAPL_DURATION"])
        writer.writerow([granularity, np.mean(durations_none), np.mean(durations_pdu), np.mean(durations_redfish), np.mean(durations_rapl)])

def run_granularity_tests(results_dir):
    for granularity in granularity_values:
        durations_pdu = []
        durations_redfish = []
        durations_rapl = []
        durations_none = []
        for i in range(2):
            durations_pdu.append(test_pdu_granularity(granularity))
            durations_redfish.append(test_redfish_granularity(granularity))
            durations_rapl.append(test_rapl_granularity(granularity))
            durations_none.append(test_none_granularity(granularity))
        store_results(results_dir, granularity, durations_pdu, durations_redfish, durations_rapl, durations_none)
        print(f"\nResults for granularity {granularity}:")
        logger.info(f"\nResults for granularity {granularity}:")
        print(f"PDU durations: {np.mean(durations_pdu)}")
        logger.info(f"PDU durations: {np.mean(durations_pdu)}")
        print(f"Redfish durations: {np.mean(durations_redfish)}")
        logger.info(f"Redfish durations: {np.mean(durations_redfish)}")
        print(f"RAPL durations: {np.mean(durations_rapl)}\n")
        logger.info(f"RAPL durations: {np.mean(durations_rapl)}\n")