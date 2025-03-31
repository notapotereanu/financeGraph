import matplotlib.pyplot as plt
import numpy as np
import os

# Create output directory if it doesn't exist
os.makedirs('figures', exist_ok=True)

# Set consistent styling
plt.style.use('seaborn-v0_8-pastel')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial']
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['axes.labelsize'] = 12

def generate_figure_9():
    """Bar chart comparing task completion times and accuracy between Finance Graph Explorer and traditional tools"""
    print("Generating Figure 9...")
    
    # Data
    tools = ['Finance Graph Explorer', 'Traditional Tools']
    completion_time = [4.2, 15.5]  # minutes
    accuracy = [85, 63]  # percentage

    # Set width of bars
    barWidth = 0.3
    r1 = np.arange(len(tools))
    r2 = [x + barWidth for x in r1]

    # Create the figure and axes
    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax2 = ax1.twinx()

    # Create bars
    ax1.bar(r1, completion_time, width=barWidth, color='#4E79A7', label='Completion Time (min)')
    ax2.bar(r2, accuracy, width=barWidth, color='#59A14F', label='Accuracy (%)')

    # Add labels and title
    ax1.set_xlabel('Tools')
    ax1.set_ylabel('Completion Time (minutes)', color='#4E79A7')
    ax2.set_ylabel('Accuracy (%)', color='#59A14F')
    plt.title('Task Completion Time and Accuracy Comparison')

    # Set x-axis ticks
    plt.xticks([r + barWidth/2 for r in range(len(tools))], tools)

    # Create legends
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper center')

    # Add grid
    ax1.grid(axis='y', linestyle='--', alpha=0.7)

    # Save figure
    plt.tight_layout()
    plt.savefig('figures/figure9_task_comparison.png', dpi=300)
    plt.close()

def generate_figure_10():
    """Pie chart showing relative time spent gathering data from different sources"""
    print("Generating Figure 10...")
    
    # Data
    sources = ['SEC EDGAR (Insiders)', 'SEC EDGAR (Officers)', 'Google Trends', 'News APIs', 'Market Data APIs']
    time_spent = [4.7, 3.2, 2.8, 0.25, 0.13]  # minutes

    # Colors
    colors = ['#F28E2B', '#E15759', '#76B7B2', '#59A14F', '#B07AA1']

    # Create pie chart
    plt.figure(figsize=(10, 7))
    patches, texts, autotexts = plt.pie(
        time_spent, 
        labels=sources, 
        colors=colors, 
        autopct='%1.1f%%', 
        startangle=90,
        shadow=False,
        wedgeprops={'edgecolor': 'w', 'linewidth': 1}
    )
    
    # Style text elements
    for text in texts:
        text.set_fontsize(11)
    for autotext in autotexts:
        autotext.set_fontsize(10)
        autotext.set_weight('bold')
        autotext.set_color('white')
    
    plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    plt.title('Relative Time Spent Gathering Data from Different Sources')
    plt.tight_layout()
    plt.savefig('figures/figure10_data_gathering_pie.png', dpi=300)
    plt.close()

def generate_figure_11():
    """Line chart showing query performance advantage of graph database scaling with dataset size and query complexity"""
    print("Generating Figure 11...")
    
    # Data
    dataset_sizes = ['Small', 'Medium', 'Large']
    simple_queries = [0.7, 0.8, 0.9]  # Performance ratio (Neo4j/SQL)
    complex_queries = [5.3, 8.7, 12.5]  # Performance ratio (Neo4j/SQL)

    plt.figure(figsize=(10, 6))
    plt.plot(dataset_sizes, simple_queries, marker='o', color='#E15759', linewidth=2.5, markersize=10, label='Simple Queries')
    plt.plot(dataset_sizes, complex_queries, marker='s', color='#4E79A7', linewidth=2.5, markersize=10, label='Complex Queries')

    plt.axhline(y=1.0, color='gray', linestyle='--', alpha=0.7, label='Equal Performance')

    # Add annotations
    for i, value in enumerate(complex_queries):
        plt.annotate(f"{value}x", 
                   xy=(i, value), 
                   xytext=(0, 10),  
                   textcoords="offset points",
                   ha='center',
                   fontweight='bold',
                   fontsize=10)
    
    for i, value in enumerate(simple_queries):
        plt.annotate(f"{value}x", 
                   xy=(i, value), 
                   xytext=(0, -15),  
                   textcoords="offset points",
                   ha='center',
                   fontweight='bold',
                   fontsize=10)

    plt.xlabel('Dataset Size')
    plt.ylabel('Performance Ratio (Neo4j/SQL)')
    plt.title('Query Performance Advantage by Dataset Size and Query Complexity')
    plt.ylim(0, 15)
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('figures/figure11_query_performance.png', dpi=300)
    plt.close()

def generate_figure_12():
    """Bar chart comparing data gathering times with and without optimizations"""
    print("Generating Figure 12...")
    
    # Data
    data_sources = ['SEC EDGAR', 'Google Trends', 'News APIs', 'Market Data', 'All Sources']
    without_opt = [7.9, 2.8, 0.25, 0.13, 11.08]  # minutes
    with_opt = [2.5, 0.9, 0.08, 0.04, 3.52]  # minutes

    x = np.arange(len(data_sources))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 7))
    rects1 = ax.bar(x - width/2, without_opt, width, label='Without Optimizations', color='#E15759')
    rects2 = ax.bar(x + width/2, with_opt, width, label='With Optimizations', color='#59A14F')

    # Add labels and other details
    ax.set_ylabel('Time (minutes)')
    ax.set_xlabel('Data Source')
    ax.set_title('Data Gathering Time With and Without Optimizations')
    ax.set_xticks(x)
    ax.set_xticklabels(data_sources)
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    # Add percentage improvement labels
    for i, (w, wo) in enumerate(zip(with_opt, without_opt)):
        improvement = (wo - w) / wo * 100
        ax.annotate(f'{improvement:.0f}% faster', 
                    xy=(i, w + 0.1), 
                    ha='center', 
                    va='bottom',
                    fontsize=10,
                    fontweight='bold')

    plt.tight_layout()
    plt.savefig('figures/figure12_optimization_comparison.png', dpi=300)
    plt.close()

def generate_figure_13():
    """Line chart showing query performance improvements with optimizations"""
    print("Generating Figure 13...")
    
    # Data
    query_complexity = ['Simple', 'Medium', 'Complex', 'Very Complex']
    before_opt = [120, 350, 820, 1900]  # milliseconds
    after_opt = [45, 140, 290, 570]  # milliseconds

    plt.figure(figsize=(10, 6))
    plt.plot(query_complexity, before_opt, marker='o', linewidth=2.5, markersize=10, color='#E15759', label='Before Optimization')
    plt.plot(query_complexity, after_opt, marker='s', linewidth=2.5, markersize=10, color='#59A14F', label='After Optimization')

    # Calculate and display improvement percentages
    for i in range(len(query_complexity)):
        improvement = (before_opt[i] - after_opt[i]) / before_opt[i] * 100
        mid_y = (before_opt[i] + after_opt[i]) / 2
        plt.annotate(f'{improvement:.0f}% faster', 
                    xy=(i, mid_y),
                    xytext=(15, 0),
                    textcoords='offset points',
                    ha='left',
                    fontweight='bold',
                    fontsize=10,
                    arrowprops=dict(arrowstyle='->', color='#4E79A7'))

    plt.xlabel('Query Complexity')
    plt.ylabel('Execution Time (ms)')
    plt.title('Query Performance Improvements with Optimizations')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig('figures/figure13_query_optimization.png', dpi=300)
    plt.close()

def generate_figure_14():
    """Bar chart comparing visualization rendering times with and without optimizations"""
    print("Generating Figure 14...")
    
    # Data
    visualization_types = ['Network Graph', 'Sentiment-Price Chart', 'Insider Analysis']
    small_before = [1.2, 0.8, 0.7]  # seconds
    small_after = [0.8, 0.5, 0.5]  # seconds
    large_before = [10.5, 3.2, 2.8]  # seconds
    large_after = [3.2, 1.5, 1.3]  # seconds

    # Set width of bars
    barWidth = 0.2
    r1 = np.arange(len(visualization_types))
    r2 = [x + barWidth for x in r1]
    r3 = [x + barWidth for x in r2]
    r4 = [x + barWidth for x in r3]

    # Create the figure
    fig, ax = plt.subplots(figsize=(12, 7))

    # Create bars
    bars1 = ax.bar(r1, small_before, width=barWidth, color='#F28E2B', label='Small Dataset (Before)')
    bars2 = ax.bar(r2, small_after, width=barWidth, color='#76B7B2', label='Small Dataset (After)')
    bars3 = ax.bar(r3, large_before, width=barWidth, color='#E15759', label='Large Dataset (Before)')
    bars4 = ax.bar(r4, large_after, width=barWidth, color='#59A14F', label='Large Dataset (After)')

    # Add labels and other details
    ax.set_xlabel('Visualization Type')
    ax.set_ylabel('Rendering Time (seconds)')
    ax.set_title('Visualization Rendering Times With and Without Optimizations')
    ax.set_xticks([r + barWidth*1.5 for r in range(len(visualization_types))])
    ax.set_xticklabels(visualization_types)
    ax.legend()
    ax.grid(axis='y', alpha=0.3)

    # Add improvement labels for large datasets
    for i in range(len(visualization_types)):
        improvement = (large_before[i] - large_after[i]) / large_before[i] * 100
        ax.annotate(f'{improvement:.0f}% faster', 
                    xy=(r4[i], large_after[i] + 0.2),
                    ha='center',
                    fontsize=10,
                    fontweight='bold')

    plt.tight_layout()
    plt.savefig('figures/figure14_visualization_performance.png', dpi=300)
    plt.close()

def generate_figure_15():
    """Radar chart showing user satisfaction before and after improvements across different dimensions"""
    print("Generating Figure 15...")
    
    # Data
    dimensions = ['Ease of Understanding', 'Visualization Clarity', 
                'Performance', 'Analysis Depth', 'Interface Usability']
    before = [3.2, 3.4, 3.1, 4.2, 3.7]  # Scores out of 5
    after = [4.5, 4.6, 4.1, 4.5, 4.6]  # Scores out of 5

    # Calculate improvement percentages
    improvements = [(a - b) / b * 100 for a, b in zip(after, before)]

    # Number of variables
    N = len(dimensions)

    # We need to repeat the first value to close the circular graph
    dimensions = dimensions + [dimensions[0]]
    before = before + [before[0]]
    after = after + [after[0]]

    # Compute angle for each dimension
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]  # Close the loop

    # Initialize the figure
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    # Draw one axis per variable + add labels
    plt.xticks(angles[:-1], dimensions[:-1], size=12)

    # Draw the limit lines for each variable (0-5)
    ax.set_rlabel_position(0)
    plt.yticks([1, 2, 3, 4, 5], ["1", "2", "3", "4", "5"], color="grey", size=10)
    plt.ylim(0, 5)

    # Plot data
    ax.plot(angles, before, color='#E15759', linewidth=2, label='Before Improvements')
    ax.fill(angles, before, color='#E15759', alpha=0.1)
    ax.plot(angles, after, color='#4E79A7', linewidth=2, label='After Improvements')
    ax.fill(angles, after, color='#4E79A7', alpha=0.1)

    # Add simple improvement labels (without arrows which were causing issues)
    for i in range(len(dimensions)-1):
        improvement = improvements[i]
        # Position between the before and after lines
        radius = (before[i] + after[i]) / 2
        angle = angles[i]
        plt.annotate(f"+{improvement:.0f}%", 
                  xy=(angle, radius),
                  ha='center',
                  va='center',
                  fontsize=10,
                  fontweight='bold',
                  color='green',
                  bbox=dict(boxstyle="round,pad=0.3", 
                           fc="white", 
                           ec="green", 
                           alpha=0.8))

    # Add legend
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))

    # Add title
    plt.title('User Satisfaction Before and After Improvements', size=15)

    plt.tight_layout()
    plt.savefig('figures/figure15_user_satisfaction.png', dpi=300)
    plt.close()

def main():
    """Generate all figures for the Finance Graph Database Explorer evaluation chapter"""
    print("Starting to generate all figures...")
    
    # Generate each figure
    generate_figure_9()
    generate_figure_10()
    generate_figure_11()
    generate_figure_12()
    generate_figure_13()
    generate_figure_14()
    generate_figure_15()
    
    print(f"All figures generated successfully and saved to the 'figures' directory!")

if __name__ == "__main__":
    main() 