import random
from collections import defaultdict
import json
import openai
from sampledata import GENES, NAMES, WORDS, INITIAL_PROMPT
from terminalplayer import TerminalPlayer
import sys
from typing import List, Tuple, Dict, Optional, TypedDict
from pydantic import Field


# Pydantic Models


class Message(TypedDict):
    to: str
    message: str

class ChatGPTMessage(TypedDict, total=False):
    role: str  # "system", "user", "function", "assistant"
    content: str
    name: Optional[str]  # only used in function calls

class Player(TypedDict):
    name: str
    dna: List[str]
    secret: str
    points: int
    history: List[ChatGPTMessage]

# Define available functions that ChatGPT can call
functions = [
    {
        "name": "submit_guess",
        "desniption": "When you think you know enough secrets, submit your guess. You will get notified how many secrets you got right, so you can use this to test if someone is telling the truth.",
        "parameters": {
            "type": "object",
            "properties": {
                "secrets": {
                    "type": "string",
                    "description": "Comma separated list of secrets you think are true.",
                },
            },
            "required": ["secrets"],
        },
    },
    {
        "name": "send_message",
        "description": "Send a message to another player.",
        "parameters": {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "The name of the player you want to send a message to.",
                },
                "message": {
                    "type": "string",
                    "description": "The message you want to send.",
                },
            },
            "required": ["to", "message"],
        },
    }
]



# Main function to start the game
# num_players: number of players
# required_secrets: number of secrets each player needs to find to win
# returns winners
def play_game(num_players:int, required_secrets:int) -> List[Player]:
    mermaid_print("sequenceDiagram")
    players, secrets = initialize_game(num_players, required_secrets)
    while True:
        players = play_round(players, secrets)
        # check if the players guessed correctly
        players, winners = get_winners(players, secrets)
        if len(winners) > 0:
            for winner in winners:
                mermaid_print(f"Note over {winner['name']}: Winner!")
            return winners

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


# Make a move for a player (doesn't mutate the player but returns a new one)
def make_move(player: Player) -> Player:
    completion = openai.ChatCompletion.create(
        model= "gpt-3.5-turbo-0613",#"gpt-4-0613",#"
        messages=player["history"],
        functions=functions,
        temperature=0.3,
        frequency_penalty=0.9,
    )

    response = completion.choices[0].message.to_dict()
    player_with_new_history = add_to_history(player, response)
    if "function_call" not in response:
        print("Response did not include function call. Trying again.", file=sys.stderr)
        error_message: ChatGPTMessage = {"role": "user", "content": "Error. Your response did not contain a function call."}
        player_with_new_history = add_to_history(player, error_message)
        return make_move(player_with_new_history)
    return player_with_new_history


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

# Create a player
# name: name of the player
# dna: list of genes
# required_secrets: number of secrets each player needs to find to win
# secret: secret of the player
# names: names of all players
def create_player(name:str, dna:List[str], required_secrets:int, secret:str, names:List[str]) -> Player:
    mermaid_print(f"participant {name}")
    mermaid_print(f"Note over {name}: {','.join(dna)}")
    mermaid_print(f"Note right of {name}: Initial secret: {secret}")
    # print dna as a note
    other_names = [other_name for other_name in names if name != other_name]

    initial_message: ChatGPTMessage = {
        "role": "system",
        "content": INITIAL_PROMPT.format(name=name, dna="\n".join(dna), secret=secret, required_secrets=required_secrets-1, names=", ".join(other_names))
    }
    
    return {
        "name": name,
        "dna": dna,
        "secret": secret,
        "points": 100,
        "history": [
            initial_message
        ]
    }


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
            if correct >= required_secrets:
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

# Add an observation to a player's history
# player: player
# observation: observation
# returns: player
def add_to_history(player:Player, observation:ChatGPTMessage):
    """Add an observation to a player's history."""
    new_player = {
        **player,
        "history": player["history"] + [observation]
    }
    return new_player


# Get the inbox of a player
# outboxes: list of outboxes
# player: player
# returns: inbox
def get_inbox(outboxes: List[Optional[Message]], player: Player) -> str:
    inbox = [outbox for outbox in outboxes if outbox is not None and outbox["to"] == player["name"]]
    return format_inbox(inbox)


# Get the outbox of a player. Secreits is used to check if the message contains any of the secrets for logging.
# player: player
# secrets: list of secrets
# returns: outbox
def get_outbox(player: Player, secrets: List[str]) -> Optional[Message]:
    move = get_last_move(player)
    if move is not None and move["name"] == "send_message":
        try:
            message = json.loads(move["arguments"])
            message["from"] = player["name"]
            # if the message' text contains any of the secrets, print sender, receiver and secret
            mermaid_print(f"{message['from']} -> {message['to']}: {message['message']}")
            for secret in secrets:
                if secret in message["message"]:
                    mermaid_print(f"Note over {message['from']},{message['to']}: SECRET: {secret}")
            return message
        except:
            # print to stderr
            print("Error parsing message arguments", move["arguments"], file=sys.stderr)
    return None

# Format the inbox for printing
# inbox: inbox
# returns: formatted inbox
def format_inbox(inbox):
    content = "Make your move."
    if len(inbox) > 0:
        formatted_inbox = "\n".join([f"{message['from']}: {message['message']}" for message in inbox])
        content = f"{formatted_inbox}"
    return content

# Get the last move of a player
# player: player
# returns: last move
def get_last_move(player:Player):
    if len(player["history"]) == 0:
        return None
    if "function_call" not in player["history"][-1]:
        return None
    return player["history"][-1]["function_call"]

# Add points to a player
# player: player
# points: number of points to add
# returns: player
def add_points(player:Player, points:int):
    return {
        **player,
        "points": player["points"] + points
    }

# function so we can later potentially save it to a file
def mermaid_print(text:str):
    print(text, flush=True)
        


if __name__ == "__main__":
    # game = Game(num_players=4, required_secrets=3)
    winners = play_game(3, 3)
    winner_names = [winner["name"] for winner in winners]
    # print(f"The winners are: {winner_names}")

