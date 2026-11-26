from dataclasses import dataclass
from game.environment import GameEnvironment
from agents.q_learning.q_learning_controller import QLearningController
import uuid
from game.schemas import GameStateSnapshot
from agents.llm.llm_controller import LLMController
from agents.llm.llm_client import LLMClient
from typing import Literal
@dataclass
class GameSession:
    game_id: str
    mode: str
    runner: object
    status: Literal[
                    "ready",
                    "running",
                    "finished",
                    "failed",
                                 ]="ready"

games={}


def get_game_session(game_id):
    return games.get(game_id,None)


#适配三种模式中获取状态快照的接口
def get_state_snapshot(session:GameSession) ->GameStateSnapshot:
    if session.mode=="human":
        return session.runner.get_state_snapshot()
    elif session.mode=="q_learning":
        return session.runner.get_state()
    elif session.mode=="llm":
        return session.runner.get_state()
    else:
        raise ValueError(
            "接口不存在"
        )




def create_game_session(mode,seed=None):
    if mode=="human":
        env=GameEnvironment(seed=seed)
        runner=env


    elif mode=="q_learning":
        controller=QLearningController()
        controller.load_checkpoint("outputs/models/q_learning.json")
        controller.new_game(seed=seed)
        runner=controller



    elif mode=="llm":
        llmclient=LLMClient()
        llmcontroller=LLMController(llmclient)

        llmcontroller.new_game(seed=seed)
        runner=llmcontroller
    else:
        raise ValueError("不支持的游戏模式")



    #统一创建会话
    game_id=str(uuid.uuid4())
    session=GameSession(
        game_id=game_id,mode=mode,
        runner=runner
    )
    return session


def register_game_session(session:GameSession):
    games[session.game_id]=session