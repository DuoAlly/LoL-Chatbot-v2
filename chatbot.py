import os
import openai
from datetime import datetime

MAX_HISTORY = 10


def print_header():
    print("╔══════════════════════════════════════════════╗")
    print("║       Enhanced LoL Expert Bot v2.0           ║")
    print("╚══════════════════════════════════════════════╝\n")
    print("Ask me anything about League of Legends:")
    print("• Champion abilities and combos")
    print("• Item builds and rune setups")
    print("• Matchups and counters")
    print("• Role-specific tips and strategy\n")
    print("Type 'help' for commands or 'exit' to quit.\n")


def timestamp() -> str:
    return datetime.now().strftime("[%H:%M:%S]")


def print_user(message: str):
    print(f"{timestamp()} You: {message}")


def print_bot(content: str):
    print(f"{timestamp()} Bot:\n{content}\n")


def prune_history(history: list):
    if len(history) > MAX_HISTORY:
        del history[:-MAX_HISTORY]


def chat_loop(client):
    print_header()
    history = []
    system_base = {
        "role": "system",
        "content": (
            "You are an expert League of Legends assistant. "
            "Only answer questions related to League of Legends gameplay, champions, items, runes, matchups, or strategy. "
            "If asked anything unrelated to League of Legends, respond with: 'I’m sorry, but I only answer questions about League of Legends.'"
        )
    }

    while True:
        user_input = input().strip()
        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break
        if user_input.lower() == "help":
            print("Commands:\nhelp - Show this help message\nexit, quit - Quit the chat")
            continue

        print_user(user_input)
        messages = [system_base] + history + [{"role": "user", "content": user_input}]

        try:
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
            bot_msg = response.choices[0].message.content.strip()
            history.append({"role": "assistant", "content": bot_msg})
            prune_history(history)
            print_bot(bot_msg)
        except openai.OpenAIError as e:
            print(f"OpenAI API error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY environment variable is not set.")
        exit(1)

    openai.api_key = api_key
    client = openai.OpenAI()
    chat_loop(client)


if __name__ == "__main__":
    main()
