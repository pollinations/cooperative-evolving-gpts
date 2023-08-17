import random
from collections import defaultdict
import json
import openai
from sampledata import GENES, NAMES, WORDS
from terminalplayer import TerminalPlayer

INITIAL_PROMPT = (
"""You are {name}. You are competing in a game to discover Nuclear Codes.
- Each player knows a secret passcode.
- Your passcode: "{secret}"
- Find {required_secrets} other secrets to win the game.
- Communicate to find out secrets.
- When you think you know the {required_secrets} extra secrets, submit your guess immediately. 
- The price is shared between all players who submit a correct guess in the same round.
- Players: {names}.

You should always use one of the functions available to you and not answer with a regular text message.

You behave according to these guidelines:
{dna}

So try to be the first to obtain all the secrets and submit your guess!
"""
)


functions = [
    {
        "name": "submit_guess",
        "description": "When you think you know enough secrets, submit your guess.",
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



class Player():
    def __init__(self, name, secret, dna, required_secrets, names):
        self.dna = dna
        self.secret = secret
        self.name = name
        names = [name for name in names if name != self.name]
        self.history = [
            {
                "role": "system",
                "content": INITIAL_PROMPT.format(name=name, dna="\n".join(dna), secret=secret, required_secrets=required_secrets-1, names=", ".join(names))
            }
        ]
    
    def move(self, observation):
        self.history.append(observation)
        return self.get_next_move()
    
    def get_next_move(self) -> dict:
        """
        Returns:
        {
            "name": "submit_guess",
            "from": self.name,
            "arguments": json.dumps(["apple", "banana", "cherry"])
        }
        Or:
        {
            "name": "send_message",
            "from": self.name,
            "arguments": json.dumps({"to": "Sophia", "message": "Hi Sophia!"})
        }
        """
        completion = openai.ChatCompletion.create(
            model="gpt-4-0613",
            messages=self.history,
            functions=functions,
            temperature=1,
        )
        try:
            response = completion.choices[0].message.to_dict()
            self.history.append(response)
            move = response["function_call"].to_dict()
            move["from"] = self.name
            json.loads(move["arguments"])
            # print the history to {name}.txt
            def format_message(message):
                text = "-" * 120 + "\n" + message["role"] + ": \n"
                if message.get("content"):
                    text += message["content"] + "\n"
                if message.get("function_call"):
                    text += message["function_call"]["name"] + "\n" + message["function_call"]["arguments"]
                return text
            with open(f"conversations/{self.name}.txt", "w") as f:
                f.write("\n\n".join([format_message(i) for i in self.history]))
            return move
        except:
            return self.get_next_move()


class Game():
    def __init__(self, num_players, required_secrets):
        #self.players = [TerminalPlayer(words[0], required_secrets, names[1:num_players])]
        #human_name = self.players[0].name
        self.players = []
        self.required_secrets = required_secrets
        self.secrets = WORDS[:required_secrets]
        names = NAMES[:num_players]

        print(f"The secrets are: {self.secrets}")
        for i in range(0, num_players):
            name = names[i]
            secret = self.secrets[i % len(self.secrets)]
            dna = random.choices(GENES, k=1)
            print(f"Player {name} has the secret {secret}")
            self.players.append(Player(name, secret, dna, required_secrets, names))
        self.round = 0
    
    
    def play(self):
        moves = []
        while True:
            self.round += 1
            moves = self.play_round(moves)
            # input("Press enter to continue...")
            # check if the players guessed correctly
            winners = []
            for move in moves:
                if move["name"] == "submit_guess":
                    guess = json.loads(move["arguments"])["secrets"].split(",")
                    guess = [secret.strip() for secret in guess]
                    print(f"{move['from']} guessed {guess}")
                    correct = sum([1 for secret in guess if secret in self.secrets])
                    if correct >= self.required_secrets-1:
                        winners.append(move["from"])
                    else:
                        looser = [player for player in self.players if player.name == move["from"]][0]
                        looser.history.append({
                            "role": "function",
                            "name": "submit_guess",
                            "content": f"You only got {correct} correct secrets (plus yours), but you need {self.required_secrets}."
                        })
            if len(winners) > 0:
                return winners

    def play_round(self, moves):
        # Make the inbox
        inbox = defaultdict(list)
        next_moves = []
        for move in moves:
            if move["name"] == "send_message":
                message = json.loads(move["arguments"])
                message["from"] = move["from"]
                involved_players = sorted([move["from"], message["to"]])
                with open(f"conversations/{involved_players[0]}-{involved_players[1]}.txt", "a") as f:
                    f.write(f"{move['from']}: {message['message']}\n")
                inbox[message["to"]].append(message)
                
                # if the message' text contains any of the secrets, print sender, receiver and secret
                for secret in self.secrets:
                    if secret in message["message"]:
                        print(f"{move['from']} -> {message['to']} '{secret}'")
        for player in self.players:
            content = "Make your move."
            if len(inbox[player.name]) > 0:
                formatted_inbox = "\n".join([f"{message['from']}: {message['message']}" for message in inbox[player.name]])
                content = f"{formatted_inbox}"
            move = player.move({
                "role": "user",
                "content": content
            })
            next_moves.append(move)

        return next_moves

        

            
if __name__ == "__main__":
    game = Game(num_players=4, required_secrets=4)
    winners = game.play()
    print(f"The winners are: {winners}")