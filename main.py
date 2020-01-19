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
        "MENU_LOAD":
        {
            "Text": "Available save files:\n\n",
            "Question": "Choose the save file you want to load. ",
            "Any_key": False
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
            "Stats": {"HP": 100, "FIT": 0, "SRV": 0,
                      "COM": 0, "SOC": 0, "LUC": 0},
            "Max Stats": {"HP": 100, "FIT": 1, "SRV": 1,
                          "COM": 1, "SOC": 1, "LUC": 1},
            "Location": "",
            "Items": {}}
        self.version = "Game_A"
        self.mapfile = None
        self.time = 0
        self.time_limit = 0
        self.fail = False


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
            try:
                self.json_file = json.load(file)
                self.json_load_ok = True
            except Exception:
                self.json_load_ok = False


class Game:

    def __init__(self, data_object):
        self.data = data_object
        self.data.platform = sys.platform

# Parsing functions:

    def parse_from_json(self, json, overlap):
        self.data.location_types = json["List of Locations"]
        if not overlap:
            self.data.item_types = json["List of Items"]
            self.data.text_variation = json["Text Variants"]
            self.data.call_types = json["List of Calls"]
            self.data.character_types = json["Playable Characters"]
            self.data.dict_of_stats = json["Player Stats"]
            self.data.mapfile = json["Name"]
            self.data.time_limit = json["Time Limit"]
        else:
            self.data.player = json["Player"]
            self.data.time = json["Time"]

    def dump_to_json(self):
        save_data = {
            "Version": self.data.version,
            "Name": self.data.mapfile,
            "List of Locations": self.data.location_types,
            "Player": self.data.player,
            "Time": self.data.time
        }
        return save_data

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
        self.get_screen("player").screen_reset()
        timer_str = f"You have {self.data.time_limit-self.data.time} turns."
        self.get_screen("player").screen_add(self.show_player_stats())
        self.get_screen("player").screen_add(self.show_player_items())
        self.get_screen("player").screen_add(timer_str)

# COMMAND PROMPT (CP) methods:

    def cp_update_rollback(self, function, *args):
        self.data.rollback = function
        self.data.rollback_args = args

    def exit(self, *args):
        confirm = input(
            "\nAre you sure about that? (Type in QUIT to confirm) ")
        if confirm.lower() == "quit":
            self.get_screen("command").screen_clear()
            exit()
        else:
            self.refresh_screens()
            return self.data.rollback(*self.data.rollback_args)

    def save(self, *args):
        confirm = input("\nType in the name of your save state."
                        "(Type in CANCEL to cancel) ")
        if confirm.lower() == "cancel":
            self.refresh_screens()
            return self.data.rollback(*self.data.rollback_args)
        else:
            try:
                with open(f"save_{confirm}.json", "w") as file:
                    json.dump(self.dump_to_json(), file, indent=4)
                print("Saved successfully.")
                return self.cp_call_user("GENERIC")
            except Exception:
                print("Unacceptable name. Please enter another name.")
                self.save()

    def check_health(self):
        if self.data.player["Stats"]["HP"] <= 0:
            print("You have died and thus failed the mission. GAME OVER")
            self.data.fail = True

    def timer_tick(self):
        if self.data.time < self.data.time_limit:
            self.data.time += 1
        else:
            print("You have run out of time and "
                  "thus failed the mission. GAME OVER")
            self.data.fail = True

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
            else:
                raise Exception
        except Exception:
            sys.exit(f"Something went wrong, call {call} does not exist.")
        return dict(
            (key.lower(), value) for (key, value) in loaded_call.items())

    def cp_call_user(self, call, loaded_call=None):
        self.cp_update_rollback(self.cp_call_user, call)
        self.check_health()
        if self.data.fail:
            return self.menu_loose_game()

        if loaded_call is None:
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
        elif answer == ["save"]:
            valid_answer = True
            return self.save()
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
            if call == "DANGER":
                return self.cp_invalid_input(
                    call, self.random_text("Invalid Danger Command"))
            elif call == "GENERIC":
                return self.cp_invalid_input(
                    call, self.random_text("Invalid Command"))
            else:
                return self.cp_invalid_input(
                    call, self.random_text("Invalid Command"))

# Starting the program

    def start(self):
        self.activate_screen("command")
        Menu(self, "MENU_SCENARIO")
        return self.cp_call_user("MENU_SCENARIO")

    def keep_going(self, func_tuple):
        func, func_attribs = func_tuple
        return func(*func_attribs)

# Menu methods called by the CP

    def menu_new_game(self, *args):
        Menu(self, "MENU_INTRO")
        return self.cp_call_user("MENU_INTRO")

    def menu_load_game(self, *args):
        Menu(self, "MENU_LOAD")
        return self.cp_call_user("MENU_LOAD")

    def menu_save_chosen(self, savefile, *args):
        self.parse_from_json(ReaderJSON(savefile).json_file, overlap=True)
        return self.begin_adventure(state="loaded")

    def menu_scenario_chosen(self, scenario, *args):
        self.parse_from_json(ReaderJSON(scenario).json_file, overlap=False)
        Menu(self, "MENU_MAIN")
        return self.cp_call_user("MENU_MAIN")

    def menu_pick_character(self, *args):
        Menu(self, "MENU_CHARACTER")
        return self.cp_call_user("MENU_CHARACTER")

    def pick_character(self, character, *args):
        for entry in self.data.character_types[character]:
            self.data.player[entry] = self.data.character_types[
                character][entry]
        return self.begin_adventure(state="new")

    def begin_adventure(self, state):
        self.get_screen("menu").screen_reset()
        self.activate_screen("location")
        self.activate_screen("player")
        self.deactivate_screen("menu")
        if state == "new":
            for location_id, location in self.data.location_types.items():
                if "is_start" in location:
                    return self.appear(location_id, "LD_START")
        elif state == "loaded":
            return self.appear(self.data.player["Location"], "LD_START")

    def menu_win_game(self):
        self.deactivate_screen("location")
        self.deactivate_screen("player")
        Menu(self, "MENU_VICTORY")
        return self.cp_call_user("MENU_VICTORY")

    def menu_loose_game(self):
        self.deactivate_screen("location")
        self.deactivate_screen("player")
        Menu(self, "MENU_LOST")
        return self.cp_call_user("MENU_LOST")

# Generic methods called by the CP

    def search_location(self, *args):
        location = self.clocation()[1]
        try:
            # spend some time
            if "Search Level" not in location.keys():
                location["Search Level"] = 3
            if "Search Rewards" not in location.keys()\
                    or type(location["Search Rewards"]) is not dict:
                location["Search Rewards"] = {"1": [], "2": [], "3": []}
            for level in {"1", "2", "3"}:
                if level not in location["Search Rewards"].keys()\
                        or type(location["Search Rewards"][level]) is not list:
                    location["Search Rewards"][level] = []
            if location["Search Level"] < 3:
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
            return self.cp_call_user("GENERIC")
        except KeyError as ex:
            if ex.args[0] in {'1', '2', '3'}:
                return self.cp_invalid_input(
                    "GENERIC", f"MISSING SEARCH REWARDS "
                    f"FOR LEVEL {ex.args[0]}!")

    def go_to(self, *args):
        found_it = False
        for location_id, location in self.data.location_types.items():
            if "Name" in location.keys():
                if location["Name"].lower() == args[0]:
                    if location_id == self.clocation()[0]:
                        return self.cp_invalid_input(
                            "GENERIC", self.random_text("Already Here"))
                    elif not self.check_path(location_id):
                        return self.cp_invalid_input(
                            "GENERIC", self.random_text("Missing Path"))
                    else:
                        previous_location_id = self.clocation()[0]
                        self.data.player["Location"] = location_id
                        self.timer_tick()
                        return self.arrive(location_id, previous_location_id)
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", self.random_text("Imaginary Path"))

    def take_item(self, *args):
        location = self.clocation()[1]
        if "List of Items" not in location.keys():
            return self.cp_invalid_input(
                "GENERIC", "There is nothing to take.")
        found_it = False
        if args[0] == "all":
            if len(location["List of Items"]) == 0:
                return self.cp_invalid_input(
                    "GENERIC", "There is nothing to take.")
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
                        return self.cp_invalid_input(
                            "GENERIC", "There is nothing like that here.")
                    else:
                        found_it = True
                        self.take_it(item_id)
                        location["List of Items"].remove(item_id)
                        self.get_screen("command").screen_add(
                            f"You took {self.get_item(item_id)['Name']}.",
                            True)
                        self.update_screens()
                        break
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", self.random_text("Imaginary Item"))
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
                            "GENERIC", self.random_text("Missing Item"))
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
                "GENERIC", self.random_text("Imaginary Item"))
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
                        self.use_it(item_id=item_id, use_all=True)
                self.get_screen("command").screen_add(
                    "You used every item you could.", True)
                self.clean_backpack()
                self.update_screens()
        else:
            if self.get_item_from_name(args[0])\
                    not in self.data.player["Items"]:
                return self.cp_invalid_input(
                    "GENERIC", self.random_text("Missing Item"))
            for item_id in self.data.player["Items"]:
                if self.get_item(item_id)["Name"].lower() == args[0]:
                    if self.data.player["Items"][item_id] == 0:
                        return self.cp_invalid_input(
                            "GENERIC", self.random_text("Missing Item"))
                    else:
                        found_it = True
                        self.use_it(item_id=item_id)
                        self.get_screen("command").screen_add(
                            f"You used {self.get_item(item_id)['Name']}. "
                            f"{self.get_item(item_id)['Action Description']}",
                            True)
                        self.clean_backpack()
                        self.update_screens()
        if not found_it:
            return self.cp_invalid_input(
                "GENERIC", self.random_text("Imaginary Item"))
        return self.cp_call_user("GENERIC")

    def examine(self, *args):
        return self.cp_call_user("GENERIC")

    def do_event(self, *args):
        location = self.clocation()[1]
        success = False
        try:
            choice_index = int(args[1]) - 1
            if choice_index < 0 or\
                    choice_index > len(location["List of Events"]) - 1:
                raise ValueError
        except (TypeError, ValueError):
            return self.cp_invalid_input(
                args[1], self.random_text("Invalid Command"))

        event = location["List of Events"][choice_index]

        if event["Type"] == "Payment":
            if self.check_item_cost(event["Requirements"]):
                for item in event["Requirements"]:
                    self.drop_it(item, True)
                    success = True
            else:
                return self.cp_invalid_input(
                    args[0], "You don't have enough items!")
        elif event["Type"] == "Choice":
            success = True
        elif event["Type"] == "Check":
            if self.check_stat_cost(event["Requirements"]):
                success = True
            else:
                return self.cp_invalid_input(
                    args[0], self.random_text("Low Stat"))
        if success:
            self.get_screen("command").screen_add(event["Thank Text"], True)
            self.give_rewards(event["Rewards"], source="event")
            location.pop("List of Events")
            location.pop("Event Description")
            location.pop("Dangerous Event", None)
        self.update_screens()
        return self.cp_call_user("GENERIC")

# Functions for player:

    def check_stat_cost(self, requirement_list):
        logical_carry = True
        for min_value, value in zip(requirement_list,
                                    self.data.player["Stats"].values()):
            if value >= min_value and logical_carry:
                logical_carry = True
            else:
                return False
        return True

    def show_player_stats(self):
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
        return stats_str

    def show_player_items(self):
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
        return (self.data.player["Location"],
                self.data.location_types[self.data.player["Location"]])

    def get_location(self, location_id):
        return self.data.location_types[location_id]

    def check_path(self, location_id):
        if "List of Paths" not in self.clocation()[1].keys():
            return False
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
        if "is_win" in location and location["is_win"]:
            return self.cp_call_user("ENDING")
        elif "Dangerous Event" not in location\
                or not location["Dangerous Event"]:
            return self.cp_call_user("GENERIC")
        else:
            return self.cp_call_user("DANGER")

    def show_items(self):
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
        path_str = ""
        location = self.clocation()[1]
        if "List of Paths" not in location.keys():
            path_str = "MISSING PATHS ENTRY!"
        elif len(location["List of Paths"]) == 0:
            path_str = self.random_text(["No Paths"])
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

    def give_rewards(self, reward_list, source):
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

    def clean_backpack(self):
        new_dict = {}
        for item_id, item_count in self.data.player["Items"].items():
            if item_count != 0:
                new_dict[item_id] = item_count
        self.data.player["Items"] = new_dict

    def get_item(self, item_id):
        return self.data.item_types[item_id]

    def get_item_from_name(self, item_name):
        for item_id, item in self.data.item_types.items():
            if item["Name"].lower() == item_name:
                return item_id

    def use_it(self, item_id=None, use_all=False, item=None):
        player = self.data.player
        if item is None:
            item = self.get_item(item_id)
        if item is not None or self.check_item_prereq(item_id):
            if item["Type"] == "Consumable"\
                    and item["Action"][0] == "StatUp":

                for stat, stat_value in item["Action"][1].items():

                    if player["Stats"][stat] == player["Max Stats"][stat]\
                            and stat_value >= 0:

                        if not use_all or item is not None:
                            return self.cp_invalid_input(
                                "GENERIC", self.random_text("Max Stat"))

                    elif stat_value + player["Stats"][stat] >\
                            player["Max Stats"][stat]:

                        player["Stats"][stat] = player["Max Stats"][stat]

                    if item is None:
                        player["Items"][item_id] -= 1

                else:
                    player["Stats"][stat] += stat_value
                    if item is None:
                        player["Items"][item_id] -= 1

        else:
            if not use_all:
                return self.cp_invalid_input(
                    "GENERIC", self.random_text("Low Stat"))

    def check_item_prereq(self, item_id):
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

    def take_it(self, item_id):
        if item_id not in self.data.player["Items"]:
            self.data.player["Items"][item_id] = 0
        self.data.player["Items"][item_id] += 1

    def drop_it(self, item_id, destroy=False):
        self.data.player["Items"][item_id] -= 1
        if not destroy:
            self.clocation()[1]["List of Items"].append(item_id)

    def check_item_cost(self, requirement_list):
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

# Functions for examination:

# Text randomness:

    def random_text(self, key):
        return random.choice(self.data.text_variation[key])


class Menu:

    def __init__(self, game, call_key):
        self.game = game
        self.data = self.game.data
        self.call_key = call_key
        self.start()

    def start(self):
        self.game.activate_screen("menu")
        self.game.get_screen("menu").screen_clear()
        self.read_menu()

    def read_menu(self):
        self.game.get_screen("menu").screen_reset()
        call = self.game.cp_call_check(self.call_key)

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
        for each in self.data.character_types:
            self.game.get_screen("menu").screen_add(
                self.data.character_types[each]["Menu Description"])

    def read_directory(self, read_type="map"):
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

    def add_scenarios_as_answers(self, scenarios, add_type="map"):
        if add_type == "map":
            call = "MENU_SCENARIO"
            next_function = "menu_scenario_chosen"
        elif add_type == "save":
            call = "MENU_LOAD"
            next_function = "menu_save_chosen"
        for index, entry in enumerate(scenarios):
            self.data.sys_call_types[call][f"{index + 1}"] =\
                [next_function, entry[0]]

    def show_ending_screen(self, state):
        self.game.get_screen("menu").screen_add(
            f"Your name: {self.data.player['Name']}")
        self.game.get_screen("menu").screen_add(
            f"Turns left {self.data.time_limit - self.data.time}"
            f"/{self.data.time_limit}")
        self.get_screen("menu").screen_add(self.show_player_stats())
        self.get_screen("menu").screen_add(self.show_player_items())


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
