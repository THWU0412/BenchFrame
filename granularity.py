import os
from src.measure import read_PDU, setup_PDU, read_rapl, read_Redfish, setup_Redfish
from time import sleep
from datetime import datetime
import numpy as np
    
def test_granularity(granularity):
    # PDU_L, PDU_R = setup_PDU()
    # REDFISH_OBJ = setup_Redfish()
    # rapl_sockets = len([name for name in os.listdir('/sys/class/powercap') if name.startswith('intel-rapl') and ':' in name and name.count(':') == 1])
    
    
    print(f"Start granularity test: {granularity}")
    now = datetime.now()

    measurements_counter = 0
    error_counter = 0
    
    while measurements_counter < 100:
        measurements_counter += 1
        # data_PDU = read_PDU(PDU_L, PDU_R)
        # data_RAPL = read_rapl(rapl_sockets)
        # data_REDFISH = read_Redfish(REDFISH_OBJ)
        if False:
            error_counter += 1
        sleep(granularity)
    duration = (datetime.now() - now).total_seconds()
    print(f"Finished with {error_counter} errors in {duration} seconds")

    # REDFISH_OBJ.logout()

    return duration


granularity_values = [0, 0.001, 0.01, 0.05, 0.1]
errors = []

for i in range(5):
    errors.append([])
    for j in granularity_values:
        errors[i].append(test_granularity(j))
print(errors)
print(np.mean(errors, axis=0))