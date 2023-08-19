import random
from collections import defaultdict
import json
import openai
from sampledata import GENES, NAMES, WORDS, INITIAL_PROMPT
from terminalplayer import TerminalPlayer
import sys

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

def create_player(name, dna, required_secrets,secret, names):
    mermaid_print(f"participant {name}")
    mermaid_print(f"Note right of {name}: Initial secret: {secret}")
    other_names = [other_name for other_name in names if name != other_name]
    return {
        "name": name,
        "dna": dna,
        "secret": secret,
        "points": 100,
        "history": [
            {
                "role": "system",
                "content": INITIAL_PROMPT.format(name=name, dna="\n".join(dna), secret=secret, required_secrets=required_secrets-1, names=", ".join(other_names))
            }
        ]
    }


def add_to_history(player, observation):
    new_player = {
        **player,
        "history": player["history"] + [observation]
    }
    log_move(new_player)
    return new_player


def initialize_game(num_players, required_secrets):
    secrets = WORDS[:required_secrets]
    names = NAMES[:num_players]
    players = []
    for i in range(num_players):
        name = names[i]
        secret = secrets[i % len(secrets)]
        dna = random.choices(GENES, k=1)
        players.append(create_player(name, dna, required_secrets, secret, names))
    return players, secrets


def play_round(players, secrets):
    # breakpoint()

    outboxes = [get_outbox(player, secrets) for player in players]

    modified_players = []
    for player in players:
        inbox = get_inbox(outboxes, player)
        secret_and_inbox = "Your secret: " + player["secret"] + "\nYour points: "+str(player["points"]) + "\n" + inbox
        chat_message = {
            "role": "user",
            "content": secret_and_inbox
        }
        player_with_new_history = add_to_history(player, chat_message)
        new_player = make_move(player_with_new_history)
        new_player = add_points(new_player, -1)
        modified_players.append(new_player)
    # breakpoint()
    return modified_players

def get_inbox(outboxes, player):
    inbox = [outbox for outbox in outboxes if outbox is not None and outbox["to"] == player["name"]]
    return format_inbox(inbox)


def get_outbox(player, secrets):
    move = get_last_move(player)
    if move is not None and move["name"] == "send_message":
        try:
            message = json.loads(move["arguments"])
            message["from"] = player["name"]
            involved_players = sorted([message["from"], message["to"]])
            with open(f"conversations/{involved_players[0]}-{involved_players[1]}.txt", "a") as f:
                if not "message" in message:
                    breakpoint()
                f.write(f"{message['from']}: {message['message']}\n")
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


def format_inbox(inbox):
    content = "Make your move."
    if len(inbox) > 0:
        formatted_inbox = "\n".join([f"{message['from']}: {message['message']}" for message in inbox])
        content = f"{formatted_inbox}"
    return content



def make_move(player):
    completion = openai.ChatCompletion.create(
        model= "gpt-4-0613",#"gpt-3.5-turbo-0613",#
        messages=player["history"],
        functions=functions,
        temperature=0.3,
        frequency_penalty=0.9,
    )

    response = completion.choices[0].message.to_dict()
    player_with_new_history = add_to_history(player, response)
    if "function_call" not in response:
        print("Response did not include function call. Trying again.", file=sys.stderr)
        player_with_new_history = add_to_history(player, {"role": "user", "content": "Error. Your response did not contain a function call."})
        return make_move(player_with_new_history)
    return player_with_new_history

def log_move(player):
    # print the history to {name}.txt
    with open(f"conversations/{player['name']}.txt", "w") as f:
        f.write("\n\n".join([format_message(i) for i in player["history"]]))


def format_message(message):
    text = "-" * 120 + "\n" + message["role"] + ": \n"
    if message.get("content"):
        text += message["content"] + "\n"
    if message.get("function_call"):
        text += message["function_call"]["name"] + "\n" + message["function_call"]["arguments"]
    return text


def play_game(num_players, required_secrets):
    mermaid_print("sequenceDiagram")
    players, secrets = initialize_game(num_players, required_secrets)
    while True:
        players = play_round(players, secrets)
        # check if the players guessed correctly
        players, winners = get_winners(required_secrets, players, secrets)
        if len(winners) > 0:
            for winner in winners:
                mermaid_print(f"Note over {winner['name']}: Winner!")
            return winners

def get_winners(required_secrets, players, secrets):
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


def get_last_move(player):
    if len(player["history"]) == 0:
        return None
    if "function_call" not in player["history"][-1]:
        return None
    return player["history"][-1]["function_call"]
        
def add_points(player, points):
    return {
        **player,
        "points": player["points"] + points
    }

# function so we can later potentially save it to a file
def mermaid_print(text):
    print(text, flush=True)
        


if __name__ == "__main__":
    # game = Game(num_players=4, required_secrets=3)
    winners = play_game(3, 3)
    winner_names = [winner["name"] for winner in winners]
    # print(f"The winners are: {winner_names}")

