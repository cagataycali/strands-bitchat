# 🔧 BitChat for Strands Agents

**P2P Encrypted Communication Tool for Strands Agent Development**

Add decentralized, peer-to-peer encrypted chat capabilities to your Strands agents using Bluetooth Low Energy mesh networking.

[![PyPI](https://img.shields.io/pypi/v/strands-bitchat)](https://pypi.org/project/strands-bitchat/)

## 📦 **Installation**

```bash
pip install strands-bitchat
```

## 🔧 **Basic Integration**

```python
from strands import Agent
from strands_bitchat import bitchat
from strands_tools import use_agent

# Add BitChat to your existing agent
agent = Agent(
    tools=[bitchat, use_agent],  # Required: bitchat + use_agent
    system_prompt="Your agent with P2P communication capabilities"
)

# Enable P2P networking
agent.tool.bitchat(action="start", agent=agent)
agent.tool.bitchat(action="enable_agent", trigger_keyword="max", agent=agent)
```

## 🛠️ **Core Actions**

| Action | Purpose | Required Parameters |
|--------|---------|-------------------|
| `start` | Initialize P2P network | `agent` |
| `send_public` | Broadcast to all peers | `message`, `agent` |
| `send_private` | Encrypted direct message | `message`, `recipient`, `agent` |
| `join_channel` | Join/create channel | `channel`, `agent` |
| `enable_agent` | Enable auto-responses | `trigger_keyword`, `agent` |
| `list_peers` | Show connected peers | - |
| `status` | Network status | - |

## 🤖 **Agent-to-Agent Communication**

```python
# Agent A
from strands import Agent
from strands_tools import use_agent

from strands_bitchat import bitchat

# Agent A
coordinator = Agent(system_prompt="BitChat enabled agent. Agent coordinator. Agent A. Can call 'worker'.", tools=[bitchat, use_agent], record_direct_tool_call=False)
coordinator.tool.bitchat(action="start", agent=coordinator)
coordinator.tool.bitchat(action="enable_agent", trigger_keyword="coord", agent=coordinator)

# Agent B  
worker = Agent(system_prompt="BitChat enabled agent. Agent B. Can call 'coord' for coordinator agent.", tools=[bitchat, use_agent], record_direct_tool_call=False)
worker.tool.bitchat(action="start", agent=worker)
worker.tool.bitchat(action="enable_agent", trigger_keyword="worker", agent=worker)

# Now agents can communicate:
# "coord, start task X"
# "worker, process data Y"
```

## 🔧 **Development Notes**

- **Always include both tools**: `[bitchat, use_agent]`
- **Agent parameter required**: Pass `agent=agent` to actions
- **Auto-installs dependencies**: Bluetooth LE stack installed automatically
- **~5 seconds**: Time needed for peer discovery

## 🐛 **Troubleshooting**

- **No peers found**: Check Bluetooth is enabled
- **Agent not responding**: Verify trigger keyword and `use_agent` tool
- **Permission issues**: Grant Bluetooth system permissions

## 📄 **License**

MIT License

---

**🚀 Enable your Strands agents to collaborate directly via P2P mesh networking**