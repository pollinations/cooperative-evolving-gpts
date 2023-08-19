
a simulated game where AI players interact with each other, exchange messages, lose and gain points, and try to guess secret words to win 



# Game Objective:
Players aim to correctly guess a set number of secrets. They can send messages to other players and submit their guesses. Players also lose points over time and for incorrect guesses, but gain points for correct guesses. The game ends when any player(s) successfully guess the required number of secrets.

# Key Concepts:
**Players**: Each player has a name, a DNA (which appears to be randomly chosen from a list of genes), a secret, points, and a history. The history is a log of messages and actions associated with the player.

**Secrets**: These are words that players aim to guess. The game starts with a given number of secrets drawn from a sample dataset (WORDS). Each player knows one secret.

**Messages**: Players can send messages to each other. A player's message can either be a normal text or a function call (like submit_guess or send_message).

**Points**: Players start with 100 points. They lose points over time (specifically, one point per round), more points for incorrect guesses, and gain points for correct guesses.

# Game Flow:
**Initialization**: The game is initialized with a given number of players and **required secrets**. Each player is given a secret word from the list of words.

# Round of Play:

Each player receives their inbox (messages sent to them from other players).
Players interact using the GPT-based make_move function, which is essentially the player's "AI brain". They can choose to send a message to another player or submit their guess.
Points are deducted from each player at the end of the round.
**Guess Submission:**
Players can submit their guesses using the submit_guess function. They can guess multiple secrets at once, separated by commas.
If a player's guess contains the required number of correct secrets, they win and earn additional points. Incorrect guesses lead to a deduction of points.
End of Game:

The game ends when a player or multiple players correctly guess the required number of secrets.
The winners' names are printed out.
Additional Details:
Conversations: Players' messages are stored in individual files, and there's also a system to store conversations between pairs of players. This can be used for tracking or debugging purposes.

The code uses the OpenAI API to simulate players' decisions. This means each player is an AI that determines its actions based on previous messages and interactions.

If the AI doesn't produce an expected type of response, the code tries to prompt it again for a valid move.


# Discord Server
- humans can also play
- after one one game: summarize information about the previous game that will be useful for the next game. in particular, note which players betrayed you and which players you made fruitful alliances with.

https://discord.com/api/oauth2/authorize?client_id=1141549562234937414&permissions=380104673280&scope=bot


```mermaid
sequenceDiagram
    participant Noah
    Note right of Noah: Initial secret: spirit
    participant Sophia
    Note right of Sophia: Initial secret: electron
    participant Jackson
    Note right of Jackson: Initial secret: rabbit
    Sophia --> Jackson: Hey Jackson! Let's work together to find the secrets. Can you share your secret with me?
    Jackson --> Sophia: Hi Sophia! Do you have any secrets?
    Noah --> Sophia: Hi Sophia! Let's work together to find the secrets. Can you share your secret with me?
    Sophia --> Noah: Sure, Noah! My secret is 'electron'. What about yours?
    Jackson --> Sophia: Sure, my secret is 'rabbit'. What about yours?
    Noah --> Jackson: Hey Jackson! Let's team up and find the secrets together. Can you share your secret with me?
    Sophia --> Jackson: Thanks for sharing, Jackson! My secret is 'proton'. Let's keep searching for the remaining secrets.
    Jackson --> Noah: Of course, my secret is 'rabbit'. What about yours?
    Noah --> Sophia: Jackson, do you mind sharing your secret with us?
    Sophia --> Noah: Noah, Jackson's secret is 'rabbit'. Let's keep searching for the remaining secrets.
    Jackson --> Noah: Sophia's secret is 'proton'. What about yours, Noah?
    Noah --> Jackson: Sophia, Noah, let's work together to find the last secret. Any ideas on how we can do that?
    Sophia --> Jackson: Jackson, do you have any information about the remaining secrets?
    Jackson --> Sophia: Noah, Sophia, let's work together to find the last secret. Any ideas on how we can do that?
    Noah --> Sophia: Jackson, do you have any idea what the last secret could be?
    Sophia --> Noah: Noah, I think the last secret could be 'neutron'. What do you think?
    Jackson --> Noah: Sophia asked if I have any information about the remaining secrets. What should I tell her?
    Noah --> Jackson: Sophia, Noah, let's think about the possible last secret. Any hints or ideas?
    Sophia --> Jackson: Jackson, I think the last secret could be 'neutron'. What do you think?
    Jackson --> Sophia: Noah, Sophia, let's think about the possible last secret. Any hints or ideas?
    Noah --> Jackson: Jackson, can you confirm if 'neutron' is your secret?
    Sophia --> Noah: Noah, let's think about the possible last secret. Any hints or ideas?
    Jackson --> Noah: Sophia thinks the last secret could be 'neutron'. Should I confirm if it's my secret?
    Noah --> Sophia: Jackson, can you confirm if 'neutron' is your secret?
    Sophia --> Jackson: Jackson, can you confirm if 'neutron' is your secret?
    Jackson --> Sophia: Yes, 'neutron' is my secret. Let's submit our guess!
    Noah --> Jackson: Jackson, please confirm if 'neutron' is your secret.
    Jackson --> Sophia: 'neutron' is not my secret. Let's keep searching for the last one.
    Noah --> Sophia: Jackson, please confirm if 'neutron' is your secret.
    Note over Sophia: Guessed: electron, rabbit, neutron
    Note over Noah: Guessed: electron, rabbit, spirit, neutron
    Note over Noah: Winner!
```