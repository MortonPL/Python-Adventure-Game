'''
    THIS IS THE MAIN GAME FILE
    LATEST UPDATE: 23/01/20
    LATEST VERSION: GAME_C
'''
import os
import sys
import json
import random
# import subprocess


class GameData:
    """Contains data needed by the game, has no methods of its own. In order
    to have other classes use it, pass the instance as argument during the
    initialization."""
    def __init__(self):
        self.path = sys.path[0]
        self.platform = None
        self.dict_of_screens = {"player": Screen(),
                                "menu": Screen(),
                                "location": Screen(),
                                "command": Screen()}
        self.rollback = None
        self.rollback_args = ()
        self.sys_call_types = {
            "MENU_LOAD":
            {
                "Text": "Available save files:\n\n",
                "Question": "Choose the save file you want to load. ",
                "Any_key": False},
            "MENU_SCENARIO":
            {
                "Question": "Choose the scenario you want to play. ",
                "Any_key": False}}
        self.call_types = {}
        self.location_types = {}
        self.list_of_menus = []
        self.item_types = {}
        self.character_types = {}
        self.dict_of_stats = {}
        self.text_variation = {}
        self.player = {
            "Name": "Anonymus",
            "Stats": {"HP": 100, "FIT": 0, "SRV": 0,
                      "COM": 0, "SOC": 0, "LUC": 0},
            "Max Stats": {"HP": 100, "FIT": 1, "SRV": 1,
                          "COM": 1, "SOC": 1, "LUC": 1},
            "Location": "",
            "Items": {}}
        self.version = "Game_C"
        self.mapfile = None
        self.time = 0
        self.time_limit = 0
        self.max_search = 0
        self.fail = False
        self.already_failed = False


class Screen:
    """Class representing an independent screen - part of the console window.

    Variables:

    ``active`` (bool): If False, stops screen from showing its content.

    ``frozen`` (bool): If True, stops screen from removing temporary strings.
    Otherwise, temporary strings are removed from screen after being shown in
    console."""

    def __init__(self):
        self.active = False
        self.frozen = False
        self.strlist = []

    def screen_add(self, string: str, temporary=False,
                   exclusive=False):
        """Adds (but not shows!) given ``string`` to screen's ``strlist``.

        If ``temporary`` is True, add the ``string`` as temporary.

        If ``exclusive`` is True, ``string`` is not added when it already
        exists."""
        if not exclusive or (string not in self.strlist and exclusive):
            self.strlist.append((string, temporary))

    def screen_reset(self):
        """Empties screen ``strlist``."""
        self.strlist.clear()

    def screen_show(self):
        """If screen is active, prints a dividing line and every string in
        own ``strlist`` in the console window and removes the temporary
        strings.

        If screen is frozen, temporary strings are not removed."""
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
        """Clears the console window."""
        if sys.platform == "win32":
            os.system("cls")
        elif sys.platform == "linux":
            os.system("clear")


class ReaderJSON:
    """A simple JSON wrapper that loads JSON file content to ``json_file``
    and sets ``json_load_ok`` if JSON file is correct."""
    def __init__(self, path):
        with open(os.path.join(sys.path[0], path), "r") as file:
            try:
                self.json_file = json.load(file)
                self.json_load_ok = True
            except Exception:
                self.json_load_ok = False


class Game:
    """This class contains almost all game functions: the command interpreter,
    menu state handler, screen handler, all gameplay options, saving/loading.

    Variables:

    ``data_object`` (GameData): Game "memory" object."""

    def __init__(self, data_object: GameData):
        self.data = data_object

# Parsing functions:

    def parse_from_json(self, json: ReaderJSON, overlap: str):
        """Loads relevant data from given JSON file into ``GameData instance``

        Set ``overlap`` to True if you're loading a save file."""
        self.data.location_types = json["List of Locations"]
        if not overlap:
            self.data.item_types = json["List of Items"]
            self.data.text_variation = json["Text Variants"]
            self.data.call_types = json["List of Calls"]
            self.data.character_types = json["Playable Characters"]
            self.data.dict_of_stats = json["Player Stats"]
            self.data.mapfile = json["Name"]
            self.data.time_limit = json["Time Limit"]
            self.data.max_search = json["Maximum Search Level"]
        else:
            self.data.player = json["Player"]
            self.data.time = json["Time"]

    def dump_to_json(self):
        """Returns a ``dict`` containing all the data that's being put in a save file.
        """
        save_data = {
            "Version": self.data.version,
            "Name": self.data.mapfile,
            "List of Locations": self.data.location_types,
            "Player": self.data.player,
            "Time": self.data.time
        }
        return save_data

# Screen functions:

    def get_screen(self, key: str):
        """Returns a ``Screen`` object with corresponding ``key``."""
        return self.data.dict_of_screens[key]

    def refresh_screens(self):
        """Clears the console window and shows content of every ``Screen``
        object."""
        self.get_screen("command").screen_clear()
        for screen in self.data.dict_of_screens:
            self.get_screen(screen).screen_show()

    def activate_screen(self, key: str):
        """Sets the ``Screen`` object with the corresponding ``key`` to active
        state."""
        self.get_screen(key).active = True

    def deactivate_screen(self, key: str):
        """Sets the ``Screen`` object with the corresponding ``key`` to inactive
        state."""
        self.get_screen(key).active = False

    def freeze_screen(self, key: str):
        """Sets the ``Screen`` object with the corresponding ``key`` to unfrozen
        state."""
        self.get_screen(key).frozen = True

    def unfreeze_screen(self, key: str):
        """Sets the ``Screen`` object with the corresponding ``key`` to frozen
        state."""
        self.get_screen(key).frozen = False

    def update_screens(self):
        """Updates the "player" and "location" ``Screen`` objects in order to contain
        most recent data and refreshes the console."""
        self.update_location_screen()
        self.update_player_screen()
        self.refresh_screens()

    def update_location_screen(self):
        """Updates "location" ``Screen`` informations about location
        description, items, paths to other locations and current events."""
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
        if "is_win" in location and location["is_win"]:
            return None
        self.get_screen("location").screen_add(
            self.show_items())
        self.get_screen("location").screen_add(
            self.show_paths())
        if "List of Events" in location.keys():
            try:
                self.get_screen("location").screen_add(
                    f"{location['Event Description']}\n")
            except KeyError:
                self.get_screen("location").screen_add(
                    "MISSING EVENT DESCRIPTION!")
            finally:
                self.get_screen("location").screen_add(
                    self.show_events())
        if "Dangerous Event" in location and location["Dangerous Event"]:
            self.get_screen("location").screen_add(self.random_text("Danger"))

    def update_player_screen(self):
        """Updates "player" ``Screen`` informations about current time,
        statistics and carried items."""
        self.get_screen("player").screen_reset()
        timer_str = f"You have {self.data.time_limit - self.data.time}"
        timer_str_2 = " turns left."
        self.get_screen("player").screen_add(self.show_stats())
        self.get_screen("player").screen_add(self.show_player_items())
        self.get_screen("player").screen_add(timer_str+timer_str_2)

# Command Interpreter (CI) methods:

    def ci_update_rollback(self, function, *args):
        """Sets the function to roll back to if player doesn't confirm
        quitting or cancels saving."""
        self.data.rollback = function
        self.data.rollback_args = args

    def exit(self, *args):
        """Asks player for confirmation. If the response is 'QUIT', close the
        game. Else returns rollback function with its arguments to the main
        loop."""
        confirm = input(
            "\nAre you sure about that? (Type in QUIT to confirm) ")
        if confirm.lower() == "quit":
            self.get_screen("command").screen_clear()
            exit()
        else:
            self.refresh_screens()
            return self.data.rollback(*self.data.rollback_args)

    def save(self, *args):
        """Asks player for save file name. If the name is vaild and user
        doesn't cancel, dumps selected data to a new save file. If the name is
        invalid, asks for another name. If user cancels, returns rollback
        function with its arguments to the main loop."""
        confirm = input("\nType in the name of your save state."
                        "(Type in CANCEL to cancel) ")
        if confirm.lower() == "cancel":
            self.refresh_screens()
            return self.data.rollback(*self.data.rollback_args)
        else:
            try:
                with open(f"save_{confirm}.json", "w") as file:
                    json.dump(self.dump_to_json(), file, indent=4)
                self.get_screen("command").screen_add("Saved successfully.")
                self.refresh_screens()
                return self.data.rollback(*self.data.rollback_args)
            except Exception:
                print("Unacceptable name. Please enter another name.")
                self.save()

    def check_health(self):
        """Sets the fail flag to True if player's HP is below or equal to 0 and informs
        player about it."""
        if self.data.player["Stats"]["HP"] <= 0:
            self.get_screen("command").screen_add(
                "You have died and thus failed the mission. GAME OVER", True)
            self.refresh_screens()
            self.data.fail = True

    def timer_tick(self, reverse=False):
        """Decreases the time counter. If counter is 0, sets the fail flag
        to True and informs player about it."""
        if reverse:
            self.data.time -= 1
        elif self.data.time < self.data.time_limit:
            self.data.time += 1
        else:
            self.get_screen("command").screen_add(
                "You have run out of time and "
                "thus failed the mission. GAME OVER", True)
            self.data.fail = True

    def ci_invalid_input(self, call: str,
                         string="Please choose a valid option.",
                         testing=False):
        """Informs player that given input is invalid and repeats the
        ``call``."""
        if not testing:
            self.get_screen("command").screen_add(string, True, True)
            self.refresh_screens()
            return self.ci_call_user(call)
        else:
            return False

    def ci_question(self, question=""):
        """Asks for player input while showing ``question``. Returns a tuple
        of answers separated by ': '."""
        return input(question).lower().split(": ")

    def ci_call_check(self, call: str):
        """Checks if the given ``call`` call key is in dictionary of hardcoded calls
        or loaded mapfile calls. If it's true, returns lower-case content of
        the call. If it's false, informs the player and stops the game."""
        loaded_call = None
        try:
            if call in self.data.sys_call_types:
                loaded_call = self.data.sys_call_types[call]
            elif call in self.data.call_types:
                loaded_call = self.data.call_types[call]
            else:
                raise Exception
            return dict(
                (key.lower(), value) for (key, value) in loaded_call.items())
        except Exception:
            input(f"Call {call} seems to be corrupted. Press enter to quit.")
            sys.exit()

    def ci_call_user(self, call=None, loaded_call=None, answer=None,
                     testing=False):
        """This is the main function that interprets player input.
        First, it checks if the failure condition is met and ends the game if
        it's true. Then it looks up for a call to execute with the ``call``
        key and asks for player input. If player's answer is defined in the
        call dictionary, returns the corresponding function with its arguments
        to the main loop. Otherwise informs the player and asks for input
        again.

        ``loaded_call``, not-None ``answer`` and ``testing`` are used in unit
        tests. ``loaded_call`` overrides the loading of the call from data
        based on the ``call`` key. ``answer`` overrides the player input.
        ``testing`` forces the function to return Game.ci_invalid_input itself
        instead of calling it - this is used in result assertion."""
        self.check_health()
        if self.data.fail and not self.data.already_failed:
            input()
            return self.menu_end_game("FAILURE")

        if loaded_call is None:
            loaded_call = self.ci_call_check(call)
        try:
            if answer is None:
                answer = self.ci_question(loaded_call["question"])
            else:
                answer = answer.lower().split(": ")
        except Exception:
            return self.data.rollback(*self.data.rollback_args)
        valid_answer = False
        self.ci_update_rollback(self.ci_call_user, call)
        if answer == ["quit"]:
            if call in {"MENU_SCENARIO", "MENU_VICTORY", "MENU_LOST"}:
                exit()
            else:
                valid_answer = True
                return self.exit()
        elif answer == ["save"]:
            if call not in {"MENU_SCENARIO", "MENU_MAIN", "MENU_INTRO",
                            "MENU_CHARACTER", "ENDING"}:
                valid_answer = True
                return self.save()
            else:
                return self.ci_invalid_input(
                    call, "You cannot save here.\n")
        elif loaded_call["any_key"]:
            valid_answer = True
            action = getattr(self, loaded_call["any"][0])
            action_attributes = (loaded_call["any"][1:])
            return action, action_attributes
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
            if call == "MENU_SCENARIO":
                return self.ci_invalid_input(call, "Invalid Command.\n")
            if call == "DANGER":
                return self.ci_invalid_input(
                    call, self.random_text("Invalid Danger Command"))
            elif call == "GENERIC":
                return self.ci_invalid_input(
                    call, self.random_text("Invalid Command"))
            elif testing:
                return self.ci_invalid_input, ()
            else:
                return self.ci_invalid_input(
                    call, self.random_text("Invalid Command"))

# Starting the game:

    def start(self):
        """First function executed by the game, starts in the
        MENU_SCENARIO state."""
        self.activate_screen("command")
        Menu(self, "MENU_SCENARIO")
        return self.ci_call_user("MENU_SCENARIO")

    def keep_going(self, func_tuple: tuple):
        """Main game loop:

        Executes ``ci_call_user``, returns new ``func_tuple``,

        Executes function from ``func_tuple``, returns ci_call_user params."""
        while True:
            function, function_attributes = func_tuple
            func_tuple = function(*function_attributes)

# Menu methods called by the CI:

    def menu_new_game(self, *args):
        """Goes to "MENU_INTRO" state that shows mapfile description."""
        Menu(self, "MENU_INTRO")
        return self.ci_call_user("MENU_INTRO")

    def menu_load_game(self, *args):
        """Goes to "MENU_LOAD" state that lets player choose the save file
        to load."""
        Menu(self, "MENU_LOAD")
        return self.ci_call_user("MENU_LOAD")

    def menu_save_chosen(self, savefile: str, *args):
        """Goes to an inbetween state that loads save file data
        and resumes the adventure."""
        self.parse_from_json(ReaderJSON(savefile).json_file, overlap=True)
        return self.begin_adventure(state="loaded")

    def menu_scenario_chosen(self, scenario: str, *args):
        """Loads mapfile content and goes to "MENU_MAIN" state that shows
        the main menu."""
        self.parse_from_json(ReaderJSON(scenario).json_file, overlap=False)
        Menu(self, "MENU_MAIN")
        return self.ci_call_user("MENU_MAIN")

    def menu_pick_character(self, *args):
        """Goes to "MAP_CHARACTER" state that loads playable characters
        and lets player choose one of them."""
        Menu(self, "MENU_CHARACTER")
        return self.ci_call_user("MENU_CHARACTER")

    def pick_character(self, character: str, *args):
        """Goes to an inbetween state that loads character data
        and begins the adventure."""
        for entry in self.data.character_types[character]:
            self.data.player[entry] = self.data.character_types[
                character][entry]
        return self.begin_adventure(state="new")

    def begin_adventure(self, state: str):
        """Begins the playable segment of the game: activates "location"
        and "player" screens and puts player in the starting/loaded location,
        depending on the given ``state``."""
        self.activate_screen("location")
        self.activate_screen("player")
        self.deactivate_screen("menu")
        if state == "new":
            for location_id, location in self.data.location_types.items():
                if "is_start" in location and location["is_start"]:
                    self.take_it("PLANS")
                    self.take_it("MONEY")
                    self.take_it("MONEY")
                    return self.appear(location_id, "LD_START")
        elif state == "loaded":
            return self.appear(self.data.player["Location"], "LD_START")

    def menu_end_game(self, result: str):
        """Depending on the ``result``, goes to either "MENU_VICTORY" or
        "MENU_LOST" state that shows the final outcome and allows to quit."""
        self.deactivate_screen("location")
        self.deactivate_screen("player")
        if result == "VICTORY":
            Menu(self, "MENU_VICTORY")
            return self.ci_call_user("MENU_VICTORY")
        elif result == "FAILURE":
            Menu(self, "MENU_LOST")
            self.data.already_failed = True
            return self.ci_call_user("MENU_LOST")

# Generic methods called by the CI:

    def search_location(self, *args):
        """GENERIC GAMEPLAY FUNCTION

        Makes player increase search level for current location if it's
        less than 3 and gives search rewards if there are any."""
        location = self.clocation()[1]
        try:
            if "Search Level" not in location.keys():
                location["Search Level"] = self.data.max_search
            if "Search Rewards" not in location.keys()\
                    or type(location["Search Rewards"]) is not dict:
                location["Search Rewards"] = {"1": [], "2": [], "3": []}
            for level in {"1", "2", "3"}:
                if level not in location["Search Rewards"].keys()\
                        or type(location["Search Rewards"][level]) is not list:
                    location["Search Rewards"][level] = []
            if location["Search Level"] < self.data.max_search:
                location["Search Level"] += 1
                if location["Search Rewards"][
                        str(location["Search Level"])] != []:
                    self.get_screen("command").screen_add(
                        self.random_text("Search Success"), True)
                    self.give_rewards(location["Search Rewards"][
                            str(location["Search Level"])],
                            source="search")
                else:
                    self.get_screen("command").screen_add(
                        self.random_text("Search Failed"), True)
                self.timer_tick()
            else:
                self.get_screen("command").screen_add(
                    self.random_text("Search Max"),
                    True)
            self.update_screens()
            return self.ci_call_user("GENERIC")
        except KeyError as ex:
            if ex.args[0] in {'1', '2', '3'}:
                return self.ci_invalid_input(
                    "GENERIC", f"MISSING SEARCH REWARDS "
                    f"FOR LEVEL {ex.args[0]}!")

    def go_to(self, *args):
        """GENERIC GAMEPLAY FUNCTION

        Changes player location to given location if it exists
        and there's a path to it."""
        found_it = False
        if args == ():
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Invalid Command"))
        for location_id, location in self.data.location_types.items():
            if "Name" in location.keys():
                if location["Name"].lower() == args[0]:
                    if location_id == self.clocation()[0]:
                        return self.ci_invalid_input(
                            "GENERIC", self.random_text("Already Here"))
                    elif not self.check_path(location_id):
                        return self.ci_invalid_input(
                            "GENERIC", self.random_text("Missing Path"))
                    else:
                        previous_location_id = self.clocation()[0]
                        self.data.player["Location"] = location_id
                        self.timer_tick()
                        return self.arrive(location_id, previous_location_id)
        if not found_it:
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Imaginary Path"))

    def take_item(self, testing=False, *args):
        """GENERIC GAMEPLAY FUNCTION

        If answer is take: item;
        Picks up the given item and puts it in player's backpack if the item
        exists and is in the current location.

        If answer is take: all;
        Picks up all existing items in the current location."""
        if args == ():
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Invalid Command"),
                testing=testing)
        location = self.clocation()[1]
        if "List of Items" not in location.keys():
            return self.ci_invalid_input(
                "GENERIC", "There is nothing to take.",
                testing=testing)
        found_it = False
        if args[0] == "all":
            if len(location["List of Items"]) == 0:
                return self.ci_invalid_input(
                    "GENERIC", "There is nothing to take.",
                    testing=testing)
            found_it = True
            for item_id in location["List of Items"]:
                self.take_it(item_id)
            location["List of Items"] = []
            self.get_screen("command").screen_add(
                "You took every item you found.", True)
            self.update_screens()
        else:
            for item_id in self.data.item_types:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if item_id not in location["List of Items"]:
                        return self.ci_invalid_input(
                            "GENERIC", "There is nothing like that here.",
                            testing=testing)
                    else:
                        found_it = True
                        self.take_it(item_id)
                        location["List of Items"].remove(item_id)
                        self.get_screen("command").screen_add(
                            f"You took {self.get_item(item_id)['Name']}.",
                            True)
                        if not testing:
                            self.update_screens()
                        break
        if not found_it:
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Imaginary Item"),
                testing=testing)
        if not testing:
            return self.ci_call_user("GENERIC")

    def drop_item(self, *args):
        """GENERIC GAMEPLAY FUNCTION

        If answer is drop: item;
        Drops down the given item in the current location and removes it from
        player's backpack if the item exists, is not a key item and is in the
        backpack.

        If answer is drop: all;
        Drops down all carried non-key items in the current location."""
        found_it = False
        if args == ():
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Invalid Command"))
        if args[0] == "all":
            if sum(self.data.player["Items"].values()) == 0:
                return self.ci_invalid_input(
                    "GENERIC", "You don't have anything to drop.")
            else:
                found_it = True
                for item_id, item_count in self.data.player["Items"].items():
                    for item in range(item_count):
                        self.drop_it(item_id, destroy=False, drop_all=True)
                self.get_screen("command").screen_add(
                    "You dropped every item you could.", True)
                self.clean_backpack()
                self.update_screens()
        else:
            for item_id in self.data.item_types:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if item_id not in self.data.player["Items"] \
                            or self.data.player["Items"][item_id] == 0:
                        return self.ci_invalid_input(
                            "GENERIC", self.random_text("Missing Item"))
                    else:
                        found_it = True
                        self.drop_it(item_id, destroy=False, drop_all=False)
                        self.clean_backpack()
                        self.update_screens()
        if not found_it:
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Imaginary Item"))
        return self.ci_call_user("GENERIC")

    def use_item(self, *args):
        """GENERIC GAMEPLAY FUNCTION

        If answer is use: item;
        Uses given item if it exists, is not a key item, is in player's
        backpack and player meets the item prerequisites.

        If answer is use: all;
        Uses every possible non-key item."""
        found_it = False
        if args == ():
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Invalid Command"))
        if args[0] == "all":
            if sum(self.data.player["Items"].values()) == 0:
                return self.ci_invalid_input(
                    "GENERIC", "You don't have anything to use.")
            else:
                found_it = True
                for item_id, item_count in self.data.player["Items"].items():
                    for item in range(item_count):
                        self.use_it(item_id=item_id, use_all=True)
                self.get_screen("command").screen_add(
                    "You used every item you could.", True)
                self.clean_backpack()
                self.update_screens()
        else:
            if self.get_item_from_name(args[0])\
                    not in self.data.player["Items"]:
                return self.ci_invalid_input(
                    "GENERIC", self.random_text("Missing Item"))
            for item_id in self.data.player["Items"]:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if self.data.player["Items"][item_id] == 0:
                        return self.ci_invalid_input(
                            "GENERIC", self.random_text("Missing Item"))
                    else:
                        found_it = True
                        self.use_it(item_id=item_id)
                        self.clean_backpack()
                        self.update_screens()
        if not found_it:
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Imaginary Item"))
        return self.ci_call_user("GENERIC")

    def examine(self, *args):
        """ TODO """
        if args == ():
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Invalid Command"))
        if self.get_item_from_name(args[0]) not in self.data.player["Items"]:
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Missing Item"))
        for item_id in self.data.player["Items"]:
            if self.get_item(item_id)["Name"].lower() == args[0]:
                found_it = True
                self.get_screen("command").screen_add(
                    self.get_item(item_id)["Description"], True)
                self.update_screens()
        if not found_it:
            return self.ci_invalid_input(
                "GENERIC", self.random_text("Imaginary Item"))

        return self.ci_call_user("GENERIC")

    def do_event(self, *args):
        """GENERIC GAMEPLAY FUNCTION

        Chooses one of the event options if the requirements are met."""
        location = self.clocation()[1]
        success = False
        if len(args) <= 1:
            return self.ci_invalid_input(
                args[0], self.random_text("Invalid Command"))
        try:
            choice_index = int(args[1]) - 1
            if choice_index < 0 or\
                    choice_index > len(location["List of Events"]) - 1:
                raise ValueError
        except (TypeError, ValueError):
            return self.ci_invalid_input(
                args[0], self.random_text("Invalid Command"))

        event = location["List of Events"][choice_index]

        if event["Type"] == "Payment":
            if self.check_item_cost(event["Requirements"]):
                for item in event["Requirements"]:
                    self.drop_it(item, drop_all=True, destroy=True)
                    success = True
                    self.clean_backpack()
            else:
                return self.ci_invalid_input(
                    args[0], "You don't have enough items!")
        elif event["Type"] == "Choice":
            success = True
        elif event["Type"] == "Check":
            if self.check_stat_cost(event["Requirements"]):
                success = True
            else:
                return self.ci_invalid_input(
                    args[0], self.random_text("Low Stat"))
        elif event["Type"] == "Timed":
            for turn in range(event["Requirements"][0]):
                self.timer_tick()
            success = True
        if success:
            self.get_screen("command").screen_add(event["Thank Text"], True)
            self.give_rewards(event["Rewards"], source="event")
            location.pop("List of Events", None)
            location.pop("Event Description", None)
            location.pop("Dangerous Event", None)
        self.update_screens()
        return self.ci_call_user("GENERIC")

# Functions for player:

    def check_stat_cost(self, requirement_list: list):
        """Checks if player has high enough statistics to choose an event option.
        """
        logical_carry = True
        for min_value, value in zip(requirement_list,
                                    self.data.player["Stats"].values()):
            if value >= min_value and logical_carry:
                logical_carry = True
            else:
                return False
        return True

    def show_stats(self, item_id=None):
        """Returns a string containing information about player's statistics
        or given item requirements."""
        player = self.data.player
        if item_id is None:
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
        else:
            stats_str = " You need "
            item = self.get_item(item_id)
            i = 0
            for stat_name in self.data.dict_of_stats.values():
                stat_value = item["Prerequisite"][i]
                i += 1
                end = ", "
                if stat_value > 0:
                    stats_str = "".join([stats_str, f"{stat_value} ",
                                        stat_name, end])
                if i == len(item["Prerequisite"]):
                    stats_str = "".join([stats_str[:-2], "."])
        return stats_str

    def show_player_items(self):
        """Returns a string containing information about player's items."""
        player = self.data.player
        items_str = "You have "
        if len(player["Items"]) == 0:
            items_str = self.random_text("Empty Backpack")
        i = 0
        for item, amount in player["Items"].items():
            i += 1
            if not i == len(player["Items"]):
                end = ", "
            else:
                end = "."
            items_str = "".join([
                items_str, f"{self.get_item(item)['Name']} ({amount}){end}"])
        return items_str

# Functions for locations:

    def clocation(self):
        """Returns a tuple containing current location key and data (dict)."""
        return (self.data.player["Location"],
                self.data.location_types[self.data.player["Location"]])

    def get_location(self, location_id: str):
        """Returns all data (dict) of the location with given ``location_id``.
        """
        return self.data.location_types[location_id]

    def check_path(self, location_id: str):
        """"Returns ``True`` if the current location contains a path to given
        location. If there is no path or no "List of Paths" entry in the
        current location, returns ``False``."""
        if "List of Paths" not in self.clocation()[1].keys():
            return False
        for path in self.clocation()[1]["List of Paths"]:
            if path == location_id:
                return True
        return False

    def appear(self, location_id: str, previous_location_id: str):
        """Magically teleports player to the location with ``location_id`` key
        and sets the previous location to given ``previous_location_id``.
        If no ``previous_location_id`` is given, defaults to "LD_START"."""
        self.data.player["Location"] = location_id
        return self.arrive(location_id, previous_location_id)

    def arrive(self, location_id: str, previous_location_id: str):
        """Moves player to the location with ``location_id`` key and marks
        the location with ``previous_location_id`` as already explored.

        If the location is the game objective, makes "ENDING" call that
        finishes the adventure.

        If the location is dangerous, makes "DANGER" call instead of "GENERIC"
        call that forces the player to finish the event before doing anything
        else."""
        location = self.get_location(location_id)
        previous_location = self.get_location(previous_location_id)
        if "is_new" not in location:
            location["is_new"] = True
        self.update_screens()
        if previous_location["is_new"]:
            previous_location["is_new"] = False
        if "is_win" in location and location["is_win"]:
            return self.ci_call_user("ENDING")
        elif "Dangerous Event" not in location\
                or not location["Dangerous Event"]:
            return self.ci_call_user("GENERIC")
        else:
            return self.ci_call_user("DANGER")

    def show_items(self):
        """Returns a string containing information about current location
        items. If the "List of Items" entry is missing,
        returns ``"MISSING ITEMS ENTRY!"``."""
        location = self.clocation()[1]
        item_str = ""
        try:
            if len(location["List of Items"]) == 0:
                item_str = self.random_text("No Items")
            elif len(location["List of Items"]) == 1:
                item = self.get_item(location['List of Items'][0])
                item_str = f"There is {item['Article']} {item['Name']}."
            else:
                i = 0
                item_str = "There are "
                for item in location["List of Items"]:
                    i += 1
                    if not i == len(location["List of Items"]):
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
        """Returns a string containing information about current location
        paths. If the "List of Paths" entry is missing,
        returns ``"MISSING PATHS ENTRY!"``."""
        path_str = ""
        location = self.clocation()[1]
        if "List of Paths" not in location.keys():
            path_str = "MISSING PATHS ENTRY!"
        elif len(location["List of Paths"]) == 0:
            path_str = self.random_text("No Paths")
        else:
            i = 0
            path_str = "There are paths to "
            for each_location in location["List of Paths"]:
                i += 1
                if not i == len(location["List of Paths"]):
                    end = ", "
                else:
                    end = "."
                if "Name" in self.get_location(each_location).keys():
                    name = self.get_location(each_location)['Name']
                else:
                    name = f"{each_location} MISSING NAME"
                path_str = "".join([path_str, f"{name}{end}"])
        return path_str

    def show_events(self):
        """Returns a string containing information about current location
        event. If the "List of Events" entry is missing,
        returns ``"MISSING EVENTS ENTRY!"``.
        If the "List of Events" entry is empty, returns empty string."""
        event_str = ""
        location = self.clocation()[1]
        try:
            if not len(location["List of Events"]) == 0:
                for event in location["List of Events"]:
                    event_str = "".join([event_str, event["Text"]])
        except KeyError:
            event_str = "MISSING EVENTS ENTRY!"
        finally:
            return event_str

# Functions for items:

    def give_rewards(self, reward_list: list, source: str):
        """Gives all rewards in ``reward_list``.

        If the reward is a location,
        creates a new path to this location from the current one.

        If the reward is an item, gives this item to player.

        If the reward is statistics change (a dictionary), creates a fake
        StatUp Consumable item and uses it on player."""
        location = self.clocation()[1]
        for reward in reward_list:
            if type(reward) is dict:
                fake_item = {"Type": "Consumable",
                             "Action": ["StatUp", reward]}
                self.use_it(item=fake_item)
            elif reward in self.data.location_types:
                location["List of Paths"].append(reward)
                if "Name" in self.get_location(reward).keys():
                    name = self.get_location(reward)["Name"]
                else:
                    name = f"{reward} MISSING NAME"
                self.get_screen("command").screen_add(
                    f"You find a path to {name}!", True)
            elif reward in self.data.item_types:
                if source == "search":
                    location["List of Items"].append(reward)
                    reward_str = "You find "
                elif source == "event":
                    self.take_it(reward)
                    reward_str = "You receive "
                self.get_screen("command").screen_add(
                    f"{reward_str}{self.get_item(reward)['Article']} "
                    f"{self.get_item(reward)['Name']}!", True)
            elif type(reward) is int and reward > 0:
                for turn in range(reward):
                    self.timer_tick(reverse=True)
                self.get_screen("command").screen_add(
                    f"You gained {reward} more turns!", True)

    def clean_backpack(self):
        """Removes all items (keys) with the value of 0 from player's backpack.
        """
        new_dict = {}
        for item_id, item_count in self.data.player["Items"].items():
            if item_count != 0:
                new_dict[item_id] = item_count
        self.data.player["Items"] = new_dict

    def get_item(self, item_id: str):
        """Returns data (dict) of the item with corresponding ``item_id``."""
        return self.data.item_types[item_id]

    def get_item_from_name(self, item_name: str):
        """Returns item key of the item with given ``item_name``."""
        for item_id, item in self.data.item_types.items():
            if item["Name"].lower() == item_name:
                return item_id

    def use_it(self, item_id=None, use_all=False, item=None):
        """Applies item effect if the requirements are met.
        ``item_id`` is used when this function is executed by "use" command.
        ``item`` is used when a fake item (not in "List of Items") is created
        and used.
        ``use_all`` is used when this function is executed by "use: all"
        command and supresses notifications about max stats.

        ``Consumable``-type items disappear after being used.

        ``Key``-type items cannot be used or dropped.

        ``Event``-type items cannot be used but can be dropped.

        ``StatUp`` action increases/decreases player statistics by
        certain value if the statistics are not at player's maximum.

        ``Restore`` action sets player statistics to maximum.

        ``Grow`` action increases/decreases player statistics by certain value.
        """
        player = self.data.player
        applied = False
        if item is None:
            item = self.get_item(item_id)
        if item_id is None or self.check_item_prereq(item_id):
            if item["Type"] == "Consumable":

                if item["Action"][0] == "StatUp":

                    for stat, stat_value in item["Action"][1].items():
                        if player["Stats"][stat] == player["Max Stats"][stat]\
                                and stat_value > 0:
                            pass
                        elif stat_value + player["Stats"][stat] >\
                                player["Max Stats"][stat]:
                            player["Stats"][stat] = player["Max Stats"][stat]
                            applied = True
                        else:
                            player["Stats"][stat] += stat_value
                            if player["Stats"][stat] < 0:
                                player["Stats"][stat] = 0
                            applied = True

                    if applied:
                        if item_id is not None:
                            self.consume_item(item_id)
                    else:
                        if use_all or item_id is None:
                            pass
                        else:
                            self.get_screen("command").screen_add(
                                self.random_text("Max Stat"), True)

                if item["Action"][0] == "Restore":
                    for stat in item["Action"][1]:
                        if player["Stats"][stat] != player["Max Stats"][stat]:
                            player["Stats"][stat] = player["Max Stats"][stat]
                            applied = True
                    if applied:
                        if item_id is not None:
                            self.consume_item(item_id)
                    else:
                        if use_all or item_id is None:
                            pass
                        else:
                            self.get_screen("command").screen_add(
                                self.random_text("Max Stat"), True)

                if item["Action"][0] == "Grow":
                    for stat, stat_value in item["Action"][1].items():
                        player["Max Stats"][stat] += stat_value
                        player["Stats"][stat] += stat_value
                    if item_id is not None:
                        self.consume_item(item_id)

            if item["Type"][0] == "Key":
                self.get_screen("command").screen_add(
                    self.random_text("Lock Key"))
            if item["Type"][0] == "Event":
                self.get_screen("command").screen_add(
                    self.random_text("Not Consumable"))

        else:
            if not use_all:
                str_1 = self.random_text("Low Stat")
                str_2 = self.show_stats(item_id)
                return self.ci_invalid_input(
                    "GENERIC", str_1+str_2)

    def consume_item(self, item_id: str):
        """Called by ``use_it``, removes the item from player's backpack
        and informs the player about it."""
        self.data.player["Items"][item_id] -= 1
        name = self.get_item(item_id)['Name']
        desc = self.get_item(item_id)['Action Description']
        self.get_screen("command").screen_add(
            f"You used {name}. {desc}", True)

    def check_item_prereq(self, item_id: str):
        """Checks if player meets the item requirements."""
        item = self.get_item(item_id)
        logical_carry = True
        for min_value, value in zip(
                item["Prerequisite"],
                self.data.player["Stats"].values()):
            if value >= min_value and logical_carry:
                logical_carry = True
            else:
                return False
        return True

    def take_it(self, item_id: str):
        """Called by ``take_item``, removes the given item from location
        and adds it to player's backpack."""
        if item_id not in self.data.player["Items"]:
            self.data.player["Items"][item_id] = 0
        self.data.player["Items"][item_id] += 1

    def drop_it(self, item_id: str, destroy: bool, drop_all: bool):
        """Called by ``drop_item``, removes the given item from player's backpack if
        it's a non-key item. If ``destroy`` is false, the item appears in the
        current location. If ``drop_all`` is true, doesn't notify the player
        about the fact."""
        if destroy:
            self.data.player["Items"][item_id] -= 1
        elif self.get_item(item_id)["Type"] == "Key":
            if not drop_all:
                self.get_screen("command").screen_add(
                    self.random_text("Lock Key"), True)
        else:
            self.data.player["Items"][item_id] -= 1
            self.clocation()[1]["List of Items"].append(item_id)
            self.get_screen("command").screen_add(
                f"You dropped {self.get_item(item_id)['Name']}.", True, True)

    def check_item_cost(self, requirement_list: list):
        """Returns True if player has enough items requested by the
        ``requirement_list``."""
        total_cost = {}
        logical_carry = True
        for item_id in requirement_list:
            if item_id not in self.data.player["Items"]:
                return False
            if item_id not in total_cost:
                total_cost[item_id] = 0
            total_cost[item_id] += 1
        for item_id, item_cost in total_cost.items():
            if item_cost <= self.data.player["Items"][item_id]\
                    and logical_carry:
                logical_carry = True
            else:
                return False
        return True

# Text randomness:

    def random_text(self, key):
        """Returns a random string from string group with the given ``key``."""
        return random.choice(self.data.text_variation[key])


class Menu:
    """A class representing menu state. Each menu has a ``call_key``
    to the corresponding call. Depending on the ``call_key``, menu
    can also use a specific hardcoded function.

    Example: Menu with ``call_key`` "MENU_SCENARIO" shows all valid mapfiles
    and adds them as "MENU_SCENARIO" call answers."""

    def __init__(self, game: Game, call_key: str):
        self.game = game
        self.data = self.game.data
        self.call_key = call_key
        self.start()

    def start(self):
        """Shows content of the menu state."""
        self.game.activate_screen("menu")
        self.game.get_screen("menu").screen_clear()
        self.read_menu()

    def read_menu(self):
        """Gets text to show from the corresponding call type.
        Calls a hardcoded function bound to the ``self.call_key``."""
        self.game.get_screen("menu").screen_reset()
        call = self.game.ci_call_check(self.call_key)

        if "text" in call:
            self.game.get_screen("menu").screen_add(call["text"])
        if self.call_key == "MENU_CHARACTER":
            self.write_characters()
        elif self.call_key == "MENU_SCENARIO":
            self.add_scenarios_as_answers(
                self.read_directory(read_type="map"), add_type="map")
        elif self.call_key == "MENU_LOAD":
            self.add_scenarios_as_answers(
                self.read_directory(read_type="save"), add_type="save")
        elif self.call_key == "MENU_VICTORY":
            self.show_ending_screen()
        elif self.call_key == "MENU_LOST":
            self.show_ending_screen()

        self.game.refresh_screens()

    def write_characters(self):
        """Add to "menu" screen playable character descriptions."""
        for each in self.data.character_types:
            self.game.get_screen("menu").screen_add(
                self.data.character_types[each]["Menu Description"])

    def read_directory(self, read_type: str):
        """Searches the game directory for valid JSON files and returns
        a list of their file names and/or map names. If ``read_type`` is "map",
        searches for files with ``map_`` prefix, if ``read_type`` is "save",
        searches for files with ``save_`` prefix."""
        scenarios = []
        prefix = f"{read_type}_"
        folder = list(filter(
            lambda x: x.endswith(".json") and x.startswith(prefix),
            os.listdir(self.data.path)))
        for file in folder:
            reader = ReaderJSON(file)
            if reader.json_load_ok:
                if "Version" in reader.json_file\
                        and reader.json_file["Version"] == self.data.version:
                    if read_type == "map":
                        scenarios.append((file, reader.json_file["Name"]))
                    elif read_type == "save":
                        scenarios.append((file, file))
                else:
                    self.game.get_screen("menu").screen_add(
                        f"{file} has incorrect version.")
            else:
                self.game.get_screen("menu").screen_add(
                    f"{file} contains a JSON error.")

        if len(scenarios) != 0:
            for index, entry in enumerate(scenarios):
                self.game.get_screen("menu").screen_add(
                    f"{index+1}. {entry[1]}")
        else:
            if read_type == "map":
                self.game.get_screen("command").screen_add(
                    "\nNo valid scenarios detected. Type 'quit' to exit.")
            elif read_type == "save":
                self.game.get_screen("command").screen_add(
                    "\nNo valid save files detected. Type 'quit' to exit.")
        return scenarios

    def add_scenarios_as_answers(self, scenarios: list, add_type: str):
        """Adds files from ``scenarios`` list as option for the CI. If ``add_type``
        is "map", adds them to "MENU_SCENARIO" call. If ``add_typ`` is "save",
        adds them to "MENU_LOAD" call."""
        if add_type == "map":
            call = "MENU_SCENARIO"
            next_function = "menu_scenario_chosen"
        elif add_type == "save":
            call = "MENU_LOAD"
            next_function = "menu_save_chosen"
        for index, entry in enumerate(scenarios):
            self.data.sys_call_types[call][f"{index + 1}"] =\
                [next_function, entry[0]]

    def show_ending_screen(self):
        """Adds player data: name, items and time, to the ending screen."""
        self.game.get_screen("menu").screen_add(
            f"Your name: {self.data.player['Name']}")
        self.game.get_screen("menu").screen_add(
            f"Turns left {self.data.time_limit - self.data.time}"
            f"/{self.data.time_limit}")
        self.game.get_screen("menu").screen_add(self.game.show_stats())
        self.game.get_screen("menu").screen_add(self.game.show_player_items())


if __name__ == "__main__":
    game = Game(GameData())
    function = game.start()
    game.keep_going(function)
