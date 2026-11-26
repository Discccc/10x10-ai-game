from pydantic import BaseModel,Field
from typing import Literal
from game.schemas import GameStateSnapshot,StepResult

GameModel=Literal["human","q_learning","llm"]

class CreateGameRequest(BaseModel):
    mode:GameModel
    seed : int |None=None



class CreateGameResponse(BaseModel):
    game_id:str=Field(min_length=1)
    mode: GameModel
    state:GameStateSnapshot
    status:str

class MoveRequest(BaseModel):
    piece_index:int =Field(ge=0,le=2)
    anchor_row:int=Field(ge=0,le=9)
    anchor_col:int=Field(ge=0,le=9)


class AIStepResponse(BaseModel):
    action:MoveRequest
    result:StepResult