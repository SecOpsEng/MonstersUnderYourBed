import sqlite3
import networkx as nx
import plotly.graph_objects as go
import json

# Load conf file
conf = json.load(open("conf.json", "r"))
# Connect to DB
conn = sqlite3.connect('onion_services.db')
c = conn.cursor()
# Visualization using NetworkX and Plotly
G = nx.DiGraph()
# Pull all services from the DB, filtering for noise
# c.execute('SELECT url, inbound, outbound, findings FROM services')
c.execute('SELECT url, inbound, outbound, findings FROM services WHERE findings > {}'.format(conf["noise_filter"])) # <-- Noise eliminated
services = c.fetchall()
urls = [service[0] for service in services]
for service in services:
    # Create node in graph
    G.add_node(service[0], url=service[0], inbound=service[1], outbound=service[2], findings=service[3])
# Pull all connection from the DB
c.execute('SELECT source, target FROM connections')
connections = c.fetchall()
for connection in connections:
    if connection[0] in urls and connection[1] in urls:
        # Create edge in graph
        G.add_edge(connection[0], connection[1])

pos = nx.spring_layout(G)
nodes = [G.nodes[node] for node in G.nodes]
inbound = [G.nodes[node]['inbound'] for node in G.nodes]
outbound = [G.nodes[node]['outbound'] for node in G.nodes]
findings = [G.nodes[node]['findings'] for node in G.nodes]

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.append(x0)
    edge_x.append(x1)
    edge_x.append(None)
    edge_y.append(y0)
    edge_y.append(y1)
    edge_y.append(None)

edge_trace = go.Scatter(
    x=edge_x, y=edge_y,    line=dict(width=0.5, color='black'),
    hoverinfo='none',
    mode='lines')

node_x = []
node_y = []
node_size = []
node_color = []
for node in G.nodes():
    x, y = pos[node]
    node_x.append(x)
    node_y.append(y)
    node_size.append(G.nodes[node]['inbound']*10)
    node_color.append(G.nodes[node]['findings'])

node_trace = go.Scatter(
    x=node_x, 
    y=node_y,
    mode='markers',
    hoverinfo='text',
    marker=dict(
        showscale=True,
        colorscale='YlGnBu',
        size=10,
        color=node_color,
        colorbar=dict(
            thickness=15,
            title='Findings',
            xanchor='left',
            titleside='right'
        )
    )
)

node_trace.text = [f'{nodes[i]}' for i in range(len(G.nodes))]

fig = go.Figure(data=[edge_trace, node_trace],
                layout=go.Layout(
                    title='Western Union - Dark Web Search',
                    titlefont_size=16,
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    annotations=[dict(
                        text="Western Union Scan Results",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002 )],
                    xaxis=dict(showgrid=False, zeroline=False),
                    yaxis=dict(showgrid=False, zeroline=False))
                )


# BREAK GLASS FOR DARK MODE
# fig.update_layout(plot_bgcolor = "gray")

fig.show()