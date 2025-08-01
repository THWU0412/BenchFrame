# BenchFrame
BenchFrame is a benchmark framework designed to evaluate and analyze the performance and energy efficiency of computational workloads. It provides a streamlined setup for running experiments, collecting results, and integrating with the Continuum project for infrastructure management. The framework supports reproducible benchmarking through virtual environments and automated result storage, making it suitable for research and development in high-performance and energy-aware computing.


## Steps to Set Up a `venv`

1. **Create a Virtual Environment**:
    ```bash
    python -m venv venv
    ```

2. **Activate the Virtual Environment**:
    ```bash
    source venv/bin/activate
    ```

3. **Install Packages**:
    ```bash
    pip install -r requirements.txt
    ``````

4. **Deactivate**:
    ```bash
    deactivate
    ```

## Required Tools
### Measurement Tools
This framework is build to work with Intel RAPL, IPMI/Redfish, and Netio PowerPDU 4KS. 
Therefore, these monitoring tools need to be installed and set up as mentioned in their manuals.

### Benchmarking tools
The current set of benchmark experiments include four tools. These tools need to be installed and added to the `PATH` variable.

These tools are:
| Name          | Component | Link                                           |
|---------------|-----------|------------------------------------------------|
| stress-ng     | CPU       | https://github.com/ColinIanKing/stress-ng      |
| iperf3        | Network   | https://github.com/esnet/iperf                 |
| fio           | Storage   | https://github.com/axboe/fio                   |
| stressapptest | RAM       | https://github.com/stressapptest/stressapptest |

## How to add experiments
The `scripts` directory contains all benchmark experiment scripts. To add a new experiment, simply create a shell script in this directory. Ensure the script has a unique and descriptive name, as it will serve as the identifier for running the experiment.

## Run the Framework
1. Create the infrastructure using the continuum project found here:\
[Continuum Project Repository](https://github.com/atlarge-research/continuum)
2. Run the application
    ```bash
    sudo -E python main.py
    ```
3. The results are stored in `results/`