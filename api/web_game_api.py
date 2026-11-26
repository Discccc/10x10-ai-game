from fastapi import FastAPI,HTTPException
from game.schemas import StepResult
from api.schemas import CreateGameRequest,CreateGameResponse,MoveRequest,AIStepResponse
from api.game_session import create_game_session,get_game_session,get_state_snapshot,register_game_session
app=FastAPI()



@app.post(
    "/api/games",
    response_model=CreateGameResponse
    )
def create_game(request:CreateGameRequest):
    mode=request.mode
    seed=request.seed
    session=create_game_session(mode,seed)
    snapshot=get_state_snapshot(session)
    state=snapshot
    status=session.status
    game_id=session.game_id
    response=CreateGameResponse(
        game_id=game_id,
        mode=mode,
        status=status,
        state=state
    )
    register_game_session(session)
    return response


@app.get(
    "/api/games/{game_id}",
    response_model=CreateGameResponse

)
def get_game(game_id:str):
    session=get_game_session(game_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="游戏不存在"
        )

    snapshot=get_state_snapshot(session)
    state=snapshot
    mode=session.mode
    status=session.status
    game_id=session.game_id

    response=CreateGameResponse(
        game_id=game_id,
        mode=mode,
        status=status,
        state=state
    )
    return response

@app.post(
    "/api/games/{game_id}/moves",
    response_model=StepResult
)
def place_piece(game_id:str,request:MoveRequest):
    session=get_game_session(game_id=game_id)
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="游戏不存在"
            )
    if session.mode !="human":
        raise HTTPException(
            status_code=409,
            detail="模式不符合要求"
        )

    action=(request.piece_index,request.anchor_row,request.anchor_col)
    result=session.runner.step(action)

    if result.success:
        if result.state.game_over==True:
            #代表游戏结束
            session.status="finished"
        else:
            session.status="running"
    return result


@app.post(
    "/api/games/{game_id}/ai/step",
    response_model=AIStepResponse
)
def ai_step(game_id:str):
    session=get_game_session(game_id=game_id)

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="游戏对局不存在"
        )
    if session.mode not in("q_learning","llm"):
        raise HTTPException(
            status_code=409,
            detail="模式不符合要求"
            )

    snapshot=get_state_snapshot(session)
    if snapshot.game_over is True:
        session.status="finished"
        raise HTTPException(
            status_code=409,
            detail="游戏已经结束"
        )

    result = session.runner.play_step()

    step_result=result["result"]
    #获得落子后的状态
    snapshot = get_state_snapshot(session)

    if snapshot.game_over:
        session.status = "finished"

    elif step_result.success is False:
        session.status="failed"
    else:
        session.status = "running"

    return result