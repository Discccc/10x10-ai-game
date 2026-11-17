from pydantic import BaseModel,Field


class ErrorInfo(BaseModel):
    code:str=Field(min_length=1)
    message:str=Field(min_length=1)

class GameStateSnapshot(BaseModel):
    board:list[list[int]]
    score:int=Field(ge=0)
    available_pieces:  list[list[tuple[int,int]]|None]
    #三层，最内层是相对坐标组成的集合表达相对位置（元组）。第二层是由相对位置集合描述的方块（列表）。
    #第三层是三个可放置（或者None）的方块组成的方块槽位（列表）
    game_over:bool

class StepResult(BaseModel):
    success:bool
    error:ErrorInfo|None
    score_gained:int=Field(ge=0)
    cleared_rows:list[int]
    cleared_cols:list[int]
    batch_refreshed:bool
    #表示是否触发了新一批三个方块的生成
    state:GameStateSnapshot