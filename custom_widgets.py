import streamlit as st
import re
from pyvis.network import Network
import ast

# Global variables for agent styling
agent_colors = {}
agent_icons = {}
colors_list = ["red", "blue", "green", "orange", "purple", "cyan", "magenta", "yellow", "brown", "pink"]
robot_icons_list = ["🤖", "🦾", "👾", "🤡", "🦍", "🦄", "🐱‍👓", "🤖🏻", "🤖🏼", "🤖🏽"]
agent_index = 0


def extract_widget_info(widget_string):
    # Regular expression to capture the widget name and arguments
    pattern = r"(\w+)\((.*)\)"
    match = re.match(pattern, widget_string)
    
    if match:
        widget_name = match.group(1)
        arguments_str = match.group(2)
        
        # Use ast.literal_eval to safely evaluate the arguments string into a tuple
        arguments = ast.literal_eval(f"({arguments_str})")
        
        return widget_name, arguments
    else:
        raise ValueError("Invalid widget string format")


def assign_agent_color_icon(agent_name):
    """Assigns a distinct color and cute robot icon to each agent (up to 10 agents)."""
    global agent_index
    if agent_name not in agent_colors:
        agent_colors[agent_name] = colors_list[agent_index % len(colors_list)]
        agent_icons[agent_name] = robot_icons_list[agent_index % len(robot_icons_list)]
        agent_index += 1
    return agent_colors[agent_name], agent_icons[agent_name]

def parse_flows(markdown_text):
    """
    Parses the markdown text and extracts flows.
    Each flow starts (and ends the previous one) with a marker like:
    <span style="font-weight: bold"></span><span style="font-weight: bold; color: #E850A8"> Flow started with ID: ...</span>
    """
    flows = []
    # Regular expression to capture the flow ID (the text following "Flow started with ID:")
    flow_pattern = r'<span style="font-weight: bold"></span><span style="font-weight: bold; color: #E850A8">\s*Flow started with ID:\s*([^<]+)</span>'
    parts = re.split(flow_pattern, markdown_text)
    # parts[0] is text before the first flow (if any), then alternating flow IDs and flow content
    for i in range(1, len(parts), 2):
        flow_id = parts[i].strip()
        flow_content = parts[i + 1]
        tasks = parse_tasks(flow_content)
        flows.append({"flow_id": flow_id, "tasks": tasks})
    return flows

def parse_tasks(flow_text):
    """
    Simplified parsing of a flow's text into tasks with dependency tracking.
    
    Process:
      1. Extract all text between <span> tags.
      2. Iterate through the spans looking for groups:
           "# Agent:"  ->  Agent Name  ->  Marker (either "## Task:" or "## Final Answer:")  ->  Content
      3. When a "## Task:" event is found:
            - Create a new task record with:
                - "agent": agent name,
                - "task": task description,
                - "final_answer": "" (empty initially),
                - "dependencies": a copy of the list of currently open tasks.
            - Then add the new task's index to the open tasks list.
      4. When a "## Final Answer:" event is found:
            - Attach the final answer text to the earliest open task for that agent and remove that task from the open tasks list.
    
    This way, if multiple tasks are started before any are finished, they are considered to be executed in parallel,
    and any subsequent task will depend on all those still open.
    """
    # Step 1: Extract all text between <span> tags.
    spans = re.findall(r'<span[^>]*>(.*?)</span>', flow_text, re.DOTALL)
    spans = [s.strip() for s in spans if len(s.strip())>0]

    tasks = []
    open_agents = []
    actual_dependencies = [] 
    open_tasks = [] 
    closed_tasks = []  # List of indices for tasks that have been closed
    i = 0
    while i < len(spans):
        # Look for the pattern: "# Agent:" then Agent Name, then Marker, then Content.
        if spans[i] == "# Agent:" and i + 1 < len(spans):
            agent = spans[i+1]
            open_agents.append(agent)
            i += 2
        elif spans[i] == "## Task:" and i + 1 < len(spans):
            content = spans[i+1]
            if len(closed_tasks) > 0:
                # If there are closed tasks, they are now dependencies for the new task.
                dependencies = closed_tasks.copy()
                closed_tasks = []
                actual_dependencies = dependencies.copy()
            else:
                dependencies = actual_dependencies.copy()
            
            # Create a new task with the current open_tasks as dependencies.
            new_task = {
                "agent": open_agents.pop(0),
                "task": content,
                "final_answer": "",
                "dependencies": dependencies  # copy the current list of open task indices
            }
            tasks.append(new_task)
            open_tasks.append(new_task)
            i += 2
        elif spans[i] == "## Final Answer:":
            agent = open_agents.pop(0)
            content = spans[i+1]
            # Attach the final answer to the earliest open task for this agent.
            for open_task in open_tasks:
                if open_task["agent"] == agent:
                    open_task["final_answer"] = content
                    closed_tasks.append(tasks.index(open_task))
                    open_tasks.remove(open_task)
                    break
            i += 2
        else:
            # If the marker doesn't match, just move forward.
            i += 1
    return tasks

def create_graph(flow):
    """
    Creates an interactive graph for a given flow using PyVis.
    
    - Each node represents a task (showing a truncated version of the task description).
    - On hover or click, the node reveals the final answer.
    - Nodes are colored and labeled with a cute robot icon based on the agent.
    - Edges are drawn sequentially to show dependencies.
    """
    net = Network(height="1000px", width="100%", directed=True)
    tasks = flow["tasks"]
    node_ids = []
    for idx, task in enumerate(tasks):
        agent = task["agent"]
        task_desc = re.sub(r'((\S+\s+){6})', r'\1\n', task["task"])
        final_ans = task["final_answer"]
        color, icon = assign_agent_color_icon(agent)
        short_desc = task_desc if len(task_desc) <= 50 else task_desc[:50] + "..."
        label = f"{icon} {agent}"
        title = task_desc if task_desc else "No task description provided."
        node_id = f"node_{idx}"
        net.add_node(node_id, label=label, title=title, color=color)
        node_ids.append(node_id)
        # Create dependencies edges
        for dependency in task["dependencies"]:
            net.add_edge(node_ids[dependency], node_id)
    
        
    # Save the generated graph as an HTML file and return its content
    html = net.generate_html("graph.html", notebook=False)
    
    return html

def ConsensusTasksWidget(markdown_file, tab_names):
    """
    Custom widget to display CrewAI flow tasks from a markdown file.
    
    Arguments:
        markdown_file: Path to the markdown file (e.g., 'media/results.md').
        *tab_names: Optional custom tab names for each flow. For example:
                    ConsensusResultWidget('media/results.md', 'Experiment 1', 'Experiment 2', 'Experiment 3', 'Experiment 4')
                    
    Each flow found in the file is displayed in its own tab. If not enough tab names are provided,
    the remaining tabs will be named with the default "flow1", "flow2", etc.
    """
    # Read the markdown file content
    try:
        with open(markdown_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return

    # Parse the flows from the markdown text
    flows = parse_flows(text)
    if not flows:
        st.error("No flows detected in the markdown file.")
        return
    
    

    num_flows = len(flows)
    # Determine tab names: use provided names or default to "flow1", "flow2", etc.
    if tab_names:
        tab_names_list = list(tab_names)
        if len(tab_names_list) < num_flows:
            tab_names_list.extend([f"flow{i+1}" for i in range(len(tab_names_list), num_flows)])
    else:
        tab_names_list = [f"flow{i+1}" for i in range(num_flows)]

    # Create a tab for each flow and display the corresponding graph
    tabs = st.tabs(tab_names_list)
    for idx, tab in enumerate(tabs):
        with tab:
            st.subheader(f"Flow ID: {flows[idx]['flow_id']}")
            html_graph = create_graph(flows[idx])
            st.components.v1.html(html_graph, height=600, scrolling=True)


def ConsensusResultsWidget(markdown_file, tab_names):
    """
    Custom widget to display CrewAI flow results from a markdown file.
    
    Arguments:
        markdown_file: Path to the markdown file (e.g., 'media/results.md').
        *tab_names: Optional custom tab names for each flow. For example:
                    ConsensusResultWidget('media/results.md', 'Experiment 1', 'Experiment 2', 'Experiment 3', 'Experiment 4')
                    
    Each flow found in the file is displayed in its own tab. If not enough tab names are provided,
    the remaining tabs will be named with the default "flow1", "flow2", etc.
    """
    # Read the markdown file content
    try:
        with open(markdown_file, "r", encoding="utf-8") as f:
            text = f.read()
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return

    # Parse the flows from the markdown text
    flows = parse_flows(text)
    if not flows:
        st.error("No flows detected in the markdown file.")
        return
    
    

    num_flows = len(flows)
    # Determine tab names: use provided names or default to "flow1", "flow2", etc.
    if tab_names:
        tab_names_list = list(tab_names)
        if len(tab_names_list) < num_flows:
            tab_names_list.extend([f"flow{i+1}" for i in range(len(tab_names_list), num_flows)])
    else:
        tab_names_list = [f"flow{i+1}" for i in range(num_flows)]

    # Create a tab for each flow and display the corresponding graph
    tabs = st.tabs(tab_names_list)
    for idx, tab in enumerate(tabs):
        with tab:
            # For each flow, create two sub-tabs: "Result" (displayed first) and "Development"
            sub_tabs = st.tabs(["Result", "Development"])

            # Result sub-tab: show the final answer (assumed to be the last task)
            with sub_tabs[0]:
                st.markdown(f"### Result")
                with st.expander("Final Answer - Click to show", expanded=False):
                    st.markdown(flows[idx]["tasks"][-1]["final_answer"])

            # Development sub-tab: show each intermediate task in expanders
            with sub_tabs[1]:
                st.markdown(f"### Development")
                for task in flows[idx]["tasks"][:-1]:
                    with st.expander(f"{task['agent']} - {task['task']}", expanded=False):
                        st.markdown(task['final_answer'])
