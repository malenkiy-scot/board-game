"""
This module implements the following multi-player board game:

The board is a directed graph with at least one starting pointand at least one finishing point.  Each player starts in
one of the starting points.  A player rolls the dice and can move the number of steps that he rolled.  The winner is
the player who lands first on one of the finishing squares.

In the beginning each player has 0 or more mines.  When moving he may leave the mines on the squares he is moving
through (including the initial square, but excluding the final square).

When moving a player can't step on a square where another player is currently located.  If there is a turn-off RIGHT
BEFORE that square he must take it, otherwise he must stop one step before the square where another player is located.

If while moving a player steps on a mine he must stop on that square.  In one version of the rules he may take the mine
and use it later, in another the mine is removed from the game.

The initial implementation is console I/O based.  Eventually, the implementation should accommodate GUI and the game
could be played over the Internet.
"""

import controller


class Game(object):
    instance = None

    @classmethod
    def create_game(cls, config):
        if cls.instance is None:
            cls.instance = Game(config)
        return cls.instance

    def __init__(self, config):
        self.board = None
        self.rules = None
        self.players = None
        self.game_state = None
        self.main_controller = None
        self.set_up(config)

    def start_game(self):
        while not self.game_state.is_game_over():
            event = self.game_state.next_event_to_queue()
            self.main_controller.enqueue_event(event)
            self.main_controller.process_events()

    def set_up(self, config):
        self.rules = Rules(config)
        self.players = self.create_players(config)
        self.board = self.create_board(config)
        self.game_state = self.create_game_state()
        self.main_controller = GameController(self)

    def stop_game(self):
        # TODO: implement this
        pass

    def pause_game(self):
        # TODO: implement
        pass


class Rules(object):
    # TODO: flesh this class out
    def __init__(self, config=None):
        # TODO: implement this
        pass


class GameController(controller.Controller):
    def __init__(self, game):
        controller.Controller.__init__(self)
