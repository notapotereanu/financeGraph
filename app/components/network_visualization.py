"""Network visualization components for graph data."""

import json
from pyvis.network import Network

def format_tooltip_value(value):
    """Format a value for proper display in a tooltip."""
    if isinstance(value, (list, dict)):
        return json.dumps(value, indent=2)
    elif value is None:
        return "N/A"
    else:
        return str(value)

def create_network_graph(nodes, relationships, physics_settings=None):
    """Create an interactive network visualization using pyvis."""
    # Create network
    net = Network(height="700px", width="100%", bgcolor="#222222", font_color="white", directed=True)
    
    # Default physics settings
    if physics_settings is None:
        physics_settings = {
            "enabled": True,
            "solver": "forceAtlas2Based",
            "forceAtlas2Based": {
                "gravitationalConstant": -50,
                "centralGravity": 0.01,
                "springLength": 200,
                "springConstant": 0.08,
                "damping": 0.4,
                "avoidOverlap": 0.8
            },
            "stabilization": {
                "enabled": True,
                "iterations": 1000,
                "updateInterval": 25,
                "fit": True
            }
        }
    
    # Set options
    net.set_options("""
    const options = {
        "nodes": {
            "font": {
                "size": 15,
                "face": "Tahoma",
                "strokeWidth": 2,
                "strokeColor": "#ffffff"
            },
            "scaling": {
                "min": 10,
                "max": 30,
                "label": {
                    "enabled": true,
                    "min": 14,
                    "max": 30
                }
            },
            "shadow": {
                "enabled": true
            }
        },
        "edges": {
            "arrows": {
                "to": {
                    "enabled": true,
                    "scaleFactor": 0.5
                }
            },
            "color": {
                "inherit": true
            },
            "smooth": {
                "enabled": true,
                "type": "dynamic",
                "roundness": 0.5
            },
            "font": {
                "size": 12,
                "strokeWidth": 0,
                "align": "middle"
            },
            "width": 1.5,
            "length": 200
        },
        "physics": %s,
        "interaction": {
            "navigationButtons": true,
            "keyboard": true,
            "hover": true,
            "multiselect": true,
            "tooltipDelay": 300
        }
    }
    """ % json.dumps(physics_settings))
    
    # Add nodes with appropriate size, color and tooltip
    for node in nodes:
        node_id = node['id']
        label = node['labels'][0] if node['labels'] else "Unknown"
        
        # Get appropriate display name for node
        if "Insider" in node['labels'] or "Officer" in node['labels']:
            # For insiders and officers, ensure we use the person's name
            # First try the properties directly, then fallback to the name field
            properties = node.get('properties', {})
            
            # Handle Company Officers - prioritize property values
            if "Officer" in node['labels']:
                # Try to get the name from properties with various possible keys
                name = (properties.get('name') or 
                        properties.get('officer_name') or 
                        properties.get('officer') or
                        node.get('name'))
                display_name = name if name else 'Unknown Officer'
            else:
                # For regular Insiders
                display_name = node.get('name', 'Unknown')
                
            # Include ticker in parentheses if available
            ticker = node.get('ticker')
            if ticker:
                node_label = f"{display_name} ({ticker})"
            else:
                node_label = display_name
        elif "Committee" in node['labels']:
            # For committee nodes, always use the name of the committee
            display_name = node.get('name', 'Unknown Committee')
            node_label = display_name
        else:
            # For other nodes, use the display_name from the query
            display_name = str(node.get('display_name', 'Unknown'))
            node_label = display_name
        
        # Set title (tooltip) with all properties
        # Use HTML properly for tooltip
        tooltip = f"<div style='font-family:Arial; max-width:300px;'><h3>{display_name}</h3><table style='width:100%; border-collapse:collapse;'>"
        
        # Add node type
        tooltip += f"<tr><td><strong>Type:</strong></td><td>{label}</td></tr>"
        
        # Add all properties to the tooltip table
        for prop, value in node.get('properties', {}).items():
            if prop not in ['name', 'ticker', 'display_name'] and value is not None:
                # Format the value properly
                formatted_value = format_tooltip_value(value)
                tooltip += f"<tr><td><strong>{prop}:</strong></td><td>{formatted_value}</td></tr>"
                
        # Close the tooltip table and div
        tooltip += "</table></div>"
        
        # Set node color and size based on type
        if "Stock" in node['labels']:
            color = "#4878CF"  # blue
            size = 30
            shape = "circle"
        elif "Insider" in node['labels']:
            color = "#D65F5F"  # red
            size = 25
            shape = "dot" 
        elif "Officer" in node['labels']:
            color = "#E15759"  # darker red
            size = 25
            shape = "diamond"
        elif "Committee" in node['labels']:
            color = "#8A2BE2"  # violet
            size = 22
            shape = "hexagon"
        elif "Institution" in node['labels']:
            color = "#59A14F"  # green
            size = 25
            shape = "dot"
        elif "Analyst" in node['labels']:
            color = "#B879B8"  # purple
            size = 22
            shape = "dot"
        elif "News" in node['labels']:
            color = "#FF9D45"  # orange
            size = 20
            shape = "triangle"
        else:
            color = "#888888"  # gray
            size = 20
            shape = "dot"
        
        # Add node to network
        net.add_node(
            node_id, 
            label=node_label,
            title=tooltip,
            color=color,
            size=size,
            shape=shape,
            borderWidth=2,
            borderWidthSelected=4
        )
    
    # Add edges with labels and tooltips
    for rel in relationships:
        source = rel['source']
        target = rel['target']
        
        # Skip if source or target not in nodes
        if source is None or target is None:
            continue
            
        # Create label and tooltip
        label = rel['type']
        
        # HTML tooltip for edge
        tooltip = f"<div style='font-family:Arial; max-width:250px;'><h3>{label}</h3><table style='width:100%; border-collapse:collapse;'>"
        
        # Add shares information if available
        if rel.get('shares'):
            tooltip += f"<tr><td><strong>Shares:</strong></td><td>{rel['shares']}</td></tr>"
        
        # Add other properties to tooltip
        for prop, value in rel.get('properties', {}).items():
            if prop != 'shares' and value is not None:
                formatted_value = format_tooltip_value(value)
                tooltip += f"<tr><td><strong>{prop}:</strong></td><td>{formatted_value}</td></tr>"
                
        # Close the tooltip table and div
        tooltip += "</table></div>"
        
        # Add the edge
        net.add_edge(
            source, 
            target, 
            title=tooltip, 
            label=label if rel.get('shares') else label,
            arrows="to"
        )
    
    return net

def get_network_html(net):
    """Generate HTML for network visualization without saving to disk."""
    html = net.generate_html()
    
    # Inject custom CSS to make the visualization responsive
    html = html.replace(
        '</head>',
        '''
        <style>
        #mynetwork {
            width: 100% !important;
            height: 700px !important;
            border: 1px solid #ccc;
            border-radius: 5px;
            background-color: #222;
        }
        /* Make tooltips render HTML properly */
        .vis-tooltip {
            position: absolute;
            visibility: hidden;
            padding: 8px;
            white-space: normal !important;
            font-family: Arial;
            font-size: 14px;
            color: #000000;
            background-color: #f5f4ed;
            border: 1px solid #808074;
            border-radius: 3px;
            box-shadow: 3px 3px 10px rgba(0, 0, 0, 0.2);
            pointer-events: none;
            z-index: 5;
            max-width: 400px;
            overflow: visible;
        }
        /* Tooltip table styling */
        .vis-tooltip table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 5px;
        }
        .vis-tooltip td {
            padding: 3px;
            border-bottom: 1px solid #e0e0e0;
        }
        .vis-tooltip tr:last-child td {
            border-bottom: none;
        }
        .vis-tooltip h3 {
            margin-top: 0;
            margin-bottom: 10px;
            color: #333;
            font-size: 16px;
            border-bottom: 1px solid #ccc;
            padding-bottom: 5px;
        }
        </style>
        </head>
        '''
    )
    
    # Add zoom controls
    html = html.replace(
        '<div id="mynetwork"></div>',
        '''
        <div class="controls" style="margin-bottom: 10px;">
            <button onclick="network.fit()" style="padding: 5px 10px; margin-right: 5px;">Fit Graph</button>
            <button onclick="network.zoomIn()" style="padding: 5px 10px; margin-right: 5px;">Zoom In</button>
            <button onclick="network.zoomOut()" style="padding: 5px 10px;">Zoom Out</button>
        </div>
        <div id="mynetwork"></div>
        '''
    )
    
    # Enhanced tooltip handling - completely replace the tooltip code to properly handle HTML
    html = html.replace(
        'function openTooltip(e) {',
        '''
        function openTooltip(e) {
            // Remove any existing tooltip
            closeTooltip();
            
            // Create new tooltip
            const divElement = document.createElement("div");
            divElement.id = "tooltip";
            divElement.className = "vis-tooltip";
            
            // Get the tooltip content from the node/edge
            let content = e.target.title || "";
            
            // Set innerHTML directly to render HTML properly
            divElement.innerHTML = content;
            
            // Position the tooltip near the mouse
            divElement.style.left = e.pageX + 5 + "px";
            divElement.style.top = e.pageY + 5 + "px";
            divElement.style.visibility = "visible";
            
            // Add tooltip to body
            document.body.appendChild(divElement);
            
            // Store tooltip reference
            tooltip = divElement;
        '''
    )
    
    # Replace the close tooltip function as well for consistency
    html = html.replace(
        'function closeTooltip() {',
        '''
        function closeTooltip() {
            // Remove tooltip if exists
            if (tooltip !== undefined) {
                tooltip.parentNode.removeChild(tooltip);
                tooltip = undefined;
            }
        '''
    )
    
    # Remove the redrawTooltip function since we're completely replacing the tooltip system
    html = html.replace(
        'function redrawTooltip() {',
        '''
        function redrawTooltip() {
            // This function is no longer needed
        '''
    )
    
    return html 