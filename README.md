# 🔧 BitChat for Strands Agents

[![Awesome Strands Agents](https://img.shields.io/badge/Awesome-Strands%20Agents-00FF77?style=flat-square&logo=data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjkwIiBoZWlnaHQ9IjQ2MyIgdmlld0JveD0iMCAwIDI5MCA0NjMiIGZpbGw9Im5vbmUiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+CjxwYXRoIGQ9Ik05Ny4yOTAyIDUyLjc4ODRDODUuMDY3NCA0OS4xNjY3IDcyLjIyMzQgNTYuMTM4OSA2OC42MDE3IDY4LjM2MTZDNjQuOTgwMSA4MC41ODQzIDcxLjk1MjQgOTMuNDI4MyA4NC4xNzQ5IDk3LjA1MDFMMjM1LjExNyAxMzkuNzc1QzI0NS4yMjMgMTQyLjc2OSAyNDYuMzU3IDE1Ni42MjggMjM2Ljg3NCAxNjEuMjI2TDMyLjU0NiAyNjAuMjkxQy0xNC45NDM5IDI4My4zMTYgLTkuMTYxMDcgMzUyLjc0IDQxLjQ4MzUgMzY3LjU5MUwxODkuNTUxIDQxMS4wMDlMMTkwLjEyNSA0MTEuMTY5QzIwMi4xODMgNDE0LjM3NiAyMTQuNjY1IDQwNy4zOTYgMjE4LjE5NiAzOTUuMzU1QzIyMS43ODQgMzgzLjEyMiAyMTQuNzc0IDM3MC4yOTYgMjAyLjU0MSAzNjYuNzA5TDU0LjQ3MzggMzIzLjI5MUM0NC4zNDQ3IDMyMC4zMjEgNDMuMTg3OSAzMDYuNDM2IDUyLjY4NTcgMzAxLjgzMUwyNTcuMDE0IDIwMi43NjZDMzA0LjQzMiAxNzkuNzc2IDI5OC43NTggMTEwLjQ4MyAyNDguMjMzIDk1LjUxMkw5Ny4yOTAyIDUyLjc4ODRaIiBmaWxsPSIjRkZGRkZGIi8+CjxwYXRoIGQ9Ik0yNTkuMTQ3IDAuOTgxODEyQzI3MS4zODkgLTIuNTc0OTggMjg0LjE5NyA0LjQ2NTcxIDI4Ny43NTQgMTYuNzA3NEMyOTEuMzExIDI4Ljk0OTIgMjg0LjI3IDQxLjc1NyAyNzIuMDI4IDQ1LjMxMzhMNzEuMTcyNyAxMDMuNjcxQzQwLjcxNDIgMTEyLjUyMSAzNy4xOTc2IDE1NC4yNjIgNjUuNzQ1OSAxNjguMDgzTDI0MS4zNDMgMjUzLjA5M0MzMDcuODcyIDI4NS4zMDIgMjk5Ljc5NCAzODIuNTQ2IDIyOC44NjIgNDAzLjMzNkwzMC40MDQxIDQ2MS41MDJDMTguMTcwNyA0NjUuMDg4IDUuMzQ3MDggNDU4LjA3OCAxLjc2MTUzIDQ0NS44NDRDLTEuODIzOSA0MzMuNjExIDUuMTg2MzcgNDIwLjc4NyAxNy40MTk3IDQxNy4yMDJMMjE1Ljg3OCAzNTkuMDM1QzI0Ni4yNzcgMzUwLjEyNSAyNDkuNzM5IDMwOC40NDkgMjIxLjIyNiAyOTQuNjQ1TDQ1LjYyOTcgMjA5LjYzNUMtMjAuOTgzNCAxNzcuMzg2IC0xMi43NzcyIDc5Ljk4OTMgNTguMjkyOCA1OS4zNDAyTDI1OS4xNDcgMC45ODE4MTJaIiBmaWxsPSIjRkZGRkZGIi8+Cjwvc3ZnPgo=&logoColor=white)](https://github.com/cagataycali/awesome-strands-agents)

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