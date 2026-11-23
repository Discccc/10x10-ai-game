import copy
import numpy as np

from game.state import GameState

class FeatureExtractor:

    FEATURE_NAMES=(
        "bias",
        "piece_size",
        "cleared_lines",
        "board_occupancy",
        "near_full_rows",
        "near_full_cols"
    )

    BOARD_SIZE=10
    MAX_PIECE_SIZE=6
    MAX_CLEARED_LINES=7
    NEAR_FULL_MIN_CELLS=8

    def extract_features(self,state:GameState,action):
        piece_index,row,col=action
        piece=state.available_pieces[piece_index]
        simulated_board=copy.deepcopy(state.board)

        if not simulated_board.place_piece(piece,row,col):
            raise ValueError("extract_features requires a legal action")
        affected_rows,affected_cols=simulated_board.get_affected_lines(piece,row,col)
        cleared_rows,cleared_cols=simulated_board.clear_lines(affected_rows,affected_cols)
        occupancy=np.count_nonzero(simulated_board.grid)/(self.BOARD_SIZE*self.BOARD_SIZE)

        row_counts = np.count_nonzero(simulated_board.grid, axis=1)
        col_counts = np.count_nonzero(simulated_board.grid, axis=0)

        near_full_rows = []
        near_full_cols = []

        for i in range(self.BOARD_SIZE):
            if 8 <= row_counts[i] < 10:
                near_full_rows.append(i)

            if 8 <= col_counts[i] < 10:
                near_full_cols.append(i)

        piece_size=len(piece)/self.MAX_PIECE_SIZE
        cleared_lines=(len(cleared_rows)+len(cleared_cols))/self.MAX_CLEARED_LINES
        features=np.array(
            [
                1.0,
                piece_size,
                cleared_lines,
                occupancy,
                len(near_full_rows)/self.BOARD_SIZE,
                len(near_full_cols)/self.BOARD_SIZE

            ],dtype=float
        )
        return features