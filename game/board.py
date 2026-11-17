import numpy as np




class Board:

    def __init__(self):
        #创建棋盘
        self.grid=np.zeros(shape=(10,10),dtype=int)
        self.num_rows,self.num_cols=self.grid.shape



    def can_place(self,piece,anchor_row,anchor_col):
        if len(piece)==0:
            print("方块不合法")
            return False

        for relative_row,relative_col in piece:
            target_row=relative_row+anchor_row
            target_col=relative_col+anchor_col




            if target_row<0 or target_row>=self.num_rows or target_col<0 or target_col>=self.num_cols :
                return False

            if self.grid[target_row,target_col]!=0:
                return False
        return True

    def place_piece(self,piece,anchor_row,anchor_col):

        if  not self.can_place(piece,anchor_row,anchor_col) :
            print("放置位置不合法，请换一个位置试试")
            return False

        for relative_row,relative_col in piece:

            target_row=relative_row+anchor_row
            target_col=relative_col+anchor_col

            self.grid[target_row,target_col]=1
        return True

    def get_affected_lines(self,piece,anchor_row,anchor_col):
            affected_rows=set()
            affected_cols=set()

            for relative_row,relative_col in piece:
                target_row=relative_row+anchor_row
                target_col=relative_col+anchor_col
                affected_rows.add(target_row)
                affected_cols.add(target_col)

            return(affected_rows,affected_cols)

    def clear_lines(self,affected_rows,affected_cols):
        full_rows=[]
        full_cols=[]
        for row in affected_rows:
            if np.all(self.grid[row,:]==1):
                full_rows.append(row)
        for col in affected_cols:
            if np.all(self.grid[:,col]==1):
                full_cols.append(col)


        for row in full_rows:
            self.grid[row,:]=0
        for col in full_cols:
            self.grid[:,col]=0

        return full_rows,full_cols



if __name__=="__main__":
    board = Board()

    # 构造十字形
    board.grid[2, :] = 1
    board.grid[:, 4] = 1

    # 添加一个不应该被消除的格子
    board.grid[0, 0] = 1

    print("消除前：")
    print(board.grid)

    # 模拟本次放置影响了第 2 行和第 4 列
    board.clear_lines({2}, {4})

    print("消除后：")
    print(board.grid)

    # 验证结果
    print("整行已清空：", np.all(board.grid[2, :] == 0))
    print("整列已清空：", np.all(board.grid[:, 4] == 0))
    print("无关格子保留：", board.grid[0, 0] == 1)