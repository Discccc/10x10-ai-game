
from game.environment import GameEnvironment
from game.schemas import GameStateSnapshot
from agents.observation import format_observation


def test_format_observation():
    """测试初始状态和落子后的动态状态"""

    # 1. 创建游戏环境
    env = GameEnvironment(seed=42)

    # 2. 获取初始状态快照
    snapshot = env.get_state_snapshot()

    # 3. 生成初始 Observation
    observation = format_observation(snapshot)

    # 4. 检查初始返回结果
    assert isinstance(observation, str)
    assert "【当前棋盘】" in observation
    assert "【当前方块】" in observation
    assert "【当前分数】" in observation
    assert "【游戏状态】" in observation

    assert snapshot.score == 0
    assert snapshot.game_over is False
    assert "进行中" in observation

    print("\n========== 初始 Observation ==========")
    print(observation)

    # 5. 执行一次合法放置
    result = env.step((0, 0, 0))
    assert result.success

    # 6. 获取更新后的状态快照
    new_snapshot = env.get_state_snapshot()

    # 7. 重新生成 Observation
    new_observation = format_observation(new_snapshot)

    # 8. 检查动态状态
    assert isinstance(new_observation, str)
    assert new_snapshot.available_pieces[0] is None
    assert "槽位0：USED" in new_observation
    assert new_observation != observation
    assert "■" in new_observation

    print("\n========== 放置后的 Observation ==========")
    print(new_observation)

    print("\n初始状态与动态状态测试通过！")


def test_observation_game_over():
    """测试游戏结束状态的格式化"""

    # 1. 构造游戏结束状态快照
    snapshot = GameStateSnapshot(
        board=[[1 for _ in range(10)] for _ in range(10)],
        available_pieces=[
            [(0, 0)],
            [(0, 0), (0, 1)],
            [(0, 0), (1, 0)]
        ],
        score=100,
        game_over=True
    )

    # 2. 生成 Observation
    observation = format_observation(snapshot)

    # 3. 检查游戏结束状态
    assert isinstance(observation, str)
    assert "【游戏状态】" in observation
    assert "已结束" in observation
    assert "进行中" not in observation

    print("\n========== 游戏结束 Observation ==========")
    print(observation)

    print("\n游戏结束状态测试通过！")


if __name__ == "__main__":
    test_format_observation()
    test_observation_game_over()

    print("\n========== 所有 Observation 测试通过！ ==========")
