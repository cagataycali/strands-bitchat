import os
from strands import Agent
from strands.models.ollama import OllamaModel
from strands_tools import use_agent

from strands_bitchat import bitchat

model = OllamaModel(
    host="http://localhost:11434", model_id=os.getenv("STRANDS_MODEL_ID", "qwen3:8b")
)


def main():
    """Main entry point for strands-bitchat agent."""
    agent = Agent(
        model=model,
        system_prompt="BitChat enabled agent.",
        tools=[bitchat, use_agent],
        load_tools_from_directory=True,
    )

    print("🔐 BitChat Strands Agent")
    print("Type 'start bitchat' to begin P2P communication")
    print("Type 'exit' to quit\n")

    while True:
        try:
            q = input("\n> ").strip()
            if q.lower() == "exit":
                print("\nGoodbye! 👋")
                break
            if len(q) == 0:
                continue

            agent(q)
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except EOFError:
            print("\n\nGoodbye! 👋")
            break


if __name__ == "__main__":
    main()
