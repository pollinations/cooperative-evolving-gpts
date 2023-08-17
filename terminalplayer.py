


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
