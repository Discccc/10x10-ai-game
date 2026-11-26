
from pathlib import Path
from datetime import datetime

import numpy as np

from agents.q_learning.q_learning_controller import QLearningController


# ==============================
# 一、训练配置
# ==============================

EPISODES = 5000
TRAINING_SEED = 42

# 每训练多少局保存一次模型
SAVE_INTERVAL = 50

# 是否加载已有模型继续训练
RESUME_TRAINING = True

CHECKPOINT_PATH = "outputs/models/q_learning.json"
OUTPUT_DIR ="outputs/experiments/formal_train_03"

# ==============================
# 二、算法超参数
# ==============================

AGENT_PARAMS = {
    "epsilon_start": 1.0,
    "epsilon_min": 0.01,
    "epsilon_decay_steps": 10000,
    "gamma": 0.95,
    "learning_rate": 0.01
}


# ==============================
# 三、训练入口
# ==============================

def main():

    # 检查训练配置
    if type(EPISODES) is not int or EPISODES <= 0:
        raise ValueError("EPISODES 必须是正整数")

    if type(SAVE_INTERVAL) is not int or SAVE_INTERVAL <= 0:
        raise ValueError("SAVE_INTERVAL 必须是正整数")

    # 设置 NumPy 随机种子
    np.random.seed(TRAINING_SEED)

    # 为本次实验创建独立的日志目录
    run_time = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    experiment_dir = Path(OUTPUT_DIR) / run_time

    checkpoint_path = Path(CHECKPOINT_PATH)

    # 避免从零训练时覆盖已有模型
    if not RESUME_TRAINING and checkpoint_path.exists():
        raise FileExistsError(
            "模型文件已经存在。"
            "请修改 CHECKPOINT_PATH，"
            "或者设置 RESUME_TRAINING = True"
        )

    controller = QLearningController(
        training_seed=TRAINING_SEED,
        output_dir=str(experiment_dir),
        agent_params=AGENT_PARAMS
    )

    # 加载历史模型
    if RESUME_TRAINING:

        if not checkpoint_path.exists():
            raise FileNotFoundError(
                f"找不到需要继续训练的模型: {checkpoint_path}"
            )

        controller.load_checkpoint(checkpoint_path)

        print("已加载历史模型")

    else:
        print("从零开始训练")

    # 输出实际训练配置
    print("\n========== 训练配置 ==========")

    print("本次训练局数:", EPISODES)
    print("随机种子:", TRAINING_SEED)
    print("保存间隔:", SAVE_INTERVAL)
    print("是否继续训练:", RESUME_TRAINING)
    print("已有训练局数:", controller.total_episodes)
    print("已有训练步数:", controller.total_steps)
    print("模型路径:", checkpoint_path)
    print("实验目录:", experiment_dir)

    print("\n实际生效的算法超参数:")

    print("epsilon_start:", controller.agent.epsilon_start)
    print("epsilon_min:", controller.agent.epsilon_min)
    print("epsilon_decay_steps:", controller.agent.epsilon_decay_steps)
    print("gamma:", controller.agent.gamma)
    print("learning_rate:", controller.agent.learning_rate)

    print("\n========== 开始训练 ==========")

    trained_episodes = 0

    # 分批训练与定期保存
    while trained_episodes < EPISODES:

        batch_size = min(
            SAVE_INTERVAL,
            EPISODES - trained_episodes
        )

        result = controller.train(
            episodes=batch_size
        )

        path = controller.save_checkpoint(
            checkpoint_path
        )

        trained_episodes += batch_size

        print(
            f"\n训练进度: "
            f"{trained_episodes}/{EPISODES} | "
            f"{trained_episodes / EPISODES:.2%}"
        )

        print("Checkpoint 保存成功:", path)
        print()

    # 最终训练结果
    print("\n========== 训练完成 ==========")

    print("本次训练局数:", trained_episodes)
    print("累计训练局数:", result["total_episodes"])
    print("累计训练步数:", result["total_steps"])
    print("模型保存路径:", path)
    print("实验编号:", result["run_id"])
    print("局级数据:", result["episodes_file"])
    print("步级数据:", result["q_steps_file"])
    print("最终模型权重:", controller.agent.weights)


if __name__ == "__main__":
    main()
