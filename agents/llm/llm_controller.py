from game.environment import GameEnvironment
from agents.llm.llm_agent import LLMAgent


class LLMController:

    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.environment = None
        self.agent = None

    def new_game(self, seed=None):
        self.environment = GameEnvironment(seed=seed)

        self.agent = LLMAgent(
            llmclient=self.llm_client,
            env=self.environment
        )

        return self.environment.get_state_snapshot()


    def get_state(self):
        if self.environment is None:
            raise RuntimeError("请先调用 new_game()")

        return self.environment.get_state_snapshot()

    def play_step(self):
        if self.agent is None:
            raise RuntimeError("请先调用 new_game()")
        return self.agent.play_step()

    def decide(self):
        if self.agent is None:
            raise RuntimeError("请先调用 new_game()")

        return self.agent.decide()

    def execute(self,validated_args):
        if self.agent is None:
            raise RuntimeError("请先调用 new_game()")

        return self.agent.execute(validated_args)