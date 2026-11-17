

from .board import Board
from dataclasses import dataclass,field

@dataclass
class GameState:
    board:Board=field(default_factory=Board)
    score:int=0
    available_pieces:list=field(default_factory=list)
    game_over:bool=False