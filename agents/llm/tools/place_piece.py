from .schemas import PlacePieceArgs
from .base import BaseTool
from game.environment import GameEnvironment
from game.schemas import StepResult

class PlacePieceTool(BaseTool):
    name="place_piece"
    description="在棋盘上指定位置放置一个方块"
    args_schema=PlacePieceArgs



    def __init__(self,env:GameEnvironment):
        self.environment=env


    def execute(self,validated_args:PlacePieceArgs)->StepResult:
        piece_index=validated_args.piece_index
        anchor_row=validated_args.anchor_row
        anchor_col=validated_args.anchor_col
        action= (piece_index,anchor_row,anchor_col)
        return self.environment.step(action)
