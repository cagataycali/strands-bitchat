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
| `start` | Initialize P2P network | - |
| `stop` | Stop P2P network | - |
| `status` | Network status | - |
| `send_public` | Broadcast to all peers | `message` |
| `send_private` | Encrypted direct message | `message`, `recipient` |
| `send_channel` | Send to specific channel | `message`, `channel` |
| `join_channel` | Join/create channel | `channel` |
| `leave_channel` | Leave current channel | - |
| `list_peers` | Show connected peers | - |
| `list_channels` | Show discovered channels | - |
| `get_messages` | Get recent message history | - |
| `set_nickname` | Change your nickname | `nickname` |
| `block_user` / `unblock_user` | Block/unblock users | `nickname` |
| `enable_agent` | Enable auto-responses | `trigger_keyword`, `agent` |
| `enable_monitor` | Monitor all messages silently | `agent` |
| `disable_agent` | Disable agent integration | - |
| `agent_status` | Check agent integration status | - |

## 🤖 **Agent-to-Agent Communication**

```python
# Agent A
from strands import Agent
from strands_tools import use_agent
from strands_bitchat import bitchat

# Agent A - Coordinator
coordinator = Agent(
    system_prompt="BitChat enabled agent. Agent coordinator. Agent A. Can call 'worker'.", 
    tools=[bitchat, use_agent], 
    record_direct_tool_call=False
)
coordinator.tool.bitchat(action="start", agent=coordinator)
coordinator.tool.bitchat(action="enable_agent", trigger_keyword="coord", agent=coordinator)

# Agent B - Worker  
worker = Agent(
    system_prompt="BitChat enabled agent. Agent B. Can call 'coord' for coordinator agent.", 
    tools=[bitchat, use_agent], 
    record_direct_tool_call=False
)
worker.tool.bitchat(action="start", agent=worker)
worker.tool.bitchat(action="enable_agent", trigger_keyword="worker", agent=worker)

# Now agents can communicate:
# "coord, start task X"
# "worker, process data Y"

# Additional features:
# Monitor mode (processes all messages, no auto-response)
coordinator.tool.bitchat(action="enable_monitor", agent=coordinator)

# Channel operations
coordinator.tool.bitchat(action="join_channel", channel="#team", password="secret")
coordinator.tool.bitchat(action="send_channel", message="Hello team!", channel="#team")

# Private messaging
coordinator.tool.bitchat(action="send_private", message="Direct message", recipient="worker")

# Network management
coordinator.tool.bitchat(action="list_peers")
coordinator.tool.bitchat(action="get_messages")
coordinator.tool.bitchat(action="agent_status")
```

## 🔧 **Development Notes**

- **Always include both tools**: `[bitchat, use_agent]` for agent integration
- **Agent parameter**: Required only for `enable_agent` and `enable_monitor` actions
- **Auto-installs dependencies**: Bluetooth LE stack installed automatically on first use
- **~5 seconds**: Time needed for peer discovery and connection
- **Two modes**: Trigger mode (auto-responds) or Monitor mode (silent processing)
- **Channel passwords**: Use for secure team communications

## 🐛 **Troubleshooting**

- **No peers found**: Check Bluetooth is enabled
- **Agent not responding**: Verify trigger keyword and `use_agent` tool
- **Permission issues**: Grant Bluetooth system permissions

## 📄 **License**

MIT License

---

**🚀 Enable your Strands agents to collaborate directly via P2P mesh networking**