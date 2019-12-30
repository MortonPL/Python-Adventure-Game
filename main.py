'''
    THIS IS THE MAIN GAME FILE
'''
import os
import sys
import json
import data


class Screen:

    def __init__(self, key):
        self.key = key
        self.strlist = []

    def add(self, string, temporary=False, exclusive=False):
        if not exclusive or (string not in self.strlist and exclusive):
            self.strlist.append((string, temporary))

    def clear_memory(self):
        self.strlist.clear()

    def show(self):
        new_strlist = []
        print(f"Current screen:"
              f"{data.current_screen}\n".upper())
        for line in self.strlist:
            print(line[0])
            if not line[1]:
                new_strlist.append(line)
        self.strlist = new_strlist


class ReaderTXT:

    def __init__(self, path):
        self.sectlist = []
        self.strlist = []
        with open(os.path.join(sys.path[0], path), "r") as file:
            counter = 0
            for line in file:
                line = line.strip('\n')
                if line == "$":
                    self.sectlist.append(self.strlist)
                    self.strlist = []
                else:
                    self.strlist.append(line)
                counter += 1

    def get_section(self, wanted_section):
        for index, section in enumerate(self.sectlist):
            if index == wanted_section:
                return section


class ReaderJSON:
    def __init__(self, path):
        with open(os.path.join(sys.path[0], path), "r") as file:
            self.json_file = json.load(file)


class Game():

    def __init__(self):
        data.platform = sys.platform

    def start(self):
        data.list_of_menus[0].start()

    def create_locations(self, json_section):
        for entry in json_section:
            data.list_of_locations.append(
                Location(self, json_section[entry], entry))

# SCREEN METHODS:

    def screen_get(self, key):
        return data.list_of_screens[key]

    def screen_add(self, key, screen):
        data.list_of_screens[key] = screen

    def screen_change(self, key):
        data.current_screen = key

    def screen_refresh(self):
        self.screen_clear()
        self.screen_get(data.current_screen).show()

    def screen_reset(self, key):
        self.screen_get(key).clear_memory()

    def screen_clear(self):
        if data.platform == "win32":
            os.system("cls")
        elif data.platform == "linux":
            os.system("clear")

# COMMAND PROMPT (CP) METHODS:

    def update_rollback(self, function, *args):
        data.rollback = function
        data.rollback_args = args

    def exit(self, *args):
        if input("\nAre you sure about that? (Type in QUIT to confirm.) ") == \
                "QUIT":
            self.screen_clear()
            exit()
        else:
            print("we're back")
            self.screen_refresh()
            data.rollback(*data.rollback_args)

    def question(self, question=""):
        return input(question)

    def invalid_input(self):
        self.screen_get(data.current_screen).add(
            "\nPlease choose a valid option.", True, True)
        self.screen_refresh()

# MENU FUNCTIONS CALLED BY THE CP

    def menu_new_game(self, *args):
        data.list_of_menus[1].start()

    def menu_load_game(self, *args):
        pass

    def menu_new_scenario(self, scenario, *args):
        data.mapfile = ReaderJSON(scenario)
        data.list_of_calls =\
            data.mapfile.json_file["List of Calls"]
        data.playable_characters =\
            data.mapfile.json_file["Playable Characters"]
        self.create_locations(data.mapfile.json_file["List of Locations"])
        data.list_of_menus[2].start()

    def menu_pick_character(self, *args):
        data.list_of_menus[3].start()

    def pick_character(self, character, *args):
        data.player = Player(data.playable_characters[character])
        self.begin_adventure()

    def begin_adventure(self):
        for location in data.list_of_locations:
            if "is_start" in location.ldata_variables:
                data.player.go_to(location)


class CommandPrompt():

    def __init__(self, game):
        self.game = game

    def question(self, question=""):
        return input(question).lower().split(": ")

    def call_check(self, call):
        try:
            if call in data.list_of_system_calls:
                loaded_call = data.list_of_system_calls[call]
            elif call in data.list_of_calls:
                loaded_call = data.list_of_calls[call]
        except Exception:
            sys.exit(f"Something went wrong, call {call} does not exist.")
        return loaded_call

    def call_user(self, call):
        self.game.update_rollback(self.call_user, call)

        loaded_call = self.call_check(call)
        try:
            answer = self.question(loaded_call["Question"])
        except Exception as ex:
            sys.exit(f"Something went wrong, entry {ex} in call {call} "
                     "does not exist.")
        valid_answer = False
        if answer == ["quit"]:
            valid_answer = True
            self.game.exit()
        elif loaded_call["Any_key"]:
            valid_answer = True
            action = getattr(self.game, loaded_call["any"][0])
            action()
        else:
            for each_option in loaded_call:
                if answer[0] == each_option and answer[0] not in {"Question",
                                                                  "Any_key"}:
                    valid_answer = True
                    action = getattr(self.game, loaded_call[answer[0]][0])
                    action(*loaded_call[answer[0]][1:],
                           *answer[1:])
                    break
        if not valid_answer:
            self.game.invalid_input()
            self.call_user(call)


class Menu():

    def __init__(self, game, cp, call_key):
        self.game = game
        self.cp = cp
        self.call_key = call_key

    def start(self):
        self.game.screen_change("menu")
        self.game.screen_clear()
        self.read_menu()
        self.cp.call_user(self.call_key)

    def read_menu(self):
        self.game.screen_reset("menu")

        if "Text" in self.cp.call_check(self.call_key):
            self.game.screen_get("menu").add(self.cp.call_check(self.call_key)[
                "Text"])
        if self.call_key == "MENU_CHARACTER":
            self.write_characters()
        if self.call_key == "MENU_SCENARIO":
            self.add_scenarios_as_answers(self.read_directory())

        self.game.screen_refresh()

    def write_characters(self):
        for each in data.playable_characters:
            self.game.screen_get("menu").add(data.playable_characters[each][
                    "Menu Description"])
            self.game.screen_get("menu").add("")

    def read_directory(self):
        scenarios = []
        folder = list(filter(
            lambda x: x.endswith(".json") and x.startswith("map_"),
            os.listdir(data.path)))
        for mapfile in folder:
            reader = ReaderJSON(mapfile)
            if "Version" in reader.json_file and reader.json_file["Version"]\
                    == data.version:
                scenarios.append((mapfile, reader.json_file["Name"]))
        for index, entry in enumerate(scenarios):
            self.game.screen_get("menu").add(f"{index+1}. {entry[1]}")
        return scenarios

    def add_scenarios_as_answers(self, scenarios):
        for index, entry in enumerate(scenarios):
            data.list_of_system_calls["MENU_SCENARIO"][f"{index + 1}"] =\
                ["menu_new_scenario", entry[0]]


class Player(Game):

    def __init__(self, player_data):
        self.player_data = player_data

    def go_to(self, location):
        self.player_data["Location"] = location
        location.arrive()


class Location(Game):

    def __init__(self, game, json_section, id):
        self.game = game
        self.id = id
        self.ldata_variables = json_section

    def arrive(self):
        self.game.screen_change("location")
        self.game.screen_reset("menu")
        if "is_new" not in self.ldata_variables:
            self.ldata_variables["is_new"] = True
        if self.ldata_variables["is_new"]:
            self.ldata_variables["is_new"] = False
            self.game.screen_get(data.current_screen).add(
                self.ldata_variables["New Description"])
            # read new description
        elif not self.ldata_variables["is_new"]:
            self.game.screen_get(data.current_screen).add(
                self.ldata_variables["Description"])
            # read description
        self.game.screen_refresh()
        # do shit


if __name__ == "__main__":
    system = ReaderJSON("system.json")

    data.path = sys.path[0]
    data.list_of_system_calls = system.json_file["List of Calls"]

    game = Game()
    command_prompt = CommandPrompt(game)
    menu_main = Menu(game, command_prompt, "MENU_MAIN")
    menu_scenario = Menu(game, command_prompt, "MENU_SCENARIO")
    menu_intro = Menu(game, command_prompt, "MENU_INTRO")
    menu_character = Menu(game, command_prompt, "MENU_CHARACTER")
    data.list_of_menus = [menu_main, menu_scenario, menu_intro, menu_character]
    data.list_of_screens = {"menu": Screen("menu"),
                            "location": Screen("location")}

    game.start()
