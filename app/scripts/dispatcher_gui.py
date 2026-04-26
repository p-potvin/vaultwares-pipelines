import gradio as gr
import redis
import json
import threading
import os
import re
import time

# State
agents_state = {}
live_logs = []
tasks_file = os.path.join(os.getcwd(), 'TASKS.md')

def parse_tasks_md():
    if not os.path.exists(tasks_file): return []
    parsed = []
    with open(tasks_file, 'r', encoding='utf-8') as f:
        for line in f:
            line_str = line.strip()
            main_match = re.match(r"^(\d+)\s+\[(.*?)\]\s+(.*)$", line_str)
            sub_match = re.match(r"^(\d+[a-z]+)\s+\[(.*?)\]\s+(.*)$", line_str)
            m = main_match or sub_match
            if m:
                parsed.append([m.group(1), m.group(2).strip(), m.group(3).strip()])
    return parsed

def redis_listener():
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    pubsub = r.pubsub()
    pubsub.subscribe('tasks')
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                agent = data.get('agent', 'Unknown')
                action = data.get('action', '')
                task = data.get('task', '')
                
                # Update Agents State
                if action == 'STATUS':
                    status = data.get('details', {}).get('status', 'UNKNOWN')
                    agents_state[agent] = [agent, status, str(task) if task else 'None']
                elif action == 'ASSIGN':
                    target = data.get('target')
                    if target in agents_state:
                        agents_state[target] = [target, 'WORKING', str(task)]
                elif action == 'COMPLETE':
                    if agent in agents_state:
                        agents_state[agent] = [agent, 'RELAXING', 'None']
                
                # Update Logs
                log_msg = ''
                if action in ('MSG', 'LOG'):
                    log_msg = data.get('details', {}).get('message', '')
                elif action == 'COMPLETE':
                    log_msg = f"Task {task} completed."
                elif action == 'ASSIGN':
                    target = data.get('target', '')
                    log_msg = f"Assigned {task} to {target}."
                
                if log_msg:
                    timestamp = time.strftime("%H:%M:%S", time.localtime())
                    # Keep latest 20 logs
                    live_logs.insert(0, f"[{timestamp}] [{agent}] {log_msg}")
                    if len(live_logs) > 20:
                        live_logs.pop()
            except Exception:
                pass

# Start redis listener thread
threading.Thread(target=redis_listener, daemon=True).start()

def get_agents_data():
    if not agents_state:
        return [["No agents connected", "-", "-"]]
    return list(agents_state.values())

def get_logs_data():
    return "\n".join(live_logs) if live_logs else "No activity yet..."

def get_tasks_data():
    tasks = parse_tasks_md()
    return tasks if tasks else [["No tasks found", "-", "-"]]

with gr.Blocks(title="Dispatcher Dashboard", theme=gr.themes.Monochrome()) as demo:
    gr.Markdown("# 🤖 Vaultwares Agent Dispatcher UI")
    
    with gr.Row():
        with gr.Column(scale=2):
            gr.Markdown("### 👨‍💻 Active Agents")
            agents_df = gr.Dataframe(
                headers=["Agent ID", "Status", "Current Task"],
                value=get_agents_data,
                interactive=False
            )
            
            gr.Markdown("### 📝 Tasks Queue (From TASKS.md)")
            tasks_df = gr.Dataframe(
                headers=["ID", "Status ([ ]/ [x])", "Title"],
                value=get_tasks_data,
                interactive=False
            )
            
        with gr.Column(scale=1):
            gr.Markdown("### 📡 Live Feed")
            logs_box = gr.Textbox(
                value=get_logs_data,
                lines=20,
                interactive=False,
                label="Agent Logs & Events"
            )

    # Refresh elements every 1 second
    demo.load(fn=get_agents_data, outputs=agents_df, every=1)
    demo.load(fn=get_tasks_data, outputs=tasks_df, every=1)
    demo.load(fn=get_logs_data, outputs=logs_box, every=1)

if __name__ == "__main__":
    demo.queue().launch(server_name="127.0.0.1", server_port=7860)
