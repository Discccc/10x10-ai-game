from game.schemas import GameStateSnapshot

import numpy as np

def format_observation(snapshot:GameStateSnapshot)->str:
    observed_board=np.empty((10,10),dtype=str)
    for row_idx,row in enumerate(snapshot.board):
        for col_idx,cell in enumerate(row):
            if cell==0:
                observed_board[row_idx,col_idx]="□"
            else:
                observed_board[row_idx,col_idx]="■"
    rows=[]
    for row in observed_board:
        row_text=" ".join(row)
        rows.append(row_text)
    board_result="\n".join(rows)

    observed_available_pieces=[]
    for  idx,piece in enumerate(snapshot.available_pieces):

        if piece is None:
            info=f"槽位{idx}：USED"
            observed_available_pieces.append(info)
        else:
            piece_text=str(piece)
            observed_available_pieces.append(f"槽位{idx}:{piece_text}")
    piece_result="\n".join(observed_available_pieces)


    score_result=snapshot.score

    if snapshot.game_over is False:
        game_over_text="进行中"
    else:
        game_over_text="已结束"

    total_result = (
    f"【当前棋盘】\n{board_result}\n\n"
    f"【当前方块】\n{piece_result}\n\n"
    f"【当前分数】\n{score_result}\n\n"
    f"【游戏状态】\n{game_over_text}"
    )
    return total_result