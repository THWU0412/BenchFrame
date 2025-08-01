import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np
from collections import Counter

# Run with:
# sudo -E python -c 'from src.diagram import plot_diagrams; plot_diagrams("results/(keep)2025-05-18_16-17-04/cpu_ramp-up_benchmark.csv", "results/(keep)2025-05-18_16-17-04/cpu_ramp-up_benchmark_cpu.png")'
def plot_diagrams(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Power Consumption Diagrams', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]

    # Plot Current
    # axes[0, 0].plot(timestamp_diff, data['PDU-L_Current'], label='PDU-L_Current')
    # axes[0, 0].plot(timestamp_diff, data['PDU-R_Current'], label='PDU-R_Current')
    axes[0, 0].plot(timestamp_diff, data['PDU-L_Current'] + data['PDU-R_Current'], 
                    label='Sum_Current_PDU', linestyle='--')
    axes[0, 0].set_title('Current')
    axes[0, 0].set_xlabel('Duration (s)')
    axes[0, 0].set_ylabel('Current (mA)')
    axes[0, 0].legend()

    # Plot PowerFactor
    # axes[0, 1].plot(timestamp_diff, data['PDU-L_PowerFactor'], label='PDU-L_PowerFactor')
    # axes[0, 1].plot(timestamp_diff, data['PDU-R_PowerFactor'], label='PDU-R_PowerFactor')
    axes[0, 1].plot(timestamp_diff, (data['PDU-L_PowerFactor'] + data['PDU-R_PowerFactor']) / 2, 
                    label='Avg_PowerFactor', linestyle='--')
    axes[0, 1].set_title('PowerFactor')
    axes[0, 1].set_xlabel('Duration (s)')
    axes[0, 1].set_ylabel('PowerFactor')
    axes[0, 1].legend()

    # Plot Load
    # axes[1, 0].plot(timestamp_diff, data['PDU-L_Load'], label='PDU-L_Load')
    # axes[1, 0].plot(timestamp_diff, data['PDU-R_Load'], label='PDU-R_Load')
    axes[1, 0].plot(timestamp_diff, data['PDU-L_Load'] + data['PDU-R_Load'], 
                    label='Sum_Load')
    axes[1, 0].plot(timestamp_diff, data['IPMI_Current'], label='IPMI_Current')
    load_smooth = (data['PDU-L_Load'] + data['PDU-R_Load']).rolling(window=10).mean()
    axes[1, 0].plot(timestamp_diff, load_smooth, label='Smoothed PDU Load', color='red', linestyle='--')
    
    rounded_load = np.round((data['PDU-L_Load'] + data['PDU-R_Load']) / 5) * 5
    counts = Counter(rounded_load)
    
    min_count = 20
    
    plateau_values = [val for val, count in counts.items() if count >= min_count]
    min_val = np.min(load_smooth)
    max_val = np.max(load_smooth)
    
    for val in plateau_values:
        axes[1, 0].axhline(y=val, linestyle=':', color='gray', linewidth=1)
        axes[1, 0].text(timestamp_diff[-1], val, f"{val:.1f}", va='center', ha='right', fontsize=8)

    # Add min and max lines in a different style
    axes[1, 0].axhline(y=min_val, linestyle='--', color='blue', label=f"Min: {min_val:.2f}")
    axes[1, 0].axhline(y=max_val, linestyle='--', color='green', label=f"Max: {max_val:.2f}")
    
    axes[1, 0].set_title('Load')
    axes[1, 0].set_xlabel('Duration (s)')
    axes[1, 0].set_ylabel('Load (W)')
    axes[1, 0].legend()

    # Plot Energy
    # axes[1, 1].plot(timestamp_diff, data['PDU-L_Energy'], label='PDU-L_Energy')
    # axes[1, 1].plot(timestamp_diff, data['PDU-R_Energy'], label='PDU-R_Energy')
    axes[1, 1].plot(timestamp_diff, data['PDU-L_Energy'] + data['PDU-R_Energy'], 
                    label='Sum_Energy', linestyle='--')
    axes[1, 1].set_title('Energy')
    axes[1, 1].set_xlabel('Duration (s)')
    axes[1, 1].set_ylabel('Energy (Wh)')
    axes[1, 1].legend()
    
    wattseconds = data['PDU-L_Energy'].iloc[-1] + data['PDU-R_Energy'].iloc[-1]
    print(f"(PDU) Total energy consumed: {wattseconds / 3600} W = {wattseconds} Joules = {wattseconds * 1000000} microJoules")

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

# Run with:
# sudo -E python -c 'from src.diagram import plot_rapl; plot_rapl("results/(keep)2025-05-18_16-17-04/idle_benchmark.csv", "results/(keep)2025-05-18_16-17-04/idle_benchmark_rapl.png")'
def plot_rapl(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(1, 2, figsize=(15, 10))
    fig.suptitle('RAPL Power Consumption', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]
    # How to understand this rapl value
    # So rapl just counts the energy units. One energy unit is just an abstract value and can be different depending on the processor.
    # Apparently, we can figure that value out by readin the msr registry (whatever that is).
    # So first load it with `sudo modprobe msr`
    # Then read the value with `sudo rdmsr -X 0x606`
    # This returns:
    #   0xA0E03 = 1010 0000 01110 0000 0011
    # And now somewhere in there is the value we are looking for.
    # Chatty returned this table:
    # RAPL MSR 0x606 field breakdown:
    # | Field        | Bits     | Value (binary) | Value (decimal) |
    # | ------------ | -------- | -------------- | --------------- |
    # | Power Units  | [3:0]    | 0011           | 3               |
    # | Energy Units | [12:8]   | 01110          | 14              |
    # | Time Units   | [19:16]  | 1010           | 10              |
    #  So that would mean that the energy unit is 1/2^14 = 0.000061035 joules = 61.035 microJoules
    
    # It seems like this assumption is correct. But only if we read the value from the register.
    # The value we read from energy_uj is the total energy consumed in microjoules.
    
    for col in rapl_columns:
        diffs = data[col].diff().fillna(0)
        axes[0].plot(timestamp_diff, diffs, label=col)
        axes[0].set_title('RAPL Power Consumption Per Socket')
        axes[0].set_xlabel('Duration (s)')
        axes[0].set_ylabel('Power Units (?J)')
        axes[0].legend()
    if rapl_columns:
        diffs_total = data[rapl_columns].sum(axis=1).diff().fillna(0)
        axes[1].plot(timestamp_diff, diffs_total, label='Sum_RAPL', linestyle='--', color='black')
        axes[1].set_title('RAPL Power Consumption Total')
        axes[1].set_xlabel('Duration (s)')
        axes[1].set_ylabel('Power Units (?J)')
        axes[1].legend()
    microjoules = diffs_total.iloc[-1] * 61.035
    print(f"Diffs total: {diffs_total.iloc[-1]}")
    print(f"(RAPL) Total energy consumed: {microjoules / 3600} Wh = {microjoules / 1000000} Joules = {microjoules} microJoules")
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()
    
# Run with:
# python3 -c 'from src.diagram import print_rapl_data; print_rapl_data("results/2025-05-30_13-09-27/idle_benchmark.csv")'
def print_rapl_data(csv_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    for col in rapl_columns:
        diffs = data[col].diff().fillna(0)
    if rapl_columns:
        diffs_total = data[rapl_columns].sum(axis=1).diff().fillna(0)
    microjoules = diffs_total.iloc[-1] * 61.035
    print(f"Diffs total: {diffs_total.iloc[-1]}")
    print(f"(RAPL) Total energy consumed: {microjoules / 3600} Wh = {microjoules / 1000000} Joules = {microjoules} microJoules")
    
def plot_redfish(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(figsize=(15, 10))
    fig.suptitle('Redfish Power Consumption', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]

    columns = [
        "Redfish_PowerControl_Current",
        "Redfish_PowerSupplies1_InputWatts",
        "Redfish_PowerSupplies1_OutputWatts",
        "Redfish_PowerSupplies2_InputWatts",
        "Redfish_PowerSupplies2_OutputWatts",
    ]
    colors = ['green', 'blue', 'orange', 'purple', 'red']
    for col, color in zip(columns, colors):
        if col in data.columns:
            axes.plot(timestamp_diff, data[col], label=col, linewidth=2, color=color)
            # print(f"{col}: min={data[col].min()}, max={data[col].max()}, mean={data[col].mean()}")

    axes.set_title('Redfish Power Consumption Over Time')
    axes.set_xlabel('Duration (s)')
    axes.set_ylabel('Power (W)')
    axes.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

# Run with:
# python -c 'from src.diagram import plot_avg_cpu_usage; plot_avg_cpu_usage("results/(keep)2025-05-18_16-17-04/cpu_ramp-up_benchmark.csv", "results/(keep)2025-05-18_16-17-04/cpu_ramp-up_benchmark_avg.png")'
# python -c 'from src.diagram import plot_avg_cpu_usage; plot_avg_cpu_usage("results/2025-05-08_11-33-52/simultaneous.csv", "results/2025-05-08_11-33-52/cpu_simultaneous.png")'
def plot_avg_cpu_usage(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(figsize=(15, 10))
    fig.suptitle('CPU Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    # TODO: Change to be more generic (Per CPU column)
    # rapl_columns = [col for col in data.columns if 'CPU' in col and 'RAPL' not in col]
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]

    data['Average_CPU'] = data[[f'CPU{i}' for i in range(1, 21)]].mean(axis=1)
    data['Avg_CPU_smooth'] = data['Average_CPU'].rolling(window=10).mean()
    axes.plot(timestamp_diff, data['Average_CPU'], label='Average_CPU', color='red', linewidth=2)
    axes.plot(timestamp_diff, data['Avg_CPU_smooth'], label='Smoothed Avg CPU', color='blue', linewidth=2)

    axes.set_title('CPU Usage Over Time')
    axes.set_xlabel('Duration (s)')
    axes.set_ylabel('Avg CPU Usage (%)')
    axes.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, -0.1))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

# Run with:
# python -c 'from src.diagram import plot_all_cpus; plot_all_cpus("results/2025-05-07_16-56-44/sequential.csv", "results/2025-05-07_16-56-44/cpu_sequential_all.png")'
# python -c 'from src.diagram import plot_all_cpus; plot_all_cpus("results/2025-05-07_16-56-44/simultaneous.csv", "results/2025-05-07_16-56-44/cpu_simultaneous_all.png")'
def plot_all_cpus(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(4, 5, figsize=(15, 10))  # 4 rows, 5 columns
    fig.suptitle('CPU Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]

    for i in range(1, 21):
        row = (i - 1) // 5
        col = (i - 1) % 5
        ax = axes[row, col]
        ax.plot(timestamp_diff, data[f'CPU{i}'], label=f'CPU{i}')
        ax.set_title(f'CPU {i}')
        ax.set_xlabel('Duration (s)')
        ax.set_ylabel('Usage (%)')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

def plot_memory_usage(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(figsize=(15, 10))
    fig.suptitle('Memory Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]

    axes.plot(timestamp_diff, data['Memory_Usage'], label='Memory Usage', color='green', linewidth=2)

    axes.set_title('Memory Usage Over Time')
    axes.set_xlabel('Duration (s)')
    axes.set_ylabel('Memory Usage (%)')
    axes.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()


# Run with:
# python -c 'from src.diagram import make_cpu_usage_gif; make_cpu_usage_gif("results/2025-05-07_16-56-44/sequential.csv", "results/2025-05-07_16-56-44/cpu_sequential.gif")'
# python -c 'from src.diagram import make_cpu_usage_gif; make_cpu_usage_gif("results/2025-05-07_16-56-44/simultaneous.csv", "results/2025-05-07_16-56-44/cpu_simultaneous.gif")'
def make_cpu_usage_gif(csv_file, output_file, interval_ms=200):
    df = pd.read_csv(csv_file, parse_dates=['timestamp'])

    cpu_columns = [col for col in df.columns if col.startswith("CPU")]
    num_cpus = len(cpu_columns)

    fig, ax = plt.subplots(figsize=(10, num_cpus * 0.3))
    bars = ax.barh(cpu_columns, [0] * num_cpus, color='skyblue')
    ax.set_xlim(0, 100)
    ax.set_xlabel("CPU Usage (%)")

    def update(frame):
        usage_values = df.loc[frame, cpu_columns]
        for bar, usage in zip(bars, usage_values):
            bar.set_width(usage)
        timestamp = df.loc[frame, 'timestamp']
        ax.set_title(f"CPU Usage - {timestamp}")
        return bars

    anim = FuncAnimation(fig, update, frames=len(df), interval=interval_ms, blit=False)

    anim.save(output_file, writer=PillowWriter(fps=1000 // interval_ms))
    plt.close()

# Run with:
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_benchmark_cleaned.png")'
def plot_pdu_ipmi_redfish_rapl(csv_file, output_file):
    data = pd.read_csv(
        csv_file, 
        parse_dates=['timestamp'],
        date_format='%H:%M:%S')

    fig, axes = plt.subplots(figsize=(15, 10))
    fig.suptitle('PDU, IPMI and Redfish Power', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    timestamp_diff = [(value - data['timestamp'][0]).total_seconds() for value in data['timestamp']]

    axes.plot(timestamp_diff, data['IPMI_Current'], label='IPMI Power', color='blue', linewidth=2)
    axes.plot(timestamp_diff, data['Redfish_PowerControl_Current'], label='Redfish Power', color='green', linewidth=2)
    axes.plot(timestamp_diff, data['PDU-L_Load'] + data['PDU-R_Load'], 
                    label='PDU Power', linestyle='--', color='orange', linewidth=2)
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    if rapl_columns:
        rapl_power = data[rapl_columns].sum(axis=1).diff().fillna(0) * 61.035 / 10000000
        print(data[rapl_columns][130:140])
        print(rapl_power[130:140])
        axes.plot(timestamp_diff, rapl_power, label='RAPL Power', linestyle='--', color='purple', linewidth=2)

    axes.set_title('PDU, IPMI and Redfish Power Over Time')
    axes.set_xlabel('Duration (s)')
    axes.set_ylabel('Power (Watt)')
    axes.legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()
    
# Run with:
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_linear_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_linear_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_ramp-up_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_ramp-up_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_sim-ramp-up_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_sim-ramp-up_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/idle_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/idle_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/mem_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/mem_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/network_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/network_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_all_50_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_all_50_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/cpu_half_100_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_half_100_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/storage_read_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/storage_read_benchmark_cleaned.png")'
# sudo -E python3 -c 'from src.diagram import plot_cleaned_data; plot_cleaned_data("results/2025-06-11_19-33-53/cleaned/storage_write_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/storage_write_benchmark_cleaned.png")'
def plot_cleaned_data(csv_file, output_file):
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

    fig, ax = plt.subplots(figsize=(15, 10))
    fig.suptitle('Cleaned Power Data (Multiple Runs)', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    label_ipmi = f'IPMI_Current'
    label_redfish = f'Redfish_PowerControl_Current'
    label_pdu = f'PDU_Load'
    label_rapl = f'RAPL_Load'

    # This plots the power per second with range
    min_length = min(len(r) for r in runs)
    avg_ipmi = np.mean([r['IPMI_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    avg_redfish = np.mean([r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    avg_pdu = np.mean([(r['PDU-L_Load'].astype(float) + r['PDU-R_Load'].astype(float)).iloc[:min_length].values for r in runs], axis=0)
    
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    if rapl_columns:
        # print([r[rapl_columns].astype(float).sum(axis=1).diff() / 1000000 for r in runs][0].head(4))
        avg_rapl = np.mean([r[rapl_columns].astype(float).sum(axis=1).diff().fillna(0).iloc[:min_length].values / 1000000 for r in runs], axis=0)
    
    avg_timestamp = runs[0]['timestamp'].iloc[:min_length]

    ax.plot(avg_timestamp, avg_ipmi, label=label_ipmi, color='red', linestyle='-')
    ax.plot(avg_timestamp, avg_redfish, label=label_redfish, color='green', linestyle='--')
    ax.plot(avg_timestamp, avg_pdu, label=label_pdu, color='blue', linestyle='-')
    ax.plot(avg_timestamp, avg_rapl, label=label_rapl, color='blue', linestyle='--')

    # This adds the range
    min_pdu = np.min([r['PDU-L_Load'].astype(float).iloc[:min_length].values + r['PDU-R_Load'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    max_pdu = np.max([r['PDU-L_Load'].astype(float).iloc[:min_length].values + r['PDU-R_Load'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    ax.plot(avg_timestamp, min_pdu, color='blue', linestyle=':')
    ax.plot(avg_timestamp, max_pdu, color='blue', linestyle=':')
    ax.fill_between(avg_timestamp, min_pdu, max_pdu, color='blue', alpha=0.2, label='PDU Range')
    
    # TEST FOR RAPL
    # if rapl_columns:
    #     for col in rapl_columns:
    #         avg_rapl_col = np.mean([r[col].astype(float).fillna(0).iloc[:min_length].values / 1000000 for r in runs], axis=0)
    #         ax.plot(avg_timestamp, avg_rapl_col, label=f'{col} (avg)', linestyle='--')
    #         print("Average value for", col, ":", np.mean(avg_rapl_col))
    
    
    ax.set_title('IPMI, Redfish, and PDU Power Over Time (All Runs)')
    ax.set_xlabel('Duration (s)')
    ax.set_ylabel('Power (W)')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.08))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()
    
    
    # ----- Total Energy Plot ------
    
    fig, ax = plt.subplots(figsize=(15, 10))
    fig.suptitle('Total Energy Consumption (Multiple Runs)', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    total_energy_ipmi = [r['IPMI_Current'].astype(float).iloc[:min_length].sum() for r in runs]
    total_energy_redfish = [r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].sum() for r in runs]
    total_energy_pdu = [r['PDU-L_Load'].astype(float).iloc[:min_length].sum() + r['PDU-R_Load'].astype(float).iloc[:min_length].sum() for r in runs]
    total_energy_rapl = [
        (r[rapl_columns].astype(float).sum(axis=1).iloc[min_length - 1] - r[rapl_columns].astype(float).sum(axis=1).iloc[0]) / 1_000_000
        for r in runs
    ] if rapl_columns else []
    
    # print(total_energy_ipmi)
    # print(total_energy_redfish)
    # print(total_energy_pdu)
    # print(total_energy_rapl)
    
    ax.boxplot(total_energy_ipmi, positions=[0], widths=0.4, patch_artist=True, 
               boxprops=dict(facecolor='black', color='black', alpha=0.5), medianprops=dict(color='black'))
    ax.boxplot(total_energy_redfish, positions=[1], widths=0.4, patch_artist=True, 
               boxprops=dict(facecolor='red', color='red', alpha=0.5), medianprops=dict(color='red'))
    ax.boxplot(total_energy_pdu, positions=[2], widths=0.4, patch_artist=True, 
               boxprops=dict(facecolor='blue', color='blue', alpha=0.5), medianprops=dict(color='blue'))
    if total_energy_rapl:
        ax.boxplot(total_energy_rapl, positions=[3], widths=0.4, patch_artist=True, 
                   boxprops=dict(facecolor='green', color='green', alpha=0.5), medianprops=dict(color='green'))
    ax.set_xticklabels(['IPMI', 'REDFISH', 'PDU', 'RAPL'])
    ax.set_title('Total Energy Consumption')
    ax.set_ylabel('Energy (Joules)')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend([label_ipmi, label_redfish, label_pdu, label_rapl], loc='upper right', fontsize=10)
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file.replace('.png', '_total.png'))
    plt.close()

# Run with:
# sudo -E python3 -c 'from src.diagram import plot_cleaned_cpu_data; plot_cleaned_cpu_data("results/2025-06-11_19-33-53/cleaned/cpu_benchmark_cleaned.csv", "results/2025-06-11_19-33-53/cleaned/cpu_benchmark_cleaned_cpu.png")'
def plot_cleaned_cpu_data(csv_file, output_file):
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

    fig, ax = plt.subplots(figsize=(15, 10))
    fig.suptitle('Average CPU Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')
    
    # This plots the power per second with range
    min_length = min(len(r) for r in runs)
    avg_ipmi = np.mean([r['IPMI_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    avg_redfish = np.mean([r['Redfish_PowerControl_Current'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    avg_pdu = np.mean([(r['PDU-L_Load'].astype(float) + r['PDU-R_Load'].astype(float)).iloc[:min_length].values for r in runs], axis=0)
    
    rapl_columns = [col for col in data.columns if 'RAPL' in col]
    if rapl_columns:
        # print([r[rapl_columns].astype(float).sum(axis=1).diff() / 1000000 for r in runs][0].head(4))
        avg_rapl = np.mean([r[rapl_columns].astype(float).sum(axis=1).diff().fillna(0).iloc[:min_length].values / 1000000 for r in runs], axis=0)
    
    avg_timestamp = runs[0]['timestamp'].iloc[:min_length]

    ax.plot(avg_timestamp, avg_ipmi, label=label_ipmi, color='red', linestyle='-')
    ax.plot(avg_timestamp, avg_redfish, label=label_redfish, color='green', linestyle='--')
    ax.plot(avg_timestamp, avg_pdu, label=label_pdu, color='blue', linestyle='-')
    ax.plot(avg_timestamp, avg_rapl, label=label_pdu, color='blue', linestyle='--')
    
    
    # This adds the range
    min_pdu = np.min([r['PDU-L_Load'].astype(float).iloc[:min_length].values + r['PDU-R_Load'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    max_pdu = np.max([r['PDU-L_Load'].astype(float).iloc[:min_length].values + r['PDU-R_Load'].astype(float).iloc[:min_length].values for r in runs], axis=0)
    ax.plot(avg_timestamp, min_pdu, label=label_pdu, color='blue', linestyle=':')
    ax.plot(avg_timestamp, max_pdu, label=label_pdu, color='blue', linestyle=':')
    ax.fill_between(avg_timestamp, min_pdu, max_pdu, color='blue', alpha=0.2, label='PDU Range')
    
    # TEST FOR RAPL
    # if rapl_columns:
    #     for col in rapl_columns:
    #         avg_rapl_col = np.mean([r[col].astype(float).fillna(0).iloc[:min_length].values / 1000000 for r in runs], axis=0)
    #         ax.plot(avg_timestamp, avg_rapl_col, label=f'{col} (avg)', linestyle='--')
    #         print("Average value for", col, ":", np.mean(avg_rapl_col))
    
    
    ax.set_title('IPMI, Redfish, and PDU Power Over Time (All Runs)')
    ax.set_xlabel('Duration (s)')
    ax.set_ylabel('Power (W)')
    ax.legend(ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.08))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()
        
    