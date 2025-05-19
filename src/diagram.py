import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

# Run with:
# python -c 'from src.diagram import plot_diagrams; plot_diagrams("results/2025-05-14_09-33-14/cpu_seq.csv", "results/2025-05-14_09-33-14/cpu_seq.png")'
# python -c 'from src.diagram import plot_diagrams; plot_diagrams("results/2025-05-07_11-54-49/simultaneous.csv", "results/2025-05-07_11-54-49/simultaneous.png")'

def plot_diagrams(csv_file, output_file):
    data = pd.read_csv(csv_file, parse_dates=['timestamp'])

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Power Consumption Diagrams', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')

    # Plot Current
    # axes[0, 0].plot(data['timestamp'], data['PDU-L_Current'], label='PDU-L_Current')
    # axes[0, 0].plot(data['timestamp'], data['PDU-R_Current'], label='PDU-R_Current')
    axes[0, 0].plot(data['timestamp'], data['PDU-L_Current'] + data['PDU-R_Current'], 
                    label='Sum_Current_PDU', linestyle='--')
    axes[0, 0].set_title('Current')
    axes[0, 0].set_xlabel('Timestamp')
    axes[0, 0].set_ylabel('Current (mA)')
    axes[0, 0].legend()

    # Plot PowerFactor
    # axes[0, 1].plot(data['timestamp'], data['PDU-L_PowerFactor'], label='PDU-L_PowerFactor')
    # axes[0, 1].plot(data['timestamp'], data['PDU-R_PowerFactor'], label='PDU-R_PowerFactor')
    axes[0, 1].plot(data['timestamp'], (data['PDU-L_PowerFactor'] + data['PDU-R_PowerFactor']) / 2, 
                    label='Avg_PowerFactor', linestyle='--')
    axes[0, 1].set_title('PowerFactor')
    axes[0, 1].set_xlabel('Timestamp')
    axes[0, 1].set_ylabel('PowerFactor')
    axes[0, 1].legend()

    # Plot Load
    # axes[1, 0].plot(data['timestamp'], data['PDU-L_Load'], label='PDU-L_Load')
    # axes[1, 0].plot(data['timestamp'], data['PDU-R_Load'], label='PDU-R_Load')
    axes[1, 0].plot(data['timestamp'], data['PDU-L_Load'] + data['PDU-R_Load'], 
                    label='Sum_Load', linestyle='--')
    axes[1, 0].plot(data['timestamp'], data['IPMI_Current'], label='IPMI_Current')
    axes[1, 0].set_title('Load')
    axes[1, 0].set_xlabel('Timestamp')
    axes[1, 0].set_ylabel('Load (W)')
    axes[1, 0].legend()

    # Plot Energy
    # axes[1, 1].plot(data['timestamp'], data['PDU-L_Energy'], label='PDU-L_Energy')
    # axes[1, 1].plot(data['timestamp'], data['PDU-R_Energy'], label='PDU-R_Energy')
    axes[1, 1].plot(data['timestamp'], data['PDU-L_Energy'] + data['PDU-R_Energy'], 
                    label='Sum_Energy', linestyle='--')
    axes[1, 1].set_title('Energy')
    axes[1, 1].set_xlabel('Timestamp')
    axes[1, 1].set_ylabel('Energy (Wh)')
    axes[1, 1].legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

# Run with:
# python -c 'from src.diagram import plot_avg_cpu_usage; plot_avg_cpu_usage("results/2025-05-08_11-33-52/sequential.csv", "results/2025-05-08_11-33-52/cpu_sequential.png")'
# python -c 'from src.diagram import plot_avg_cpu_usage; plot_avg_cpu_usage("results/2025-05-08_11-33-52/simultaneous.csv", "results/2025-05-08_11-33-52/cpu_simultaneous.png")'
def plot_avg_cpu_usage(csv_file, output_file):
    data = pd.read_csv(csv_file, parse_dates=['timestamp'])

    fig, axes = plt.subplots(figsize=(15, 10))
    fig.suptitle('CPU Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')

    data['Average_CPU'] = data[[f'CPU{i}' for i in range(1, 21)]].mean(axis=1)
    data['Avg_CPU_smooth'] = data['Average_CPU'].rolling(window=10).mean()
    axes.plot(data['timestamp'], data['Average_CPU'], label='Average_CPU', color='red', linewidth=2)
    axes.plot(data['timestamp'], data['Avg_CPU_smooth'], label='Smoothed Avg CPU', color='blue', linewidth=2)

    axes.set_title('CPU Usage Over Time')
    axes.set_xlabel('Timestamp')
    axes.set_ylabel('Avg CPU Usage (%)')
    axes.legend(ncol=2, loc='upper center', bbox_to_anchor=(0.5, -0.1))

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

# Run with:
# python -c 'from src.diagram import plot_all_cpus; plot_all_cpus("results/2025-05-07_16-56-44/sequential.csv", "results/2025-05-07_16-56-44/cpu_sequential_all.png")'
# python -c 'from src.diagram import plot_all_cpus; plot_all_cpus("results/2025-05-07_16-56-44/simultaneous.csv", "results/2025-05-07_16-56-44/cpu_simultaneous_all.png")'
def plot_all_cpus(csv_file, output_file):
    data = pd.read_csv(csv_file, parse_dates=['timestamp'])

    fig, axes = plt.subplots(4, 5, figsize=(15, 10))  # 4 rows, 5 columns
    fig.suptitle('CPU Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')

    for i in range(1, 21):
        row = (i - 1) // 5
        col = (i - 1) % 5
        ax = axes[row, col]
        ax.plot(data['timestamp'], data[f'CPU{i}'], label=f'CPU{i}')
        ax.set_title(f'CPU {i}')
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Usage (%)')

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()

def plot_memory_usage(csv_file, output_file):
    data = pd.read_csv(csv_file, parse_dates=['timestamp'])

    fig, axes = plt.subplots(figsize=(15, 10))
    fig.suptitle('Memory Usage', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')

    axes.plot(data['timestamp'], data['Memory_Usage'], label='Memory Usage', color='green', linewidth=2)

    axes.set_title('Memory Usage Over Time')
    axes.set_xlabel('Timestamp')
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