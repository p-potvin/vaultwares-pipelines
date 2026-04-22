import re

files = [
    "vaultwares_agentciation/hook_registry.py",
    "vaultwares_agentciation/redis_coordinator.py",
    "vaultwares_agentciation/skills/redis_comm_skill.py"
]

for f in files:
    with open(f, "r") as file:
        content = file.read()

    content = re.sub(r'<<<<<<< HEAD\n(.*?)\n=======\n(.*?)\n>>>>>>> [a-f0-9]+', r'\1', content, flags=re.DOTALL)

    with open(f, "w") as file:
        file.write(content)
