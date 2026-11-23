from game.environment import GameEnvironment
from agents.q_learning.linear_q_agent import LinearQAgent
import time
from experiments.logger import ExperimentLogger

class LinearQTrainer:

    def __init__(
    self,
    environment: GameEnvironment,
    agent: LinearQAgent,
    logger: ExperimentLogger | None = None
    ):
        self.environment = environment
        self.agent = agent
        self.logger = logger

        self.total_steps = 0
        self.total_episodes = 0


    def interact_once(self):
        state=self.environment.game_state
        legal_action=self.environment.get_legal_actions(state)

        if not legal_action:
            raise RuntimeError("当前没有合法动作")

        epsilon=self.agent.get_epsilon(self.total_steps)
        action=self.agent.select_action(state,legal_action,epsilon)
        result=self.environment.step(action)

        if not result.success:
            raise RuntimeError(f"动作执行失败：{result.error}")

        #训练过程累计步数+1
        self.total_steps+=1

        next_state=self.environment.game_state
        done=next_state.game_over

        if done:
            next_legal_actions=[]
        else:
            next_legal_actions=self.environment.get_legal_actions(next_state)


        return {
            "state":state,
            "action":action,
            "reward":result.score_gained,
            "next_state":next_state,
            "next_legal_actions":next_legal_actions,
            "done":done,
            "epsilon":epsilon,
            "result":result
        }

    def train_once(self):

        interaction=self.interact_once()
        state = interaction["state"]
        action = interaction["action"]
        reward = interaction["reward"]
        next_state = interaction["next_state"]
        next_legal_actions = interaction["next_legal_actions"]
        done = interaction["done"]

        learn_result=self.agent.learn(
            state,
            action,
            reward,
            next_state,
            next_legal_actions,
            done
        )
        return {
            **interaction,
            "learning_result":learn_result
        }



    def train_episode(self):

        # 1. 重置环境
        self.environment.reset()

        episode_number = self.total_episodes + 1

        # 为本局生成唯一 ID
        game_id = (
            self.logger.new_game_id()
            if self.logger else None
        )

        episode_start_time = time.perf_counter()

        # 2. 初始化本局统计数据
        episode_steps = 0
        episode_reward = 0

        total_rows_cleared = 0
        total_cols_cleared = 0

        epsilon_start = None
        epsilon_end = None

        done = False

        # 3. 持续训练直到游戏结束
        while not done:

            step_start_time = time.perf_counter()

            step_result = self.train_once()

            step_duration_ms = (
                time.perf_counter() - step_start_time
            ) * 1000

            # 更新本局统计
            episode_steps += 1

            episode_reward += step_result["reward"]

            done = step_result["done"]

            # 记录 Epsilon 的变化范围
            epsilon = step_result["epsilon"]

            if epsilon_start is None:
                epsilon_start = epsilon

            epsilon_end = epsilon

            # 统计消除的行列数量
            game_result = step_result["result"]

            total_rows_cleared += len(
                game_result.cleared_rows
            )

            total_cols_cleared += len(
                game_result.cleared_cols
            )

            # 4. 自动保存每一步的 Q-learning 数据
            if self.logger is not None:

                self.logger.log_q_learning_step(
                    game_id=game_id,
                    episode=episode_number,
                    step_in_episode=episode_steps,
                    total_steps=self.total_steps,
                    interaction=step_result,
                    step_duration_ms=step_duration_ms
                )

        # 5. 本局结束，更新全局局数
        self.total_episodes += 1

        # 从真实游戏环境获取最终得分
        final_score = self.environment.game_state.score

        episode_duration_ms = (
            time.perf_counter() - episode_start_time
        ) * 1000

        # 6. 整理本局数据
        episode_result = {
            "episode": self.total_episodes,
            "game_id": game_id,
            "episode_steps": episode_steps,
            "pieces_placed": episode_steps,
            "episode_reward": episode_reward,
            "final_score": final_score,
            "rows_cleared": total_rows_cleared,
            "cols_cleared": total_cols_cleared,
            "total_lines_cleared": (
                total_rows_cleared + total_cols_cleared
            ),
            "epsilon_start": epsilon_start,
            "epsilon_end": epsilon_end,
            "total_steps": self.total_steps,
            "game_over": done,
            "episode_duration_ms": episode_duration_ms
        }

        # 7. 自动保存本局汇总数据
        if self.logger is not None:

            self.logger.log_episode(
                agent_type="q_learning",
                phase="train",
                **episode_result
            )

        return episode_result
