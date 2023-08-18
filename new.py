import json
import random
import os
import asyncio
from interactions import (
    slash_command,
    slash_option,
    OptionType,
    SlashCommandChoice,
    Client,
    Intents,
    SlashContext,
    listen
)
from sampledata import GENES, names, words
import os
from dotenv import load_dotenv
import openai
from collections import defaultdict


load_dotenv()
token = os.getenv("DISCORD_TOKEN")

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
        "description": "When you think you know enough secrets, submit your guess. You will get notified how many secrets you got right, so you can use this to test if someone is telling the truth.",
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
    
    async def move(self, observation):
        self.history.append(observation)
        return await self.get_next_move()
    
    async def get_next_move(self) -> dict:
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
        completion = await openai.ChatCompletion.acreate(
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
            return await self.get_next_move()
        



class DiscordGame():
    @classmethod
    async def create(cls, ctx, num_players, required_secrets):
        self = cls()
        self.ctx = ctx
        self.human = await DiscordPlayer.create(ctx, words[0], required_secrets, names[1:num_players])
        self.players = [self.human]

        human_name = self.players[0].name
        self.required_secrets = required_secrets
        for i in range(1, num_players):
            name = names[i]
            secret = words[i]
            dna = random.choices(GENES, k=5)
            self.players.append(Player(name, secret, dna, required_secrets, [human_name] + names[1:num_players]))
        self.round = 0
        self.last_moves = []
        return self
    
    
    async def play(self, human_move):
        moves = [human_move] + self.last_moves
        moves = await self.play_round(moves)
        self.last_moves = moves
        winners = []
        for move in moves + [human_move]:
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
                    print("looser", looser)

        print("winners", winners)
        await self.human.maybe_send_rest_of_history()
        if len(winners) > 0:
            # TODO send the winner message
            await self.human.send(f"The winners are {', '.join(winners)}!")
            if self.players[0].name in winners:
                await self.human.send(f"Congratulations, you won ${int(100/len(winners))}!")
            return winners

        else:
            return None

    async def play_round(self, moves):
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
                formatted_inbox = "\n\n".join([f"{message['from']}: {message['message']}" for message in inbox[player.name]])
                content = f"You have received the following messages: {formatted_inbox}"
            move = await player.move({
                "role": "user",
                "content": content
            })
            if move is not None:
                next_moves.append(move)

        return next_moves


class DiscordPlayer():
    @classmethod
    async def create(cls, ctx, secret, required_secrets, names):
        self = cls()
        self.name = ctx.author.user.username
        self.secret = secret
        self.required_secrets = required_secrets
        self.names = names
        self.thread = await ctx.channel.create_thread(f'game-{ctx.author.user.username}')
        await self.send(f"Your secret is {secret}.")
        await self.send(f"You are playing with {', '.join(names)}.")
        await self.send(f"You need {required_secrets} correct secrets to win.")
        await self.send("You can send messages to other players using the /send command.")
        await self.send("You can submit your guess using the /submit command. You will get feedback how many secrets you guessed correctly.")
        await self.send("Good luck!")
        self.history = []
        return self
    
    async def send(self, message):
        print(message)
        await self.thread.send(message)
    
    async def maybe_send_rest_of_history(self):
        if len(self.history) > 0:
            await self.send("\n".join([history["content"] for history in self.history]))
            self.history = []
        
    async def move(self, observation):
        await self.send(observation["content"])


bot = Client(intents=Intents.DEFAULT)
bot.games = {}


@slash_command(name="newgame", description="Start a new game of Nuclear Codes")
@slash_option(
    name="num_players",
    description="Number of players in the game",
    required=True,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="num_secrets",
    description="Number of secrets required to win",
    required=True,
    opt_type=OptionType.INTEGER
)
async def newgame(ctx: SlashContext, num_players: int, num_secrets: int):
    await ctx.defer()
    game = await DiscordGame.create(ctx, num_players, num_secrets)
    bot.games[game.human.thread.id] = game


@slash_command(name="submit", description="Submit your guess for the secrets")
@slash_option(
    name="secrets",
    description="Comma separated list of secrets you think are true",
    required=True,
    opt_type=OptionType.STRING
)
async def submit(ctx: SlashContext, secrets: str):
    await ctx.defer()
    game = bot.games.get(ctx.channel_id)
    if game is not None:
        secrets_list = secrets.split(",")
        secrets_list = [secret.strip() for secret in secrets_list]
        secrets_list = [i for sublist in secrets_list for i in sublist.split(" ")]
        secrets_list = ",".join(secrets_list)
        move = {
            "name": "submit_guess",
            "from": ctx.author.user.username,
            "arguments": json.dumps({"secrets": secrets_list})
        }
        print(move)
        await game.play(move)


@slash_command(name="send", description="Send a message to another player in the game")
@slash_option(
    name="name",
    description="Name of the player you want to send a message to",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="message",
    description="The message you want to send",
    required=True,
    opt_type=OptionType.STRING
)
async def send(ctx: SlashContext, name: str, message: str):
    await ctx.defer()
    print(name, message)
    game = bot.games.get(ctx.channel_id)
    if game is not None:
        move = {
            "name": "send_message",
            "from": ctx.author.user.username,
            "arguments": json.dumps({"to": name, "message": message})
        }
        await game.play(move)


@listen()
async def on_ready():
    print("Ready")
    print(f"This bot is owned by {bot.owner}")


token = os.getenv("DISCORD_TOKEN")
bot.start(token)