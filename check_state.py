from game.state import GameState
import copy

# 创建正式状态
state = GameState()

# 创建工作副本
working_state = copy.deepcopy(state)

# 只修改工作副本
working_state.score = 100
working_state.board.grid[3, 4] = 1
working_state.available_pieces.append([(0, 0)])

# 检查正式状态
print("正式分数：", state.score)
print("正式棋盘：", state.board.grid[3, 4])
print("正式方块：", state.available_pieces)

# 检查工作副本
print("工作分数：", working_state.score)
print("工作棋盘：", working_state.board.grid[3, 4])
print("工作方块：", working_state.available_pieces)