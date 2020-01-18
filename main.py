'''
    THIS IS THE MAIN GAME FILE
'''
import os
import sys
import json
import random


system = {
    "List of Calls":
    {
        "MENU_MAIN":
        {
            "Text": "\t\tNONAME GAME\n\n\tThis is the main menu.\n\t1. "
            "Begin a new game.\n\t2. Load a saved game.\n\t3. Exit.",
            "Question": "What do you do? ",
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
            "Question": "Choose the scenario you want to play. ",
            "Any_key": False
        }
    }
}


class GameData:
    def __init__(self):
        # This is the major data object
        self.path = None
        self.platform = None
        self.dict_of_screens = {}
        self.rollback = None
        self.rollback_args = ()
        self.sys_call_types = {}
        self.call_types = {}
        self.location_types = {}
        self.list_of_menus = []
        self.item_types = {}
        self.character_types = {}
        self.dict_of_stats = {}
        self.text_variation = {}
        self.player = {
            "Name": "Anonymus",
            "Stats": {"HP": 100, "FIT": 0, "REF": 0, "DET": 0,
                      "COM": 0, "SOC": 0, "LUC": 0},
            "Max Stats": {"HP": 100, "FIT": 1, "REF": 1, "DET": 1,
                          "COM": 1, "SOC": 1, "LUC": 1},
            "Location": "",
            "Items": {}}
        self.version = "Game_A"


class Screen:

    def __init__(self):
        self.active = False
        self.frozen = False
        self.strlist = []

    def screen_add(self, string, temporary=False,
                   exclusive=False):
        if not exclusive or (string not in self.strlist and exclusive):
            self.strlist.append((string, temporary))

    def screen_get_index(self, string):
        for index, line in enumerate(self.strlist):
            if line == string:
                return index

    def screen_replace(self, string, index):
        self.strlist[index] = string

    def screen_reset(self):
        self.strlist.clear()

    def screen_show(self):
        if self.active:
            new_strlist = []
            print(f"\n||========================================"
                  "=============================="
                  "========================================||\n")
            for line in self.strlist:
                print(line[0])
                if not line[1] or (line[1] and self.frozen):
                    new_strlist.append(line)
            self.strlist = new_strlist

    def screen_clear(self):
        if sys.platform == "win32":
            os.system("cls")
        elif sys.platform == "linux":
            os.system("clear")


class ReaderJSON:
    def __init__(self, path):
        with open(os.path.join(sys.path[0], path), "r") as file:
            self.json_file = json.load(file)


class Game:

    def __init__(self, data_object):
        self.data = data_object
        self.data.platform = sys.platform

# Parsing functions:

    def parse_from_json(self, json):
        self.data.location_types = json["List of Locations"]
        self.data.item_types = json["List of Items"]
        self.data.text_variation = json["Text Variants"]
        self.data.call_types = json["List of Calls"]
        self.data.character_types = json["Playable Characters"]
        self.data.dict_of_stats = json["Player Stats"]

# Screen functions:

    def get_screen(self, key):
        return self.data.dict_of_screens[key]

    def refresh_screens(self):
        self.get_screen("command").screen_clear()
        for screen in self.data.dict_of_screens:
            self.get_screen(screen).screen_show()

    def activate_screen(self, key):
        self.get_screen(key).active = True

    def deactivate_screen(self, key):
        self.get_screen(key).active = False

    def freeze_screen(self, key):
        self.get_screen(key).frozen = True

    def unfreeze_screen(self, key):
        self.get_screen(key).frozen = False

    def update_screens(self):
        self.update_location_screen()
        self.update_player_screen()
        self.refresh_screens()

    def update_location_screen(self):
        self.get_screen("location").screen_reset()
        location = self.clocation()[1]
        if location["is_new"]:
            try:
                self.get_screen("location").screen_add(
                    location["New Description"])
            except KeyError:
                self.get_screen("location").screen_add(
                    "MISSING NEW DESCRIPTION!")
        else:
            try:
                self.get_screen("location").screen_add(location["Description"])
            except KeyError:
                self.get_screen("location").screen_add("MISSING DESCRIPTION!")
        self.get_screen("location").screen_add(
            self.show_items())
        self.get_screen("location").screen_add(
            self.show_paths())

    def update_player_screen(self):
        self.get_screen("player").screen_reset()
        player = self.data.player
        stats_str = "You have "
        i = 0
        for stat, stat_name in self.data.dict_of_stats.items():
            stat_value = player["Stats"][stat]
            stat_max = player["Max Stats"][stat]
            i += 1
            if not i == len(player["Stats"]):
                end = ", "
            else:
                end = ". "
            stats_str = "".join([stats_str, f"{stat_value}/{stat_max} ",
                                 stat_name, end])
        self.get_screen("player").screen_add(stats_str)

# COMMAND PROMPT (CP) methods:

    def cp_update_rollback(self, function, *args):
        self.data.rollback = function
        self.data.rollback_args = args

    def exit(self, *args):
        if input("\nAre you sure about that? (Type in QUIT to confirm.) ") == \
                "QUIT":
            self.get_screen("command").screen_clear()
            exit()
        else:
            self.refresh_screens()
            return self.data.rollback(*self.data.rollback_args)

    def cp_invalid_input(self, call, string="Please choose a valid option."):
        self.get_screen("command").screen_add(string, True, True)
        self.refresh_screens()
        return self.cp_call_user(call)

    def cp_question(self, question=""):
        return input(question).lower().split(": ")

    def cp_call_check(self, call):
        loaded_call = None
        try:
            if call in self.data.sys_call_types:
                loaded_call = self.data.sys_call_types[call]
            elif call in self.data.call_types:
                loaded_call = self.data.call_types[call]
        except Exception:
            sys.exit(f"Something went wrong, call {call} does not exist.")
        return dict(
            (key.lower(), value) for (key, value) in loaded_call.items())

    def cp_call_user(self, call):
        self.cp_update_rollback(self.cp_call_user, call)

        loaded_call = self.cp_call_check(call)
        try:
            answer = self.cp_question(loaded_call["question"])
        except Exception:
            sys.exit(f"Something went wrong, call {call} or its' part"
                     " does not exist.")
        valid_answer = False
        if answer == ["quit"]:
            valid_answer = True
            return self.exit()
        elif loaded_call["any_key"]:
            valid_answer = True
            action = getattr(self, loaded_call["any"][0])
            return action, ()
        else:
            for option in loaded_call:
                if answer[0] == option and answer[0] not in {
                        "question", "any_key"}:
                    valid_answer = True
                    action = getattr(self, loaded_call[answer[0]][0])
                    action_attributes = (*loaded_call[answer[0]][1:],
                                         *answer[1:])
                    return action, action_attributes
        if not valid_answer:
            return self.cp_invalid_input(call, "There is no such command.")

# Starting the program

    def start(self):
        self.activate_screen("command")
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
        self.parse_from_json(ReaderJSON(scenario).json_file)
        Menu(self.data, self, "MENU_INTRO")
        return self.cp_call_user("MENU_INTRO")

    def menu_pick_character(self, *args):
        Menu(self.data, self, "MENU_CHARACTER")
        return self.cp_call_user("MENU_CHARACTER")

    def pick_character(self, character, *args):
        for entry in self.data.character_types[character]:
            self.data.player[entry] = self.data.character_types[
                character][entry]
        return self.begin_adventure()

    def begin_adventure(self):
        self.get_screen("menu").screen_reset()
        self.activate_screen("location")
        self.activate_screen("player")
        self.deactivate_screen("menu")
        for location_id, location in self.data.location_types.items():
            if "is_start" in location:
                return self.appear(location_id, "LD_START")

# Generic methods called by the CP

    def search_location(self, *args):
        try:
            # spend some time
            if self.clocation()[1]["Search Level"] < 3:
                self.clocation()[1]["Search Level"] += 1
                if len(self.clocation()[1]["Search Rewards"][
                        str(self.clocation()[1]["Search Level"])]) > 0:
                    self.get_screen("command").screen_add(
                        self.random_text("Search_2"), True)
                    self.give_search_rewards(self.clocation()[1][
                        "Search Rewards"][
                            str(self.clocation()[1]["Search Level"])])
                else:
                    self.get_screen("command").screen_add(
                        self.random_text("Search_1"), True)
            else:
                self.get_screen("command").screen_add(
                    self.random_text("Search_3"),
                    True)
            self.update_screens()
            return self.cp_call_user("GENERIC")
        except KeyError as ex:
            if ex.args[0] in {'1', '2', '3'}:
                return self.cp_invalid_input(
                    "GENERIC", f"MISSING SEARCH REWARDS "
                    f"FOR LEVEL {ex.args[0]}!")
            else:
                return self.cp_invalid_input(
                    "GENERIC", "MISSING SEARCH LEVEL!")

    def go_to(self, *args):
        found_it = False
        for location_id, location in self.data.location_types.items():
            if location["Name"].lower() == args[0]:
                if location_id == self.clocation()[0]:
                    return self.cp_invalid_input(
                        "GENERIC", "You are already there.")
                elif not self.check_path(location_id):
                    return self.cp_invalid_input(
                        "GENERIC", "You cannot go there from here.")
                else:
                    previous_location_id = self.clocation()[0]
                    self.data.player["Location"] = location_id
                    return self.arrive(location_id, previous_location_id)
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", "This place does not exist.")

    def take_item(self, *args):
        found_it = False
        if args[0] == "all":
            if len(self.clocation()[1]["List of Items"]) == 0:
                return self.cp_invalid_input(
                    "GENERIC", "There is nothing to take.")
            found_it = True
            for item_id in self.clocation()[1]["List of Items"]:
                self.take_it(item_id)
            self.clocation()[1]["List of Items"] = []
            self.get_screen("command").screen_add(
                "You took every item you found.", True)
            self.update_screens()
        else:
            for item_id in self.data.item_types:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if item_id not in self.clocation()[1]["List of Items"]:
                        return self.cp_invalid_input(
                            "GENERIC", "There is nothing like that here.")
                    else:
                        found_it = True
                        self.take_it(item_id)
                        self.clocation()[1]["List of Items"].remove(item_id)
                        self.get_screen("command").screen_add(
                            f"You took {self.get_item(item_id)['Name']}.",
                            True)
                        self.update_screens()
                        break
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", "There is no such item.")
        return self.cp_call_user("GENERIC")

    def drop_item(self, *args):
        found_it = False
        if args[0] == "all":
            if sum(self.data.player["Items"].values()) == 0:
                return self.cp_invalid_input(
                    "GENERIC", "You don't have anything to drop.")
            else:
                found_it = True
                for item_id, item_count in self.data.player["Items"].items():
                    for item in range(item_count):
                        self.drop_it(item_id)
                self.get_screen("command").screen_add(
                    "You dropped every item you had.", True)
                self.clean_backpack()
                self.update_screens()
        else:
            for item_id in self.data.item_types:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if item_id not in self.data.player["Items"] \
                            or self.data.player["Items"][item_id] == 0:
                        return self.cp_invalid_input(
                            "GENERIC", "You don't have this item.")
                    else:
                        found_it = True
                        self.drop_it(item_id)
                        self.get_screen("command").screen_add(
                            f"You dropped {self.get_item(item_id)['Name']}.",
                            True, True)
                        self.clean_backpack()
                        self.update_screens()
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", "There is no such item.")
        return self.cp_call_user("GENERIC")

    def use_item(self, *args):
        found_it = False
        if args[0] == "all":
            if sum(self.data.player["Items"].values()) == 0:
                return self.cp_invalid_input(
                    "GENERIC", "You don't have anything to use.")
            else:
                found_it = True
                for item_id, item_count in self.data.player["Items"].items():
                    for item in range(item_count):
                        self.use_it(item_id)
                self.get_screen("command").screen_add(
                    "You used every item you could.", True)
                self.clean_backpack()
                self.update_screens()
        else:
            for item_id in self.data.player["Items"]:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if item_id not in self.data.player["Items"] \
                            or self.data.player["Items"][item_id] == 0:
                        return self.cp_invalid_input(
                            "GENERIC", "You don't have this item.")
                    else:
                        found_it = True
                        self.use_it(item_id)
                        self.get_screen("command").screen_add(
                            f"You used {self.get_item(item_id)['Name']}. "
                            f"{self.get_item(item_id)['Action Description']}",
                            True)
                        self.clean_backpack()
                        self.update_screens()
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", "There is no such item.")
        return self.cp_call_user("GENERIC")

    def open_inv(self):
        self.get_screen("command").screen_add(
            self.show_backpack(), True, True)
        self.refresh_screens()
        return self.cp_call_user("GENERIC")

    def examine(self, *args):
        return self.cp_call_user("GENERIC")

# Functions for locations:

    def clocation(self):
        return (self.data.player["Location"],
                self.data.location_types[self.data.player["Location"]])

    def get_location(self, location_id):
        return self.data.location_types[location_id]

    def check_path(self, location_id):
        for path in self.clocation()[1]["List of Paths"]:
            if path == location_id:
                return True
        return False

    def appear(self, location_id, previous_location_id):
        self.data.player["Location"] = location_id
        return self.arrive(location_id, previous_location_id)

    def arrive(self, location_id, previous_location_id):
        location = self.get_location(location_id)
        previous_location = self.get_location(previous_location_id)

        if "is_new" not in location:
            location["is_new"] = True
        self.update_screens()
        if previous_location["is_new"]:
            previous_location["is_new"] = False
        # do shit
        return self.cp_call_user("GENERIC")

    def show_items(self):
        item_str = ""
        try:
            if len(self.clocation()[1]["List of Items"]) == 0:
                item_str = "There is nothing of value."
            elif len(self.clocation()[1]["List of Items"]) == 1:
                item = self.get_item(self.clocation()[1]['List of Items'][0])
                item_str = f"There is {item['Article']} {item['Name']}."
            else:
                i = 0
                item_str = "There are "
                for item in self.clocation()[1]["List of Items"]:
                    i += 1
                    if not i == len(self.clocation()[1]["List of Items"]):
                        end = ", "
                    else:
                        end = ". "
                    item_str = "".join(
                        [item_str, f"{self.get_item(item)['Name']}{end}"])
        except KeyError:
            item_str = "MISSING ITEMS ENTRY!"
        finally:
            return item_str

    def show_paths(self):
        path_str = ""
        try:
            if len(self.clocation()[1]["List of Paths"]) == 0:
                path_str = "You are helplessly stuck here!"
            else:
                i = 0
                path_str = "There are paths to "
                for location in self.clocation()[1]["List of Paths"]:
                    i += 1
                    if not i == len(self.clocation()[1]["List of Paths"]):
                        end = ", "
                    else:
                        end = "."
                    path_str = "".join(
                        [path_str,
                         f"{self.get_location(location)['Name']}{end}"])
        except KeyError:
            path_str = "MISSING PATHS ENTRY!"
        finally:
            return path_str

    def give_search_rewards(self, reward_list):
        for reward in reward_list:
            if reward in self.data.location_types:
                self.clocation()[1]["List of Paths"].append(reward)
                self.get_screen("command").screen_add(
                    f"You find a path to "
                    f"{self.get_location(reward)['Name']}!", True)
            elif reward in self.data.item_types:
                self.clocation()[1]["List of Items"].append(reward)
                self.get_screen("command").screen_add(
                    f"You find {self.get_item(reward)['Article']} "
                    f"{self.get_item(reward)['Name']}!", True)
        # add events later

# Functions for items:

    def show_backpack(self):
        if len(self.data.player["Items"]) == 0:
            return "You have nothing with you."
        item_str = "You have "
        i = 0
        for item, amount in self.data.player["Items"].items():
            i += 1
            if not i == len(self.data.player["Items"]):
                end = ", "
            else:
                end = "."
            item_str = "".join([
                item_str, f"{self.get_item(item)['Name']} ({amount}){end}"])
        return item_str

    def clean_backpack(self):
        new_dict = {}
        for item_id, item_count in self.data.player["Items"].items():
            if item_count != 0:
                new_dict[item_id] = item_count
        self.data.player["Items"] = new_dict

    def get_item(self, item_id):
        return self.data.item_types[item_id]

    def use_it(self, item_id):
        item = self.get_item(item_id)
        if self.check_item_prereq(item_id):
            if item["Type"] == "Consumable":
                self.data.player["Items"][item_id] -= 1
                if item["Action"][0] == "StatUp":
                    self.data.player["Stats"][item["Action"][1]]\
                        += item["Action"][2]

    def check_item_prereq(self, item_id):
        item = self.get_item(item_id)
        result = True
        for min_value, value, max_value in zip(
                item["Prerequisite"],
                self.data.player["Stats"].values(),
                self.data.player["Max Stats"].values()):
            if value >= min_value and value < max_value and result:
                result = value >= min_value and value < max_value
            else:
                return False
        return True

    def take_it(self, item_id):
        if item_id not in self.data.player["Items"]:
            self.data.player["Items"][item_id] = 0
        self.data.player["Items"][item_id] += 1

    def drop_it(self, item_id):
        self.data.player["Items"][item_id] -= 1
        self.clocation()[1]["List of Items"].append(item_id)

# Functions for examination:

# Text randomness:

    def random_text(self, key):
        return random.choice(self.data.text_variation[key])


class Menu:

    def __init__(self, data_object, game, call_key):
        self.data = data_object
        self.game = game
        self.call_key = call_key
        self.start()

    def start(self):
        self.game.activate_screen("menu")
        self.game.get_screen("menu").screen_clear()
        self.read_menu()

    def read_menu(self):
        self.game.get_screen("menu").screen_reset()

        if "text" in self.game.cp_call_check(self.call_key):
            self.game.get_screen("menu").screen_add(self.game.cp_call_check(
                self.call_key)["text"])
        if self.call_key == "MENU_CHARACTER":
            self.write_characters()
        if self.call_key == "MENU_SCENARIO":
            self.add_scenarios_as_answers(self.read_directory())

        self.game.refresh_screens()

    def write_characters(self):
        for each in self.data.character_types:
            self.game.get_screen("menu").screen_add(
                self.data.character_types[each]["Menu Description"])

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
            self.data.sys_call_types["MENU_SCENARIO"][f"{index + 1}"] =\
                ["menu_new_scenario", entry[0]]


if __name__ == "__main__":
    game_data = GameData()
    game_data.sys_call_types = system["List of Calls"]

    game_data.path = sys.path[0]

    game = Game(game_data)
    game_data.dict_of_screens = {"player": Screen(),
                                 "menu": Screen(),
                                 "location": Screen(),
                                 "command": Screen(),
                                 }

    function = game.start()
    while True:
        function = (game.keep_going(function))
