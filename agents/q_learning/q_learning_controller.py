
import json
from pathlib import Path

import numpy as np

from game.environment import GameEnvironment
from agents.q_learning.linear_q_agent import LinearQAgent
from agents.q_learning.linear_q_trainer import LinearQTrainer
from experiments.logger import ExperimentLogger


class QLearningController:

    def __init__(
        self,
        training_seed=42,
        output_dir="outputs/experiments",
        agent_params=None
    ):
        self.training_seed = training_seed
        self.output_dir = output_dir

        agent_params = agent_params or {}

        # Q-learning 算法
        self.agent = LinearQAgent(**agent_params)

        # 训练相关组件
        self.trainer = None
        self.logger = None

        # 游玩使用独立的游戏环境
        self.play_environment = None

        # 累计训练进度
        self.total_steps = 0
        self.total_episodes = 0

    # ==================================
    # 一、训练功能（仅本地调用）
    # ==================================

    def _get_trainer(self):
        """获取训练器，首次调用时创建"""

        if self.trainer is None:

            environment = GameEnvironment(
                seed=self.training_seed
            )

            self.logger = ExperimentLogger(
                output_dir=self.output_dir,
                seed=self.training_seed,
                feature_names=(
                    self.agent.feature_extractor.FEATURE_NAMES
                )
            )

            self.trainer = LinearQTrainer(
                environment=environment,
                agent=self.agent,
                logger=self.logger
            )

            # 恢复已经累计的训练进度
            self.trainer.total_steps = self.total_steps
            self.trainer.total_episodes = self.total_episodes

        return self.trainer

    def train(self, episodes: int):
        """训练指定局数，保留现有权重"""

        if type(episodes) is not int or episodes <= 0:
            raise ValueError("episodes 必须是正整数")

        trainer = self._get_trainer()

        last_result = None

        for _ in range(episodes):

            last_result = trainer.train_episode()

            print(
                f"Episode {last_result['episode']} | "
                f"Score: {last_result['final_score']} | "
                f"Steps: {last_result['episode_steps']} | "
                f"Epsilon: {last_result['epsilon_end']:.6f}"
            )

        self.total_steps = trainer.total_steps
        self.total_episodes = trainer.total_episodes

        return {
            "trained_episodes": episodes,
            "total_episodes": self.total_episodes,
            "total_steps": self.total_steps,
            "last_episode": last_result,
            "run_id": self.logger.run_id,
            "episodes_file": str(self.logger.episodes_file),
            "q_steps_file": str(self.logger.q_steps_file)
        }

    # ==================================
    # 二、模型保存和加载
    # ==================================

    def save_checkpoint(self, path):
        """原子保存权重、超参数和累计训练进度"""

        if self.trainer is not None:
            self.total_steps = self.trainer.total_steps
            self.total_episodes = self.trainer.total_episodes

        checkpoint = {
            "version": 1,

            "feature_names": list(
                self.agent.feature_extractor.FEATURE_NAMES
            ),

            "weights": self.agent.weights.tolist(),

            "agent_params": {
                "epsilon_start": self.agent.epsilon_start,
                "epsilon_min": self.agent.epsilon_min,
                "epsilon_decay_steps": self.agent.epsilon_decay_steps,
                "gamma": self.agent.gamma,
                "learning_rate": self.agent.learning_rate
            },

            "training_progress": {
                "total_steps": self.total_steps,
                "total_episodes": self.total_episodes
            }
        }

        file_path = Path(path)

        # 1. 提前完成 JSON 序列化
        content = json.dumps(
            checkpoint,
            ensure_ascii=False,
            indent=2,
            allow_nan=False
        )

        # 2. 确保模型保存目录存在
        file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        # 3. 构造同目录临时文件路径
        temp_path = file_path.with_suffix(
            file_path.suffix + ".tmp"
        )

        # 4. 将模型完整写入临时文件
        with temp_path.open(
            "w",
            encoding="utf-8"
        ) as file:
            file.write(content)

        # 5. 原子替换正式模型文件
        temp_path.replace(file_path)

        return str(file_path)

    def load_checkpoint(self, path):
        """加载已经保存的 Q-learning 模型"""

        file_path = Path(path)

        with file_path.open(
            "r",
            encoding="utf-8"
        ) as file:
            checkpoint = json.load(file)

        if checkpoint.get("version") != 1:
            raise ValueError("不支持的 Checkpoint 版本")

        # 检查特征是否与当前代码一致
        expected_features = list(
            self.agent.feature_extractor.FEATURE_NAMES
        )

        if checkpoint["feature_names"] != expected_features:
            raise ValueError("Checkpoint 特征定义不匹配")

        # 使用保存的超参数创建 Agent
        agent = LinearQAgent(
            **checkpoint["agent_params"]
        )

        weights = np.asarray(
            checkpoint["weights"],
            dtype=float
        )

        if (
            weights.shape != agent.weights.shape
            or not np.isfinite(weights).all()
        ):
            raise ValueError("Checkpoint 权重数据无效")

        progress = checkpoint["training_progress"]

        total_steps = progress["total_steps"]
        total_episodes = progress["total_episodes"]

        if (
            type(total_steps) is not int
            or type(total_episodes) is not int
            or total_steps < 0
            or total_episodes < 0
        ):
            raise ValueError("Checkpoint 训练进度无效")

        agent.weights = weights.copy()

        self.agent = agent
        self.total_steps = total_steps
        self.total_episodes = total_episodes

        # 训练器下次使用时重新绑定 Agent
        self.trainer = None
        self.logger = None

        # 加载新模型后，要求重新开始游玩
        self.play_environment = None

        return {
            "total_steps": self.total_steps,
            "total_episodes": self.total_episodes,
            "weights": self.agent.weights.tolist()
        }

    # ==================================
    # 三、模型推理与游玩功能
    # ==================================

    def new_game(self, seed=None):
        """创建一局独立的 Q-learning 游戏"""

        self.play_environment = GameEnvironment(
            seed=seed
        )

        return self.play_environment.get_state_snapshot()

    def get_state(self):
        """获取当前游戏状态"""

        if self.play_environment is None:
            raise RuntimeError("请先调用 new_game()")

        return self.play_environment.get_state_snapshot()

    def play_step(self):
        """AI 执行一步，不更新 Q-learning 权重"""

        action=self.decide()

        result = self.execute(action)

        return {
            "action": {
                "piece_index": int(action[0]),
                "anchor_row": int(action[1]),
                "anchor_col": int(action[2])
            },
            "result": result
        }

    def decide(self):
        if self.play_environment is None:
            raise RuntimeError("请先调用 new_game()")

        state = self.play_environment.game_state

        if state.game_over:
            raise RuntimeError("游戏已经结束")

        legal_actions = (
            self.play_environment.get_legal_actions(state)
        )

        if not legal_actions:
            raise RuntimeError("当前没有合法动作")

        # 游玩阶段只选择 Q 值最高的动作
        action = self.agent.get_greedy_action(
            state,
            legal_actions
        )
        return action

    def execute(self,action):
        if self.play_environment is None:
            raise RuntimeError("请先调用 new_game()")
        result = self.play_environment.step(action)

        if not result.success:
            raise RuntimeError(
                f"Q-learning 落子失败：{result.error}"
                )
        return result


    def run_game(self):
        """自动运行完整一局游戏，不更新 Q-learning 权重"""

        if self.play_environment is None:
            raise RuntimeError("请先调用 new_game()")

        results = []

        while not self.play_environment.game_state.game_over:

            # 复用已有的单步游玩接口
            step_result = self.play_step()

            # 保存每一步的动作及执行结果
            results.append(step_result)

        return {
            "final_score": self.play_environment.game_state.score,
            "total_steps": len(results),
            "game_over": self.play_environment.game_state.game_over,
            "steps": results
        }