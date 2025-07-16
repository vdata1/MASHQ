import json
import matplotlib.pyplot as plt
from collections import defaultdict

# activate latex text rendering
plt.rc('text', usetex=True)
plt.rc('axes', linewidth=2)
plt.rc('font', weight='bold')
plt.rcParams['text.latex.preamble'] = r'\usepackage{sfmath} \boldmath'


# Load JSON data from file
with open('test_data.json', 'r') as f:
    data = json.load(f)

# Color codes by OS
os_colors = {
    'linux': 'tab:blue',
    'windows': 'tab:orange'
}

# Line styles by dataset
dataset_styles = {
    'test262': 'solid',
    'v8': 'dashed',
    'webkit': 'dotted'
}

# Group data by (dataset, operating_system)
grouped_data = defaultdict(list)
for entry in data:
    if entry['dataset'] != 'webkit':
        key = (entry['dataset'], entry['operating_system'])
        grouped_data[key].append((entry['round_number'], entry['triggered_filters']))

# Plotting
plt.figure(figsize=(10, 6))
for (dataset, os), values in grouped_data.items():
    # Sort values by round_number
    values.sort(key=lambda x: x[0])
    rounds, triggered = zip(*values)
    label = f'{dataset} on {os}'
    plt.plot(
        rounds,
        triggered,
        label=label,
        color=os_colors[os],
        linestyle=dataset_styles[dataset],
        marker='o'
    )

# Labels and legend
plt.xlabel(r'\textbf{Round Number}', fontsize=18)
plt.ylabel(r'\textbf{Total Number of Differences}', fontsize=18)

ax = plt.gca()
ax.xaxis.set_tick_params(labelsize=20)
ax.yaxis.set_tick_params(labelsize=20)
ax.yaxis.set_tick_params(rotation=45)  

#plt.title('Filters Triggered vs. Rounds')
plt.legend(prop={'weight': 'bold', 'size': 15})
plt.grid(False)
plt.tight_layout()


# Save plot to PDF
plt.savefig('filters_vs_rounds.pdf', format='pdf')

# Show plot
plt.show()