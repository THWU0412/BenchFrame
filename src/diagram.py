import pandas as pd
import matplotlib.pyplot as plt

# Run with:
# python -c 'from src.diagram import plot_diagrams; plot_diagrams("results/2025-04-30_09-36-04/simultaneous.csv", "results/2025-04-30_09-36-04/simultaneous.png")'

def plot_diagrams(csv_file, output_file):
    data = pd.read_csv(csv_file, parse_dates=['timestamp'])

    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Power Consumption Diagrams', fontsize=16)
    fig.text(0.5, 0.94, f'{csv_file.split("/")[-1].split(".")[0].capitalize()}', ha='center', fontsize=10, color='gray')

    # Plot Current
    axes[0, 0].plot(data['timestamp'], data['Node3-L_Current'], label='Node3-L_Current')
    axes[0, 0].plot(data['timestamp'], data['Node3-R_Current'], label='Node3-R_Current')
    axes[0, 0].plot(data['timestamp'], data['IPMI_Current'], label='IPMI_Current')
    axes[0, 0].plot(data['timestamp'], data['Node3-L_Current'] + data['Node3-R_Current'], 
                    label='Sum_Current_Node3', linestyle='--')
    axes[0, 0].set_title('Current')
    axes[0, 0].set_xlabel('Timestamp')
    axes[0, 0].set_ylabel('Current')
    axes[0, 0].legend()

    # Plot PowerFactor
    # axes[0, 1].plot(data['timestamp'], data['Node3-L_PowerFactor'], label='Node3-L_PowerFactor')
    # axes[0, 1].plot(data['timestamp'], data['Node3-R_PowerFactor'], label='Node3-R_PowerFactor')
    axes[0, 1].plot(data['timestamp'], data['Node3-L_PowerFactor'] + data['Node3-R_PowerFactor'], 
                    label='Sum_PowerFactor', linestyle='--')
    axes[0, 1].set_title('PowerFactor')
    axes[0, 1].set_xlabel('Timestamp')
    axes[0, 1].set_ylabel('PowerFactor')
    axes[0, 1].legend()

    # Plot Load
    # axes[1, 0].plot(data['timestamp'], data['Node3-L_Load'], label='Node3-L_Load')
    # axes[1, 0].plot(data['timestamp'], data['Node3-R_Load'], label='Node3-R_Load')
    axes[1, 0].plot(data['timestamp'], data['Node3-L_Load'] + data['Node3-R_Load'], 
                    label='Sum_Load', linestyle='--')
    axes[1, 0].set_title('Load')
    axes[1, 0].set_xlabel('Timestamp')
    axes[1, 0].set_ylabel('Load')
    axes[1, 0].legend()

    # Plot Energy
    # axes[1, 1].plot(data['timestamp'], data['Node3-L_Energy'], label='Node3-L_Energy')
    # axes[1, 1].plot(data['timestamp'], data['Node3-R_Energy'], label='Node3-R_Energy')
    axes[1, 1].plot(data['timestamp'], data['Node3-L_Energy'] + data['Node3-R_Energy'], 
                    label='Sum_Energy', linestyle='--')
    axes[1, 1].set_title('Energy')
    axes[1, 1].set_xlabel('Timestamp')
    axes[1, 1].set_ylabel('Energy')
    axes[1, 1].legend()

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(output_file)
    plt.close()
