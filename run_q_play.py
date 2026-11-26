

import time

from agents.q_learning.q_learning_controller import QLearningController


# ==============================
# 游玩配置
# ==============================

SEED = 42
CHECKPOINT_PATH = "outputs/models/q_learning.json"

# 每次落子后的展示延迟（秒）
PLAY_DELAY = 0.5

# 是否刷新终端画面
CLEAR_SCREEN = True


def render_game(snapshot, steps, action=None, score_gained=0):

    if CLEAR_SCREEN:
        print("\033[2J\033[H", end="", flush=True)

    print("=" * 50)
    print("              10 × 10 AI GAME")
    print("               Q-learning")
    print("=" * 50)

    print(f"随机种子: {SEED}")
    print(f"当前得分: {snapshot.score}")
    print(f"当前步数: {steps}")
    print(f"本步得分: +{score_gained}")

    # 绘制棋盘
    print("\n棋盘:")
    print("    " + " ".join(str(i) for i in range(10)))
    print("   +" + "-" * 21 + "+")

    for index, row in enumerate(snapshot.board):

        cells = [
            "#" if cell else "."
            for cell in row
        ]

        print(f" {index} | " + " ".join(cells) + " |")

    print("   +" + "-" * 21 + "+")

    # 绘制三个方块
    print("\n剩余方块:")

    piece_views = []

    for piece in snapshot.available_pieces:

        view = ["       " for _ in range(4)]

        if piece is None:
            view[1] = " Used  "

        else:
            cells = set(map(tuple, piece))

            view = [
                " ".join(
                    "#" if (r, c) in cells else " "
                    for c in range(4)
                )
                for r in range(4)
            ]

        piece_views.append(view)

    print()
    print("Piece 0     Piece 1     Piece 2")

    for r in range(4):
        print("     ".join(
            view[r] for view in piece_views
        ))

    # 最近一次动作
    if action is not None:
        print(
            f"\n最近动作: Piece {action['piece_index']} "
            f"-> ({action['anchor_row']}, "
            f"{action['anchor_col']})"
        )

    # 游戏状态
    if snapshot.game_over:
        print("\n状态: 游戏结束")
    else:
        print("\n状态: 游戏进行中")

    print("=" * 50)


def main():

    controller = QLearningController()

    controller.load_checkpoint(CHECKPOINT_PATH)

    snapshot = controller.new_game(seed=SEED)

    steps = 0

    # 展示初始棋盘
    render_game(snapshot, steps)

    time.sleep(PLAY_DELAY)

    # 自动游玩
    while not snapshot.game_over:

        data = controller.play_step()

        action = data["action"]
        result = data["result"]

        if not result.success:
            print("落子失败:", result.error)
            break

        steps += 1

        snapshot = result.state

        render_game(
            snapshot=snapshot,
            steps=steps,
            action=action,
            score_gained=result.score_gained
        )

        time.sleep(PLAY_DELAY)

    # 最终结果
    print("\n========== 游戏结果 ==========")
    print("游戏模式: Q-learning")
    print("最终得分:", snapshot.score)
    print("总步数:", steps)
    print("是否正常结束:", snapshot.game_over)


if __name__ == "__main__":
    main()
