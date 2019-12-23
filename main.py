'''
    THIS IS THE MAIN GAME FILE
'''
import os


class Game:

    def __init__(self):
        self.screens = {'menu': Screen('menu')}
        self.rollback = None
        menu_main = Menu(self, "mainmenu.txt", 1, False,
                         {"1": "newgame",
                          "2": "loadgame",
                          "3": "exit"})
        menu_intro = Menu(self, "mainmenu.txt", 2, True,
                          {"any": "exit"})
        self.menu_list = [menu_intro, menu_intro]
        menu_main.start()

    def screen_get(self, key):
        return self.screens[key]

    def screen_add(self, key, screen):
        self.screens[key] = screen

    def screen_refresh(self, key):
        self.clear()
        self.screen_get(key).show()

    def screen_reset(self, key):
        self.screen_get(key).clear_memory()

    def clear(self):
        os.system('cls')
        os.system('cls')

    def update_rollback(self, function):
        self.rollback = function

    def exit(self):
        if input('\nAre you sure about that? (Type in QUIT to confirm.) ') == \
                'QUIT':
            self.clear
            exit()
        else:
            print("we're back")
            self.rollback()

    def question(self, key, mute_question):
        if not mute_question:
            self.screen_get(key).add('\nWhat do you do? ', True)
            self.screen_refresh(key)
        return input()


class Menu:

    def __init__(self, game, menufile_path, file_section, any_key, choices):
        self.game = game
        self.menufile = ReaderTXT(menufile_path)
        self.file_section = file_section
        self.any_key = any_key
        self.choices = choices

    def start(self):
        self.game.clear()
        self.read_menu()
        self.userchoice()

    def read_menu(self):
        self.game.screen_reset('menu')
        for line in self.menufile.get_section(self.file_section):
            self.game.screen_get('menu').add(line)
        self.game.screen_refresh('menu')

    def userchoice(self):
        self.game.update_rollback(self.userchoice)
        answer = self.game.question('menu', False)
        valid_answer = False
        if self.any_key:
            valid_answer = True
            action = getattr(self, self.choices["any"])
            action()
        else:
            for choice in self.choices:
                if answer == choice:
                    valid_answer = True
                    action = getattr(self, self.choices[answer])
                    action()
                    break
        if not valid_answer:
            self.game.screen_get('menu').add(
                '\nPlease choose a valid option.', True, True)
            self.userchoice()

    def newgame(self):
        self.game.menu_list[1].start()

    def loadgame(self):
        pass

    def exit(self):
        self.game.exit()


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


class ReaderTXT:

    def __init__(self, path):
        self.sectlist = []
        self.strlist = []
        with open(path, "r") as file:
            counter = 0
            for line in file:
                line = line.strip('\n')
                if line == '$':
                    self.sectlist.append(self.strlist)
                    self.strlist = []
                else:
                    self.strlist.append(line)
                counter += 1

    def get_section(self, wanted_section):
        for index, section in enumerate(self.sectlist):
            if index == wanted_section:
                return section
