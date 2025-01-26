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
        Enhanced League of Legends chatbot with improved features and error handling.
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
        
        # Updated keyword patterns (still no "combo" since your JSON doesn't have it)
        self.patterns = {
            "abilities": r"abilities?|skills?|spells?",
            "items": r"items?|builds?|buy|purchase",
            "runes": r"runes?|perks?",
            "matchups": r"matchups?|versus|vs|counter|against",
            "role": r"role|position|lane",
            "tips": r"tips?|advice|help|guide"
        }
        
        # For single-ability references, map user queries (ult, ultimate) to "R", etc.
        self.single_ability_map = {
            "passive": "passive",
            "q": "Q",
            "w": "W",
            "e": "E",
            "r": "R",
            "ult": "R",
            "ultimate": "R"
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
        Find champion name in text with a direct or fuzzy match.
        Returns the champion key if found, otherwise None.
        """
        # We'll split on any non-alphanumeric to be safer with punctuation
        text_words = re.findall(r'\w+', text.lower())

        # Direct match first
        for champion in self.CHAMPION_DATA.keys():
            if champion.lower() in text_words:
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
        champ_data = self.CHAMPION_DATA.get(champion, {})
        abilities = champ_data.get("abilities", {})
        
        # If no abilities data is found:
        if not abilities:
            return f"Sorry, I don't have detailed ability info for {self.format_champion_name(champion)}."
        
        # Safely access each ability
        passive = abilities.get("passive", "No passive info available.")
        q_ability = abilities.get("Q", "No Q info available.")
        w_ability = abilities.get("W", "No W info available.")
        e_ability = abilities.get("E", "No E info available.")
        r_ability = abilities.get("R", "No R info available.")
        
        return (f"Abilities for {self.format_champion_name(champion)}:\n"
                f"Passive: {passive}\n"
                f"Q: {q_ability}\n"
                f"W: {w_ability}\n"
                f"E: {e_ability}\n"
                f"R: {r_ability}")

    def generate_single_ability_info(self, champion: str, ability_key: str) -> str:
        """
        Return info for a single ability (Q, W, E, R, passive) given a champion.
        ability_key must be one of 'passive', 'Q', 'W', 'E', 'R'.
        """
        champ_data = self.CHAMPION_DATA.get(champion, {})
        abilities = champ_data.get("abilities", {})
        
        # Provide the single ability description or a fallback
        description = abilities.get(ability_key, f"No {ability_key} info available for {self.format_champion_name(champion)}.")
        
        if ability_key in ["Q", "W", "E", "R"]:
            return f"{self.format_champion_name(champion)}'s {ability_key} ability: {description}"
        elif ability_key == "passive":
            return f"{self.format_champion_name(champion)}'s Passive: {description}"
        else:
            return f"{self.format_champion_name(champion)}: {description}"

    def get_contextual_response(self, user_input: str) -> str:
        """
        Generate a response based on user input and context.
        """
        user_input_lower = user_input.lower()
        champion = self.find_champion(user_input_lower)
        
        # If no champion found, check if "it" might refer to the last mentioned champion
        if not champion and self.last_champion_mentioned and "it" in user_input_lower:
            champion = self.last_champion_mentioned
        
        # If still no champion, return a general response
        if not champion:
            return self.get_general_response(user_input_lower)
        
        # Update last champion mentioned for context
        self.last_champion_mentioned = champion
        champ_data = self.CHAMPION_DATA.get(champion, {})

        # ---------------------------------------------------------
        # 1) Check if user is asking: "Is [item] good on [champion]?"
        #             or  "Should I buy [item] on [champion]?"
        # ---------------------------------------------------------
        # We'll capture whatever is in place of [item] and do a
        # case-insensitive match against recommended_items.
        if re.search(r"is .* good on", user_input_lower) or re.search(r"should i buy .* on", user_input_lower):
            # Try to capture the item name from either pattern
            item_match = re.search(r"is (.*?) good on", user_input_lower)
            if not item_match:
                item_match = re.search(r"should i buy (.*?) on", user_input_lower)
            
            if item_match:
                item_name = item_match.group(1).strip()
                
                recommended_items = champ_data.get("recommended_items", [])
                found = False
                for rec_item in recommended_items:
                    if rec_item.lower() == item_name.lower():
                        found = True
                        break
                
                if found:
                    return f"Yes, {self.format_champion_name(champion)} commonly builds {item_name}."
                else:
                    # Optional: show typical items
                    if recommended_items:
                        return (f"No, {item_name} is not typically recommended on {self.format_champion_name(champion)}.\n"
                                f"They usually build: {', '.join(recommended_items)}")
                    else:
                        return (f"No, {item_name} is not typically recommended on {self.format_champion_name(champion)}.\n"
                                "I currently have no recommended items listed for them.")

        # ----------------------------------------------------------------
        # 2) Check if user is asking for a specific ability (Q, W, E, R, ult, ultimate, passive)
        #    using a word-boundary regex so it doesn't match partial words.
        # ----------------------------------------------------------------
        for raw_key, ability_key in self.single_ability_map.items():
            if re.search(rf"\b{re.escape(raw_key.lower())}\b", user_input_lower):
                return self.generate_single_ability_info(champion, ability_key)

        # 3) If not a single ability or item inquiry, check other queries
        if re.search(self.patterns["abilities"], user_input_lower):
            return self.generate_ability_info(champion)
        
        elif re.search(self.patterns["items"], user_input_lower):
            items = champ_data.get("recommended_items", [])
            if items:
                return f"Recommended items for {self.format_champion_name(champion)}:\n" + ", ".join(items)
            else:
                return f"Sorry, I don't have recommended item info for {self.format_champion_name(champion)}."
        
        elif re.search(self.patterns["runes"], user_input_lower):
            runes = champ_data.get("recommended_runes", [])
            if runes:
                return f"Recommended runes for {self.format_champion_name(champion)}:\n" + ", ".join(runes)
            else:
                return f"Sorry, I don't have recommended rune info for {self.format_champion_name(champion)}."
        
        elif re.search(self.patterns["matchups"], user_input_lower):
            matchups = champ_data.get("matchups", {})
            strong = matchups.get("strong_against", [])
            weak = matchups.get("weak_against", [])
            if strong or weak:
                strong_str = ", ".join(strong) if strong else "N/A"
                weak_str = ", ".join(weak) if weak else "N/A"
                return (f"{self.format_champion_name(champion)} matchups:\n"
                        f"Strong against: {strong_str}\n"
                        f"Weak against: {weak_str}")
            else:
                return f"Sorry, I don't have matchup info for {self.format_champion_name(champion)}."
        
        elif re.search(self.patterns["role"], user_input_lower):
            role = champ_data.get("role", "No role information available.")
            return f"{self.format_champion_name(champion)} is typically played as: {role}"
        
        elif re.search(self.patterns["tips"], user_input_lower):
            tips = champ_data.get("tips", "No tips available for this champion.")
            return f"Tips for {self.format_champion_name(champion)}:\n{tips}"

        # 4) If no specific query, give a short overview
        role = champ_data.get("role", "No role data available.")
        tips = champ_data.get("tips", "No tips available.")
        return (f"Champion Overview - {self.format_champion_name(champion)}:\n"
                f"Role: {role}\n"
                f"Tips: {tips}\n"
                f"\nYou can ask about {self.format_champion_name(champion)}'s abilities, "
                "items, runes, or matchups!")

    def get_general_response(self, user_input: str) -> str:
        """
        Handle general queries and commands when no specific champion is identified.
        """
        if any(word in user_input for word in ["hello", "hi", "hey"]):
            return ("Hello! I'm your League of Legends expert. "
                    "Ask me about any champion's abilities, items, runes, or matchups!")
        
        elif "help" in user_input:
            return (
                "Try these commands:\n"
                "- 'Tell me about [champion]'\n"
                "- '[champion] abilities' (for a full ability list)\n"
                "- '[champion] recommended items'\n"
                "- '[champion] runes'\n"
                "- '[champion] matchups'\n"
                "- '[champion] tips'\n"
                # "- 'What is [champion] Q/W/E/R/passive?' or 'What is [champion] ult/ultimate?'\n"
                # "- 'Is [item] good on [champion]?' or 'Should I buy [item] on [champion]?'"
            )
        
        return (
            "I'm not sure what you're asking about. "
            "Try mentioning a specific champion, or type 'help' to see available commands!"
        )

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
    ║       Enhanced LoL Expert Bot v2.1           ║
    ╚══════════════════════════════════════════════╝
    
    Ask me about any champion's:
    • Abilities (Q, W, E, R, or Passive)
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
