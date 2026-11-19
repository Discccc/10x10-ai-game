from pydantic import BaseModel,ConfigDict,Field

class PlacePieceArgs(BaseModel):
    model_config=ConfigDict(
    extra="forbid",
    strict=True
    )
    piece_index:int=Field(ge=0,le=2,description="当前批次中方块的槽位索引")
    anchor_row:int=Field(ge=0,le=9,description="方块放置锚点的行坐标，从上到下为0到9")
    anchor_col:int=Field(ge=0,le=9,description="方块放置锚点的列坐标，从左到右为0到9")