'''
    THIS IS THE MAIN GAME FILE
'''
import os
import sys
import json


system = {
    "List of Calls":
    {
        "MENU_MAIN":
        {
            "Text": "\t\tNONAME GAME\n\n\tThis is the main menu.\n\t1. "
            "Begin a new game.\n\t2. Load a saved game.\n\t3. Exit.",
            "Question": "\nWhat do you do? ",
            "Any_key": False,
            "1": ["menu_new_game"],
            "Begin a new game": ["menu_new_game"],
            "2": ["menu_load_game"],
            "Load a saved game": ["menu_load_game"],
            "3": ["exit"],
            "Exit": ["exit"]
        },
        "MENU_SCENARIO":
        {
            "Question": "\n Choose the scenario you want to play. ",
            "Any_key": False
        }
    }
}


class GameData:
    def __init__(self):
        # This is the major data object
        self.path = None
        self.platform = None
        self.list_of_screens = {}
        self.current_screen = None
        self.rollback = None
        self.rollback_args = ()
        self.list_of_system_calls = {}
        self.list_of_calls = {}
        self.list_of_locations = {}
        self.list_of_menus = []
        self.list_of_items = {}
        self.playable_characters = {}
        self.player = {
            "Name": "Anonymus",
            "Strength": 100,
            "Stamina": 100,
            "Skills": {"FIT": 0, "REF": 0, "DET": 0,
                       "COM": 0, "SOC": 0, "LUC": 0},
            "Location": None,
            "Items": {}}
        self.version = "Game_A"


class Screen:

    def __init__(self, data_object, key):
        self.data = data_object
        self.key = key
        self.strlist = []

    def screen_add(self, string, temporary=False, exclusive=False):
        if not exclusive or (string not in self.strlist and exclusive):
            self.strlist.append((string, temporary))

    def quick_screen_add(self, string, temporary=False, exclusive=False):
        self.screen_add(string, temporary, exclusive)
        self.screen_show

    def screen_reset(self):
        self.strlist.clear()

    def screen_show(self):
        new_strlist = []
        print(f"Current screen: "
              f"{self.data.current_screen}".upper())
        print("====================\n")
        for line in self.strlist:
            print(line[0])
            if not line[1]:
                new_strlist.append(line)
        self.strlist = new_strlist

    def screen_clear(self):
        if self.data.platform == "win32":
            os.system("cls")
        elif self.data.platform == "linux":
            os.system("clear")

    def screen_refresh(self):
        self.screen_clear()
        self.screen_show()


class ReaderJSON:
    def __init__(self, path):
        with open(os.path.join(sys.path[0], path), "r") as file:
            self.json_file = json.load(file)


class Game:

    def __init__(self, data_object):
        self.data = data_object
        self.data.platform = sys.platform

# Parsing functions:

    def create_locations(self, json_section):
        for entry in json_section:
            self.data.list_of_locations[entry] = json_section[entry]

    def create_items(self, json_section):
        for entry in json_section:
            self.data.list_of_items[entry] = json_section[entry]

# Screen functions:

    def get_screen(self, key):
        return self.data.list_of_screens[key]

    def change_screen(self, key):
        self.data.current_screen = key

    def cscreen(self):
        return self.data.list_of_screens[self.data.current_screen]

# COMMAND PROMPT (CP) methods:

    def cp_update_rollback(self, function, *args):
        self.data.rollback = function
        self.data.rollback_args = args

    def exit(self, *args):
        if input("\nAre you sure about that? (Type in QUIT to confirm.) ") == \
                "QUIT":
            self.cscreen().screen_clear()
            exit()
        else:
            self.cscreen().screen_refresh()
            return self.data.rollback(*self.data.rollback_args)

    def cp_invalid_input(self, call, string="\nPlease choose a valid option."):
        self.cscreen().screen_add(string, True, True)
        self.cscreen().screen_refresh()
        return self.cp_call_user(call)

    def cp_question(self, question=""):
        return input(question).split(": ")

    def cp_call_check(self, call):
        loaded_call = None
        try:
            if call in self.data.list_of_system_calls:
                loaded_call = self.data.list_of_system_calls[call]
            elif call in self.data.list_of_calls:
                loaded_call = self.data.list_of_calls[call]
        except Exception:
            sys.exit(f"Something went wrong, call {call} does not exist.")
        return loaded_call

    def cp_call_user(self, call):
        self.cp_update_rollback(self.cp_call_user, call)

        loaded_call = self.cp_call_check(call)
        try:
            answer = self.cp_question(loaded_call["Question"])
        except Exception as ex:
            sys.exit(f"Something went wrong, entry {ex} in call {call} "
                     "does not exist.")
        valid_answer = False
        if answer == ["quit"]:
            valid_answer = True
            return self.exit()
        elif loaded_call["Any_key"]:
            valid_answer = True
            action = getattr(self, loaded_call["any"][0])
            return action, ()
        else:
            for each_option in loaded_call:
                if answer[0] == each_option and answer[0] not in {"Question",
                                                                  "Any_key"}:
                    valid_answer = True
                    action = getattr(self, loaded_call[answer[0]][0])
                    action_attributes = (*loaded_call[answer[0]][1:],
                                         *answer[1:])
                    return action, action_attributes
        if not valid_answer:
            return self.cp_invalid_input(call)

# Starting the program

    def start(self):
        Menu(self.data, self, "MENU_MAIN")
        return self.cp_call_user("MENU_MAIN")

    def keep_going(self, func_tuple):
        func, func_attribs = func_tuple
        return func(*func_attribs)

# Menu methods called by the CP

    def menu_new_game(self, *args):
        Menu(self.data, self, "MENU_SCENARIO")
        return self.cp_call_user("MENU_SCENARIO")

    def menu_load_game(self, *args):
        # load a saved game
        pass

    def menu_new_scenario(self, scenario, *args):
        self.data.mapfile = ReaderJSON(scenario)
        self.data.list_of_calls =\
            self.data.mapfile.json_file["List of Calls"]
        self.data.playable_characters =\
            self.data.mapfile.json_file["Playable Characters"]
        self.create_locations(self.data.mapfile.json_file["List of Locations"])
        self.create_items(self.data.mapfile.json_file["List of Items"])
        Menu(self.data, self, "MENU_INTRO")
        return self.cp_call_user("MENU_INTRO")

    def menu_pick_character(self, *args):
        Menu(self.data, self, "MENU_CHARACTER")
        return self.cp_call_user("MENU_CHARACTER")

    def pick_character(self, character, *args):
        for entry in self.data.playable_characters[character]:
            self.data.player[entry] = self.data.playable_characters[
                character][entry]
        return self.begin_adventure()

    def begin_adventure(self):
        self.cscreen().screen_reset()
        for location_id, location in self.data.list_of_locations.items():
            if "is_start" in location:
                return self.appear((location_id, location))

# Generic methods called by the CP

    def search_location(self, *args):
        # spend some time
        if self.data.player["Location"][1]["Search Level"] < 3:
            self.data.player["Location"][1]["Search Level"] += 1
            self.cscreen().screen_add(
                f"\nYou have searched. New search level:"
                f"{self.data.player['Location'][1]['Search Level']}",
                True)
        else:
            self.cscreen().screen_add(
                f"\nYou have already searched the place and find nothing new.",
                True)
        self.cscreen().screen_refresh()
        return self.cp_call_user("GENERIC")

    def go_to(self, *args):
        found_it = False
        for location_id, location in self.data.list_of_locations.items():
            if location["Name"] == args[0]:
                if location_id == self.clocation()[0]:
                    return self.cp_invalid_input(
                        "GENERIC", "\nYou are already there.")
                elif location_id not in self.data.list_of_locations:
                    return self.cp_invalid_input(
                        "GENERIC", "\nThis place does not exist.")
                elif self.check_path((location_id, location)):
                    self.data.player["Location"] = (location_id, location)
                    return self.arrive((location_id, location))
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", "\nThere is no such place.")

    def take_item(self, *args):
        found_it = False
        for item_id, item in self.data.list_of_items.items():
            if item["Name"] == args[0]:
                if item_id not in self.clocation()[1]["List of Items"]:
                    return self.cp_invalid_input(
                        "GENERIC", "\nThis item does not exist.")
                else:
                    return self.take_it(item_id, args[0])
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", "\nThere is no such item.")

# Functions called by go_to:

    def clocation(self):
        return (self.data.player["Location"],
                self.data.list_of_locations[self.data.player["Location"]])

    def check_path(self, location_tuple):
        location_id, location = location_tuple
        for path in self.clocation()[1]["List of Paths"]:
            if path[0] == location_id and path[1] <= self.clocation()[
                    1]["Search Level"]:
                return True
        return False

    def appear(self, location_tuple):
        self.data.player["Location"] = location_tuple[0]
        return self.arrive(self.clocation())

    def arrive(self, location_tuple):
        location_id, location = location_tuple
        self.change_screen("location")
        self.cscreen().screen_reset()
        if "is_new" not in location:
            location["is_new"] = True
        if location["is_new"]:
            location["is_new"] = False
            self.cscreen().screen_add(location["New Description"])
        elif not location["is_new"]:
            self.cscreen().screen_add(location["Description"])
            # read description
        self.cscreen().screen_refresh()
        # do shit
        return self.cp_call_user("GENERIC")

# Functions called by take:

    def take_it(self, item_id, item_name):
        self.data.list_of_locations[self.clocation()[0]][
            "List of Items"].remove(item_id)
        if item_id not in self.data.player["Items"]:
            self.data.player["Items"][item_id] = 0
        self.data.player["Items"][item_id] += 1
        self.cscreen().screen_add(f"\nYou picked up {item_name}", True, True)
        self.cscreen().screen_refresh()
        return self.cp_call_user("GENERIC")


class Player:
    pass


class Menu:

    def __init__(self, data_object, game, call_key):
        self.data = data_object
        self.game = game
        self.call_key = call_key
        self.start()

    def start(self):
        self.game.change_screen("menu")
        self.game.cscreen().screen_clear()
        self.read_menu()

    def read_menu(self):
        self.game.cscreen().screen_reset()

        if "Text" in self.game.cp_call_check(self.call_key):
            self.game.get_screen("menu").screen_add(self.game.cp_call_check(
                self.call_key)["Text"])
        if self.call_key == "MENU_CHARACTER":
            self.write_characters()
        if self.call_key == "MENU_SCENARIO":
            self.add_scenarios_as_answers(self.read_directory())

        self.game.cscreen().screen_refresh()

    def write_characters(self):
        for each in self.data.playable_characters:
            self.game.get_screen("menu").screen_add(
                self.data.playable_characters[each]["Menu Description"])

    def read_directory(self):
        scenarios = []
        folder = list(filter(
            lambda x: x.endswith(".json") and x.startswith("map_"),
            os.listdir(self.data.path)))
        for mapfile in folder:
            reader = ReaderJSON(mapfile)
            if "Version" in reader.json_file and reader.json_file["Version"]\
                    == self.data.version:
                scenarios.append((mapfile, reader.json_file["Name"]))
        for index, entry in enumerate(scenarios):
            self.game.get_screen("menu").screen_add(f"{index+1}. {entry[1]}")
        return scenarios

    def add_scenarios_as_answers(self, scenarios):
        for index, entry in enumerate(scenarios):
            self.data.list_of_system_calls["MENU_SCENARIO"][f"{index + 1}"] =\
                ["menu_new_scenario", entry[0]]


if __name__ == "__main__":
    game_data = GameData()
    game_data.list_of_system_calls = system["List of Calls"]

    game_data.path = sys.path[0]

    game = Game(game_data)
    game_data.list_of_screens = {"menu": Screen(game_data, "menu"),
                                 "location": Screen(game_data, "location")}

    function = game.start()
    while True:
        function = (game.keep_going(function))
