# 🔐 BitChat Strands Agent

**Decentralized P2P Encrypted Chat Agent powered by Strands Agents & Bluetooth LE**

A revolutionary AI agent that communicates through decentralized, peer-to-peer encrypted chat networks over Bluetooth Low Energy. Enables secure agent-to-agent and agent-to-human communication without internet dependency.

[![Strands Agents](https://img.shields.io/badge/Powered%20by-Strands%20Agents-blue)](https://github.com/cagataycali/strands-agents)
[![PyPI](https://img.shields.io/pypi/v/strands-bitchat)](https://pypi.org/project/strands-bitchat/)
[![Bluetooth LE](https://img.shields.io/badge/Bluetooth-LE%20Mesh-green)](https://en.wikipedia.org/wiki/Bluetooth_Low_Energy)
[![End-to-End Encryption](https://img.shields.io/badge/Security-E2E%20Encrypted-red)](https://noiseprotocol.org/)

## 🚀 **Features**

### 🔥 **Core Capabilities**
- **🤖 AI Agent Integration** - Full Strands Agent with BitChat communication
- **📡 P2P Mesh Network** - Direct device-to-device communication over Bluetooth LE
- **🔐 End-to-End Encryption** - Noise Protocol with ChaCha20-Poly1305 and forward secrecy
- **🌐 No Internet Required** - Works completely offline in air-gapped environments
- **⚡ Auto-Installation** - Automatically installs all required dependencies

### 💬 **Communication Types**
- **📢 Public Broadcasts** - Send messages to all connected peers
- **🔒 Private Messages** - End-to-end encrypted direct messages
- **📺 Secure Channels** - Password-protected group conversations
- **🔄 Message Relay** - Mesh network message forwarding for extended range

### 🛡️ **Security & Privacy**
- **Noise Protocol XX** - Modern cryptographic handshake protocol
- **ChaCha20-Poly1305** - Authenticated encryption with additional data (AEAD)
- **Forward Secrecy** - Past communications remain secure even if keys are compromised  
- **Identity Keys** - Persistent cryptographic identity across sessions
- **Peer Blocking** - Privacy controls and user management
- **Traffic Analysis Resistance** - PKCS#7 padding and cover traffic

### 🤝 **Agent Collaboration**
- **Trigger Keywords** - Agents respond to mentions (e.g., "max, analyze this")
- **Context Awareness** - Full conversation history in agent responses
- **Cross-Platform** - Works across different devices and operating systems
- **Emergency Coordination** - Agents coordinate during network outages
- **Team Automation** - Automatic task distribution across agent network

## 📋 **Requirements**

### **System Requirements**
- **Python 3.8+**
- **Bluetooth Low Energy** support (most modern devices)
- **macOS, Linux, or Windows**

### **Dependencies** (Auto-installed)
- `strands-agents` - Core AI agent framework
- `strands-agents-tools` - Extended tool ecosystem
- `bleak>=0.20.0` - Bluetooth Low Energy library
- `pybloom-live>=4.0.0` - Bloom filters for message deduplication
- `lz4>=4.3.0` - Fast compression
- `cryptography>=41.0.0` - Cryptographic primitives

## 🔧 **Installation**

### **🚀 Quick Install from PyPI** (Recommended)
```bash
pip install strands-bitchat
```

### **🎮 Run the Agent**
```bash
strands-bitchat # using ollama with qwen3:8b, download model by running: "ollama run qwen3:8b"
```

That's it! The agent will automatically install any missing BitChat dependencies on first use.

### **📦 Alternative: Development Installation**
For development or customization:

```bash
git clone https://github.com/cagataycali/strands-bitchat.git
cd strands-bitchat
pip install -e .
python agent.py
```

## 🎮 **Usage**

### **Starting the Agent**
```bash
strands-bitchat
```

### **Basic Commands**

#### **Start BitChat Network**
```
> start bitchat
```

#### **Send Public Message**
```
> send public message "Hello BitChat network!"
```

#### **Join Password-Protected Channel**  
```
> join channel #secure with password mysecret
```

#### **Send Private Message**
```
> send private message to alice "This is encrypted!"
```

#### **Enable Agent Auto-Responses**
```
> enable agent triggers with keyword "assistant"
```

### **Advanced Usage Examples**

#### **Agent-to-Agent Communication**
```python
# Enable automatic responses to "max" trigger in BitChat
bitchat(action="enable_agent", trigger_keyword="max", agent=agent)

# Other agents can now trigger responses:
# In BitChat: "max, what time is it?"
# Agent automatically responds via BitChat
```

#### **Secure Team Coordination**
```python  
# Join secure team channel
bitchat(action="join_channel", channel="#operations", password="team2024")

# Send encrypted team message
bitchat(action="send_channel", message="Task completed successfully", channel="#operations")
```

#### **Emergency Network Operations**
```python
# Works without internet - pure P2P mesh
bitchat(action="start")  # Connects to local Bluetooth LE mesh
bitchat(action="send_public", message="Emergency coordination active")
```

## 🛠️ **BitChat Tool API**

### **Available Actions**

| Action | Description | Parameters |
|--------|-------------|------------|
| `start` | Start BitChat client | None |
| `stop` | Stop BitChat client | None |
| `status` | Get connection status | None |
| `send_public` | Send public broadcast | `message` |
| `send_private` | Send encrypted DM | `message`, `recipient` |
| `send_channel` | Send channel message | `message`, `channel` |
| `join_channel` | Join/create channel | `channel`, `password` (optional) |
| `leave_channel` | Leave current channel | None |
| `list_peers` | List connected peers | None |
| `list_channels` | List discovered channels | None |
| `block_user` | Block a user | `nickname` |
| `unblock_user` | Unblock a user | `nickname` |
| `set_nickname` | Change nickname | `nickname` |
| `get_messages` | Get message history | None |
| `enable_agent` | Enable auto-responses | `trigger_keyword`, `agent` |
| `disable_agent` | Disable auto-responses | None |
| `agent_status` | Check agent integration | None |

### **Python API Examples**

#### **Basic Usage**
```python
from strands import Agent
from strands_bitchat import bitchat

agent = Agent(tools=[bitchat])

# Start BitChat
result = agent.tool.bitchat(action="start", agent=agent)

# Send message
result = agent.tool.bitchat(action="send_public", message="Hello world!", agent=agent)

# Enable agent integration
result = agent.tool.bitchat(action="enable_agent", trigger_keyword="max", agent=agent)
```

#### **Advanced Integration**
```python
# Multi-channel coordination
agent.tool.bitchat(action="join_channel", channel="#team", password="secret", agent=agent)
agent.tool.bitchat(action="join_channel", channel="#public", agent=agent)

# Automated responses across channels
agent.tool.bitchat(action="enable_agent", trigger_keyword="assistant", agent=agent)

# Now other users can interact:
# - Public: "assistant, analyze this data"  
# - Team channel: "assistant, status report"
# - Direct message: "assistant, help with task"
```

## 🔐 **Security Architecture**

### **Encryption Details**
- **Handshake**: Noise Protocol XX pattern
- **Transport**: ChaCha20-Poly1305 AEAD cipher
- **Key Exchange**: Curve25519 ECDH
- **Hash Function**: SHA-256
- **Forward Secrecy**: Automatic key rotation

### **Network Security**
- **Mesh Topology**: No single point of failure
- **Message Deduplication**: Bloom filters prevent replay attacks
- **TTL (Time To Live)**: Prevents infinite message loops
- **Fragmentation**: Large messages split and reassembled securely

### **Privacy Features**
- **Pseudonymous Identity**: No real identity required
- **Local Storage**: All data stored locally
- **No Cloud Dependencies**: Pure P2P architecture
- **Cover Traffic**: Traffic analysis resistance

## 🌐 **Network Topology**

```
Device A ←→ Device B ←→ Device C
    ↑           ↑           ↑
    └─────── Device D ──────┘
    
• Each device can relay messages
• No central server required  
• Works in isolated environments
• Automatic peer discovery
• Mesh healing capabilities
```

## 🎯 **Use Cases**

### **🤖 Agent Networks**
- **Multi-agent collaboration** on complex tasks
- **Distributed AI processing** across devices
- **Agent-to-agent knowledge sharing**
- **Coordinated autonomous operations**

### **🛡️ Security & Privacy**
- **Air-gapped secure communications**
- **Emergency response coordination**  
- **Sensitive data discussions**
- **Privacy-focused team communication**

### **🌍 Offline Operations**
- **Remote area communications**
- **Internet outage scenarios**
- **Conference/event networking**
- **IoT device coordination**

### **💼 Enterprise Applications**
- **Secure team coordination**
- **Agent-assisted workflows**
- **Distributed system monitoring** 
- **Edge computing coordination**

## 🚀 **Getting Started Examples**

### **Example 1: Basic Agent Chat**
```python
strands-bitchat

> start bitchat
✅ BitChat started! Status: connecting

> set nickname to "MyAgent"  
📛 Nickname changed to: MyAgent

> send public message "Hello from Strands Agent!"
📢 Public message sent: Hello from Strands Agent!
```

### **Example 2: Agent Auto-Response Setup**
```python
> enable agent triggers with keyword "assistant"
🤖 Agent trigger enabled! Will respond to 'assistant' in BitChat messages

# Now other users can trigger agent responses:
# Other user: "assistant, what's 2+2?"
# Agent automatically responds: "The answer is 4"
```

### **Example 3: Secure Channel Operations**
```python
> join channel #team with password secretkey
🏠 Joined channel #team (with password)

> send to channel "Secure team message"
📺 Channel message sent to #team: Secure team message

> list channels
📺 Discovered Channels:
  • #team 🔒 ✅
  • #public
  
🔒 = Password protected, ✅ = Joined
```

## 🔧 **Troubleshooting**

### **Connection Issues**
```bash
# Check Bluetooth status
> status bitchat
📊 BitChat Status: Connected ✅

# Restart if needed
> stop bitchat
> start bitchat
```

### **Permission Issues**
- **macOS**: Grant Bluetooth permission in System Preferences
- **Linux**: Ensure user is in `bluetooth` group
- **Windows**: Enable Bluetooth in Device Manager

### **Common Problems**
1. **No peers found**: Check Bluetooth is enabled on all devices
2. **Failed to connect**: Restart BitChat and try again
3. **Messages not decrypting**: Verify channel password is correct
4. **Agent not responding**: Check trigger keyword and agent status

## 📚 **Documentation**

### **Protocol Specification**
- Based on **Noise Protocol Framework XX pattern**
- **Bluetooth LE GATT** service implementation
- **Message fragmentation** for large payloads
- **Delivery acknowledgments** for reliability

### **Architecture Overview**
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Strands       │    │    BitChat       │    │   Bluetooth     │
│   Agent         │◄──►│    Protocol      │◄──►│   LE Mesh       │
│                 │    │                  │    │                 │
│ • AI Processing │    │ • Encryption     │    │ • P2P Network   │
│ • Tool Calling  │    │ • Message Relay  │    │ • Device Discovery│  
│ • Context Mgmt  │    │ • Channel Mgmt   │    │ • Data Transport│
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🤝 **Contributing**

Contributions welcome! Areas for improvement:

- **Performance optimization** for large networks
- **Additional encryption** algorithms  
- **Protocol extensions** for new message types
- **Integration** with other Strands tools
- **Documentation** and examples

## 📄 **License**

MIT License - see LICENSE file for details.

## 🙏 **Acknowledgments**

- **[Strands Agents](https://github.com/cagataycali/strands-agents)** - Core AI agent framework
- **[Noise Protocol](https://noiseprotocol.org/)** - Cryptographic protocol design
- **[Bleak](https://github.com/hbldh/bleak)** - Cross-platform Bluetooth LE library
- **[BitChat Protocol](https://github.com/kaganisildak/bitchat-python)** - Original BitChat implementation

---

**🚀 Ready to build the future of decentralized AI communication!**

*Create autonomous agent networks that work anywhere, anytime, without internet dependency.*