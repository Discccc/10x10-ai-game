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

        error=self.validate_action(action)

        if error is not None:
            return StepResult(
                success=False,
                error=error,
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


    def get_legal_actions(self,state:GameState):
        legel_actions=[]
        for row in range(0,10):
            for col in range (0,10):
                for index,piece in enumerate(state.available_pieces):
                    if piece is None:
                        continue
                    if state.board.can_place(piece, row,col):
                        legel_actions.append((index,row,col))

        return legel_actions



    def validate_action(self,action)->ErrorInfo|None:

        if self.game_state.game_over:
            return ErrorInfo(
            code="game_already_over",
            message="游戏已经结束，无法继续放置"

        )


        if type(action)is not tuple or len(action)!=3:
            return ErrorInfo(
                    code="invalid_action_format",
                    message="action格式有问题，请重新检查"
                )

        piece_index, anchor_row, anchor_col = action

        if type(piece_index) is not  int or type(anchor_row) is not int or type(anchor_col) is not int:
            return ErrorInfo(
                    code="invalid_action_type",
                    message="piece_index、anchor_row 和 anchor_col 必须都是整数"
                )

        if not self.is_valid_piece_index(piece_index):
            return ErrorInfo(
                code="invalid_piece_index",
                message="方块索引无效或对应槽位已经使用"
            )

        if not self.game_state.board.can_place(
            self.game_state.available_pieces[piece_index],
            anchor_row,
            anchor_col
            ):
            return ErrorInfo(
                    code="invalid_position",
                    message="该位置不可放置"
                )

        return None