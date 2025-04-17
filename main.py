import genanki
import json
import anthropic
from pathlib import Path
import zipfile
import sqlite3
import tempfile
import shutil
import os
from typing import List, Dict
from dotenv import load_dotenv

load_dotenv()

def evaluate_importance(cards: List[Dict], api_key: str) -> List[Dict]:
    """Use Claude to evaluate card importance."""
    client = anthropic.Client(api_key=api_key)
    
    evaluated_cards = []
    total_cards = len(cards)
    
    for idx, card in enumerate(cards, 1):
        print(f"Evaluating card {idx}/{total_cards}")
        
        prompt = f"""As an educational content expert, rate the importance of this flashcard 
        from 1-10 based on its educational value and knowledge fundamentality.
        Only respond with a single number.
        
        Card content: {card['content']}"""
        
        message = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        importance = int(message.content)
        evaluated_cards.append({
            'nid': card['nid'],
            'importance': importance,
            'content': card['content']
        })
    
    return evaluated_cards

def get_top_20_percent(cards: List[Dict]) -> List[int]:
    """Return the note IDs of the top 20% most important cards."""
    sorted_cards = sorted(cards, key=lambda x: x['importance'], reverse=True)
    cutoff = int(len(sorted_cards) * 0.2)
    return [card['nid'] for card in sorted_cards[:cutoff]]

def main():
    # Get API key from environment variable
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
    
    # Get deck file path from command line argument
    import sys
    if len(sys.argv) > 1:
        deck_path = sys.argv[1]
    else:
        print("Please provide the path to your .apkg file as a command line argument")
        sys.exit(1)
    
    print(f"Processing deck: {deck_path}")
    
    # Extract and evaluate cards
    cards = extract_cards_from_apkg(deck_path)
    print(f"Found {len(cards)} cards")
    
    evaluated_cards = evaluate_importance(cards, api_key)
    important_nids = get_top_20_percent(evaluated_cards)
    
    # Save results
    output_file = 'important_card_nids.txt'
    with open(output_file, 'w') as f:
        for nid in important_nids:
            f.write(f"{nid}\n")
    
    print(f"Saved {len(important_nids)} important note IDs to {output_file}")
    print("\nTo use these in Anki:")
    print("1. Open Anki's browser")
    print("2. Search for: nid:" + " or nid:".join(str(nid) for nid in important_nids))
    print("3. Select all other cards (Ctrl+A, then Ctrl+Shift+A)")
    print("4. Press Ctrl+J to suspend the unimportant cards")

if __name__ == "__main__":
    main()