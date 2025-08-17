import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
from collections import Counter
from src.util import logger, config
import os

# TODO: Put into a config file
MAX_RAPL_VALUE = int(config['host']['MAX_RAPL_VALUE'])

def plot_cleaned_data(
    csv_file,
    output_file,
    wide=True,
    include_error=False,
    include_cpu=False,
    include_mem=False,
    long_ticks=False
):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    # Split the data into runs based on rows starting with '-'
    run_indices = data.index[data['PDU-L_Current'].astype(str).str.startswith('-')].tolist()
    runs = []
    start_idx = 0
    for idx in run_indices + [len(data)]:
        run = data.iloc[start_idx:idx].copy()
        # Remove any separator rows (those starting with '-')
        run = run[~run['PDU-L_Current'].astype(str).str.startswith('-')]
        if not run.empty:
            runs.append(run.reset_index(drop=True))
        start_idx = idx + 1
        
    # ----- Line Plot ------

    width = 15 if wide else 12
    fig, ax = plt.subplots(figsize=(width, 10))
    fig.suptitle(f'{csv_file.split("/")[-1].split(".")[0].split("_benchmark")[0].upper()}', fontsize=30, x=0.55, y=0.96)

    label_redfish = f'Redfish'
    label_pdu = f'PDU'
    label_rapl = f'RAPL'

    # This plots the power per second with range
    min_length = min(len(r) for r in runs)
    avg_redfish = np.mean([r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    avg_pdu = np.mean([(r['PDU-L_Load'].astype(float) + r['PDU-R_Load'].astype(float)).iloc[:min_length].values for r in runs], axis=0)
    
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    if rapl_columns:
        processed_rapl_runs = []
        for r in runs:
            rapl_data = r[rapl_columns].astype(float)
            total_rapl = rapl_data.sum(axis=1)

            rapl_diff = total_rapl.diff().bfill()

            rapl_diff[rapl_diff < 0] += MAX_RAPL_VALUE

            trimmed = rapl_diff.iloc[:min_length].values / 1_000_000

            processed_rapl_runs.append(trimmed)

        avg_rapl = np.mean(processed_rapl_runs, axis=0)
    
    avg_timestamp = runs[0]['timestamp'].iloc[:min_length]

    ln1 = ax.plot(avg_timestamp, avg_redfish, label=label_redfish, color='green', linestyle='--')
    ln2 = ax.plot(avg_timestamp, avg_pdu, label=label_pdu, color='blue', linestyle='--')
    ln3 = ax.plot(avg_timestamp, avg_rapl, label=label_rapl, color='purple', linestyle='--')
    
    lns = ln1 + ln2 + ln3
    labels = ["Redfish", "PowerPDU", "RAPL"]
    
    # This adds the error range
    if include_error:
        min_redfish = np.min([r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
        max_redfish = np.max([r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
        ax.plot(avg_timestamp, min_redfish, color='green', linestyle=':')
        ax.plot(avg_timestamp, max_redfish, color='green', linestyle=':')
        ax.fill_between(avg_timestamp, min_redfish, max_redfish, color='green', alpha=0.2, label='Redfish Range')

        min_pdu = np.min([r['PDU-L_Load'].astype(float).iloc[:min_length].values + r['PDU-R_Load'].astype(float).iloc[:min_length].values for r in runs], axis=0)
        max_pdu = np.max([r['PDU-L_Load'].astype(float).iloc[:min_length].values + r['PDU-R_Load'].astype(float).iloc[:min_length].values for r in runs], axis=0)
        ax.plot(avg_timestamp, min_pdu, color='blue', linestyle=':')
        ax.plot(avg_timestamp, max_pdu, color='blue', linestyle=':')
        ax.fill_between(avg_timestamp, min_pdu, max_pdu, color='blue', alpha=0.2, label='PDU Range')

        min_rapl = np.min(processed_rapl_runs, axis=0) if processed_rapl_runs else None
        max_rapl = np.max(processed_rapl_runs, axis=0) if processed_rapl_runs else None
        ax.plot(avg_timestamp, min_rapl, color='orange', linestyle=':')
        ax.plot(avg_timestamp, max_rapl, color='orange', linestyle=':')
        ax.fill_between(avg_timestamp, min_rapl, max_rapl, color='orange', alpha=0.2, label='RAPL Range')
        
    # This adds the CPU utilization
    if include_cpu:
        cpu_columns = [col for col in data.columns if 'CPU' in col and 'RAPL' not in col]
        if cpu_columns:
            processed_cpu_runs = []
            for r in runs:
                cpu_data = r[cpu_columns].astype(float)
                total_cpu = cpu_data.mean(axis=1)
                trimmed = total_cpu.iloc[:min_length].values
                processed_cpu_runs.append(trimmed)
            avg_cpu = np.mean(processed_cpu_runs, axis=0)
        print(f"Average CPU Utilization: {np.mean(avg_cpu)}%")
        logger.info(f"Average CPU Utilization: {np.mean(avg_cpu)}%")

        ax2 = ax.twinx()
        ax2.set_ylabel('CPU Utilization (%)', fontsize=28, labelpad=10)
        yticks = np.arange(0, 120, 20)
        ax2.set_yticks(yticks)
        ax2.set_ylim(0, 100)
        
        ln4 = ax2.plot(avg_timestamp, avg_cpu, label='CPU Utilization', color='red', linestyle='-')
        lns = lns + ln4
        labels.append('CPU Utilization')
    elif include_mem:
        avg_mem = np.mean([r['Memory_Usage'].astype(float).iloc[:min_length].values for r in runs], axis=0)
        print(f"Average Memory Utilization: {np.mean(avg_mem)}%")
        logger.info(f"Average Memory Utilization: {np.mean(avg_mem)}%")

        ax2 = ax.twinx()
        ax2.set_ylabel('Memory Utilization (%)', fontsize=28, labelpad=10)
        yticks = np.arange(0, 120, 20)
        ax2.set_yticks(yticks)
        ax2.set_ylim(0, 100)

        ln4 = ax2.plot(avg_timestamp, avg_mem, label='Memory Utilization', color='red', linestyle='-')
        lns = lns + ln4
        labels.append('Memory Utilization')

    ax.set_xlabel('Duration (s)', fontsize=28)
    ax.set_ylabel('Power (W)', fontsize=28)
    cols = 2 if include_cpu or include_mem else 3
    ax.legend(lns, labels, ncol=cols, loc='upper center', bbox_to_anchor=(0.5, -0.14), fontsize=24)

    ax.set_xlim(0, np.max(ax.get_xticks()))
    y_min = np.floor(np.min([avg_redfish, avg_pdu, avg_rapl]) / 10) * 10
    y_max = np.ceil(np.max([avg_redfish, avg_pdu, avg_rapl]) / 10) * 10
    if include_error:
        y_min = min(y_min, np.floor(np.min([min_redfish, min_pdu, min_rapl]) / 10) * 10)
        y_max = max(y_max, np.ceil(np.max([max_redfish, max_pdu, max_rapl]) / 10) * 10)
    ax.set_ylim(y_min, y_max)
    
    xticks = ax.get_xticks()
    ticks_length = 30 if long_ticks else 5
    xticks_to_use = [tick for tick in xticks if tick % ticks_length == 0]
    ax.set_xticks(xticks_to_use)
    
    ax.tick_params(axis='x', labelsize=28)
    ax.tick_params(axis='y', labelsize=28)
    
    if include_cpu or include_mem:
        ax2.tick_params(axis='y', labelsize=28)
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
    else:
        ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    
    print(f"Average Redfish Power Control Current: {np.mean(avg_redfish)}")
    logger.info(f"Average Redfish Power Control Current: {np.mean(avg_redfish)}")
    print(f"Average PDU Load: {np.mean(avg_pdu)}")
    logger.info(f"Average PDU Load: {np.mean(avg_pdu)}")
    print(f"Average RAPL Current: {np.mean(avg_rapl)}")
    logger.info(f"Average RAPL Current: {np.mean(avg_rapl)}")

    print(f"Standard Deviation Redfish: {np.std(avg_redfish)}")
    logger.info(f"Standard Deviation Redfish: {np.std(avg_redfish)}")
    print(f"Standard Deviation PDU: {np.std(avg_pdu)}")
    logger.info(f"Standard Deviation PDU: {np.std(avg_pdu)}")
    print(f"Standard Deviation RAPL: {np.std(avg_rapl)}")
    logger.info(f"Standard Deviation RAPL: {np.std(avg_rapl)}")

def plot_total_energy(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    # Split the data into runs based on rows starting with '-'
    run_indices = data.index[data['PDU-L_Current'].astype(str).str.startswith('-')].tolist()
    runs = []
    start_idx = 0
    for idx in run_indices + [len(data)]:
        run = data.iloc[start_idx:idx].copy()
        # Remove any separator rows (those starting with '-')
        run = run[~run['PDU-L_Current'].astype(str).str.startswith('-')]
        if not run.empty:
            runs.append(run.reset_index(drop=True))
        start_idx = idx + 1
        
    fig, ax = plt.subplots(figsize=(10, 10))
    fig.suptitle(f'{csv_file.split("/")[-1].split(".")[0].split("_benchmark")[0].upper()}', fontsize=30, x=0.55, y=0.96)
    # fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    min_length = min(len(r) for r in runs)
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    
    # total_energy_ipmi = [r['IPMI_Current'].astype(float).iloc[:min_length].sum() for r in runs]
    total_energy_redfish = [r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].sum() for r in runs]
    total_energy_pdu = [r['PDU-L_Load'].astype(float).iloc[:min_length].sum() + r['PDU-R_Load'].astype(float).iloc[:min_length].sum() for r in runs]
    total_energy_rapl = [
        (r[rapl_columns].astype(float).sum(axis=1).iloc[min_length - 1] - r[rapl_columns].astype(float).sum(axis=1).iloc[0]) / 1_000_000
        for r in runs
    ] if rapl_columns else []

    # print(f"Total Energy IPMI: {np.mean(total_energy_ipmi)} J / {np.mean(total_energy_ipmi) / 3_600} kWh")
    print(f"Total Energy Redfish: {np.mean(total_energy_redfish):.3f} J / {np.mean(total_energy_redfish) / 3_600:.3f} kWh")
    logger.info(f"Total Energy Redfish: {np.mean(total_energy_redfish):.3f} J / {np.mean(total_energy_redfish) / 3_600:.3f} kWh")
    print(f"Max Redfish reading (kWh): {max([float(val) / 3600 for val in total_energy_redfish]):.3f}")
    logger.info(f"Max Redfish reading (kWh): {max([float(val) / 3600 for val in total_energy_redfish]):.3f}")
    print(f"Min Redfish reading (kWh): {min([float(val) / 3600 for val in total_energy_redfish]):.3f}")
    logger.info(f"Min Redfish reading (kWh): {min([float(val) / 3600 for val in total_energy_redfish]):.3f}")
    print(f"Total Energy PDU: {np.mean(total_energy_pdu):.3f} J / {np.mean(total_energy_pdu) / 3_600:.3f} kWh")
    logger.info(f"Total Energy PDU: {np.mean(total_energy_pdu):.3f} J / {np.mean(total_energy_pdu) / 3_600:.3f} kWh")
    print(f"Max PDU reading (kWh): {max([float(val) / 3600 for val in total_energy_pdu]):.3f}")
    logger.info(f"Max PDU reading (kWh): {max([float(val) / 3600 for val in total_energy_pdu]):.3f}")
    print(f"Min PDU reading (kWh): {min([float(val) / 3600 for val in total_energy_pdu]):.3f}")
    logger.info(f"Min PDU reading (kWh): {min([float(val) / 3600 for val in total_energy_pdu]):.3f}")
    print(f"Total Energy RAPL: {np.mean(total_energy_rapl):.3f} J / {np.mean(total_energy_rapl) / 3_600:.3f} kWh")
    logger.info(f"Total Energy RAPL: {np.mean(total_energy_rapl):.3f} J / {np.mean(total_energy_rapl) / 3_600:.3f} kWh")
    print(f"Max RAPL reading (kWh): {max([float(val) / 3600 for val in total_energy_rapl]):.3f}")
    logger.info(f"Max RAPL reading (kWh): {max([float(val) / 3600 for val in total_energy_rapl]):.3f}")
    print(f"Min RAPL reading (kWh): {min([float(val) / 3600 for val in total_energy_rapl]):.3f}")
    logger.info(f"Min RAPL reading (kWh): {min([float(val) / 3600 for val in total_energy_rapl]):.3f}")

    # BOXPLOTS
    # ax.boxplot(total_energy_ipmi, positions=[0], widths=0.4, patch_artist=True,
            #    boxprops=dict(facecolor='black', color='black', alpha=0.5), medianprops=dict(color='black'))
    # ax.boxplot(total_energy_redfish, positions=[1], widths=0.4, patch_artist=True, 
    #            boxprops=dict(facecolor='green', color='green', alpha=0.5), medianprops=dict(color='green'))
    # ax.boxplot(total_energy_pdu, positions=[2], widths=0.4, patch_artist=True, 
    #            boxprops=dict(facecolor='blue', color='blue', alpha=0.5), medianprops=dict(color='blue'))
    # if total_energy_rapl:
    #     ax.boxplot(total_energy_rapl, positions=[3], widths=0.4, patch_artist=True,
    #                 boxprops=dict(facecolor='orange', color='orange', alpha=0.5), medianprops=dict(color='orange'))

    # JITTERPLOTS
    x_vals = np.random.normal(loc=1, scale=0.1, size=len(total_energy_redfish))
    ax.scatter(x_vals, total_energy_redfish, color='green', alpha=0.5, label='Redfish', s=30)
    ax.hlines(np.mean(total_energy_redfish), 1 - 0.2, 1 + 0.2, colors='green', linestyles='dashed')

    x_vals = np.random.normal(loc=1, scale=0.1, size=len(total_energy_redfish))
    ax.scatter(x_vals + 1, total_energy_pdu, color='blue', alpha=0.5, label='PDU', s=30)
    ax.hlines(np.mean(total_energy_pdu), 2 - 0.2, 2 + 0.2, colors='blue', linestyles='dashed')

    x_vals = np.random.normal(loc=1, scale=0.1, size=len(total_energy_redfish))
    if total_energy_rapl:
        ax.scatter(x_vals + 2, total_energy_rapl, color='orange', alpha=0.5, label='RAPL', s=30)
    ax.hlines(np.mean(total_energy_rapl), 3 - 0.2, 3 + 0.2, colors='orange', linestyles='dashed')
    
    ax.margins(x=0.2)

    # Add mean value as text above each boxplot
    means = [np.mean(total_energy_redfish), np.mean(total_energy_pdu)]
    if total_energy_rapl:
        means.append(np.mean(total_energy_rapl))
    for i, mean_val in enumerate(means):
        ax.text(i + 1.25, mean_val, f"{mean_val:.1f}", ha='left', va='center', fontsize=20, color='black')
    
    ax.set_xticks([1, 2, 3])
    ax.set_xticklabels(['REDFISH', 'PDU', 'RAPL'])
    # Set predefined yticks for consistency across diagrams
    yticks = np.arange(2500, 6000, 500)
    ax.set_yticks(yticks)
    ax.set_ylabel('Energy (Joules)', fontsize=30, labelpad=20)
    ax.set_xlabel('Power Monitoring Tool', fontsize=30, labelpad=20)
    
    ax.tick_params(axis='x', labelsize=26)
    ax.tick_params(axis='y', labelsize=26)

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file.replace('.pdf', '_total.pdf'))
    plt.close()

def generate_diagrams_thesis(results_dir):
    # Ensure thesis output directory exists
    thesis_dir = os.path.join(results_dir, "thesis/")
    os.makedirs(thesis_dir, exist_ok=True)
    # CPU_ALL_50_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "cpu_all_50_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "cpu_all_50_benchmark_cleaned.pdf")
    plot_total_energy(csv_path, output_path)
    # CPU_HALF_100_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "cpu_half_100_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "cpu_half_100_benchmark_cleaned.pdf")
    plot_total_energy(csv_path, output_path)
    # CPU_LINEAR_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "cpu_linear_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "cpu_linear_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, include_cpu=True)
    # MEM_READ_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "mem_read_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "mem_read_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, wide=False, include_mem=True)
    # MEM_WRITE_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "mem_write_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "mem_write_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, wide=False, include_mem=True)
    # NETWORK_SEND_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "network_send_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "network_send_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, wide=False)
    # NETWORK_RECEIVE_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "network_receive_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "network_receive_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, wide=False)
    # STORAGE_READ_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "storage_read_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "storage_read_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, wide=False)
    # STORAGE_WRITE_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "storage_write_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "storage_write_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, wide=False)
    # STABILITY_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "stability_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "stability_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, long_ticks=True, include_error=True)
    # LATENCY_BENCHMARK
    csv_path = os.path.join(results_dir, "cleaned/", "latency_benchmark_cleaned.csv")
    output_path = os.path.join(thesis_dir, "latency_benchmark_cleaned.pdf")
    plot_cleaned_data(csv_path, output_path, include_cpu=True)