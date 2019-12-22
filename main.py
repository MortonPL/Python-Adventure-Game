'''
    THIS IS THE MAIN GAME FILE
'''
import os


class Game:

    def __init__(self):
        self.screens = {'menu': Screen('menu')}
        menu = Menu(self, "mainmenu.txt")
        self.clear()

    def screen_get(self, key):
        return self.screens[key]

    def screen_add(self, key, screen):
        self.screens[key] = screen

    def screen_refresh(self, key):
        self.clear()
        self.screens[key].show()

    def screen_reset(self, key):
        self.screens[key].clear_memory()

    def clear(self):
        os.system('cls')

    def exit(self, roll_function):
        if input('\nAre you sure about that? (Type in QUIT to confirm.) ') == \
                'QUIT':
            exit()
        else:
            self.rollback(roll_function)

    def rollback(self, roll_function):
        print("we're back")
        roll_function()

    def question(self, key):
        self.screens[key].add('\nWhat do you do? ', True)
        self.screen_refresh(key)
        return input()


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


class Menu:

    def __init__(self, game, menufile_path):
        self.game = game
        self.menufile = ReaderTXT(menufile_path)
        self.read_menu(0)
        self.userchoice()

    def read_menu(self, section):
        self.game.screen_reset('menu')
        for line in self.menufile.get_section(section):
            self.game.screen_get('menu').add(line)
        self.game.screen_refresh('menu')

    def userchoice(self):
        choice = self.game.question('menu')
        if choice == "1":  # Start a game
            self.newgame()
        elif choice == "2":  # Load a save
            self.loadgame()
        elif choice == "3":  # Exit
            self.game.exit(self.userchoice)
        else:
            self.game.screens['menu'].add('\nPlease choose a valid option.',
                                          True, True)
            self.userchoice()

    def newgame(self):
        pass

    def loadgame(self):
        pass


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
