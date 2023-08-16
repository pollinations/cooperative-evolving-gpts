import random
from collections import defaultdict
import json
import openai


names = [
    "Sophia",
    "Jackson",
    "Olivia",
    "Liam",
    "Emma",
    "Noah",
    "Ava",
    "Ethan",
    "Isabella",
    "Mason",
    "Mia",
    "Logan",
    "Amelia",
    "James",
    "Harper",
    "Benjamin",
    "Aria",
    "Lucas",
    "Ella",
    "Alexander"
]


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


words = [
    "apple",
    "banana",
    "cherry",
    "date",
    "elephant",
    "frog",
    "giraffe",
    "honey",
    "ice",
    "jackal",
    "kite",
    "lemon",
    "mongoose",
    "noodle",
    "orange",
    "penguin",
    "quartz",
    "rabbit",
    "snake",
    "tiger",
    "umbrella",
    "violin",
    "whale",
    "xylophone",
    "yak",
    "zebra",
    "ant",
    "bee",
    "cat",
    "dog",
    "emu",
    "fish",
    "goat",
    "horse",
    "iguana",
    "jaguar",
    "kangaroo",
    "llama",
    "monkey",
    "newt",
    "ostrich",
    "parrot",
    "quokka",
    "raccoon",
    "seal",
    "turtle",
    "urchin",
    "vulture",
    "walrus",
    "xerus",
    "yabby",
    "zebu",
    "azure",
    "blaze",
    "crimson",
    "dew",
    "ember",
    "flame",
    "glow",
    "harbor",
    "illuminate",
    "jade",
    "kaleidoscope",
    "lunar",
    "mist",
    "nebula",
    "ocean",
    "prism",
    "quasar",
    "radiance",
    "solar",
    "twilight",
    "ultraviolet",
    "vivid",
    "wavelength",
    "xenon",
    "yellow",
    "zenith",
    "arc",
    "bridge",
    "canyon",
    "delta",
    "eclipse",
    "fjord",
    "gorge",
    "horizon",
    "island",
    "jetty",
    "knoll",
    "lagoon",
    "mesa",
    "nexus",
    "oasis",
    "plateau",
    "quarry",
    "reef",
    "strait",
    "tundra",
    "upland",
    "valley",
    "wadi",
    "xeric",
    "yardang",
    "zephyr",
    "atom",
    "bond",
    "compound",
    "diode",
    "electron",
    "fusion",
    "genome",
    "hydrogen",
    "ion",
    "joule",
    "kelvin",
    "laser",
    "molecule",
    "neutron",
    "oscillator",
    "photon",
    "quantum",
    "resistor",
    "semiconductor",
    "transistor",
    "ultrasound",
    "voltage",
    "watt",
    "xenon",
    "yield",
    "zeolite",
    "allegro",
    "ballad",
    "cantata",
    "duet",
    "ensemble",
    "fugue",
    "glee",
    "harmony",
    "interlude",
    "jazz",
    "kismet",
    "lyric",
    "melody",
    "note",
    "overture",
    "pitch",
    "quintet",
    "rhapsody",
    "sonata",
    "tempo",
    "unison",
    "vibrato",
    "waltz",
    "xanadu",
    "yodel",
    "zither"
]


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


GENES = [
    "You are a good liar.",
    "You are a bad liar.",
    "You try to cooperate with other players.",
    "You don't trust other players.",
    "You only bluff when you need only one more secret.",
    "You are highly persuasive.",
    "You tend to reveal your secret early.",
    "You are secretive and reserved.",
    "You are aggressive in your approach.",
    "You tend to form alliances.",
    "You are a lone wolf.",
    "You easily fall for bluffs.",
    "You are excellent at detecting lies.",
    "You frequently change alliances.",
    "You tend to double-cross your allies.",
    "You act unpredictably.",
    "You communicate sparingly.",
    "You communicate excessively.",
    "You are prone to taking risks.",
    "You are cautious and play it safe.",
    "You tend to copy other players' strategies.",
    "You are focused on sabotaging others.",
    "You tend to panic under pressure.",
    "You are cool and composed under pressure.",
    "You act friendly but are deceptive.",
    "You are honest until the critical moment.",
    "You are consistently truthful.",
    "You are strategic and methodical.",
    "You tend to act on impulse.",
    "You are excellent at keeping secrets.",
    "You leak secrets when under pressure.",
    "You frequently make bold moves.",
    "You prefer a subtle and understated approach.",
    "You actively seek out partnerships.",
    "You are highly competitive.",
    "You are willing to share secrets for mutual benefit.",
    "You never share your secret, no matter what.",
    "You use intimidation tactics.",
    "You play the mediator among conflicting players.",
    "You often make empty threats.",
    "You are willing to sacrifice your chance to win to hinder a specific player.",
    "You often seek revenge.",
    "You are forgiving and give second chances.",
    "You use psychological tactics to gain advantage.",
    "You are a master of deception.",
    "You tend to trust easily.",
    "You often mislead others about your secret.",
    "You are adaptive and change strategies often.",
    "You often pretend to know less than you do.",
    "You tend to overthink and second guess yourself.",
    "You are assertive and make your intentions clear.",
    "You prefer to stay in the background and observe.",
    "You are often overly optimistic.",
    "You tend to be pessimistic and expect betrayal.",
    "You use humor to diffuse tense situations.",
    "You are relentless and never give up.",
    "You tend to concede when the odds are against you.",
    "You are skilled at planting misinformation.",
    "You take a logical and analytical approach.",
    "You are driven by intuition and gut feelings.",
    "You are charming and use charisma to your advantage.",
    "You are focused on self-preservation over winning.",
    "You regularly change your secret passcode.",
    "You make decisions based on emotions.",
    "You use confusion and chaos to your advantage.",
    "You seek to make alliances, but betray them at the end.",
    "You avoid confrontation at all costs.",
    "You revel in confrontation and conflict.",
    "You often underestimate your opponents.",
    "You tend to overestimate your opponents.",
    "You adapt your tactics based on your opponents’ personalities.",
    "You are rigid and stick to one strategy.",
    "You are prone to making rash decisions when time is running out.",
    "You tend to hoard information.",
    "You freely share information, true or false.",
    "You play to create the most entertaining outcome.",
    "You aim to win at all costs.",
    "You tend to form and lead coalitions.",
    "You prefer to be a follower in a group.",
    "You play erratically to throw off opponents.",
    "You are meticulous and organized.",
    "You often use reverse psychology.",
    "You tend to believe in the good of other players.",
    "You believe everyone is as deceptive as you are.",
    "You often sympathize with other players.",
    "You are indifferent to other players’ situations.",
    "You use flattery and compliments as a tactic.",
    "You tend to procrastinate and delay decisions.",
    "You are decisive and make quick judgments.",
    "You enjoy sowing discord among other players.",
    "You aim to form a lasting alliance with one other player.",
    "You rarely communicate, but observe keenly.",
    "You take pleasure in bluffing successfully.",
    "You feel guilty when lying to other players.",
    "You often second guess your own strategies.",
    "You tend to stick to your first instinct.",
    "You are known to make surprising and unconventional moves.",
    "You prefer consistency and predictability.",
    "You actively seek out the weakest player and exploit their position.",
    "You avoid drawing attention to yourself.",
    "You are vocal and seek to control the narrative.",
    "You play with a strict moral code.",
    "You view the game as a ruthless competition with no rules.",
    "You tend to stay loyal to your initial alliances.",
    "You are skeptical of all players, including your allies.",
    "You are focused on long-term strategies over short-term gains.",
    "You thrive in the chaos of the game.",
    "You are pragmatic and switch strategies as needed.",
    "You are sentimental and may make decisions based on personal feelings towards players.",
    "You are objective and unemotional in your decisions.",
    "You use logic and reason to persuade others.",
    "You prefer to win without lying.",
    "You are willing to lie constantly.",
    "You tend to form grudges and act upon them.",
    "You are usually a peacemaker among players.",
    "You see the game as a fun experience, not a competition.",
    "You play strictly to win, not for enjoyment.",
    "You tend to remain neutral in conflicts until forced to act.",
    "You seek to resolve conflicts between other players to your advantage.",
    "You consider all players as potential threats.",
    "You are able to quickly gain the trust of other players."
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
                "content": INITIAL_PROMPT.format(name=name, dna="\n".join(dna), secret=secret, required_secrets=required_secrets, names=", ".join(names))
            }
        ]
    
    def move(self, observation):
        self.history.append(observation)
        return self.get_next_move()
    
    def get_next_move(self):
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

    


class Game():
    def __init__(self, num_players, required_secrets):
        self.players = []
        self.required_secrets = required_secrets
        for i in range(num_players):
            name = names[i]
            secret = words[i]
            dna = random.choices(GENES, k=5)
            self.players.append(Player(name, secret, dna, required_secrets, names[:num_players]))
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
                formatted_inbox = "\n\n".join([f"{message['from']}: {message['message']}" for message in inbox[player.name]])
                content = f"You have received the following messages: {formatted_inbox}"
            move = player.move({
                "role": "user",
                "content": content
            })
            next_moves.append(move)

        return next_moves

        

            
if __name__ == "__main__":
    game = Game(3, 3)
    winners = game.play()
    print(f"The winners are: {winners}")