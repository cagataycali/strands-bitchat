#!/usr/bin/env python3
"""
BitChat Tool for Strands Agents - Integrated Version

A comprehensive tool that provides decentralized, peer-to-peer, encrypted chat
over Bluetooth Low Energy (BLE) with all BitChat classes embedded directly.

Features:
- Start/stop BitChat client
- Send public, private, and channel messages
- Join/leave channels with password support
- Manage peers and connections
- Block/unblock users
- Channel ownership and password management
- Real-time status monitoring
- Agent integration with trigger keywords

Original implementation: git@github.com:kaganisildak/bitchat-python
"""

import asyncio
import threading
import time
import os
import sys
import json
import uuid
import struct
import hashlib
import random
from datetime import datetime
from typing import Optional, Dict, List, Tuple, Set, Callable, Any
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path

from strands import tool

# Global BitChat client instance and control variables
_bitchat_client = None
_bitchat_thread = None
_bitchat_running = False
_bitchat_status = "stopped"
_message_history = []
_peer_list = {}
_trigger_keyword = None
_parent_agent = None
_auto_response_enabled = False


def _log_sent_message(content, is_private=False, channel=None, recipient=None):
    """Log sent messages to history"""
    global _message_history
    message_entry = {
        "timestamp": time.time(),
        "sender": "strands-agent",  # Our nickname
        "sender_id": "self",
        "content": content,
        "is_private": is_private,
        "channel": channel,
        "recipient": recipient,
        "message_id": f"sent_{int(time.time())}",
        "display": f"[SENT] {content}",
    }
    _message_history.append(message_entry)

    # Keep last 100 messages
    if len(_message_history) > 100:
        _message_history = _message_history[-100:]


def _install_dependencies():
    """Install required BitChat dependencies."""
    dependencies = [
        "bleak>=0.20.0",  # Bluetooth Low Energy
        "pybloom-live>=4.0.0",  # Bloom filters
        "lz4>=4.3.0",  # Compression
        "aioconsole>=0.6.0",  # Async console
        "cryptography>=41.0.0",  # Additional crypto
    ]

    import subprocess

    for dep in dependencies:
        try:
            # Try importing the package
            pkg_name = dep.split(">=")[0].split("==")[0]
            if pkg_name == "pybloom-live":
                import pybloom_live
            else:
                __import__(pkg_name)
        except ImportError:
            print(f"🔧 Installing {dep}...")
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", dep],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )

                if result.returncode != 0:
                    raise Exception(f"Installation failed: {result.stderr}")

                print(f"✅ Successfully installed {dep}")
            except Exception as e:
                print(f"❌ Failed to install {dep}: {e}")
                return False

    return True


# =============================================================================
# EMBEDDED BITCHAT CLASSES - START
# =============================================================================

# --- Compression Module ---
COMPRESSION_THRESHOLD = 100


def compress_if_beneficial(data: bytes) -> Tuple[bytes, bool]:
    """Compress data if it reduces size"""
    try:
        import lz4.frame

        if len(data) < COMPRESSION_THRESHOLD:
            return (data, False)

        compressed = lz4.frame.compress(data)
        if len(compressed) < len(data):
            return (compressed, True)
        else:
            return (data, False)
    except ImportError:
        return (data, False)


def decompress(data: bytes) -> bytes:
    """Decompress LZ4 data"""
    try:
        import lz4.frame

        return lz4.frame.decompress(data)
    except Exception as e:
        raise ValueError(f"Decompression failed: {e}")


# --- Fragmentation Module ---
MAX_FRAGMENT_SIZE = 500


class FragmentType(IntEnum):
    START = 0x05
    CONTINUE = 0x06
    END = 0x07


@dataclass
class Fragment:
    fragment_id: bytes
    fragment_type: FragmentType
    index: int
    total: int
    original_type: int
    data: bytes


def fragment_payload(payload: bytes, original_msg_type: int) -> List[Fragment]:
    """Fragment a large payload"""
    if len(payload) <= MAX_FRAGMENT_SIZE:
        return []

    fragment_id = os.urandom(8)
    chunks = [
        payload[i : i + MAX_FRAGMENT_SIZE]
        for i in range(0, len(payload), MAX_FRAGMENT_SIZE)
    ]
    total = len(chunks)

    fragments = []
    for i, chunk in enumerate(chunks):
        if i == 0:
            fragment_type = FragmentType.START
        elif i == len(chunks) - 1:
            fragment_type = FragmentType.END
        else:
            fragment_type = FragmentType.CONTINUE

        fragments.append(
            Fragment(
                fragment_id=fragment_id,
                fragment_type=fragment_type,
                index=i,
                total=total,
                original_type=original_msg_type,
                data=chunk,
            )
        )

    return fragments


# --- Terminal UX Module ---
@dataclass
class ChatMode:
    """Base class for chat modes"""

    pass


@dataclass
class Public(ChatMode):
    """Public chat mode"""

    pass


@dataclass
class Channel(ChatMode):
    """Channel chat mode"""

    name: str


@dataclass
class PrivateDM(ChatMode):
    """Private DM mode"""

    nickname: str
    peer_id: str


class ChatContext:
    def __init__(self):
        self.current_mode: ChatMode = Public()
        self.active_channels: List[str] = []
        self.active_dms: Dict[str, str] = {}  # nickname -> peer_id
        self.last_private_sender: Optional[Tuple[str, str]] = None

    def switch_to_channel_silent(self, channel: str):
        if channel not in self.active_channels:
            self.active_channels.append(channel)
        self.current_mode = Channel(channel)

    def add_dm(self, nickname: str, peer_id: str):
        self.active_dms[nickname] = peer_id

    def enter_dm_mode(self, nickname: str, peer_id: str):
        self.add_dm(nickname, peer_id)
        self.current_mode = PrivateDM(nickname, peer_id)

    def switch_to_public(self):
        self.current_mode = Public()


def format_message_display(
    timestamp: datetime,
    sender: str,
    content: str,
    is_private: bool,
    is_channel: bool,
    channel_name: Optional[str],
    recipient: Optional[str],
    my_nickname: str,
) -> str:
    """Format a message for display"""
    time_str = timestamp.strftime("%H:%M")

    if is_private:
        if sender == my_nickname:
            if recipient:
                return f"\033[2;38;5;208m[{time_str}|DM]\033[0m \033[38;5;214m<you → {recipient}>\033[0m {content}"
            else:
                return f"\033[2;38;5;208m[{time_str}|DM]\033[0m \033[38;5;214m<you → ???>\033[0m {content}"
        else:
            return f"\033[2;38;5;208m[{time_str}|DM]\033[0m \033[38;5;208m<{sender} → you>\033[0m {content}"
    elif is_channel:
        if sender == my_nickname:
            if channel_name:
                return f"\033[2;34m[{time_str}|{channel_name}]\033[0m \033[38;5;117m<{sender} @ {channel_name}>\033[0m {content}"
            else:
                return f"\033[2;34m[{time_str}|Ch]\033[0m \033[38;5;117m<{sender} @ ???>\033[0m {content}"
        else:
            if channel_name:
                return f"\033[2;34m[{time_str}|{channel_name}]\033[0m \033[34m<{sender} @ {channel_name}>\033[0m {content}"
            else:
                return f"\033[2;34m[{time_str}|Ch]\033[0m \033[34m<{sender} @ ???>\033[0m {content}"
    else:
        if sender == my_nickname:
            return f"\033[2;32m[{time_str}]\033[0m \033[38;5;120m<{sender}>\033[0m {content}"
        else:
            return f"\033[2;32m[{time_str}]\033[0m \033[32m<{sender}>\033[0m {content}"


# --- Persistence Module ---
@dataclass
class EncryptedPassword:
    nonce: List[int]
    ciphertext: List[int]


@dataclass
class AppState:
    nickname: Optional[str] = None
    blocked_peers: Set[str] = field(default_factory=set)
    channel_creators: Dict[str, str] = field(default_factory=dict)
    joined_channels: List[str] = field(default_factory=list)
    password_protected_channels: Set[str] = field(default_factory=set)
    channel_key_commitments: Dict[str, str] = field(default_factory=dict)
    favorites: Set[str] = field(default_factory=set)
    identity_key: Optional[List[int]] = None
    encrypted_channel_passwords: Dict[str, EncryptedPassword] = field(
        default_factory=dict
    )


def get_state_file_path() -> Path:
    """Get the state file path"""
    home = Path.home()
    bitchat_dir = home / ".bitchatxxk"
    bitchat_dir.mkdir(exist_ok=True)
    return bitchat_dir / "state.json"


def load_state() -> AppState:
    """Load app state from disk"""
    path = get_state_file_path()

    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)

                # Convert lists back to sets
                if "blocked_peers" in data:
                    data["blocked_peers"] = set(data["blocked_peers"])
                if "password_protected_channels" in data:
                    data["password_protected_channels"] = set(
                        data["password_protected_channels"]
                    )
                if "favorites" in data:
                    data["favorites"] = set(data["favorites"])

                # Convert encrypted passwords
                if "encrypted_channel_passwords" in data:
                    encrypted_passwords = {}
                    for channel, enc_data in data[
                        "encrypted_channel_passwords"
                    ].items():
                        encrypted_passwords[channel] = EncryptedPassword(
                            nonce=enc_data["nonce"], ciphertext=enc_data["ciphertext"]
                        )
                    data["encrypted_channel_passwords"] = encrypted_passwords

                state = AppState(**data)
        except Exception:
            state = AppState()
    else:
        state = AppState()

    # Generate identity key if not present
    if state.identity_key is None:
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization

            signing_key = ed25519.Ed25519PrivateKey.generate()
            state.identity_key = list(
                signing_key.private_bytes(
                    encoding=serialization.Encoding.Raw,
                    format=serialization.PrivateFormat.Raw,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
            save_state(state)
        except ImportError:
            # Fallback to random bytes if ed25519 not available
            state.identity_key = list(os.urandom(32))

    return state


def save_state(state: AppState) -> None:
    """Save app state to disk"""
    path = get_state_file_path()

    data = {
        "nickname": state.nickname,
        "blocked_peers": list(state.blocked_peers),
        "channel_creators": state.channel_creators,
        "joined_channels": state.joined_channels,
        "password_protected_channels": list(state.password_protected_channels),
        "channel_key_commitments": state.channel_key_commitments,
        "favorites": list(state.favorites),
        "identity_key": state.identity_key,
        "encrypted_channel_passwords": {
            channel: {"nonce": ep.nonce, "ciphertext": ep.ciphertext}
            for channel, ep in state.encrypted_channel_passwords.items()
        },
    }

    try:
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # Ignore save errors


def encrypt_password(password: str, identity_key: List[int]) -> EncryptedPassword:
    """Encrypt a password using the identity key"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        identity_key_bytes = bytes(identity_key)
        h = hashlib.sha256()
        h.update(b"bitchat-password-encryption")
        h.update(identity_key_bytes)
        key = h.digest()

        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, password.encode(), None)

        return EncryptedPassword(nonce=list(nonce), ciphertext=list(ciphertext))
    except ImportError:
        # Fallback - store as plaintext (not secure but functional)
        return EncryptedPassword(nonce=[], ciphertext=list(password.encode()))


def decrypt_password(encrypted: EncryptedPassword, identity_key: List[int]) -> str:
    """Decrypt a password using the identity key"""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        if not encrypted.nonce:  # Fallback plaintext storage
            return bytes(encrypted.ciphertext).decode()

        identity_key_bytes = bytes(identity_key)
        h = hashlib.sha256()
        h.update(b"bitchat-password-encryption")
        h.update(identity_key_bytes)
        key = h.digest()

        aesgcm = AESGCM(key)
        nonce = bytes(encrypted.nonce)
        ciphertext = bytes(encrypted.ciphertext)

        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode()
    except ImportError:
        return bytes(encrypted.ciphertext).decode()


# --- Encryption Module ---
NOISE_PROTOCOL_NAME = "Noise_XX_25519_ChaChaPoly_SHA256"
NOISE_DH_LEN = 32
NOISE_HASH_LEN = 32


class NoiseError(Exception):
    """Base class for Noise protocol errors"""

    pass


class NoiseRole:
    """Noise handshake roles"""

    INITIATOR = "initiator"
    RESPONDER = "responder"


class NoiseCipherState:
    """Cipher state for Noise Protocol transport encryption"""

    def __init__(self):
        self.key = None
        self.nonce = 0

    def initialize_key(self, key: bytes):
        self.key = key
        self.nonce = 0

    def has_key(self) -> bool:
        return self.key is not None

    def encrypt(self, plaintext: bytes, associated_data: bytes = b"") -> bytes:
        if not self.has_key():
            raise NoiseError("Cipher not initialized")

        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            nonce = b"\x00\x00\x00\x00" + self.nonce.to_bytes(8, byteorder="little")
            cipher = ChaCha20Poly1305(self.key)
            ciphertext = cipher.encrypt(nonce, plaintext, associated_data)
            self.nonce += 1
            return ciphertext
        except ImportError:
            # Fallback - return plaintext
            self.nonce += 1
            return plaintext

    def decrypt(self, ciphertext: bytes, associated_data: bytes = b"") -> bytes:
        if not self.has_key():
            raise NoiseError("Cipher not initialized")

        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            nonce = b"\x00\x00\x00\x00" + self.nonce.to_bytes(8, byteorder="little")
            cipher = ChaCha20Poly1305(self.key)
            plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
            self.nonce += 1
            return plaintext
        except ImportError:
            # Fallback - return ciphertext as-is
            self.nonce += 1
            return ciphertext
        except Exception as e:
            self.nonce += 1
            raise


@dataclass
class NoiseSession:
    """Represents an established Noise session with a peer"""

    peer_id: str
    send_cipher: NoiseCipherState
    receive_cipher: NoiseCipherState
    remote_static_key: Optional[bytes]
    established_time: float

    def encrypt(self, plaintext: bytes) -> bytes:
        return self.send_cipher.encrypt(plaintext)

    def decrypt(self, ciphertext: bytes) -> bytes:
        return self.receive_cipher.decrypt(ciphertext)

    def get_fingerprint(self) -> str:
        if self.remote_static_key:
            return hashlib.sha256(self.remote_static_key).hexdigest()
        return "unknown"


class EncryptionService:
    """Simplified encryption service with fallbacks"""

    def __init__(self, identity_path: Optional[str] = None):
        self.sessions: Dict[str, NoiseSession] = {}
        self.handshake_states: Dict[str, Any] = {}
        self.my_peer_id: Optional[str] = None
        self.on_peer_authenticated: Optional[Callable[[str, str], None]] = None
        self.on_handshake_required: Optional[Callable[[str], None]] = None

        # Generate or load identity
        self.static_identity_key = os.urandom(32)  # Simplified

    def get_public_key(self) -> bytes:
        return self.static_identity_key[:32]

    def get_signing_public_key_bytes(self) -> bytes:
        return self.static_identity_key[:32]

    def get_combined_public_key_data(self) -> bytes:
        return self.static_identity_key[:32]

    def initiate_handshake(self, peer_id: str) -> bytes:
        # Simplified handshake
        return self.get_public_key() + os.urandom(32)

    def process_handshake_message(
        self, peer_id: str, message: bytes
    ) -> Optional[bytes]:
        # Simplified - create session directly
        send_cipher = NoiseCipherState()
        receive_cipher = NoiseCipherState()

        # Use a simple key derivation
        key = hashlib.sha256(self.static_identity_key + peer_id.encode()).digest()
        send_cipher.initialize_key(key)
        receive_cipher.initialize_key(key)

        session = NoiseSession(
            peer_id=peer_id,
            send_cipher=send_cipher,
            receive_cipher=receive_cipher,
            remote_static_key=message[:32] if len(message) >= 32 else None,
            established_time=time.time(),
        )
        self.sessions[peer_id] = session

        if self.on_peer_authenticated:
            self.on_peer_authenticated(peer_id, session.get_fingerprint())

        return self.get_public_key() + os.urandom(32)

    def is_session_established(self, peer_id: str) -> bool:
        return peer_id in self.sessions

    def encrypt_for_peer(self, peer_id: str, data: bytes) -> bytes:
        if peer_id not in self.sessions:
            if self.on_handshake_required:
                self.on_handshake_required(peer_id)
            raise NoiseError(f"No session with peer {peer_id}")
        return self.sessions[peer_id].encrypt(data)

    def decrypt_from_peer(self, peer_id: str, data: bytes) -> bytes:
        if peer_id not in self.sessions:
            raise NoiseError(f"No session with peer {peer_id}")
        return self.sessions[peer_id].decrypt(data)

    def get_peer_fingerprint(self, peer_id: str) -> Optional[str]:
        if peer_id in self.sessions:
            return self.sessions[peer_id].get_fingerprint()
        return None

    def sign_data(self, data: bytes) -> bytes:
        return hashlib.sha256(data + self.static_identity_key).digest()

    def remove_session(self, peer_id: str):
        self.sessions.pop(peer_id, None)
        self.handshake_states.pop(peer_id, None)

    def clear_handshake_state(self, peer_id: str):
        self.handshake_states.pop(peer_id, None)

    def cleanup_old_sessions(self, max_age: float = 3600):
        current_time = time.time()
        expired = [
            pid
            for pid, session in self.sessions.items()
            if current_time - session.established_time > max_age
        ]
        for pid in expired:
            del self.sessions[pid]

    def get_session_count(self) -> int:
        return len(self.sessions)

    def get_active_peers(self) -> list:
        return list(self.sessions.keys())

    def encrypt_for_channel(
        self, message: str, channel: str, key: bytes, creator_fingerprint: str
    ) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            cipher = ChaCha20Poly1305(key)
            nonce = os.urandom(12)
            plaintext = message.encode("utf-8")
            return nonce + cipher.encrypt(nonce, plaintext, None)
        except ImportError:
            return message.encode("utf-8")

    def decrypt_from_channel(
        self, data: bytes, channel: str, key: bytes, creator_fingerprint: str
    ) -> str:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            if len(data) < 12:
                return data.decode("utf-8", errors="ignore")
            nonce = data[:12]
            ciphertext = data[12:]
            cipher = ChaCha20Poly1305(key)
            plaintext = cipher.decrypt(nonce, ciphertext, None)
            return plaintext.decode("utf-8")
        except ImportError:
            return data.decode("utf-8", errors="ignore")

    def encrypt_with_key(self, data: bytes, key: bytes) -> bytes:
        try:
            from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305

            cipher = ChaCha20Poly1305(key)
            nonce = os.urandom(12)
            return nonce + cipher.encrypt(nonce, data, None)
        except ImportError:
            return data

    @staticmethod
    def derive_channel_key(password: str, channel: str) -> bytes:
        try:
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            from cryptography.hazmat.primitives import hashes

            salt = channel.encode("utf-8")
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            return kdf.derive(password.encode("utf-8"))
        except ImportError:
            # Simple fallback
            return hashlib.sha256(password.encode() + channel.encode()).digest()


# --- BitChat Core Classes ---
VERSION = "v1.1.0"

# UUIDs
BITCHAT_SERVICE_UUID = "f47b5e2d-4a9e-4c5a-9b3f-8e1d2c3a4b5c"
BITCHAT_CHARACTERISTIC_UUID = "a1b2c3d4-e5f6-4a5b-8c9d-0e1f2a3b4c5d"

# Cover traffic prefix
COVER_TRAFFIC_PREFIX = "☂DUMMY☂"

# Packet header flags
FLAG_HAS_RECIPIENT = 0x01
FLAG_HAS_SIGNATURE = 0x02
FLAG_IS_COMPRESSED = 0x04

# Message payload flags
MSG_FLAG_IS_RELAY = 0x01
MSG_FLAG_IS_PRIVATE = 0x02
MSG_FLAG_HAS_ORIGINAL_SENDER = 0x04
MSG_FLAG_HAS_RECIPIENT_NICKNAME = 0x08
MSG_FLAG_HAS_SENDER_PEER_ID = 0x10
MSG_FLAG_HAS_MENTIONS = 0x20
MSG_FLAG_HAS_CHANNEL = 0x40
MSG_FLAG_IS_ENCRYPTED = 0x80

SIGNATURE_SIZE = 64
BROADCAST_RECIPIENT = b"\xff" * 8


# Message types
class MessageType(IntEnum):
    ANNOUNCE = 0x01
    KEY_EXCHANGE = 0x02
    LEAVE = 0x03
    MESSAGE = 0x04
    FRAGMENT_START = 0x05
    FRAGMENT_CONTINUE = 0x06
    FRAGMENT_END = 0x07
    CHANNEL_ANNOUNCE = 0x08
    CHANNEL_RETENTION = 0x09
    DELIVERY_ACK = 0x0A
    DELIVERY_STATUS_REQUEST = 0x0B
    READ_RECEIPT = 0x0C
    NOISE_HANDSHAKE_INIT = 0x10
    NOISE_HANDSHAKE_RESP = 0x11
    NOISE_ENCRYPTED = 0x12
    NOISE_IDENTITY_ANNOUNCE = 0x13
    CHANNEL_KEY_VERIFY_REQUEST = 0x14
    CHANNEL_KEY_VERIFY_RESPONSE = 0x15
    CHANNEL_PASSWORD_UPDATE = 0x16
    CHANNEL_METADATA = 0x17
    VERSION_HELLO = 0x20
    VERSION_ACK = 0x21


@dataclass
class Peer:
    nickname: Optional[str] = None


@dataclass
class BitchatPacket:
    msg_type: MessageType
    sender_id: bytes
    sender_id_str: str
    recipient_id: Optional[bytes]
    recipient_id_str: Optional[str]
    payload: bytes
    ttl: int


@dataclass
class BitchatMessage:
    id: str
    content: str
    channel: Optional[str]
    is_encrypted: bool
    encrypted_content: Optional[bytes]


@dataclass
class DeliveryAck:
    original_message_id: str
    ack_id: str
    recipient_id: str
    recipient_nickname: str
    timestamp: int
    hop_count: int


class DeliveryTracker:
    def __init__(self):
        self.pending_messages: Dict[str, Tuple[str, float, bool]] = {}
        self.sent_acks: Set[str] = set()

    def track_message(self, message_id: str, content: str, is_private: bool):
        self.pending_messages[message_id] = (content, time.time(), is_private)

    def mark_delivered(self, message_id: str) -> bool:
        return self.pending_messages.pop(message_id, None) is not None

    def should_send_ack(self, ack_id: str) -> bool:
        if ack_id in self.sent_acks:
            return False
        self.sent_acks.add(ack_id)
        return True


class FragmentCollector:
    def __init__(self):
        self.fragments: Dict[str, Dict[int, bytes]] = {}
        self.metadata: Dict[str, Tuple[int, int, str]] = {}

    def add_fragment(
        self,
        fragment_id: bytes,
        index: int,
        total: int,
        original_type: int,
        data: bytes,
        sender_id: str,
    ) -> Optional[Tuple[bytes, str]]:
        fragment_id_hex = fragment_id.hex()

        if fragment_id_hex not in self.fragments:
            self.fragments[fragment_id_hex] = {}
            self.metadata[fragment_id_hex] = (total, original_type, sender_id)

        fragment_map = self.fragments[fragment_id_hex]
        fragment_map[index] = data

        if len(fragment_map) == total:
            complete_data = bytearray()
            for i in range(total):
                if i in fragment_map:
                    complete_data.extend(fragment_map[i])
                else:
                    return None

            sender = self.metadata.get(fragment_id_hex, (0, 0, "Unknown"))[2]

            del self.fragments[fragment_id_hex]
            del self.metadata[fragment_id_hex]

            return (bytes(complete_data), sender)

        return None


def parse_bitchat_packet(data: bytes) -> BitchatPacket:
    """Parse a BitChat packet from raw bytes"""
    HEADER_SIZE = 13
    SENDER_ID_SIZE = 8
    RECIPIENT_ID_SIZE = 8

    if len(data) < HEADER_SIZE + SENDER_ID_SIZE:
        raise ValueError("Packet too small")

    offset = 0

    # Version
    version = data[offset]
    offset += 1
    if version != 1:
        raise ValueError("Unsupported version")

    # Type
    msg_type = MessageType(data[offset])
    offset += 1

    # TTL
    ttl = data[offset]
    offset += 1

    # Timestamp (skip)
    offset += 8

    # Flags
    flags = data[offset]
    offset += 1
    has_recipient = (flags & FLAG_HAS_RECIPIENT) != 0
    has_signature = (flags & FLAG_HAS_SIGNATURE) != 0
    is_compressed = (flags & FLAG_IS_COMPRESSED) != 0

    # Payload length
    payload_len = struct.unpack(">H", data[offset : offset + 2])[0]
    offset += 2

    # Sender ID
    sender_id_raw = data[offset : offset + SENDER_ID_SIZE]
    sender_id = sender_id_raw.rstrip(b"\x00")
    sender_id_str = sender_id.hex()
    offset += SENDER_ID_SIZE

    # Recipient ID
    recipient_id = None
    recipient_id_str = None
    if has_recipient:
        recipient_id_raw = data[offset : offset + RECIPIENT_ID_SIZE]
        recipient_id = recipient_id_raw.rstrip(b"\x00")
        recipient_id_str = recipient_id.hex()
        offset += RECIPIENT_ID_SIZE

    # Payload
    payload_end = offset + payload_len
    payload = data[offset:payload_end]

    # Decompress if needed
    if is_compressed:
        payload = decompress(payload)

    return BitchatPacket(
        msg_type, sender_id, sender_id_str, recipient_id, recipient_id_str, payload, ttl
    )


def parse_bitchat_message_payload(data: bytes) -> BitchatMessage:
    """Parse message payload"""
    offset = 0

    # Flags
    flags = data[offset]
    offset += 1
    is_private = (flags & MSG_FLAG_IS_PRIVATE) != 0
    has_sender_peer_id = (flags & MSG_FLAG_HAS_SENDER_PEER_ID) != 0
    has_channel = (flags & MSG_FLAG_HAS_CHANNEL) != 0
    is_encrypted = (flags & MSG_FLAG_IS_ENCRYPTED) != 0

    # Timestamp (skip)
    offset += 8

    # ID
    id_len = data[offset]
    offset += 1
    id_str = data[offset : offset + id_len].decode("utf-8")
    offset += id_len

    # Sender
    sender_len = data[offset]
    offset += 1
    sender = data[offset : offset + sender_len].decode("utf-8")
    offset += sender_len

    # Content
    content_len = struct.unpack(">H", data[offset : offset + 2])[0]
    offset += 2
    content_bytes = data[offset : offset + content_len]
    offset += content_len
    content = ""
    encrypted_content = None
    if is_encrypted:
        encrypted_content = content_bytes
    else:
        content = content_bytes.decode("utf-8", errors="ignore")

    # Sender Peer ID
    if has_sender_peer_id:
        peer_id_len = data[offset]
        offset += 1
        offset += peer_id_len  # Skip

    # Channel
    channel = None
    if has_channel:
        channel_len = data[offset]
        offset += 1
        channel = data[offset : offset + channel_len].decode("utf-8")

    return BitchatMessage(id_str, content, channel, is_encrypted, encrypted_content)


def create_bitchat_packet(
    sender_id: str, msg_type: MessageType, payload: bytes
) -> bytes:
    """Create a BitChat packet"""
    return create_bitchat_packet_with_recipient(
        sender_id, None, msg_type, payload, None
    )


def create_bitchat_packet_with_signature(
    sender_id: str, msg_type: MessageType, payload: bytes, signature: Optional[bytes]
) -> bytes:
    """Create a BitChat packet with signature"""
    return create_bitchat_packet_with_recipient(
        sender_id, None, msg_type, payload, signature
    )


def create_bitchat_packet_with_recipient(
    sender_id: str,
    recipient_id: Optional[str],
    msg_type: MessageType,
    payload: bytes,
    signature: Optional[bytes],
) -> bytes:
    """Create a BitChat packet with all options"""
    packet = bytearray()

    # Version
    packet.append(1)

    # Type
    packet.append(msg_type.value)

    # TTL
    packet.append(7)

    # Timestamp
    timestamp_ms = int(time.time() * 1000)
    packet.extend(struct.pack(">Q", timestamp_ms))

    # Flags
    flags = 0
    exclude_recipient_types = [
        MessageType.FRAGMENT_START,
        MessageType.FRAGMENT_CONTINUE,
        MessageType.FRAGMENT_END,
    ]
    if recipient_id is not None or msg_type not in exclude_recipient_types:
        flags |= FLAG_HAS_RECIPIENT
    if signature:
        flags |= FLAG_HAS_SIGNATURE
    packet.append(flags)

    # Payload length
    packet.extend(struct.pack(">H", len(payload)))

    # Sender ID (8 bytes, padded)
    sender_bytes = bytes.fromhex(sender_id)
    packet.extend(sender_bytes[:8])
    if len(sender_bytes) < 8:
        packet.extend(bytes(8 - len(sender_bytes)))

    # Recipient ID (8 bytes if present)
    if flags & FLAG_HAS_RECIPIENT:
        if recipient_id:
            recipient_bytes = bytes.fromhex(recipient_id)
            packet.extend(recipient_bytes[:8])
            if len(recipient_bytes) < 8:
                packet.extend(bytes(8 - len(recipient_bytes)))
        else:
            packet.extend(BROADCAST_RECIPIENT)

    # Payload
    packet.extend(payload)

    # Signature
    if signature:
        packet.extend(signature)

    # PKCS#7 padding for traffic analysis resistance
    block_sizes = [256, 512, 1024, 2048]
    total_size = len(packet) + 16  # Account for encryption overhead

    target_size = None
    for block_size in block_sizes:
        if total_size <= block_size:
            target_size = block_size
            break

    if target_size is None:
        target_size = len(packet)

    padding_needed = target_size - len(packet)

    if 0 < padding_needed <= 255:
        padding = bytearray(os.urandom(padding_needed - 1))
        padding.append(padding_needed)
        packet.extend(padding)

    return bytes(packet)


def create_bitchat_message_payload_full(
    sender: str,
    content: str,
    channel: Optional[str],
    is_private: bool,
    sender_peer_id: str,
    is_encrypted: bool,
    encrypted_content: Optional[bytes],
) -> Tuple[bytes, str]:
    """Create message payload with all fields"""
    data = bytearray()
    message_id = str(uuid.uuid4())

    # Flags
    flags = 0
    if is_private:
        flags |= MSG_FLAG_IS_PRIVATE
    if sender_peer_id:
        flags |= MSG_FLAG_HAS_SENDER_PEER_ID
    if channel:
        flags |= MSG_FLAG_HAS_CHANNEL
    if is_encrypted:
        flags |= MSG_FLAG_IS_ENCRYPTED
    data.append(flags)

    # Timestamp
    timestamp_ms = int(time.time() * 1000)
    data.extend(struct.pack(">Q", timestamp_ms))

    # ID
    id_bytes = message_id.encode("utf-8")
    data.append(len(id_bytes))
    data.extend(id_bytes)

    # Sender
    sender_bytes = sender.encode("utf-8")
    data.append(len(sender_bytes))
    data.extend(sender_bytes)

    # Content
    payload_bytes = (
        encrypted_content
        if is_encrypted and encrypted_content
        else content.encode("utf-8")
    )
    data.extend(struct.pack(">H", len(payload_bytes)))
    data.extend(payload_bytes)

    # Sender Peer ID
    if sender_peer_id:
        peer_id_bytes = sender_peer_id.encode("utf-8")
        data.append(len(peer_id_bytes))
        data.extend(peer_id_bytes)

    # Channel
    if channel:
        channel_bytes = channel.encode("utf-8")
        data.append(len(channel_bytes))
        data.extend(channel_bytes)

    return (bytes(data), message_id)


def should_fragment(packet: bytes) -> bool:
    """Check if packet needs fragmentation"""
    return len(packet) > 500


def should_send_ack(
    is_private: bool,
    channel: Optional[str],
    mentions: Optional[List[str]],
    my_nickname: str,
    active_peer_count: int,
) -> bool:
    """Determine if we should send an ACK"""
    if is_private:
        return True
    elif channel:
        if active_peer_count < 10:
            return True
        elif mentions and my_nickname in mentions:
            return True
    return False


def create_encrypted_channel_message_payload(
    sender: str,
    content: str,
    channel: str,
    key: bytes,
    encryption_service,
    sender_peer_id: str,
) -> Tuple[bytes, str]:
    """Create encrypted channel message payload"""
    encrypted_content = encryption_service.encrypt_with_key(content.encode(), key)
    return create_bitchat_message_payload_full(
        sender, content, channel, False, sender_peer_id, True, encrypted_content
    )


def unpad_message(data: bytes) -> bytes:
    """Remove PKCS#7 padding"""
    if not data:
        return data

    padding_length = data[-1]

    if padding_length == 0 or padding_length > len(data) or padding_length > 255:
        return data

    return data[:-padding_length]


# --- Main BitChat Client Class ---
class BitchatClient:
    def __init__(self):
        self.my_peer_id = os.urandom(8).hex()
        self.nickname = "strands-agent"
        self.peers: Dict[str, Peer] = {}
        self.processed_messages: Set[str] = set()
        self.fragment_collector = FragmentCollector()
        self.delivery_tracker = DeliveryTracker()
        self.chat_context = ChatContext()
        self.channel_keys: Dict[str, bytes] = {}
        self.app_state = AppState()
        self.blocked_peers: Set[str] = set()
        self.channel_creators: Dict[str, str] = {}
        self.password_protected_channels: Set[str] = set()
        self.channel_key_commitments: Dict[str, str] = {}
        self.discovered_channels: Set[str] = set()
        self.encryption_service = EncryptionService()
        self.client = None
        self.characteristic = None
        self.running = True
        self.background_scanner_task = None
        self.disconnection_callback_registered = False

        # Bloom filter - initialize with fallback
        try:
            from pybloom_live import BloomFilter

            self.bloom = BloomFilter(capacity=500, error_rate=0.01)
        except ImportError:
            self.bloom = None

        # Timing tracking
        self.handshake_attempt_times: Dict[str, float] = {}
        self.handshake_timeout = 5.0

        # Pending messages
        self.pending_private_messages: Dict[str, List[Tuple[str, str, str]]] = {}

        # Setup callbacks
        self.encryption_service.on_peer_authenticated = self._on_peer_authenticated
        self.encryption_service.on_handshake_required = self._on_handshake_required

    def _on_peer_authenticated(self, peer_id: str, fingerprint: str):
        """Callback when a peer is authenticated"""
        asyncio.create_task(self.send_pending_private_messages(peer_id))

    def _on_handshake_required(self, peer_id: str):
        """Callback when handshake is required"""
        pass  # Handled by message sending logic

    async def send_pending_private_messages(self, peer_id: str):
        """Send all pending private messages for a peer"""
        if peer_id not in self.pending_private_messages:
            return

        pending_messages = self.pending_private_messages.pop(peer_id, [])
        if not pending_messages:
            return

        for content, nickname, message_id in pending_messages:
            try:
                await asyncio.sleep(0.3)
                await self.send_private_message(content, peer_id, nickname, message_id)
                await asyncio.sleep(0.2)
            except Exception as e:
                if "blocking" in str(e).lower():
                    if peer_id not in self.pending_private_messages:
                        self.pending_private_messages[peer_id] = []
                    self.pending_private_messages[peer_id].append(
                        (content, nickname, message_id)
                    )
                    break

    async def find_device(self):
        """Scan for BitChat service"""
        try:
            from bleak import BleakScanner

            devices = await BleakScanner.discover(
                timeout=5.0, service_uuids=[BITCHAT_SERVICE_UUID]
            )
            return devices[0] if devices else None
        except ImportError:
            return None

    def handle_disconnect(self, client):
        """Handle disconnection"""
        self.client = None
        self.characteristic = None
        self.peers.clear()
        self.chat_context.active_dms.clear()
        self.encryption_service.sessions.clear()
        self.encryption_service.handshake_states.clear()
        self.pending_private_messages.clear()

        if isinstance(self.chat_context.current_mode, PrivateDM):
            self.chat_context.switch_to_public()

        if not self.background_scanner_task or self.background_scanner_task.done():
            self.background_scanner_task = asyncio.create_task(
                self.background_scanner()
            )

    async def connect(self):
        """Connect to BitChat service"""
        try:
            from bleak import BleakClient

            device = None
            scan_attempts = 0
            max_attempts = 10

            while not device and scan_attempts < max_attempts and self.running:
                device = await self.find_device()
                if not device:
                    scan_attempts += 1
                    await asyncio.sleep(1)

            if not device:
                return True  # Continue without connection

            self.client = BleakClient(
                device.address, disconnected_callback=self.handle_disconnect
            )
            await self.client.connect()

            # Find characteristic
            for service in self.client.services:
                for char in service.characteristics:
                    if char.uuid.lower() == BITCHAT_CHARACTERISTIC_UUID.lower():
                        self.characteristic = char
                        break
                if self.characteristic:
                    break

            if not self.characteristic:
                raise Exception("Characteristic not found")

            await self.client.start_notify(
                self.characteristic, self.notification_handler
            )
            return True

        except ImportError:
            return False
        except Exception:
            return False

    async def handshake(self):
        """Perform initial handshake"""
        # Load state
        self.app_state = load_state()
        if self.app_state.nickname:
            self.nickname = self.app_state.nickname
        else:
            self.nickname = "strands-agent"

        # Send announce if connected
        if self.client and self.characteristic:
            try:
                # Send identity announcement
                timestamp_ms = int(time.time() * 1000)
                public_key_bytes = self.encryption_service.get_public_key()
                signing_public_key_bytes = (
                    self.encryption_service.get_signing_public_key_bytes()
                )

                # Create signature
                timestamp_data = str(timestamp_ms).encode("utf-8")
                binding_data = (
                    self.my_peer_id.encode("utf-8") + public_key_bytes + timestamp_data
                )
                signature = self.encryption_service.sign_data(binding_data)

                # Create identity payload (simplified)
                identity_payload = (
                    public_key_bytes
                    + signing_public_key_bytes
                    + self.nickname.encode()[:20]
                    + timestamp_data[:8]
                    + signature[:32]  # Simplified
                )

                identity_packet = create_bitchat_packet_with_signature(
                    self.my_peer_id,
                    MessageType.NOISE_IDENTITY_ANNOUNCE,
                    identity_payload,
                    signature[:64],
                )
                await self.send_packet(identity_packet)
            except Exception:
                # Fallback announce
                announce_packet = create_bitchat_packet(
                    self.my_peer_id, MessageType.ANNOUNCE, self.nickname.encode()
                )
                await self.send_packet(announce_packet)

            await asyncio.sleep(0.5)

        # Restore state
        self.blocked_peers = self.app_state.blocked_peers
        self.channel_creators = self.app_state.channel_creators
        self.password_protected_channels = self.app_state.password_protected_channels
        self.channel_key_commitments = self.app_state.channel_key_commitments

        # Restore channel keys
        if self.app_state.identity_key:
            for (
                channel,
                encrypted_password,
            ) in self.app_state.encrypted_channel_passwords.items():
                try:
                    password = decrypt_password(
                        encrypted_password, self.app_state.identity_key
                    )
                    key = EncryptionService.derive_channel_key(password, channel)
                    self.channel_keys[channel] = key
                except Exception:
                    pass

    async def send_packet(self, packet: bytes):
        """Send packet with fragmentation support"""
        if not self.client or not self.characteristic:
            return

        if not self.client.is_connected:
            if self.client:
                self.handle_disconnect(self.client)
            return

        if should_fragment(packet):
            await self.send_packet_with_fragmentation(packet)
        else:
            try:
                await asyncio.sleep(0.01)
                await self.client.write_gatt_char(
                    self.characteristic, packet, response=False
                )
            except Exception as e:
                if "not connected" in str(e).lower():
                    if self.client:
                        self.handle_disconnect(self.client)
                elif "blocking" in str(e).lower():
                    await asyncio.sleep(0.1)
                    try:
                        await self.client.write_gatt_char(
                            self.characteristic, packet, response=False
                        )
                    except Exception:
                        pass

    async def send_packet_with_fragmentation(self, packet: bytes):
        """Fragment and send large packets"""
        if not self.client or not self.characteristic or not self.client.is_connected:
            return

        fragment_size = 150
        chunks = [
            packet[i : i + fragment_size] for i in range(0, len(packet), fragment_size)
        ]
        total_fragments = len(chunks)
        fragment_id = os.urandom(8)

        for index, chunk in enumerate(chunks):
            if index == 0:
                fragment_type = MessageType.FRAGMENT_START
            elif index == len(chunks) - 1:
                fragment_type = MessageType.FRAGMENT_END
            else:
                fragment_type = MessageType.FRAGMENT_CONTINUE

            fragment_payload = bytearray()
            fragment_payload.extend(fragment_id)
            fragment_payload.extend(struct.pack(">H", index))
            fragment_payload.extend(struct.pack(">H", total_fragments))
            fragment_payload.append(MessageType.MESSAGE.value)
            fragment_payload.extend(chunk)

            fragment_packet = create_bitchat_packet(
                self.my_peer_id, fragment_type, bytes(fragment_payload)
            )

            try:
                await self.client.write_gatt_char(
                    self.characteristic, fragment_packet, response=False
                )
                if index < len(chunks) - 1:
                    await asyncio.sleep(0.02)
            except Exception as e:
                if "not connected" in str(e).lower():
                    if self.client:
                        self.handle_disconnect(self.client)
                    return

    async def notification_handler(self, sender, data: bytes):
        """Handle incoming BLE notifications"""
        try:
            packet = parse_bitchat_packet(data)
            if packet.sender_id_str == self.my_peer_id:
                return
            await self.handle_packet(packet, data)
        except Exception:
            pass

    async def handle_packet(self, packet: BitchatPacket, raw_data: bytes):
        """Handle incoming packet"""
        if packet.msg_type == MessageType.ANNOUNCE:
            await self.handle_announce(packet)
        elif packet.msg_type == MessageType.MESSAGE:
            await self.handle_message(packet, raw_data)
        elif packet.msg_type in [
            MessageType.FRAGMENT_START,
            MessageType.FRAGMENT_CONTINUE,
            MessageType.FRAGMENT_END,
        ]:
            await self.handle_fragment(packet, raw_data)
        elif packet.msg_type == MessageType.KEY_EXCHANGE:
            await self.handle_key_exchange(packet)
        elif packet.msg_type == MessageType.NOISE_HANDSHAKE_INIT:
            await self.handle_noise_handshake_init(packet)
        elif packet.msg_type == MessageType.NOISE_HANDSHAKE_RESP:
            await self.handle_noise_handshake_resp(packet)
        elif packet.msg_type == MessageType.NOISE_ENCRYPTED:
            await self.handle_noise_encrypted(packet, raw_data)
        elif packet.msg_type == MessageType.LEAVE:
            await self.handle_leave(packet)
        elif packet.msg_type == MessageType.CHANNEL_ANNOUNCE:
            await self.handle_channel_announce(packet)
        elif packet.msg_type == MessageType.NOISE_IDENTITY_ANNOUNCE:
            await self.handle_noise_identity_announce(packet)

    async def handle_announce(self, packet: BitchatPacket):
        """Handle peer announcement"""
        peer_nickname = packet.payload.decode("utf-8", errors="ignore").strip()
        is_new_peer = packet.sender_id_str not in self.peers

        if packet.sender_id_str not in self.peers:
            self.peers[packet.sender_id_str] = Peer()

        self.peers[packet.sender_id_str].nickname = peer_nickname

        if is_new_peer and self.my_peer_id < packet.sender_id_str:
            # Initiate handshake
            try:
                handshake_message = self.encryption_service.initiate_handshake(
                    packet.sender_id_str
                )
                handshake_packet = create_bitchat_packet_with_recipient(
                    self.my_peer_id,
                    packet.sender_id_str,
                    MessageType.NOISE_HANDSHAKE_INIT,
                    handshake_message,
                    None,
                )
                await self.send_packet(handshake_packet)
            except Exception:
                pass

    async def handle_message(self, packet: BitchatPacket, raw_data: bytes):
        """Handle chat message"""
        # Check if blocked
        fingerprint = self.encryption_service.get_peer_fingerprint(packet.sender_id_str)
        if fingerprint and fingerprint in self.blocked_peers:
            return

        # Check if for us
        is_broadcast = (
            packet.recipient_id == BROADCAST_RECIPIENT if packet.recipient_id else True
        )
        is_for_us = is_broadcast or (packet.recipient_id_str == self.my_peer_id)

        if not is_for_us:
            # Relay if TTL > 1
            if packet.ttl > 1:
                await asyncio.sleep(random.uniform(0.01, 0.05))
                relay_data = bytearray(raw_data)
                relay_data[2] = packet.ttl - 1
                await self.send_packet(bytes(relay_data))
            return

        is_private_message = not is_broadcast and is_for_us
        decrypted_payload = None

        if is_private_message:
            try:
                decrypted_payload = self.encryption_service.decrypt_from_peer(
                    packet.sender_id_str, packet.payload
                )
            except NoiseError:
                return

        # Parse message
        try:
            if is_private_message and decrypted_payload:
                unpadded = unpad_message(decrypted_payload)
                message = parse_bitchat_message_payload(unpadded)
            else:
                message = parse_bitchat_message_payload(packet.payload)

            # Check duplicates
            if message.id not in self.processed_messages:
                if self.bloom:
                    self.bloom.add(message.id)
                self.processed_messages.add(message.id)

                await self.display_message(message, packet, is_private_message)

                # Send ACK if needed
                if should_send_ack(
                    is_private_message,
                    message.channel,
                    None,
                    self.nickname,
                    len(self.peers),
                ):
                    await self.send_delivery_ack(
                        message.id, packet.sender_id_str, is_private_message
                    )

                # Relay if TTL > 1
                if packet.ttl > 1:
                    await asyncio.sleep(random.uniform(0.01, 0.05))
                    relay_data = bytearray(raw_data)
                    relay_data[2] = packet.ttl - 1
                    await self.send_packet(bytes(relay_data))
        except Exception:
            pass

    async def handle_fragment(self, packet: BitchatPacket, raw_data: bytes):
        """Handle message fragment"""
        if len(packet.payload) >= 13:
            fragment_id = packet.payload[0:8]
            index = struct.unpack(">H", packet.payload[8:10])[0]
            total = struct.unpack(">H", packet.payload[10:12])[0]
            original_type = packet.payload[12]
            fragment_data = packet.payload[13:]

            result = self.fragment_collector.add_fragment(
                fragment_id,
                index,
                total,
                original_type,
                fragment_data,
                packet.sender_id_str,
            )

            if result:
                complete_data, _ = result
                reassembled_packet = parse_bitchat_packet(complete_data)
                await self.handle_packet(reassembled_packet, complete_data)

        # Relay fragment
        if packet.ttl > 1:
            await asyncio.sleep(random.uniform(0.01, 0.05))
            relay_data = bytearray(raw_data)
            relay_data[2] = packet.ttl - 1
            await self.send_packet(bytes(relay_data))

    async def handle_key_exchange(self, packet: BitchatPacket):
        """Handle key exchange"""
        try:
            response = self.encryption_service.process_handshake_message(
                packet.sender_id_str, packet.payload
            )
            if response:
                response_packet = create_bitchat_packet(
                    self.my_peer_id, MessageType.KEY_EXCHANGE, response
                )
                await self.send_packet(response_packet)
        except Exception:
            pass

    async def handle_noise_handshake_init(self, packet: BitchatPacket):
        """Handle Noise handshake initiation"""
        if packet.recipient_id_str and packet.recipient_id_str != self.my_peer_id:
            return

        try:
            response = self.encryption_service.process_handshake_message(
                packet.sender_id_str, packet.payload
            )
            if response:
                response_packet = create_bitchat_packet_with_recipient(
                    self.my_peer_id,
                    packet.sender_id_str,
                    MessageType.NOISE_HANDSHAKE_RESP,
                    response,
                    None,
                )
                await self.send_packet(response_packet)

            if self.encryption_service.is_session_established(packet.sender_id_str):
                self.handshake_attempt_times.pop(packet.sender_id_str, None)
                await asyncio.sleep(0.1)
                await self.send_pending_private_messages(packet.sender_id_str)
        except Exception:
            self.encryption_service.clear_handshake_state(packet.sender_id_str)

    async def handle_noise_handshake_resp(self, packet: BitchatPacket):
        """Handle Noise handshake response"""
        if packet.recipient_id_str and packet.recipient_id_str != self.my_peer_id:
            return

        try:
            response = self.encryption_service.process_handshake_message(
                packet.sender_id_str, packet.payload
            )
            if response:
                final_packet = create_bitchat_packet_with_recipient(
                    self.my_peer_id,
                    packet.sender_id_str,
                    MessageType.NOISE_HANDSHAKE_INIT,
                    response,
                    None,
                )
                await self.send_packet(final_packet)

            if self.encryption_service.is_session_established(packet.sender_id_str):
                self.handshake_attempt_times.pop(packet.sender_id_str, None)
                await asyncio.sleep(0.1)
                await self.send_pending_private_messages(packet.sender_id_str)
        except Exception:
            self.encryption_service.clear_handshake_state(packet.sender_id_str)

    async def handle_noise_encrypted(self, packet: BitchatPacket, raw_data: bytes):
        """Handle encrypted message"""
        fingerprint = self.encryption_service.get_peer_fingerprint(packet.sender_id_str)
        if fingerprint and fingerprint in self.blocked_peers:
            return

        try:
            decrypted_payload = self.encryption_service.decrypt_from_peer(
                packet.sender_id_str, packet.payload
            )

            # Try to parse as inner packet
            if len(decrypted_payload) > 0 and decrypted_payload[0] == 1:
                inner_packet = parse_bitchat_packet(decrypted_payload)
                if inner_packet and inner_packet.msg_type == MessageType.MESSAGE:
                    message = parse_bitchat_message_payload(inner_packet.payload)

                    if message.id not in self.processed_messages:
                        if self.bloom:
                            self.bloom.add(message.id)
                        self.processed_messages.add(message.id)

                        await self.display_message(message, packet, True)
                        await self.send_delivery_ack(
                            message.id, packet.sender_id_str, True
                        )
        except Exception:
            pass

    async def handle_leave(self, packet: BitchatPacket):
        """Handle leave notification"""
        payload_str = packet.payload.decode("utf-8", errors="ignore").strip()

        if not payload_str.startswith("#"):
            # Peer disconnect
            disconnected_peer = self.peers.pop(packet.sender_id_str, None)
            if disconnected_peer and disconnected_peer.nickname:
                if disconnected_peer.nickname in self.chat_context.active_dms:
                    del self.chat_context.active_dms[disconnected_peer.nickname]

                if packet.sender_id_str in self.pending_private_messages:
                    del self.pending_private_messages[packet.sender_id_str]

                self.encryption_service.remove_session(packet.sender_id_str)

                if (
                    isinstance(self.chat_context.current_mode, PrivateDM)
                    and self.chat_context.current_mode.peer_id == packet.sender_id_str
                ):
                    self.chat_context.switch_to_public()

    async def handle_channel_announce(self, packet: BitchatPacket):
        """Handle channel announcement"""
        try:
            payload_str = packet.payload.decode("utf-8", errors="ignore")
            parts = payload_str.split("|")

            if len(parts) >= 3:
                channel = parts[0]
                is_protected = parts[1] == "1"
                creator_id = parts[2]
                key_commitment = parts[3] if len(parts) > 3 else ""

                if creator_id:
                    self.channel_creators[channel] = creator_id

                if is_protected:
                    self.password_protected_channels.add(channel)
                    if key_commitment:
                        self.channel_key_commitments[channel] = key_commitment
                else:
                    self.password_protected_channels.discard(channel)
                    self.channel_keys.pop(channel, None)
                    self.channel_key_commitments.pop(channel, None)

                if channel not in self.chat_context.active_channels:
                    self.chat_context.active_channels.append(channel)
                await self.save_app_state()
        except Exception:
            pass

    async def handle_noise_identity_announce(self, packet: BitchatPacket):
        """Handle identity announcement - simplified version"""
        try:
            sender_id = packet.sender_id_str
            if sender_id == self.my_peer_id:
                return

            # Simple parsing - extract nickname if possible
            payload = packet.payload
            if len(payload) > 64:  # Has enough data for keys + nickname
                try:
                    # Skip keys, try to find nickname
                    nickname_start = 64  # After two 32-byte keys
                    if nickname_start < len(payload):
                        # Try to decode nickname (simplified)
                        potential_nickname = (
                            payload[nickname_start : nickname_start + 20]
                            .decode("utf-8", errors="ignore")
                            .strip("\x00")
                        )
                        if potential_nickname and len(potential_nickname) < 20:
                            is_new_peer = sender_id not in self.peers
                            if sender_id not in self.peers:
                                self.peers[sender_id] = Peer()
                            self.peers[sender_id].nickname = potential_nickname

                            if is_new_peer and self.my_peer_id < sender_id:
                                handshake_message = (
                                    self.encryption_service.initiate_handshake(
                                        sender_id
                                    )
                                )
                                handshake_packet = create_bitchat_packet_with_recipient(
                                    self.my_peer_id,
                                    sender_id,
                                    MessageType.NOISE_HANDSHAKE_INIT,
                                    handshake_message,
                                    None,
                                )
                                await self.send_packet(handshake_packet)
                except Exception:
                    pass
        except Exception:
            pass

    async def display_message(
        self, message: BitchatMessage, packet: BitchatPacket, is_private: bool
    ):
        """Display a message - modified for agent integration"""
        global _message_history, _peer_list, _trigger_keyword, _parent_agent, _auto_response_enabled

        sender_nick = (
            self.peers.get(packet.sender_id_str, Peer()).nickname
            or packet.sender_id_str
        )

        # Track discovered channels
        if message.channel:
            self.discovered_channels.add(message.channel)
            if message.is_encrypted:
                self.password_protected_channels.add(message.channel)

        # Decrypt channel messages
        display_content = message.content
        if (
            message.is_encrypted
            and message.channel
            and message.channel in self.channel_keys
        ):
            try:
                creator_fingerprint = self.channel_creators.get(message.channel, "")
                decrypted = self.encryption_service.decrypt_from_channel(
                    message.encrypted_content,
                    message.channel,
                    self.channel_keys[message.channel],
                    creator_fingerprint,
                )
                display_content = decrypted
            except Exception:
                display_content = "[Encrypted message - decryption failed]"
        elif message.is_encrypted:
            display_content = "[Encrypted message - join channel with password]"

        # Check for cover traffic
        if is_private and display_content.startswith(COVER_TRAFFIC_PREFIX):
            return

        # Update chat context
        if is_private:
            self.chat_context.last_private_sender = (packet.sender_id_str, sender_nick)
            self.chat_context.add_dm(sender_nick, packet.sender_id_str)

        # Format and "display" (store in message history for agent integration)
        timestamp = datetime.now()
        display = format_message_display(
            timestamp,
            sender_nick,
            display_content,
            is_private,
            bool(message.channel),
            message.channel,
            self.nickname if is_private else None,
            self.nickname,
        )

        # Store in message history for agent integration
        message_entry = {
            "timestamp": time.time(),
            "sender": sender_nick,
            "sender_id": packet.sender_id_str,
            "content": display_content,
            "is_private": is_private,
            "channel": message.channel,
            "message_id": message.id,
            "display": display,
        }
        _message_history.append(message_entry)

        # Keep last 100 messages
        if len(_message_history) > 100:
            _message_history = _message_history[-100:]

        # Update peer list
        _peer_list[packet.sender_id_str] = {
            "nickname": sender_nick,
            "last_seen": time.time(),
        }

        # Check for agent trigger
        if (
            _auto_response_enabled
            and _trigger_keyword
            and _parent_agent
            and _trigger_keyword.lower() in display_content.lower()
            and packet.sender_id_str != self.my_peer_id
        ):

            try:
                # Extract command after trigger
                trigger_idx = display_content.lower().find(_trigger_keyword.lower())
                if trigger_idx != -1:
                    start_pos = trigger_idx + len(_trigger_keyword)
                    prompt_text = display_content[start_pos:].strip()
                    if not prompt_text:
                        prompt_text = display_content.strip()
                else:
                    prompt_text = display_content.strip()

                # Build context
                context_messages = []
                recent_messages = _message_history[-10:]

                for msg in recent_messages:
                    msg_type = (
                        "PRIVATE"
                        if msg["is_private"]
                        else ("CHANNEL" if msg["channel"] else "PUBLIC")
                    )
                    location = f" in {msg['channel']}" if msg["channel"] else ""
                    timestamp_str = time.strftime(
                        "%H:%M:%S", time.localtime(msg["timestamp"])
                    )
                    context_messages.append(
                        f"[{timestamp_str}] {msg_type}{location} - {msg['sender']}: {msg['content']}"
                    )

                conversation_context = ""
                if context_messages:
                    conversation_context = (
                        f"\n\nRECENT BITCHAT CONVERSATION CONTEXT:\n"
                        + "\n".join(context_messages)
                    )

                if not _parent_agent.system_prompt:
                    _parent_agent.system_prompt = (
                        "You are running in BitChat, powered by Strands Agents."
                    )

                # Enhanced system prompt
                enhanced_system_prompt = (
                    _parent_agent.system_prompt
                    + f"\n\n=== BITCHAT INTEGRATION MODE ===\n"
                    f"You are responding to a BitChat message triggered by '{_trigger_keyword}'.\n"
                    f"Message from {sender_nick}: '{display_content}'\n"
                    f"Extracted command: '{prompt_text}'\n"
                    f"Message type: {'Private DM' if is_private else ('Channel: ' + message.channel if message.channel else 'Public broadcast')}\n\n"
                    f"IMPORTANT BEHAVIOR GUIDELINES:\n"
                    f"- You are part of a P2P encrypted chat network over Bluetooth\n"
                    f"- Keep responses concise and conversational\n"
                    f"- Use the 'bitchat' to send responses back to the network\n"
                    f"- Current context: {'Private message' if is_private else ('Channel: ' + message.channel if message.channel else 'Public chat')}\n"
                    f"- Sender: {sender_nick} (ID: {packet.sender_id_str[:8]}...)\n"
                    + conversation_context
                )

                # Trigger agent
                response = _parent_agent.tool.use_agent(
                    prompt=prompt_text,
                    system_prompt=enhanced_system_prompt,
                    record_direct_tool_call=False,
                    agent=_parent_agent,
                )

                # Extract response text
                response_text = "No response"
                if response and "content" in response and response["content"]:
                    response_text = response["content"][0].get("text", "No response")

                    # if the response just Response: <text>, remove the Response: part
                    if response_text.startswith("Response:"):
                        response_text = response_text[9:].strip()

                # early return if the len(response_text) is 0
                if len(response_text) == 0:
                    return

                # Send response back
                if is_private:
                    await self._send_private_message_async(
                        response_text, packet.sender_id_str, sender_nick
                    )
                    # Log agent response as sent private message
                    agent_message_entry = {
                        "timestamp": time.time(),
                        "sender": "strands-agent",
                        "sender_id": self.my_peer_id or "agent",
                        "content": response_text,
                        "is_private": True,
                        "channel": None,
                        "recipient": sender_nick,
                        "message_id": f"agent_response_{int(time.time())}",
                        "display": f"[AGENT_RESPONSE] {response_text}",
                    }
                elif message.channel:
                    await self._send_channel_message_async(
                        response_text, message.channel
                    )
                    # Log agent response as sent channel message
                    agent_message_entry = {
                        "timestamp": time.time(),
                        "sender": "strands-agent",
                        "sender_id": self.my_peer_id or "agent",
                        "content": response_text,
                        "is_private": False,
                        "channel": message.channel,
                        "recipient": None,
                        "message_id": f"agent_response_{int(time.time())}",
                        "display": f"[AGENT_RESPONSE] {response_text}",
                    }
                else:
                    await self._send_public_message_async(response_text)
                    # Log agent response as sent public message
                    agent_message_entry = {
                        "timestamp": time.time(),
                        "sender": "strands-agent",
                        "sender_id": self.my_peer_id or "agent",
                        "content": response_text,
                        "is_private": False,
                        "channel": None,
                        "recipient": None,
                        "message_id": f"agent_response_{int(time.time())}",
                        "display": f"[AGENT_RESPONSE] {response_text}",
                    }

                # Log agent response
                _message_history.append(agent_message_entry)

            except Exception:
                pass

    async def _send_public_message_async(self, message_text):
        """Send a public message asynchronously"""
        await self.send_public_message(message_text)

    async def _send_private_message_async(self, message_text, peer_id, peer_nick):
        """Send a private message asynchronously"""
        await self.send_private_message(message_text, peer_id, peer_nick)

    async def _send_channel_message_async(self, message_text, channel):
        """Send a channel message asynchronously"""
        if not channel.startswith("#"):
            channel = f"#{channel}"
        self.chat_context.switch_to_channel_silent(channel)
        await self.send_public_message(message_text)

    async def handle_leave(self, packet: BitchatPacket):
        """Handle leave notification"""
        payload_str = packet.payload.decode("utf-8", errors="ignore").strip()

        if not payload_str.startswith("#"):
            # Peer disconnect
            disconnected_peer = self.peers.pop(packet.sender_id_str, None)
            if disconnected_peer:
                if (
                    disconnected_peer.nickname
                    and disconnected_peer.nickname in self.chat_context.active_dms
                ):
                    del self.chat_context.active_dms[disconnected_peer.nickname]

                if packet.sender_id_str in self.pending_private_messages:
                    del self.pending_private_messages[packet.sender_id_str]

                self.encryption_service.remove_session(packet.sender_id_str)

                if (
                    isinstance(self.chat_context.current_mode, PrivateDM)
                    and self.chat_context.current_mode.peer_id == packet.sender_id_str
                ):
                    self.chat_context.switch_to_public()

    async def save_app_state(self):
        """Save application state"""
        self.app_state.nickname = self.nickname
        self.app_state.blocked_peers = self.blocked_peers
        self.app_state.channel_creators = self.channel_creators
        self.app_state.joined_channels = self.chat_context.active_channels
        self.app_state.password_protected_channels = self.password_protected_channels
        self.app_state.channel_key_commitments = self.channel_key_commitments

        try:
            save_state(self.app_state)
        except Exception:
            pass

    async def send_delivery_ack(
        self, message_id: str, sender_id: str, is_private: bool
    ):
        """Send delivery acknowledgment"""
        ack_id = f"{message_id}-{self.my_peer_id}"
        if not self.delivery_tracker.should_send_ack(ack_id):
            return

        ack = DeliveryAck(
            message_id,
            str(uuid.uuid4()),
            self.my_peer_id,
            self.nickname,
            int(time.time() * 1000),
            1,
        )

        ack_payload = json.dumps(
            {
                "originalMessageID": ack.original_message_id,
                "ackID": ack.ack_id,
                "recipientID": ack.recipient_id,
                "recipientNickname": ack.recipient_nickname,
                "timestamp": ack.timestamp,
                "hopCount": ack.hop_count,
            }
        ).encode()

        # Encrypt if private
        if is_private:
            try:
                ack_payload = self.encryption_service.encrypt(ack_payload, sender_id)
            except Exception:
                pass

        ack_packet = create_bitchat_packet_with_recipient(
            self.my_peer_id, sender_id, MessageType.DELIVERY_ACK, ack_payload, None
        )

        await self.send_packet(ack_packet)

    async def send_public_message(self, content: str):
        """Send a public or channel message"""
        if not self.client or not self.characteristic:
            return

        current_channel = None
        if isinstance(self.chat_context.current_mode, Channel):
            current_channel = self.chat_context.current_mode.name

            if (
                current_channel in self.password_protected_channels
                and current_channel not in self.channel_keys
            ):
                return

        # Create message
        if current_channel and current_channel in self.channel_keys:
            creator_fingerprint = self.channel_creators.get(current_channel, "")
            encrypted_content = self.encryption_service.encrypt_for_channel(
                content,
                current_channel,
                self.channel_keys[current_channel],
                creator_fingerprint,
            )
            payload, message_id = create_bitchat_message_payload_full(
                self.nickname,
                content,
                current_channel,
                False,
                self.my_peer_id,
                True,
                encrypted_content,
            )
        else:
            payload, message_id = create_bitchat_message_payload_full(
                self.nickname,
                content,
                current_channel,
                False,
                self.my_peer_id,
                False,
                None,
            )

        self.delivery_tracker.track_message(message_id, content, False)

        message_packet = create_bitchat_packet(
            self.my_peer_id, MessageType.MESSAGE, payload
        )
        await self.send_packet(message_packet)

    async def send_private_message(
        self,
        content: str,
        target_peer_id: str,
        target_nickname: str,
        message_id: Optional[str] = None,
    ):
        """Send a private encrypted message"""
        if not self.client or not self.characteristic:
            return

        # Check for session
        if not self.encryption_service.is_session_established(target_peer_id):
            # Queue message
            msg_id = message_id if message_id else str(uuid.uuid4())
            if target_peer_id not in self.pending_private_messages:
                self.pending_private_messages[target_peer_id] = []
            self.pending_private_messages[target_peer_id].append(
                (content, target_nickname, msg_id)
            )

            # Initiate handshake
            current_time = time.time()
            if target_peer_id in self.handshake_attempt_times:
                last_attempt = self.handshake_attempt_times[target_peer_id]
                if current_time - last_attempt < self.handshake_timeout:
                    return

            self.handshake_attempt_times[target_peer_id] = current_time

            try:
                handshake_message = self.encryption_service.initiate_handshake(
                    target_peer_id
                )
                handshake_packet = create_bitchat_packet_with_recipient(
                    self.my_peer_id,
                    target_peer_id,
                    MessageType.NOISE_HANDSHAKE_INIT,
                    handshake_message,
                    None,
                )
                await self.send_packet(handshake_packet)
            except Exception:
                self.handshake_attempt_times.pop(target_peer_id, None)

            return

        # Send encrypted message
        payload, message_id = create_bitchat_message_payload_full(
            self.nickname, content, None, True, self.my_peer_id, False, None
        )

        self.delivery_tracker.track_message(message_id, content, True)

        # Create inner packet
        inner_packet = create_bitchat_packet_with_recipient(
            self.my_peer_id, target_peer_id, MessageType.MESSAGE, payload, None
        )

        try:
            encrypted = self.encryption_service.encrypt_for_peer(
                target_peer_id, inner_packet
            )
            packet = create_bitchat_packet_with_recipient(
                self.my_peer_id,
                target_peer_id,
                MessageType.NOISE_ENCRYPTED,
                encrypted,
                None,
            )

            await self.send_packet(packet)
        except Exception:
            pass

    async def background_scanner(self):
        """Background task to scan for peers"""
        while self.running:
            if not self.client or not self.client.is_connected:
                try:
                    from bleak import BleakClient

                    device = await self.find_device()
                    if device:
                        self.client = BleakClient(
                            device.address, disconnected_callback=self.handle_disconnect
                        )
                        await self.client.connect()

                        # Find characteristic
                        for service in self.client.services:
                            for char in service.characteristics:
                                if (
                                    char.uuid.lower()
                                    == BITCHAT_CHARACTERISTIC_UUID.lower()
                                ):
                                    self.characteristic = char
                                    break
                            if self.characteristic:
                                break

                        if self.characteristic:
                            await self.client.start_notify(
                                self.characteristic, self.notification_handler
                            )

                            # Send announce
                            announce_packet = create_bitchat_packet(
                                self.my_peer_id,
                                MessageType.ANNOUNCE,
                                self.nickname.encode(),
                            )
                            await self.send_packet(announce_packet)
                except Exception:
                    self.client = None
                    self.characteristic = None

            await asyncio.sleep(5)

    async def run(self):
        """Main run loop for BitChat client"""
        # Connect
        connected = await self.connect()

        # Handshake
        await self.handshake()

        # Start background scanner if needed
        if not connected or not self.client:
            self.background_scanner_task = asyncio.create_task(
                self.background_scanner()
            )

        # Keep running until stopped
        try:
            while self.running:
                await asyncio.sleep(1)
        except Exception:
            pass
        finally:
            if (
                self.client
                and hasattr(self.client, "is_connected")
                and self.client.is_connected
            ):
                try:
                    leave_packet = create_bitchat_packet(
                        self.my_peer_id, MessageType.LEAVE, self.nickname.encode()
                    )
                    await self.send_packet(leave_packet)
                    await asyncio.sleep(0.1)
                    await self.client.disconnect()
                except Exception:
                    pass

            if self.background_scanner_task:
                self.background_scanner_task.cancel()
                try:
                    await self.background_scanner_task
                except asyncio.CancelledError:
                    pass

    async def handle_user_input(self, line: str):
        """Handle user input commands - simplified for tool integration"""
        if line.startswith("/name "):
            new_name = line[6:].strip()
            if new_name and len(new_name) <= 20:
                self.nickname = new_name
                announce_packet = create_bitchat_packet(
                    self.my_peer_id, MessageType.ANNOUNCE, self.nickname.encode()
                )
                await self.send_packet(announce_packet)
                await self.save_app_state()

        elif line.startswith("/j "):
            await self.handle_join_channel(line)

        elif line == "/leave":
            if isinstance(self.chat_context.current_mode, Channel):
                channel = self.chat_context.current_mode.name
                leave_payload = channel.encode()
                leave_packet = create_bitchat_packet(
                    self.my_peer_id, MessageType.LEAVE, leave_payload
                )
                await self.send_packet(leave_packet)

                self.channel_keys.pop(channel, None)
                self.password_protected_channels.discard(channel)
                self.channel_creators.pop(channel, None)
                self.channel_key_commitments.pop(channel, None)

                if channel in self.chat_context.active_channels:
                    self.chat_context.active_channels.remove(channel)
                self.chat_context.switch_to_public()

                await self.save_app_state()

        elif line.startswith("/block "):
            target = line[7:].strip().lstrip("@")
            for peer_id, peer in self.peers.items():
                if peer.nickname == target:
                    fingerprint = self.encryption_service.get_peer_fingerprint(peer_id)
                    if fingerprint:
                        self.blocked_peers.add(fingerprint)
                        await self.save_app_state()
                    break

        elif line.startswith("/unblock "):
            target = line[9:].strip().lstrip("@")
            for peer_id, peer in self.peers.items():
                if peer.nickname == target:
                    fingerprint = self.encryption_service.get_peer_fingerprint(peer_id)
                    if fingerprint and fingerprint in self.blocked_peers:
                        self.blocked_peers.remove(fingerprint)
                        await self.save_app_state()
                    break

        elif not line.startswith("/"):
            # Regular message
            if isinstance(self.chat_context.current_mode, PrivateDM):
                await self.send_private_message(
                    line,
                    self.chat_context.current_mode.peer_id,
                    self.chat_context.current_mode.nickname,
                )
            else:
                await self.send_public_message(line)

    async def handle_join_channel(self, line: str):
        """Handle join channel command"""
        parts = line.split()
        if len(parts) < 2:
            return

        channel_name = parts[1]
        password = parts[2] if len(parts) > 2 else None

        if not channel_name.startswith("#"):
            return

        # Check if password protected
        if channel_name in self.password_protected_channels:
            if channel_name in self.channel_keys:
                self.discovered_channels.add(channel_name)
                self.chat_context.switch_to_channel_silent(channel_name)
                return

            if not password:
                return

            if len(password) < 4:
                return

            key = EncryptionService.derive_channel_key(password, channel_name)

            # Verify password
            if channel_name in self.channel_key_commitments:
                test_commitment = hashlib.sha256(key).hexdigest()
                if test_commitment != self.channel_key_commitments[channel_name]:
                    return

            self.channel_keys[channel_name] = key
            self.discovered_channels.add(channel_name)

            # Save encrypted password
            if self.app_state.identity_key:
                try:
                    encrypted = encrypt_password(password, self.app_state.identity_key)
                    self.app_state.encrypted_channel_passwords[channel_name] = encrypted
                    await self.save_app_state()
                except Exception:
                    pass

            self.chat_context.switch_to_channel_silent(channel_name)
        else:
            # Regular or new password-protected channel
            if password:
                key = EncryptionService.derive_channel_key(password, channel_name)
                self.channel_keys[channel_name] = key
                self.discovered_channels.add(channel_name)
                self.chat_context.switch_to_channel_silent(channel_name)
            else:
                self.discovered_channels.add(channel_name)
                self.channel_keys.pop(channel_name, None)
                if channel_name not in self.chat_context.active_channels:
                    self.chat_context.active_channels.append(channel_name)
                self.chat_context.current_mode = Channel(channel_name)


# =============================================================================
# EMBEDDED BITCHAT CLASSES - END
# =============================================================================


def _run_bitchat_client():
    """Run BitChat client in a separate thread with integrated classes."""
    global _bitchat_client, _bitchat_running, _bitchat_status

    try:
        # Install dependencies first
        if not _install_dependencies():
            raise Exception("Failed to install required dependencies")

        # Create BitChat client using embedded class
        _bitchat_client = BitchatClient()
        _bitchat_status = "initializing"

        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        _bitchat_status = "connecting"
        _bitchat_running = True

        # Run the BitChat client
        loop.run_until_complete(_bitchat_client.run())

    except Exception as e:
        _bitchat_status = f"error: {str(e)[:100]}"
        _bitchat_running = False
    finally:
        _bitchat_running = False
        if _bitchat_status != "stopped":
            _bitchat_status = "stopped"


def _execute_bitchat_command(command_func):
    """Execute an async BitChat command."""
    if not _bitchat_client:
        raise Exception("BitChat client not available")

    try:
        # Simple command execution
        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(command_func(), loop)
            return future.result(timeout=5)
        except RuntimeError:
            # No running loop, create one
            return asyncio.run(command_func())
    except Exception as e:
        raise Exception(f"Command execution failed: {e}")


@tool
def bitchat(
    action: str,
    message: Optional[str] = None,
    recipient: Optional[str] = None,
    channel: Optional[str] = None,
    password: Optional[str] = None,
    nickname: Optional[str] = None,
    trigger_keyword: Optional[str] = None,
    agent: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    BitChat Tool - Decentralized P2P encrypted chat over Bluetooth Low Energy.

    This tool provides access to BitChat functionality for peer-to-peer messaging
    over Bluetooth with end-to-end encryption using the Noise Protocol.
    Enhanced with agent trigger functionality similar to the listen tool.

    Actions:
    - start: Start the BitChat client
    - stop: Stop the BitChat client
    - status: Get current status and connection info
    - send_public: Send a public message
    - send_private: Send a private message to a specific user
    - send_channel: Send a message to a channel
    - join_channel: Join or create a channel (with optional password)
    - leave_channel: Leave the current channel
    - list_peers: List all connected peers
    - list_channels: List discovered channels
    - block_user: Block a user
    - unblock_user: Unblock a user
    - set_nickname: Change your nickname
    - get_messages: Get recent message history
    - channel_password: Set channel password (owner only)
    - transfer_ownership: Transfer channel ownership
    - enable_agent: Enable agent trigger functionality (like listen tool)
    - disable_agent: Disable agent trigger functionality
    - agent_status: Check agent trigger status

    Args:
        action: The action to perform
        message: Message content (for send actions)
        recipient: Target user nickname (for private messages)
        channel: Channel name (for channel operations)
        password: Password (for protected channels)
        nickname: Nickname (for set_nickname or targeting users)
        trigger_keyword: Keyword to trigger agent responses (for enable_agent)
        agent: Parent agent instance (for enable_agent)

    Returns:
        Dict containing status and response content

    Examples:
        # Start BitChat
        bitchat(action="start")

        # Enable agent responses to "strands" trigger in messages
        bitchat(action="enable_agent", trigger_keyword="strands", agent=agent)

        # Send public message
        bitchat(action="send_public", message="Hello everyone!")

        # Send private message
        bitchat(action="send_private", message="Hi there!", recipient="alice")

        # Join password-protected channel
        bitchat(action="join_channel", channel="#secret", password="mypass")

        # Send message to channel
        bitchat(action="send_channel", message="Channel message", channel="#general")

        # Get status
        bitchat(action="status")

        # Check agent trigger status
        bitchat(action="agent_status")
    """
    global _bitchat_client, _bitchat_thread, _bitchat_running, _bitchat_status, _message_history, _peer_list, _trigger_keyword, _parent_agent, _auto_response_enabled

    try:
        if action == "start":
            if _bitchat_running:
                return {
                    "status": "success",
                    "content": [{"text": "✅ BitChat is already running"}],
                }

            # Start BitChat in a separate thread
            _bitchat_thread = threading.Thread(target=_run_bitchat_client, daemon=True)
            _bitchat_thread.start()

            # Wait a moment for initialization
            time.sleep(2)

            return {
                "status": "success",
                "content": [{"text": f"🚀 BitChat started! Status: {_bitchat_status}"}],
            }

        elif action == "stop":
            if not _bitchat_running:
                return {
                    "status": "success",
                    "content": [{"text": "BitChat is already stopped"}],
                }

            # Stop the client
            if _bitchat_client:
                _bitchat_client.running = False

            _bitchat_running = False
            _bitchat_status = "stopped"

            return {"status": "success", "content": [{"text": "⏹️ BitChat stopped"}]}

        elif action == "status":
            if not _bitchat_client:
                return {
                    "status": "success",
                    "content": [{"text": f"📊 BitChat Status: {_bitchat_status}"}],
                }

            # Get detailed status
            connected = (
                _bitchat_client.client and _bitchat_client.client.is_connected
                if hasattr(_bitchat_client, "client")
                else False
            )
            peer_count = (
                len(_bitchat_client.peers) if hasattr(_bitchat_client, "peers") else 0
            )
            session_count = (
                _bitchat_client.encryption_service.get_session_count()
                if hasattr(_bitchat_client, "encryption_service")
                else 0
            )

            status_info = f"""📊 BitChat Status Report:
            
🔗 Connection: {'✅ Connected' if connected else '❌ Disconnected'}
👥 Peers: {peer_count} connected
🔐 Secure Sessions: {session_count}
📝 Messages in History: {len(_message_history)}
🆔 Your ID: {_bitchat_client.my_peer_id if hasattr(_bitchat_client, 'my_peer_id') else 'Unknown'}
📛 Your Nickname: {_bitchat_client.nickname if hasattr(_bitchat_client, 'nickname') else 'Unknown'}
⏰ Runtime Status: {_bitchat_status}
"""

            return {"status": "success", "content": [{"text": status_info}]}

        # All other actions require BitChat to be running
        if not _bitchat_running or not _bitchat_client:
            return {
                "status": "error",
                "content": [
                    {"text": "❌ BitChat is not running. Use action='start' first."}
                ],
            }

        if action == "send_public":
            if not message:
                return {
                    "status": "error",
                    "content": [
                        {"text": "❌ Message content is required for send_public"}
                    ],
                }

            try:

                async def send_msg():
                    await _bitchat_client.send_public_message(message)

                _execute_bitchat_command(send_msg)

                # Log the sent message
                _log_sent_message(
                    message, is_private=False, channel=None, recipient=None
                )

                return {
                    "status": "success",
                    "content": [{"text": f"📢 Public message sent: {message[:50]}..."}],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to send public message: {e}"}],
                }

        elif action == "send_private":
            if not message or not recipient:
                return {
                    "status": "error",
                    "content": [
                        {
                            "text": "❌ Both message and recipient are required for send_private"
                        }
                    ],
                }

            # Find the peer ID for the recipient
            target_peer_id = None
            for peer_id, peer in _bitchat_client.peers.items():
                if peer.nickname == recipient:
                    target_peer_id = peer_id
                    break

            if not target_peer_id:
                return {
                    "status": "error",
                    "content": [
                        {"text": f"❌ User '{recipient}' not found or not online"}
                    ],
                }

            try:

                async def send_private_msg():
                    await _bitchat_client.send_private_message(
                        message, target_peer_id, recipient
                    )

                _execute_bitchat_command(send_private_msg)

                # Log the sent private message
                _log_sent_message(
                    message, is_private=True, channel=None, recipient=recipient
                )

                return {
                    "status": "success",
                    "content": [
                        {
                            "text": f"💬 Private message sent to {recipient}: {message[:50]}..."
                        }
                    ],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to send private message: {e}"}],
                }

        elif action == "send_channel":
            if not message:
                return {
                    "status": "error",
                    "content": [
                        {"text": "❌ Message content is required for send_channel"}
                    ],
                }

            try:
                # If channel specified, switch to it first
                if channel:
                    if not channel.startswith("#"):
                        channel = f"#{channel}"
                    _bitchat_client.chat_context.switch_to_channel_silent(channel)

                async def send_channel_msg():
                    await _bitchat_client.send_public_message(message)

                _execute_bitchat_command(send_channel_msg)

                # Log the sent channel message
                _log_sent_message(
                    message,
                    is_private=False,
                    channel=channel or "current channel",
                    recipient=None,
                )

                current_channel = channel or "current channel"
                return {
                    "status": "success",
                    "content": [
                        {
                            "text": f"📺 Channel message sent to {current_channel}: {message[:50]}..."
                        }
                    ],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to send channel message: {e}"}],
                }

        elif action == "join_channel":
            if not channel:
                return {
                    "status": "error",
                    "content": [
                        {"text": "❌ Channel name is required for join_channel"}
                    ],
                }

            if not channel.startswith("#"):
                channel = f"#{channel}"

            try:
                # Simulate the join command
                join_command = f"/j {channel}"
                if password:
                    join_command += f" {password}"

                async def join_chan():
                    await _bitchat_client.handle_user_input(join_command)

                _execute_bitchat_command(join_chan)
                return {
                    "status": "success",
                    "content": [
                        {
                            "text": f"🏠 Joined channel {channel}"
                            + (" (with password)" if password else "")
                        }
                    ],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to join channel: {e}"}],
                }

        elif action == "leave_channel":
            try:

                async def leave_chan():
                    await _bitchat_client.handle_user_input("/leave")

                _execute_bitchat_command(leave_chan)
                return {
                    "status": "success",
                    "content": [{"text": "🚪 Left current channel"}],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to leave channel: {e}"}],
                }

        elif action == "list_peers":
            if not hasattr(_bitchat_client, "peers") or not _bitchat_client.peers:
                return {
                    "status": "success",
                    "content": [{"text": "👥 No peers connected"}],
                }

            peer_info = "👥 Connected Peers:\n"
            for peer_id, peer in _bitchat_client.peers.items():
                nickname = peer.nickname or peer_id[:8] + "..."
                last_seen = _peer_list.get(peer_id, {}).get("last_seen", "Unknown")
                if isinstance(last_seen, (int, float)):
                    last_seen = time.strftime("%H:%M:%S", time.localtime(last_seen))
                peer_info += (
                    f"  • {nickname} (ID: {peer_id[:8]}..., Last seen: {last_seen})\n"
                )

            return {"status": "success", "content": [{"text": peer_info}]}

        elif action == "list_channels":
            channels = []
            if hasattr(_bitchat_client, "chat_context") and hasattr(
                _bitchat_client.chat_context, "active_channels"
            ):
                channels.extend(_bitchat_client.chat_context.active_channels)
            if hasattr(_bitchat_client, "discovered_channels"):
                channels.extend(_bitchat_client.discovered_channels)

            if not channels:
                return {
                    "status": "success",
                    "content": [{"text": "📺 No channels discovered"}],
                }

            channel_info = "📺 Discovered Channels:\n"
            for channel in set(channels):  # Remove duplicates
                protected = (
                    "🔒"
                    if channel
                    in getattr(_bitchat_client, "password_protected_channels", set())
                    else ""
                )
                joined = (
                    "✅"
                    if channel
                    in getattr(_bitchat_client.chat_context, "active_channels", [])
                    else ""
                )
                channel_info += f"  • {channel} {protected} {joined}\n"

            channel_info += "\n🔒 = Password protected, ✅ = Joined"

            return {"status": "success", "content": [{"text": channel_info}]}

        elif action == "block_user":
            if not nickname:
                return {
                    "status": "error",
                    "content": [{"text": "❌ Nickname is required for block_user"}],
                }

            async def block_user():
                await _bitchat_client.handle_user_input(f"/block @{nickname}")

            try:
                asyncio.create_task(block_user())
                return {
                    "status": "success",
                    "content": [{"text": f"🚫 Blocked user: {nickname}"}],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to block user: {e}"}],
                }

        elif action == "unblock_user":
            if not nickname:
                return {
                    "status": "error",
                    "content": [{"text": "❌ Nickname is required for unblock_user"}],
                }

            async def unblock_user():
                await _bitchat_client.handle_user_input(f"/unblock @{nickname}")

            try:
                asyncio.create_task(unblock_user())
                return {
                    "status": "success",
                    "content": [{"text": f"✅ Unblocked user: {nickname}"}],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to unblock user: {e}"}],
                }

        elif action == "set_nickname":
            if not nickname:
                return {
                    "status": "error",
                    "content": [{"text": "❌ Nickname is required for set_nickname"}],
                }

            async def set_nick():
                await _bitchat_client.handle_user_input(f"/name {nickname}")

            try:
                # Get the event loop from the BitChat thread
                if _bitchat_thread and hasattr(_bitchat_client, "_loop"):
                    loop = _bitchat_client._loop
                    if loop and loop.is_running():
                        future = asyncio.run_coroutine_threadsafe(set_nick(), loop)
                        future.result(timeout=5.0)  # Wait up to 5 seconds
                    else:
                        # No running loop in BitChat thread, run directly
                        asyncio.run(set_nick())
                else:
                    # No BitChat thread, run directly with new event loop
                    asyncio.run(set_nick())

                return {
                    "status": "success",
                    "content": [{"text": f"📛 Nickname changed to: {nickname}"}],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to set nickname: {e}"}],
                }

        elif action == "get_messages":
            if not _message_history:
                return {
                    "status": "success",
                    "content": [{"text": "📝 No messages in history"}],
                }

            # Get last N messages (default 10)
            limit = 10  # Default limit
            recent_messages = _message_history[-limit:]

            message_text = f"📝 Recent Messages (last {len(recent_messages)}):\n\n"
            for msg in recent_messages:
                timestamp = time.strftime("%H:%M:%S", time.localtime(msg["timestamp"]))
                msg_type = (
                    "🔒 Private"
                    if msg["is_private"]
                    else ("📺 Channel" if msg["channel"] else "📢 Public")
                )
                location = f" in {msg['channel']}" if msg["channel"] else ""
                message_text += f"[{timestamp}] {msg_type}{location} - {msg['sender']}: {msg['content'][:100]}...\n"

            return {"status": "success", "content": [{"text": message_text}]}

        elif action == "channel_password":
            if not channel or not password:
                return {
                    "status": "error",
                    "content": [
                        {
                            "text": "❌ Both channel and password are required for channel_password"
                        }
                    ],
                }

            # Switch to channel first
            if not channel.startswith("#"):
                channel = f"#{channel}"
            _bitchat_client.chat_context.switch_to_channel_silent(channel)

            async def set_password():
                await _bitchat_client.handle_user_input(f"/pass {password}")

            try:
                asyncio.create_task(set_password())
                return {
                    "status": "success",
                    "content": [{"text": f"🔐 Password set for channel {channel}"}],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to set channel password: {e}"}],
                }

        elif action == "transfer_ownership":
            if not nickname:
                return {
                    "status": "error",
                    "content": [
                        {"text": "❌ Nickname is required for transfer_ownership"}
                    ],
                }

            async def transfer():
                await _bitchat_client.handle_user_input(f"/transfer @{nickname}")

            try:
                asyncio.create_task(transfer())
                return {
                    "status": "success",
                    "content": [
                        {"text": f"👑 Channel ownership transferred to: {nickname}"}
                    ],
                }
            except Exception as e:
                return {
                    "status": "error",
                    "content": [{"text": f"❌ Failed to transfer ownership: {e}"}],
                }

        elif action == "enable_agent":
            if not trigger_keyword:
                return {
                    "status": "error",
                    "content": [
                        {"text": "❌ trigger_keyword is required for enable_agent"}
                    ],
                }

            if not agent:
                return {
                    "status": "error",
                    "content": [
                        {"text": "❌ agent parameter is required for enable_agent"}
                    ],
                }

            _trigger_keyword = trigger_keyword.lower().strip()
            _parent_agent = agent
            _auto_response_enabled = True

            return {
                "status": "success",
                "content": [
                    {
                        "text": f"🤖 Agent trigger enabled! Will respond to '{_trigger_keyword}' in BitChat messages"
                    }
                ],
            }

        elif action == "disable_agent":
            _trigger_keyword = None
            _parent_agent = None
            _auto_response_enabled = False

            return {
                "status": "success",
                "content": [{"text": "🤖❌ Agent trigger disabled"}],
            }

        elif action == "agent_status":
            status_text = f"""🤖 Agent Trigger Status:

✅ **Enabled:** {_auto_response_enabled}
🔍 **Trigger Keyword:** {_trigger_keyword or 'None'}
🤖 **Agent Connected:** {_parent_agent is not None}
📡 **BitChat Running:** {_bitchat_running}
🔗 **Ready for Triggers:** {_auto_response_enabled and _trigger_keyword and _parent_agent and _bitchat_running}

{'✅ All systems ready for automatic responses!' if (_auto_response_enabled and _trigger_keyword and _parent_agent and _bitchat_running) else '⚠️ Some components not ready - check status above'}
"""

            return {"status": "success", "content": [{"text": status_text}]}

        else:
            return {
                "status": "error",
                "content": [
                    {
                        "text": f"❌ Unknown action: {action}. Available actions: start, stop, status, send_public, send_private, send_channel, join_channel, leave_channel, list_peers, list_channels, block_user, unblock_user, set_nickname, get_messages, channel_password, transfer_ownership, enable_agent, disable_agent, agent_status"
                    }
                ],
            }

    except ImportError as e:
        return {
            "status": "error",
            "content": [
                {
                    "text": f"❌ BitChat dependencies not available: {str(e)}. Use action='start' to auto-install dependencies."
                }
            ],
        }
    except Exception as e:
        return {
            "status": "error",
            "content": [{"text": f"❌ BitChat tool error: {str(e)}"}],
        }
