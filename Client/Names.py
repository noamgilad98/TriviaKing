#create class for getting player names
# player name combined from first name, last name, random id

import random
import uuid

class Names:
    def __init__(self):
        self.PLAYER_FIRST_NAMES = ['Avi', 'Bar', 'Chen', 'Dana', 'Eli', 'Fadi', 'Gadi', 'Hadar', 'Ido', 'Jonathan', 'Kobi', 'Lior', 'Miri', 'Nir', 'Oren', 'Pini', 'Roni', 'Shai', 'Tal', 'Uri', 'Vlad', 'Yael', 'Ziv']
        self.PLAYER_SECONDARY_NAMES = ['Avraham', 'Ben-David', 'Cohen', 'Dahan', 'Eliyahu', 'Friedman', 'Golan', 'Haim', 'Ivri', 'Katz', 'Levi', 'Mizrahi', 'Nahari', 'Ovadia', 'Peretz', 'Rosenberg', 'Shalom', 'Tal', 'Uziel', 'Vaknin', 'Weiss', 'Xavier', 'Yosef', 'Zohar']
        #create players list to store player names and make sure they are unique
        self.players = []
        
    #get random name for player and make sure it is unique
    def get_random_name(self):
        base_name = random.choice(self.PLAYER_FIRST_NAMES)
        secondary_name = random.choice(self.PLAYER_SECONDARY_NAMES)
        unique_id = str(uuid.uuid4())[:8]
        player_name = f"{base_name} {secondary_name} {unique_id}"
        #check if player name is unique
        while player_name in self.players:
            base_name = random.choice(self.PLAYER_FIRST_NAMES)
            secondary_name = random.choice(self.PLAYER_SECONDARY_NAMES)
            unique_id = str(uuid.uuid4())[:8]
            player_name = f"{base_name} {secondary_name} {unique_id}"
        self.players.append(player_name)
        return player_name
    