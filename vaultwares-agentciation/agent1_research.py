import sys
import os
import time
import requests

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from extrovert_agent import ExtrovertAgent

def research_nvidia_wfm():
    # Simple web search and summary (placeholder)
    summary = []
    try:
        resp = requests.get('https://developer.nvidia.com/blog/tag/workflow-management/')
        if resp.ok:
            summary.append('NVIDIA WFM (Workflow Management Framework) is a set of tools and APIs for managing GPU workflows. See: https://developer.nvidia.com/blog/tag/workflow-management/')
    except Exception as e:
        summary.append(f'Error fetching NVIDIA WFM info: {e}')
    summary.append('12GB VRAM GPUs are suitable for many AI/ML workloads, but may require model optimization or reduced batch sizes.')
    return '\n'.join(summary)

def main(agent_id, output_path):
    agent = ExtrovertAgent(agent_id=agent_id)
    print(f"[Worker Agent: {agent_id}] Starting research...")
    agent.start()
    findings = research_nvidia_wfm()
    with open(output_path, 'a', encoding='utf-8') as f:
        f.write(f"\n\n--- Automated Research Findings ---\n{findings}\n")
    print(f"[Worker Agent: {agent_id}] Research complete. Results written to {output_path}")
    agent._stop_event.set()

if __name__ == "__main__":
    main('agent1', 'vaultwares-agentciation/agent1_nvidia_wfm.md')
