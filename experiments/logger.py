
import csv
from pathlib import Path
from datetime import datetime
from uuid import uuid4


class ExperimentLogger:

    # 当前 Linear Q-learning 的六个特征
    FEATURE_NAMES = (
        "bias",
        "piece_size",
        "cleared_lines",
        "board_occupancy",
        "near_full_rows",
        "near_full_cols"
    )

    # 每局游戏的统计字段
    EPISODE_FIELDS = [
        "timestamp",
        "run_id",
        "game_id",
        "agent_type",
        "phase",
        "episode",
        "seed",
        "episode_steps",
        "pieces_placed",
        "episode_reward",
        "final_score",
        "rows_cleared",
        "cols_cleared",
        "total_lines_cleared",
        "epsilon_start",
        "epsilon_end",
        "total_steps",
        "game_over",
        "episode_duration_ms"
    ]

    # Q-learning 每一步的统计字段
    Q_STEP_BASE_FIELDS = [
        "timestamp",
        "run_id",
        "game_id",
        "agent_type",
        "phase",
        "episode",
        "step_in_episode",
        "total_steps",
        "piece_index",
        "anchor_row",
        "anchor_col",
        "reward",
        "epsilon",
        "current_q",
        "td_target",
        "td_error",
        "done",
        "step_duration_ms"
    ]

    # LLM API 请求统计字段
    LLM_CALL_FIELDS = [
        "timestamp",
        "run_id",
        "game_id",
        "agent_type",
        "step_in_episode",
        "provider",
        "model",
        "latency_ms",
        "prompt_tokens",
        "completion_tokens",
        "total_tokens",
        "retry_count",
        "success"
    ]

    def __init__(
        self,
        output_dir="outputs/experiments",
        seed=None,
        feature_names=None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        # 每次实验运行生成一个独立 ID
        self.run_id = uuid4().hex

        self.seed = seed

        if feature_names is None:
            feature_names = self.FEATURE_NAMES

        self.feature_names = tuple(feature_names)

        # 动态生成六个特征及其权重字段
        self.q_step_fields = (
            self.Q_STEP_BASE_FIELDS
            + [f"feature_{name}" for name in self.feature_names]
            + [f"weight_before_{name}" for name in self.feature_names]
            + [f"weight_after_{name}" for name in self.feature_names]
        )

        self.episodes_file = (
            self.output_dir / "episodes.csv"
        )

        self.q_steps_file = (
            self.output_dir / "q_learning_steps.csv"
        )

        self.llm_calls_file = (
            self.output_dir / "llm_calls.csv"
        )

    @staticmethod
    def get_timestamp():
        return datetime.now().astimezone().isoformat(
            timespec="seconds"
        )

    @staticmethod
    def new_game_id():
        return uuid4().hex

    @staticmethod
    def _append_csv(file_path, fieldnames, data):
        """追加一行 CSV 数据，不覆盖原有记录"""

        is_new_file = (
            not file_path.exists()
            or file_path.stat().st_size == 0
        )

        # 第一次创建时使用 BOM，方便 Excel 识别 UTF-8
        encoding = "utf-8-sig" if is_new_file else "utf-8"

        with file_path.open(
            "a",
            newline="",
            encoding=encoding
        ) as file:

            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore"
            )

            if is_new_file:
                writer.writeheader()

            writer.writerow({
                field: data.get(field, "")
                for field in fieldnames
            })

    def log_episode(
        self,
        game_id,
        agent_type,
        phase,
        episode,
        **metrics
    ):
        """保存一局游戏的汇总数据"""

        data = {
            "timestamp": self.get_timestamp(),
            "run_id": self.run_id,
            "game_id": game_id,
            "agent_type": agent_type,
            "phase": phase,
            "episode": episode,
            "seed": self.seed,
            **metrics
        }

        self._append_csv(
            self.episodes_file,
            self.EPISODE_FIELDS,
            data
        )

    def log_q_learning_step(
        self,
        game_id,
        episode,
        step_in_episode,
        total_steps,
        interaction,
        step_duration_ms
    ):
        """保存 Q-learning 每一步的学习数据"""

        learning = interaction["learning_result"]

        features = learning["features"]
        weights_before = learning["weights_before"]
        weights_after = learning["weights_after"]

        action = interaction["action"]

        if not (
            len(features)
            == len(weights_before)
            == len(weights_after)
            == len(self.feature_names)
        ):
            raise ValueError("Feature 与 Weight 维度不一致")

        data = {
            "timestamp": self.get_timestamp(),
            "run_id": self.run_id,
            "game_id": game_id,
            "agent_type": "q_learning",
            "phase": "train",
            "episode": episode,
            "step_in_episode": step_in_episode,
            "total_steps": total_steps,
            "piece_index": action[0],
            "anchor_row": action[1],
            "anchor_col": action[2],
            "reward": interaction["reward"],
            "epsilon": interaction["epsilon"],
            "current_q": learning["current_q"],
            "td_target": learning["td_target"],
            "td_error": learning["td_error"],
            "done": interaction["done"],
            "step_duration_ms": step_duration_ms
        }

        # 记录特征、更新前权重、更新后权重
        for name, feature, old, new in zip(
            self.feature_names,
            features,
            weights_before,
            weights_after
        ):
            data[f"feature_{name}"] = float(feature)
            data[f"weight_before_{name}"] = float(old)
            data[f"weight_after_{name}"] = float(new)

        self._append_csv(
            self.q_steps_file,
            self.q_step_fields,
            data
        )

    def log_llm_call(
        self,
        game_id,
        step_in_episode,
        provider,
        model,
        latency_ms,
        prompt_tokens=None,
        completion_tokens=None,
        total_tokens=None,
        retry_count=0,
        success=True
    ):
        """保存一次 LLM API 请求的数据"""

        data = {
            "timestamp": self.get_timestamp(),
            "run_id": self.run_id,
            "game_id": game_id,
            "agent_type": "deepseek",
            "step_in_episode": step_in_episode,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "retry_count": retry_count,
            "success": success
        }

        self._append_csv(
            self.llm_calls_file,
            self.LLM_CALL_FIELDS,
            data
        )
