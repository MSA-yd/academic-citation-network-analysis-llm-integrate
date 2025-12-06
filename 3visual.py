#!/usr/bin/env python3
"""
Full network visualization: Main nodes=papers, Small nodes=references
Leiden community visualization with PageRank support
Output: csv + static/interactive graphs (with complete ID labels)
"""

import os
import argparse
import pandas as pd
import numpy as np
import networkx as nx
import igraph as ig
import leidenalg as la
import matplotlib.pyplot as plt
from pyvis.network import Network
from pathlib import Path
from typing import Optional, Tuple, Dict, List
from config import Config
from utils.logger import setup_logger
from utils.data_loader import load_data_files

logger = setup_logger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Generate network visualizations with Leiden community detection",
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
Examples:
  # Use default settings (auto-skip Kamada-Kawai for large graphs)
  python 3visual.py
  
  # Force skip Kamada-Kawai layout
  python 3visual.py --skip-kamada-kawai
  
  # Force compute Kamada-Kawai even for large graphs
  python 3visual.py --no-auto-skip
    """
)
parser.add_argument(
    '--skip-kamada-kawai',
    action='store_true',
    help='Skip Kamada-Kawai layout (recommended for large graphs with >5000 nodes)'
)
parser.add_argument(
    '--no-auto-skip',
    action='store_true',
    help='Disable auto-skip for large graphs (force compute Kamada-Kawai even for >5000 nodes)'
)
args = parser.parse_args()

# Ensure directories exist
Config.ensure_directories()

# 1. Load data -------------------------------------------------------------
logger.info("Loading data...")
try:
    # Load papers and edges (node_comm will be generated later, so it's optional)
    papers, edges_df, _ = load_data_files(raise_on_missing=False)
    
    # Validate that required files (papers and edges) were loaded
    if len(papers) == 0:
        raise FileNotFoundError(f"Required file not found or empty: {Config.PAPERS_CLEANED}")
    if len(edges_df) == 0:
        raise FileNotFoundError(f"Required file not found or empty: {Config.EDGES_CLEANED}")
    
    logger.info(f"Loaded: {len(papers)} papers, {len(edges_df)} edges")
except FileNotFoundError as e:
    logger.error(f"Required data files not found: {e}")
    raise

# 2. Build graph: paper → reference --------------------------------------------
G = nx.DiGraph()

# First add all paper nodes
paper_ids = set(papers["arxiv_id"])
for _, row in papers.iterrows():
    G.add_node(str(row["arxiv_id"]), node_type="paper", **row.to_dict())

# Add reference nodes and ensure they have node_type attribute
ref_nodes = set(edges_df["target"].dropna())
for rid in ref_nodes:
    if rid and str(rid) not in paper_ids:  # Ensure not a paper node
        G.add_node(str(rid), node_type="reference")

# Add edges
for _, row in edges_df.iterrows():
    src, tgt = row["source"], row["target"]
    if pd.notna(tgt) and tgt:
        G.add_edge(str(src), str(tgt))

logger.info(
    f"Full graph nodes: {len(G):,}  "
    f"(papers: {len(paper_ids):,} + references: "
    f"{len([n for n in G if G.nodes[n].get('node_type')=='reference']):,})"
)
logger.info(f"Full graph edges: {G.number_of_edges():,}")

# 3. Ensure all nodes have node_type attribute ------------------------------------
for node in G.nodes():
    if 'node_type' not in G.nodes[node]:
        # If node is in paper list, it's a paper, otherwise it's a reference
        if node in [str(pid) for pid in paper_ids]:
            G.nodes[node]['node_type'] = 'paper'
        else:
            G.nodes[node]['node_type'] = 'reference'

# 4. Leiden community detection (undirected graph) ------------------------------------------
logger.info("Detecting Leiden communities...")
undirected = G.to_undirected()
ig_graph = ig.Graph.from_networkx(undirected)
partition = la.find_partition(
    ig_graph,
    la.ModularityVertexPartition,
    seed=Config.LEIDEN_SEED
)
logger.info(f"Found {len(partition)} communities")
node_list = list(undirected.nodes())
partition_dict = {node_list[i]: comm for i, comm in enumerate(partition.membership)}

# 5. Export table (community only) --------------------------------------------------
node_df = pd.DataFrame(
    [(n, G.nodes[n]["node_type"], partition_dict[n]) for n in undirected.nodes()],
    columns=["id", "node_type", "leiden_comm"]
)
node_df.to_csv(Config.NODE_COMM, index=False, encoding='utf-8')
logger.info(f"Community data saved: {Config.NODE_COMM}")

# 6. Try multiple layout algorithms ------------------------------------------------
paper_nodes = [n for n in undirected.nodes() if G.nodes[n]["node_type"] == "paper"]
ref_nodes = [n for n in undirected.nodes() if G.nodes[n]["node_type"] == "reference"]

logger.info(f"Visualization nodes: {len(paper_nodes)} papers, {len(ref_nodes)} references")

# Method 1: Kamada-Kawai layout (based on graph distance)
layout_methods = []
num_nodes = len(undirected.nodes())
skip_kk = args.skip_kamada_kawai or (not args.no_auto_skip and num_nodes > Config.SKIP_KAMADA_KAWAI_AUTO_THRESHOLD)

if skip_kk:
    if args.skip_kamada_kawai:
        logger.info(f"Skipping Kamada-Kawai layout (nodes: {num_nodes:,}) - forced by --skip-kamada-kawai flag")
    else:
        logger.info(f"Skipping Kamada-Kawai layout (nodes: {num_nodes:,} > threshold: {Config.SKIP_KAMADA_KAWAI_AUTO_THRESHOLD}). Use --no-auto-skip to force computation.")
else:
    logger.info("Computing Kamada-Kawai layout...")
    try:
        pos_kk = nx.kamada_kawai_layout(undirected)
        layout_methods = [('kamada_kawai', pos_kk)]
        logger.info("Kamada-Kawai layout completed")
    except Exception as e:
        logger.warning(f"Kamada-Kawai layout failed: {e}, using spring layout")
        layout_methods = []

# Method 2: Community-based layout
logger.info("Computing community layout...")
try:
    # Use community information to organize layout
    pos_community = {}
    communities = {}
    for node, comm in partition_dict.items():
        if comm not in communities:
            communities[comm] = []
        communities[comm].append(node)
    
    # Assign a circular area for each community
    num_communities = len(communities)
    angle_step = 2 * np.pi / num_communities if num_communities > 0 else 0
    
    for i, (comm, nodes) in enumerate(communities.items()):
        # Community center position
        center_x = np.cos(i * angle_step)
        center_y = np.sin(i * angle_step)
        
        # Use spring layout within community
        subgraph = undirected.subgraph(nodes)
        if len(nodes) > 1:
            sub_pos = nx.spring_layout(subgraph, seed=42, k=0.3)
            for node, (x, y) in sub_pos.items():
                pos_community[node] = (center_x + x * 0.5, center_y + y * 0.5)
        else:
            pos_community[nodes[0]] = (center_x, center_y)
    
    layout_methods.append(('community_based', pos_community))
except Exception as e:
    logger.warning(f"Community layout failed: {e}")

# Method 3: Multipart layout (layered by node type)
logger.info("Computing multipart layout...")
try:
    pos_multipart = {}
    
    # Paper nodes on upper layer, reference nodes on lower layer
    paper_y = 1.0
    ref_y = 0.0
    
    # Assign x coordinates for paper nodes
    paper_nodes_sorted = sorted(paper_nodes)
    for i, node in enumerate(paper_nodes_sorted):
        x = (i - len(paper_nodes_sorted) / 2) / max(1, len(paper_nodes_sorted) / 4)
        pos_multipart[node] = (x, paper_y)
    
    # Assign positions for reference nodes, close to their connected paper nodes
    for node in ref_nodes:
        neighbors = list(undirected.neighbors(node))
        if neighbors:
            # Find average position of neighbor nodes
            neighbor_positions = [pos_multipart.get(n, (0, 0)) for n in neighbors if n in pos_multipart]
            if neighbor_positions:
                avg_x = np.mean([p[0] for p in neighbor_positions])
                # Add some random offset to avoid overlap
                pos_multipart[node] = (avg_x + np.random.normal(0, 0.1), ref_y + np.random.normal(0, 0.05))
            else:
                pos_multipart[node] = (np.random.normal(0, 1), ref_y)
        else:
            pos_multipart[node] = (np.random.normal(0, 1), ref_y)
    
    layout_methods.append(('multipart', pos_multipart))
except Exception as e:
    logger.warning(f"Multipart layout failed: {e}")

# Method 4: Improved spring layout
logger.info("Computing improved spring layout...")
pos_spring = nx.spring_layout(undirected, seed=Config.LEIDEN_SEED, k=1.5, iterations=200, scale=2)
layout_methods.append(('spring_improved', pos_spring))

# 7. Generate static graphs for each layout ------------------------------------------------
for layout_name, pos in layout_methods:
    plt.figure(figsize=(16, 12))
    
    # Draw edges
    nx.draw_networkx_edges(undirected, pos, alpha=0.15, width=0.3, edge_color="gray")
    
    # Draw reference nodes (small circles)
    if ref_nodes:
        nx.draw_networkx_nodes(undirected, pos, nodelist=ref_nodes,
                               node_color=[partition_dict[n] for n in ref_nodes],
                               node_size=80,
                               cmap="tab20", alpha=0.8, node_shape='o')
    
    # Draw paper nodes (large squares)
    if paper_nodes:
        nx.draw_networkx_nodes(undirected, pos, nodelist=paper_nodes,
                               node_color=[partition_dict[n] for n in paper_nodes],
                               node_size=400,
                               cmap="tab20", alpha=0.9, node_shape='s', 
                               edgecolors='black', linewidths=1.5)
    
    # Only show simplified labels for paper nodes
    if paper_nodes:
        paper_labels = {n: f"P{i}" for i, n in enumerate(paper_nodes)}
        nx.draw_networkx_labels(undirected, pos, labels=paper_labels,
                               font_size=6, font_color="black", font_weight="bold")
    
    plt.title(
        f"Full Network - Layout: {layout_name}\n"
        f"Square=paper, Circle=reference, Color=Leiden community",
        fontsize=12
    )
    plt.axis("off")
    plt.tight_layout()
    output_path = Config.FIG_DIR / f"full_network_{layout_name}.png"
    plt.savefig(output_path, dpi=Config.FIGURE_DPI, bbox_inches='tight')
    plt.close()
    logger.info(f"Static graph saved: {output_path}")

# 8. Interactive graph using best layout ------------------------------------------------
# Choose community layout or multipart layout as basis for interactive graph
best_pos = layout_methods[1][1] if len(layout_methods) > 1 else layout_methods[0][1]

net = Network(
    height=Config.INTERACTIVE_GRAPH_HEIGHT,
    width="100%",
    bgcolor="#ffffff",
    font_color="black"
)
net.set_options("""
var options = {
  "physics": {
    "enabled": true,
    "stabilization": {"iterations": 150},
    "repulsion": {"nodeDistance": 100},
    "springLength": 95
  }
}
""")

# Create simplified label mapping for paper nodes
paper_label_map = {n: f"P{i}" for i, n in enumerate(paper_nodes)}

for n in undirected.nodes():
    comm = int(partition_dict[n])
    ntype = G.nodes[n]["node_type"]
    
    # Set node position
    x, y = best_pos[n]
    
    if ntype == "paper":
        label = paper_label_map.get(n, n[-7:])
        net.add_node(n,
                     label=label,
                     title=f"Paper: {n}\nType: {ntype}\nCommunity: {comm}",
                     group=comm,
                     size=20,
                     x=x*100,  # Scale position
                     y=y*100,
                     shape='square',
                     borderWidth=2,
                     color={'border': '#000000', 'background': f'hsl({comm*50}, 70%, 60%)'},
                     font={'size': 14})
    else:
        net.add_node(n,
                     label="",
                     title=f"Reference: {n}\nType: {ntype}\nCommunity: {comm}",
                     group=comm,
                     size=6,
                     x=x*100,
                     y=y*100,
                     shape='dot',
                     color=f'hsl({comm*50}, 50%, 70%)')

for u, v in undirected.edges():
    net.add_edge(u, v, width=0.3, color="rgba(150,150,150,0.3)")

interactive_path = Config.FIG_DIR / "full_interactive_leiden_only.html"
net.save_graph(str(interactive_path))
logger.info(f"Interactive graph saved: {interactive_path}")

# 9. Save paper node label mapping
paper_mapping_df = pd.DataFrame(
    [(orig, label) for orig, label in paper_label_map.items()],
    columns=["arxiv_id", "display_label"]
)
mapping_path = Config.FIG_DIR / "paper_label_mapping.csv"
paper_mapping_df.to_csv(mapping_path, index=False, encoding='utf-8')
logger.info(f"Paper label mapping saved: {mapping_path}")

# 10. Community statistics ----------------------------------------------------
comm_stats = node_df.groupby(['leiden_comm', 'node_type']).size().unstack(fill_value=0)
comm_stats['total'] = comm_stats.sum(axis=1)
logger.info("\nCommunity statistics:")
logger.info(f"\n{comm_stats}")
logger.info(f"\nTotal communities: {len(comm_stats)}")

# 11. PageRank Visualization (if available) ----------------------------
if Config.PAGERANK_RESULTS.exists():
    logger.info("Generating PageRank visualizations...")
    try:
        import plotly.express as px
        import plotly.graph_objects as go
        
        df_pr = pd.read_csv(Config.PAGERANK_RESULTS)
        
        # 1. Top 20 comparison scatter plot
        top20_std = df_pr.nsmallest(20, 'rank_std')
        top20_temp = df_pr.nsmallest(20, 'rank_temp')
        top_combined = pd.concat([top20_std, top20_temp]).drop_duplicates('arxiv_id')
        
        # Scatter plot: year vs Temporal PageRank, point size = standard PageRank
        fig_scatter = px.scatter(
            top_combined,
            x='year',
            y='temporal_pagerank_score',
            size='pagerank_score',
            hover_name='title',
            hover_data=['rank_std', 'rank_temp'],
            color='rank_temp',
            color_continuous_scale='Viridis_r',
            title="Temporal PageRank Recommendation Analysis<br><sub>Point size = Standard PageRank, Color = Temporal PageRank Rank</sub>",
            labels={
                'year': 'Publication Year',
                'temporal_pagerank_score': 'Temporal PageRank Score',
                'pagerank_score': 'Standard PageRank Score'
            }
        )
        fig_scatter.update_layout(width=1200, height=800)
        scatter_path = Config.FIG_DIR / "temporal_recommendations.html"
        fig_scatter.write_html(str(scatter_path))
        logger.info(f"Scatter plot saved: {scatter_path}")
        
        # 2. Top papers comparison bar chart
        fig_bar = go.Figure()
        
        top10_std = df_pr.nsmallest(10, 'rank_std')
        top10_temp = df_pr.nsmallest(10, 'rank_temp')
        
        fig_bar.add_trace(go.Bar(
            x=top10_std['pagerank_score'],
            y=[f"{t[:50]}..." if len(t) > 50 else t for t in top10_std['title']],
            orientation='h',
            name='Standard PageRank',
            marker_color='lightblue'
        ))
        
        fig_bar.add_trace(go.Bar(
            x=top10_temp['temporal_pagerank_score'],
            y=[f"{t[:50]}..." if len(t) > 50 else t for t in top10_temp['title']],
            orientation='h',
            name='Temporal PageRank',
            marker_color='lightcoral'
        ))
        
        fig_bar.update_layout(
            title="Top 10 Papers Comparison: Standard vs Temporal PageRank",
            xaxis_title="PageRank Score",
            yaxis_title="Paper Title",
            barmode='group',
            height=800,
            width=1200
        )
        comparison_path = Config.FIG_DIR / "pagerank_comparison.html"
        fig_bar.write_html(str(comparison_path))
        logger.info(f"Comparison chart saved: {comparison_path}")
        
    except ImportError:
        logger.warning("plotly not installed. Install with: pip install plotly")
        logger.info("PageRank visualizations skipped")
    except Exception as e:
        logger.error(f"Error generating PageRank visualizations: {e}", exc_info=True)
else:
    logger.warning(f"PageRank results file not found: {Config.PAGERANK_RESULTS}")
    logger.info("Tip: Run 'python pagerank_analyzer.py' to generate recommendations")