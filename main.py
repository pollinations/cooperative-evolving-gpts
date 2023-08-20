import random
from collections import defaultdict
from typing import List, Dict
from pydantic import Field
from utils import mermaid_print
from models import Player, Message, ChatGPTMessage
from game_logic import initialize_game, play_round, get_winners


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



if __name__ == "__main__":
    # game = Game(num_players=4, required_secrets=3)
    winners = play_game(3, 3)
    winner_names = [winner["name"] for winner in winners]
    # print(f"The winners are: {winner_names}")

