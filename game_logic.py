from typing import List, Tuple, Optional
from models import Player, Message, ChatGPTMessage
import random
from sampledata import GENES, NAMES, WORDS  # Assuming these are defined in your sampledata.py
from player_logic import make_move, create_player, add_to_history, get_last_move, get_outbox, add_points
import json
from utils import mermaid_print


# Play one round of the game
# returns updated players
def play_round(players:List[Player], secrets:List[str]) -> List[Player]:
    # breakpoint()

    outboxes = [get_outbox(player, secrets) for player in players]

    modified_players = []
    for player in players:
        inbox = get_inbox(outboxes, player)
        secret_and_inbox = "Your secret: " + player["secret"] + "\nYour points: "+str(player["points"]) + "\n" + inbox
        chat_message: ChatGPTMessage = {
            "role": "user",
            "content": secret_and_inbox
        }
        player_with_new_history = add_to_history(player, chat_message)
        new_player = make_move(player_with_new_history)
        new_player = add_points(new_player, -1)
        modified_players.append(new_player)
    # breakpoint()
    return modified_players


# Initialize the game. Creates players and secrets.
# num_players: number of players
# required_secrets: number of secrets each player needs to find to win
# returns: list of players, list of secrets
def initialize_game(num_players:int, required_secrets:int) -> Tuple[List[Player], List[str]]:
    secrets = WORDS[:required_secrets]
    names = NAMES[:num_players]
    players = []
    for i in range(num_players):
        name = names[i]
        secret = secrets[i % len(secrets)]
        dna = random.choices(GENES, k=1)
        players.append(create_player(name, dna, required_secrets, secret, names))
    return players, secrets


# Check if any player guessed correctly
# returns: updated players, winners
def get_winners(players:List[Player], secrets:List[str]) -> Tuple[List[Player], List[Player]]:
    required_secrets = len(secrets)
    winners = []
    loosers = []
    new_players = []
    for player in players:
        last_move = get_last_move(player)

        if last_move is not None and last_move["name"] == "submit_guess":
            guess = json.loads(last_move["arguments"])["secrets"].split(",")
            guess = [secret.strip() for secret in guess]
            mermaid_print(f"Note over {player['name']}: Guess: {guess}")
            correct = sum([1 for secret in guess if secret in secrets])
            mistakes = [secret for secret in guess if secret not in secrets]
            is_winner = correct >= required_secrets
            if is_winner:
                winner = add_to_history(player, {
                        "role": "function",
                        "name": "submit_guess",
                        "content": f"You win. You got {correct} correct secrets. Congratulations!"
                    })
                winner = add_points(winner, 30)
                winners.append(winner)
                new_players.append(winner)
            else:
                looser = add_to_history(player, {
                        "role": "function",
                        "name": "submit_guess",
                        "content": f"You only got {correct} correct secrets but you need {required_secrets}. Wrong secrets:{','.join(mistakes)}"
                    })
                looser = add_points(looser, -10)
                loosers.append(looser)
                new_players.append(looser)
        else:
            new_players.append(player)
    # replace the players
                
    return new_players, winners



# Get the inbox of a player
# outboxes: list of outboxes
# player: player
# returns: inbox
def get_inbox(outboxes: List[Optional[Message]], player: Player) -> str:
    inbox = [outbox for outbox in outboxes if outbox is not None and outbox["to"] == player["name"]]
    return format_inbox(inbox)

# Format the inbox for printing
# inbox: inbox
# returns: formatted inbox
def format_inbox(inbox):
    content = "Make your move."
    if len(inbox) > 0:
        formatted_inbox = "\n".join([f"{message['from']}: {message['message']}" for message in inbox])
        content = f"{formatted_inbox}"
    return content
