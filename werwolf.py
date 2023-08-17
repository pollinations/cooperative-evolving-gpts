import random
from collections import defaultdict
import json
import openai
from sampledata import GENES, names, words

INITIAL_PROMPT = (
"""You are {name}. You are competing in a game of Nuclear Codes. The game works as follows:
- You know one secret passcode: "{secret}"
- You need to find {required_secrets} other secrets to win the game.
- You can send messages to other players and try to convince them to share their secret. You can also lie to them.
- The names of the other players are: {names}
- When you think you know the required number of secrets, you submit your guess.
- The price of $100 is shared between all players who submit a correct guess in the same round.

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
            model="gpt-3.5-turbo-0613",
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
            with open(f"{self.name}.txt", "w") as f:
                f.write("\n\n".join([format_message(i) for i in self.history]))
            return move
        except:
            return self.get_next_move()


class TerminalPlayer():
    def __init__(self, secret, required_secrets, names):
        print("Welcome to Nuclear Codes!")
        self.name = input("What is your name?\n")
        print(f"You know the secret: {secret}")
        print(f"You need to find {required_secrets -1} other secrets to win the game.")
        print(f"The names of the other players are: {', '.join(names)}")
        self.history = []
        self.secret = secret

    def move(self, observation):
        print("-" * 120)
        # First print the history: that might have an answer of like 'You guessed wrong'
        if len(self.history) > 0:
            print(self.history[0])
            # Then delete the history so that next round we dont print the same thing again
            self.history = []
        print(observation["content"])
        action = "guess" if input("Your move: \n[g]uess\n[s]end message\n") == "g" else "send_message"
        if action == "guess": 
            secrets = input("What are your secrets? (comma separated)\n")
            return {
                "name": "submit_guess",
                "from": self.name,
                "arguments": json.dumps({"secrets": secrets})
            }
        else:
            to = input("Who do you want to send a message to?\n")
            message = input("What is your message?\n")
            return {
                "name": "send_message",
                "from": self.name,
                "arguments": json.dumps({"to": to, "message": message})
            }


class Game():
    def __init__(self, num_players, required_secrets):
        #self.players = [TerminalPlayer(words[0], required_secrets, names[1:num_players])]
        #human_name = self.players[0].name
        self.players = []
        self.required_secrets = required_secrets
        for i in range(0, num_players):
            name = names[i]
            secret = words[i]
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
                    correct = sum([1 for secret in guess if secret in [player.secret for player in self.players]])
                    if correct >= self.required_secrets:
                        winners.append(move["from"])
                    else:
                        looser = [player for player in self.players if player.name == move["from"]][0]
                        looser.history.append({
                            "role": "function",
                            "name": "submit_guess",
                            "content": f"You only got {correct} correct secrets, but you need {self.required_secrets}."
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
                with open(f"{involved_players[0]}-{involved_players[1]}.txt", "a") as f:
                    f.write(f"{move['from']}: {message['message']}\n")
                inbox[message["to"]].append(message)
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
    game = Game(num_players=3, required_secrets=2)
    winners = game.play()
    print(f"The winners are: {winners}")