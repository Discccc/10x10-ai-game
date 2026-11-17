from .state import GameState
from .piece_generator import PieceGenerator
from .schemas import GameStateSnapshot,StepResult,ErrorInfo
import copy


class GameEnvironment:
    def __init__(self,seed=None):
        self.seed=seed
        self.piecegenerator=PieceGenerator(seed=self.seed)
        self.game_state=self._create_initial_state(self.piecegenerator)

    def is_valid_piece_index(self,piece_index):
        if type(piece_index) is not int:
            return False

        if piece_index>len(self.game_state.available_pieces)-1 or piece_index<0:
            return False

        if   self.game_state.available_pieces[piece_index]  is None:
            return False

        return True


    def calculate_score(self,cleared_rows,cleared_cols):
        rows=len(cleared_rows)
        cols=len(cleared_cols)
        return 100*(rows+cols)



    def has_any_valid_move(self,state:GameState):
        #游戏结束测试

        for row in range(0,10):
            for col in range(0,10):
                for piece in state.available_pieces:
                    if piece  is not None and state.board.can_place(piece,row,col):
                        return True
        return False

    def step(self,action):
        if self.game_state.game_over :
            return StepResult(
                success=False,
                error=ErrorInfo(
                    code="game_already_over",
                    message="游戏已经结束，无法继续放置"
                ),
                score_gained=0,
                cleared_rows=[],
                cleared_cols=[],
                batch_refreshed=False,
                state=self.get_state_snapshot()
            )

        if type(action)is not tuple or len(action)!=3:
            return StepResult(
                success=False,
                error=ErrorInfo(
                    code="invalid_action_format",
                    message="action格式有问题，请重新检查"
                ),
                score_gained=0,
                cleared_rows=[],
                cleared_cols=[],
                batch_refreshed=False,
                state=self.get_state_snapshot()
            )

        piece_index,anchor_row,anchor_col=action
        if type(piece_index) is not  int or type(anchor_row) is not int or type(anchor_col) is not int:
            return StepResult(
                success=False,
                error=ErrorInfo(
                    code="invalid_action_type",
                    message="piece_index、anchor_row 和 anchor_col 必须都是整数"
                ),
                score_gained=0,
                cleared_rows=[],
                cleared_cols=[],
                batch_refreshed=False,
                state=self.get_state_snapshot()
            )

        if not self.is_valid_piece_index(piece_index):
             return StepResult(
                success=False,
                error=ErrorInfo(
                    code="invalid_piece_index",
                    message="方块索引无效或对应槽位已经使用"
                ),
                score_gained=0,
                cleared_rows=[],
                cleared_cols=[],
                batch_refreshed=False,
                state=self.get_state_snapshot()
            )

        if not self.game_state.board.can_place(
            self.game_state.available_pieces[piece_index],
            anchor_row,
            anchor_col
            ):
            return StepResult(
                success=False,
                error=ErrorInfo(
                    code="invalid_position",
                    message="该位置不可放置"
                ),
                score_gained=0,
                cleared_rows=[],
                cleared_cols=[],
                batch_refreshed=False,
                state=self.get_state_snapshot()
            )

        working_state=copy.deepcopy(self.game_state)
        working_generator=copy.deepcopy(self.piecegenerator)
        result=self._execute_action(working_state,working_generator,action)
        (score_gained,cleared_rows,cleared_cols,batch_refreshed)=result
        self.game_state=working_state
        self.piecegenerator=working_generator

        return StepResult(
            success=True,
            error=None,
            score_gained=score_gained,
            cleared_rows=cleared_rows,
            cleared_cols=cleared_cols,
            batch_refreshed=batch_refreshed,
            state=self.get_state_snapshot()
        )

    def _execute_action(self,working_state:GameState,working_generator:PieceGenerator,action):
        piece_index,anchor_row,anchor_col=action

        piece=working_state.available_pieces[piece_index]
        working_state.board.place_piece(piece,anchor_row,anchor_col)
        (affected_rows,affected_cols)=working_state.board.get_affected_lines(piece,anchor_row,anchor_col)
        cleared_rows,cleared_cols=working_state.board.clear_lines(affected_rows,affected_cols)

        score_gained=self.calculate_score(cleared_rows,cleared_cols)
        working_state.score+=score_gained
        working_state.available_pieces[piece_index]=None

        None_count=0
        batch_refreshed=False
        for i in working_state.available_pieces :
            if i is None:
                None_count+=1

        if None_count==3:
            working_state.available_pieces=working_generator.generate_batch(count=3)
            batch_refreshed=True

        working_state.game_over= not self.has_any_valid_move(working_state)
        return (score_gained,
                cleared_rows,
                cleared_cols,
                batch_refreshed)

    def _create_initial_state(self,generator:PieceGenerator)->GameState:
        state=GameState()
        pieces=generator.generate_batch(count=3)
        state.available_pieces=pieces
        return state

    def get_state_snapshot(self):
        snapshot=GameStateSnapshot(
        board=self.game_state.board.grid.tolist(),
        score=self.game_state.score,
        available_pieces=copy.deepcopy(self.game_state.available_pieces),
        game_over=self.game_state.game_over,
        )
        return snapshot

    def reset(self):
        copied_piecegenerator=copy.deepcopy(self.piecegenerator)
        reset_game_state=self._create_initial_state(copied_piecegenerator)
        self.game_state=reset_game_state
        self.piecegenerator=copied_piecegenerator
        return self.get_state_snapshot()




if __name__ == "__main__":
    env = GameEnvironment(seed=42)

    # 1. 棋盘全部填满
    env.game_state.board.grid[:, :] = 1

    # 2. 留出三个互不相邻的空格
    env.game_state.board.grid[0, 0] = 0
    env.game_state.board.grid[0, 5] = 0
    env.game_state.board.grid[5, 0] = 0

    # 3. 设置三个方块
    env.game_state.available_pieces = [
        [(0, 0)],                 # 单格方块
        [(0, 0), (0, 1)],         # 横向两格
        [(0, 0), (1, 0)]          # 纵向两格
    ]

    # 4. 放置第一个单格方块
    result = env.step((0, 0, 0))

    print("执行结果：")
    print(result.model_dump_json(indent=2))

    print("\n最终游戏状态：")
    print("分数：", env.game_state.score)
    print("剩余方块：", env.game_state.available_pieces)
    print("游戏结束：", env.game_state.game_over)

    # 5. 验证
    assert result.success is True
    assert result.cleared_rows == []
    assert result.cleared_cols == []
    assert env.game_state.game_over is True

    # 6. 验证结束后不能继续操作
    result2 = env.step((1, 0, 5))

    assert result2.success is False
    assert result2.error.code == "game_already_over"

    print("\n游戏结束检测及结束后操作拦截测试全部通过！")
    print("\n========== reset() 基础功能测试 ==========")

    # 1. 创建一个新的游戏环境
    env_reset = GameEnvironment(seed=42)

    # 2. 人为构造一个非初始状态
    env_reset.game_state.board.grid[:, :] = 1
    env_reset.game_state.score = 1000
    env_reset.game_state.game_over = True
    env_reset.game_state.available_pieces = [None, None, None]

    # 3. 调用 reset()
    snapshot = env_reset.reset()

    # 4. 验证返回值类型
    assert isinstance(snapshot, GameStateSnapshot)
    print("✓ 返回值类型正确")

    # 5. 验证棋盘是否全部清空
    assert (env_reset.game_state.board.grid == 0).all()
    print("✓ 棋盘已清空")

    # 6. 验证分数是否归零
    assert env_reset.game_state.score == 0
    print("✓ 分数已归零")

    # 7. 验证游戏结束标记
    assert env_reset.game_state.game_over is False
    print("✓ game_over 已恢复 False")

    # 8. 验证三个方块是否重新生成
    assert len(env_reset.game_state.available_pieces) == 3
    assert all(piece is not None for piece in env_reset.game_state.available_pieces)
    print("✓ 三个方块均已重新生成")

    # 9. 验证 Snapshot 内容
    assert snapshot.score == 0
    assert snapshot.game_over is False
    assert len(snapshot.available_pieces) == 3
    assert snapshot.board == [[0] * 10 for _ in range(10)]
    print("✓ Snapshot 内容正确")

    print("\nreset() 基础功能测试全部通过！")
    print("\n========== reset() RNG 连续性测试 ==========")

    # 1. 创建游戏环境
    env_rng = GameEnvironment(seed=42)

    # 2. 保存当前 RNG 状态
    rng_before = env_rng.piecegenerator.rng.getstate()

    # 3. 创建一个独立的预期生成器
    expected_generator = copy.deepcopy(env_rng.piecegenerator)

    # 4. 使用预期生成器生成下一批方块
    expected_pieces = expected_generator.generate_batch(count=3)

    # 5. 执行 reset()
    snapshot = env_rng.reset()

    # 6. 验证生成的方块符合预期
    assert snapshot.available_pieces == expected_pieces
    print("✓ 新方块与预期随机序列一致")

    # 7. 验证正式 RNG 已经推进
    rng_after = env_rng.piecegenerator.rng.getstate()

    assert rng_before != rng_after
    print("✓ RNG 状态已经推进")

    # 8. 验证正式 RNG 与预期生成器状态一致
    assert rng_after == expected_generator.rng.getstate()
    print("✓ RNG 工作副本正确提交")

    print("\nRNG 连续性测试全部通过！")
    print("\n========== reset() Seed 可复现性测试 ==========")

    # 1. 创建两个使用相同 Seed 的游戏环境
    env1 = GameEnvironment(seed=42)
    env2 = GameEnvironment(seed=42)

    # 2. 验证初始方块是否一致
    assert (
        env1.game_state.available_pieces
        == env2.game_state.available_pieces
    )
    print("✓ 相同 Seed 的初始方块一致")

    # 3. 连续执行三次 reset
    for i in range(3):
        snapshot1 = env1.reset()
        snapshot2 = env2.reset()

        # 验证每一轮生成的方块
        assert snapshot1.available_pieces == snapshot2.available_pieces

        # 验证 RNG 内部状态
        assert (
            env1.piecegenerator.rng.getstate()
            == env2.piecegenerator.rng.getstate()
        )

        print(f"✓ 第 {i + 1} 次 reset 随机序列一致")

    print("\nSeed 可复现性测试全部通过！")

    print("\n========== reset() 异常事务隔离测试 ==========")

    # 1. 创建游戏环境
    env_fail = GameEnvironment(seed=42)

    # 2. 构造一个非初始状态
    env_fail.game_state.board.grid[:, :] = 1
    env_fail.game_state.score = 1234
    env_fail.game_state.game_over = True
    env_fail.game_state.available_pieces = [None, None, None]

    # 3. 保存原始状态
    state_before = env_fail.game_state
    generator_before = env_fail.piecegenerator

    snapshot_before = env_fail.get_state_snapshot()
    rng_before = env_fail.piecegenerator.rng.getstate()

    # 4. 保存原始方法
    original_generate_batch = PieceGenerator.generate_batch

    # 5. 定义一个故意失败的方法
    def failing_generate_batch(self, count=3):

        # 故意消耗一次随机数
        self.generate_random_piece()

        # 模拟生成过程中发生异常
        raise RuntimeError("模拟方块生成失败")


    # 6. 临时替换 generate_batch
    PieceGenerator.generate_batch = failing_generate_batch

    try:

        try:
            env_fail.reset()

        except RuntimeError:
            print("✓ 成功捕获模拟生成异常")

        else:
            raise AssertionError("预期发生异常，但 reset() 没有报错")

    finally:
        # 7. 恢复原始方法
        PieceGenerator.generate_batch = original_generate_batch


    # 8. 验证正式 GameState 没有被替换
    assert env_fail.game_state is state_before
    print("✓ 原始 GameState 对象未被替换")

    # 9. 验证正式 Generator 没有被替换
    assert env_fail.piecegenerator is generator_before
    print("✓ 原始 PieceGenerator 对象未被替换")

    # 10. 验证 RNG 状态没有变化
    assert env_fail.piecegenerator.rng.getstate() == rng_before
    print("✓ 原始 RNG 状态未发生变化")

    # 11. 验证游戏数据没有变化
    snapshot_after = env_fail.get_state_snapshot()

    assert snapshot_after.model_dump() == snapshot_before.model_dump()
    print("✓ 原始游戏数据完整保留")

    print("\nreset() 异常事务隔离测试全部通过！")