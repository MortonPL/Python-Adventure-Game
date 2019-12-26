'''
    THIS IS THE MAIN GAME FILE
'''
import os
import sys
import json


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
        for line in self.strlist:
            print(line[0])
            if not line[1]:
                new_strlist.append(line)
        self.strlist = new_strlist


class GameData:

    def __init__(self):
        self.path = None
        self.screens = None
        self.current_screen = None
        self.rollback = None
        self.rollback_args = None
        self.list_of_system_calls = None
        self.list_of_calls = None
        self.menu_list = None
        self.playable_characters = None
        self.player = None


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


class Game(GameData):

    def __init__(self, data_object):
        self.data = data_object

    def start(self):
        self.data.menu_list[0].start()

# SCREEN METHODS

    def screen_get(self, key):
        return self.data.screens[key]

    def screen_add(self, key, screen):
        self.data.screens[key] = screen

    def screen_change(self, key):
        self.data.current_screen = key

    def screen_refresh(self):
        self.screen_clear()
        self.screen_get(self.data.current_screen).show()

    def screen_reset(self, key):
        self.screen_get(key).clear_memory()

    def screen_clear(self):
        os.system("cls")

# COMMAND PROMPT (CP) METHODS:

    def update_rollback(self, function, *args):
        self.data.rollback = function
        self.data.rollback_args = args

    def exit(self):
        if input("\nAre you sure about that? (Type in QUIT to confirm.) ") == \
                "QUIT":
            self.screen_clear()
            exit()
        else:
            print("we're back")
            self.screen_refresh()
            self.data.rollback(*self.data.rollback_args)

    def question(self, question=""):
        return input(question)

    def invalid_input(self):
        self.screen_get(self.data.current_screen).add(
            "\nPlease choose a valid option.", True, True)
        self.screen_refresh()

# MENU FUNCTIONS CALLED BY THE CP

    def menu_new_game(self, *args):
        self.data.menu_list[1].start()

    def menu_load_game(self, *args):
        pass

    def menu_new_scenario(self, scenario, *args):
        self.data.mapfile = ReaderJSON(scenario)
        self.data.list_of_calls = self.data.mapfile.json_file["List of Calls"]
        self.data.playable_characters = self.data.mapfile.json_file[
            "Playable Characters"]
        self.data.menu_list[2].start()

    def menu_pick_character(self, *args):
        self.data.menu_list[3].start()

    def pick_character(self, character, *args):
        self.data.player = self.data.playable_characters[character]


class CommandPrompt(Game):

    def __init__(self, data_object):
        Game.__init__(self, data_object)
        self.data = data_object

    def question(self, question=""):
        return input(question).split(": ")

    def call_user(self, call):
        self.update_rollback(self.call_user, call)

        if call in self.data.list_of_system_calls:
            loaded_call = self.data.list_of_system_calls[call]
        elif call in self.data.list_of_calls:
            loaded_call = self.data.list_of_calls[call]
        else:
            pass
        answer = self.question(
            loaded_call["question"])
        valid_answer = False
        if answer == ["QUIT"]:
            valid_answer = True
            super().exit()
        elif loaded_call["any_key"]:
            valid_answer = True
            action = getattr(self, loaded_call["any"][0])
            action()
        else:
            for each_option in loaded_call:
                if answer[0] == each_option and answer[0] not in {"question",
                                                                  "any_key"}:
                    valid_answer = True
                    action = getattr(self, loaded_call[answer[0]][0])
                    action(*loaded_call[answer[0]][1:],
                           *answer[1:])
                    break
        if not valid_answer:
            self.invalid_input()
            self.call_user(call)


class Menu(CommandPrompt):

    def __init__(self, data_object, menufile_path, file_section, call_key):
        CommandPrompt.__init__(self, data_object)
        self.data = data_object
        self.menufile = ReaderTXT(menufile_path)
        self.file_section = file_section
        self.call_key = call_key

    def start(self):
        super().screen_change("menu")
        super().screen_clear()
        self.read_menu()
        super().call_user(self.call_key)

    def read_menu(self):
        super().screen_reset("menu")
        if self.file_section != 0:
            for line in self.menufile.get_section(self.file_section):
                super().screen_get("menu").add(line)
        if self.call_key == "MENU_CHARACTER":
            self.write_characters()
        if self.call_key == "MENU_SCENARIO":
            self.add_scenarios_as_answers(self.read_directory())
        super().screen_refresh()

    def write_characters(self):
        for each in self.data.playable_characters:
            super().screen_get("menu").add(
                self.data.playable_characters[each]["Menu Description"])
            super().screen_get("menu").add("")

    def read_directory(self):
        scenarios = []
        folder = list(filter(
            lambda x: x.endswith(".json") and x.startswith("map_"),
            os.listdir(self.data.path)))
        for mapfile in folder:
            reader = ReaderJSON(mapfile)
            # Change check to something else
            if "Name" in reader.json_file:
                scenarios.append((mapfile, reader.json_file["Name"]))
        for index, entry in enumerate(scenarios):
            super().screen_get("menu").add(f"{index+1}. {entry[1]}")
        return scenarios

    def add_scenarios_as_answers(self, scenarios):
        for index, entry in enumerate(scenarios):
            self.data.list_of_system_calls["MENU_SCENARIO"][f"{index+1}"] =\
                ["menu_new_scenario", entry[0]]


class Location():
    pass


if __name__ == "__main__":
    system = ReaderJSON("system.json")
    game_data = GameData()
    game_data.path = sys.path[0]
    game_data.list_of_system_calls = system.json_file["List of Calls"]
    menu_main = Menu(game_data, "mainmenu.txt", 1, "MENU_MAIN")
    menu_scenario = Menu(game_data, "mainmenu.txt", 2, "MENU_SCENARIO")
    menu_intro = Menu(game_data, "mainmenu.txt", 3, "MENU_INTRO")
    menu_character = Menu(game_data, "mainmenu.txt", 4, "MENU_CHARACTER")
    game_data.menu_list = [menu_main, menu_scenario, menu_intro,
                           menu_character]
    game_data.screens = {"menu": Screen("menu")}
    command_prompt = CommandPrompt(game_data)
    game = Game(game_data)
    game.start()
