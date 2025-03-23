import pandas as pd
import rdflib
from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import XSD
import networkx as nx
from pyvis.network import Network

# Example DataFrame with stock data
data = {
    'Date': ['2021-01-01', '2021-01-02'],
    'Stock': ['AAPL', 'AAPL'],
    'Open': [132.43, 133.00],
    'Close': [129.41, 131.24],
    'High': [134.00, 135.00],
    'Low': [129.00, 130.00],
    'Volume': [100000, 150000]
}
df = pd.DataFrame(data)

# Create a new RDF graph
g = Graph()
ns = Namespace("http://example.org/stock/")

for _, row in df.iterrows():
    stock_uri = URIRef(ns[row['Stock'] + "/" + row['Date']])
    g.add((stock_uri, RDF.type, URIRef(ns['Stock'])))
    g.add((stock_uri, ns['hasDate'], Literal(row['Date'], datatype=XSD.date)))
    g.add((stock_uri, ns['hasOpenPrice'], Literal(row['Open'], datatype=XSD.float)))
    g.add((stock_uri, ns['hasClosePrice'], Literal(row['Close'], datatype=XSD.float)))
    g.add((stock_uri, ns['hasHighPrice'], Literal(row['High'], datatype=XSD.float)))
    g.add((stock_uri, ns['hasLowPrice'], Literal(row['Low'], datatype=XSD.float)))
    g.add((stock_uri, ns['hasVolume'], Literal(row['Volume'], datatype=XSD.integer)))

# Convert RDF Graph to a NetworkX graph
nx_graph = nx.DiGraph()
for subj, pred, obj in g:
    subj_label = str(subj).split('/')[-1]  # Simplifying URI for readability
    obj_label = str(obj) if isinstance(obj, Literal) else str(obj).split('/')[-1]
    pred_label = str(pred).split('#')[-1]  # Simplifying URI for readability
    nx_graph.add_node(subj, label=subj_label, color='blue', size=20)
    nx_graph.add_node(obj, label=obj_label, color='green', size=15)
    nx_graph.add_edge(subj, obj, label=pred_label, color='red')

# Initialize and populate the Pyvis network
# Initialize and populate the Pyvis network with custom physics
nt = Network("100%", "100%", notebook=False)

# Customizing physics and layout for better spacing
nt.set_options("""
var options = {
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -80000,
      "centralGravity": 0.3,
      "springLength": 250,
      "springConstant": 0.04,
      "damping": 0.09,
      "avoidOverlap": 0.2
    },
    "minVelocity": 0.75
  },
  "layout": {
    "hierarchical": false
  }
}
""")

nt.from_nx(nx_graph)
nt.save_graph("rdf_graph_fullscreen.html")

