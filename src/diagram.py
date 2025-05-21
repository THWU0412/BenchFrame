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
    
    # No idea wether this is correct or not, but it seems to be the right order of magnitude.
    
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