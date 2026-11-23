
from game.environment import GameEnvironment
from agents.q_learning.linear_q_agent import LinearQAgent
from agents.q_learning.linear_q_trainer import LinearQTrainer
from experiments.logger import ExperimentLogger


def main():

    # 实验参数
    seed = 42
    num_episodes = 5

    # 1. 初始化游戏环境
    environment = GameEnvironment(seed=seed)

    # 2. 初始化 Q-learning Agent
    agent = LinearQAgent()

    # 3. 初始化数据收集器
    logger = ExperimentLogger(
        output_dir="outputs/experiments",
        seed=seed,
        feature_names=agent.feature_extractor.FEATURE_NAMES
    )

    # 4. 初始化 Trainer
    trainer = LinearQTrainer(
        environment=environment,
        agent=agent,
        logger=logger
    )

    print("========== Q-learning 实验开始 ==========")
    print("Run ID:", logger.run_id)
    print("训练局数:", num_episodes)

    # 5. 连续训练
    for _ in range(num_episodes):

        result = trainer.train_episode()

        print(
            f"Episode {result['episode']} | "
            f"Score: {result['final_score']} | "
            f"Steps: {result['episode_steps']} | "
            f"Reward: {result['episode_reward']} | "
            f"Epsilon: {result['epsilon_end']:.6f}"
        )

    print("\n========== 实验结束 ==========")

    print("Total Episodes:", trainer.total_episodes)
    print("Total Steps:", trainer.total_steps)

    print("\n数据保存位置:")
    print(logger.episodes_file)
    print(logger.q_steps_file)


if __name__ == "__main__":
    main()
