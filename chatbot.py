import re
import sys
import time
import json
from typing import Dict, List, Optional
from datetime import datetime
from difflib import get_close_matches

class EnhancedLeagueChatbot:
    def __init__(self):
        """
        Enhanced League of Legends chatbot with improved features.
        """
        self.session_history = []
        self.last_champion_mentioned = None
        self.CHAMPION_DATA = dict()

         # Load champion data from JSON file
        try:
            with open("data.json", "r") as file:
                self.CHAMPION_DATA = json.load(file)
        except FileNotFoundError:
            raise Exception("data.json file not found. Please ensure the file exists in the same directory.")
        except json.JSONDecodeError:
            raise Exception("Failed to decode data.json. Please ensure it contains valid JSON.")
        
        # Extended keyword patterns
        self.patterns = {
            "abilities": r"abilities?|skills?|spells?",
            "items": r"items?|builds?|buy|purchase",
            "runes": r"runes?|perks?",
            "matchups": r"matchups?|versus|vs|counter|against",
            "role": r"role|position|lane",
            "tips": r"tips?|advice|help|guide",
            "combo": r"combo|rotation|sequence"
        }

    def print_with_typing_effect(self, text: str, delay: float = 0.01):
        """Print text with a typing effect."""
        for char in text:
            sys.stdout.write(char)
            sys.stdout.flush()
            time.sleep(delay)
        print()

    def format_champion_name(self, name: str) -> str:
        """Format champion name with proper capitalization."""
        return name.title()

    def find_champion(self, text: str) -> Optional[str]:
        """
        Find champion name in text with fuzzy matching and suggestions.
        """
        text_words = text.lower().split()
        for champion in self.CHAMPION_DATA.keys():
            if champion in text_words:
                return champion
        
        # Fuzzy matching for similar names
        possible_champions = []
        for word in text_words:
            matches = get_close_matches(word, self.CHAMPION_DATA.keys(), n=1, cutoff=0.7)
            if matches:
                possible_champions.extend(matches)
        
        return possible_champions[0] if possible_champions else None

    def generate_ability_info(self, champion: str) -> str:
        """Generate formatted ability information for a champion."""
        abilities = self.CHAMPION_DATA[champion].get("abilities", {})
        if not abilities:
            return f"Sorry, I don't have detailed ability information for {self.format_champion_name(champion)} yet."
        
        return (f"Abilities for {self.format_champion_name(champion)}:\n"
                f"Passive: {abilities['passive']}\n"
                f"Q: {abilities['Q']}\n"
                f"W: {abilities['W']}\n"
                f"E: {abilities['E']}\n"
                f"R: {abilities['R']}")

    def get_contextual_response(self, user_input: str) -> str:
        """
        Generate a response based on user input and context.
        """
        user_input = user_input.lower()
        champion = self.find_champion(user_input)
        
        # If no champion found, check if we should use the last mentioned champion
        if not champion and self.last_champion_mentioned and "it" in user_input:
            champion = self.last_champion_mentioned
        
        if not champion:
            return self.get_general_response(user_input)
        
        self.last_champion_mentioned = champion
        champ_data = self.CHAMPION_DATA[champion]
        
        # Check for specific queries about the champion
        if re.search(self.patterns["abilities"], user_input):
            return self.generate_ability_info(champion)
        
        elif re.search(self.patterns["items"], user_input):
            items = ", ".join(champ_data["recommended_items"])
            return f"Recommended items for {self.format_champion_name(champion)}:\n{items}"
        
        elif re.search(self.patterns["runes"], user_input):
            runes = ", ".join(champ_data["recommended_runes"])
            return f"Recommended runes for {self.format_champion_name(champion)}:\n{runes}"
        
        elif re.search(self.patterns["matchups"], user_input):
            strong = ", ".join(champ_data["matchups"]["strong_against"])
            weak = ", ".join(champ_data["matchups"]["weak_against"])
            return (f"{self.format_champion_name(champion)} matchups:\n"
                   f"Strong against: {strong}\n"
                   f"Weak against: {weak}")
        
        elif re.search(self.patterns["role"], user_input):
            return f"{self.format_champion_name(champion)} is played as: {champ_data['role']}"
        
        elif re.search(self.patterns["tips"], user_input):
            return f"Tips for {self.format_champion_name(champion)}: {champ_data['tips']}"
        
        # General champion overview
        return (f"Champion Overview - {self.format_champion_name(champion)}:\n"
                f"Role: {champ_data['role']}\n"
                f"Tips: {champ_data['tips']}\n"
                f"\nYou can ask about {champion}'s abilities, items, runes, or matchups!")

    def get_general_response(self, user_input: str) -> str:
        """Handle general queries and commands."""
        if any(word in user_input for word in ["hello", "hi", "hey"]):
            return "Hello! I'm your League of Legends expert. Ask me about any champion's abilities, items, runes, or matchups!"
        
        elif "help" in user_input:
            return ("Try these commands:\n"
                   "- 'Tell me about [champion]'\n"
                   "- '[champion] abilities'\n"
                   "- '[champion] recommended items'\n"
                   "- '[champion] runes'\n"
                   "- '[champion] matchups'\n"
                   "- '[champion] tips'")
        
        return ("I'm not sure what you're asking about. Try mentioning a specific champion, "
                "or type 'help' to see available commands!")

    def log_interaction(self, user_input: str, response: str):
        """Log the interaction for context and history."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.session_history.append({
            "timestamp": timestamp,
            "user_input": user_input,
            "response": response
        })

def main():
    """Run the interactive chatbot with enhanced features."""
    bot = EnhancedLeagueChatbot()
    
    # Display welcome message
    welcome_text = """
    ╔══════════════════════════════════════════════╗
    ║       Enhanced LoL Expert Bot v2.0           ║
    ╚══════════════════════════════════════════════╝
    
    Ask me about any champion's:
    • Abilities and combos
    • Item builds
    • Rune setups
    • Matchups and counters
    • Role-specific tips
    
    Type 'help' for commands or 'exit' to quit.
    """
    print(welcome_text)
    
    while True:
        try:
            # Get timestamp and user input
            timestamp = datetime.now().strftime("%H:%M:%S")
            user_input = input(f"\n[{timestamp}] You: ").strip()
            
            # Check for exit command
            if user_input.lower() in ['exit', 'quit', 'bye']:
                bot.print_with_typing_effect("\nThanks for using the LoL Expert Bot. GLHF!")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            # Generate and display response
            print(f"\n[{timestamp}] Bot: ", end='')
            response = bot.get_contextual_response(user_input)
            bot.print_with_typing_effect(response)
            
            # Log the interaction
            bot.log_interaction(user_input, response)
            
        except KeyboardInterrupt:
            print("\n\nBot terminated by user. GLHF!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            print("Please try again with a different question.")

if __name__ == "__main__":
    main()
    
