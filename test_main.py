from main import Game, GameData, Screen, Menu, ReaderJSON  # noqa: F401
"""Reason: Those classes are used by the Game object and must be imported
even though flake8 sees no reason to."""


# Following functions are neccessary for tests to even work properly.
def create_new_enviroment(game: Game, character: str):
    """Directly feeds data into the game in order to skip all menus."""
    game.parse_from_json(ReaderJSON("map_britannia.json").json_file,
                         overlap=False)
    game.data.testing = True
    if character != "PFAKE":
        for entry in game.data.character_types[character]:
            game.data.player[entry] = game.data.character_types[
                character][entry]


def screen_setup(game):
    """Sets up necessary screens."""
    game.activate_screen("command")
    game.activate_screen("location")
    game.activate_screen("player")
    game.deactivate_screen("menu")


def start_the_test(playtest: bool, is_fake: bool, character_id=None,
                   fake_player=None, location_id=None, fake_locations=None,
                   fake_items=None):
    """Injects custom data dictionaries ``fake_player``, ``fake_locations``,
    ``fake_items`` into the game if ``is_fake`` is true. Sets the current
    location to ``location_id`` and playable character to ``character_id``.
    ``fake_player`` overrides ``character_id`` if present.

    If ``playtest`` is true, allows to normally play the game."""
    game_data = GameData()
    game = Game(game_data)
    if is_fake:
        if fake_player is not None:
            game.data.player = fake_player
            character_id = "PFAKE"
        if fake_locations is not None:
            for location_id, location in fake_locations.items():
                game.data.location_types[location_id] = location
        if fake_items is not None:
            for item_id, item in fake_items.items():
                game.data.item_types[item_id] = item
    create_new_enviroment(game=game, character=character_id)
    if not playtest:
        game.data.player["Location"] = location_id
        game.data.location_types[location_id]["is_new"] = True
    else:
        game.appear(location_id, "LD_START")
        game.keep_going()
    return game


def simulate_ci_call(game: Game, raw_command: str, call_key=None,
                     loaded_call=None):
    if loaded_call is None:
        return game.ci_call_user(
            call=call_key, answer=raw_command)
    else:
        return game.ci_call_user(
            loaded_call=loaded_call, answer=raw_command)


def test_take_item():
    """Tests if the player successfully picks up item (or ``all``) with
    ``item_name``."""
    item_name = "all"

    game = start_the_test(playtest=False, is_fake=False, character_id="PJASN",
                          location_id="RTE_PATH1")

    if item_name != "all":
        before_here = count_items_in_location(game, item_name)
    else:
        before_here = len(game.clocation()[1]["List of Items"])
    before_pack = count_items_in_backpack(game)
    game.take_item(True, (item_name))
    if item_name != "all":
        after_here = count_items_in_location(game, item_name)
        after_pack = count_items_in_backpack(game)
        assert before_here == after_here + 1
        assert before_pack == after_pack - 1
    else:
        after_here = len(game.clocation()[1]["List of Items"])
        after_pack = count_items_in_backpack(game)
        assert after_here == 0
        assert after_pack == before_pack + before_here


def count_items_in_location(game, item_name):
    item_counter = 0
    for item in game.clocation()[1]["List of Items"]:
        if item == game.get_item_from_name(item_name):
            item_counter += 1
    return item_counter


def count_items_in_backpack(game):
    item_counter = 0
    for item, amount in game.data.player["Items"].items():
        item_counter += amount
    return item_counter


def test_ci_call():
    """Tests the result of receiving ``raw_command`` (player input) in either
    the call with ``call_key`` or injected fake ``loaded_call``."""
    raw_command = "Take: all"
    call_key = "MENU_VICTORY"
    loaded_call = None

    game = start_the_test(playtest=False, is_fake=False, character_id="PJASN",
                          location_id="OXF_UNI2")
    result = simulate_ci_call(
        game, call_key=call_key, raw_command=raw_command,
        loaded_call=loaded_call)
    assert result[0].__name__ == "ci_invalid_input"
    assert result[1] == ()


if __name__ != "__main__":
    game = start_the_test(playtest=False, is_fake=False, character_id="PJASN",
                          location_id="OXF_UNI2")
    simulate_ci_call(game, call_key="GENERIC", raw_command="Take: all")
