import random

class PieceGenerator:
    def __init__(self,min_size=1,max_size=6,max_span=4,seed=None):
        if max_span < 1 or not (1 <= min_size <= max_size <= max_span * max_span):
            raise ValueError("方块生成参数不合法")
        self.min_size=min_size
        self.max_size=max_size
        self.max_span=max_span
        self.rng=random.Random(seed)

    def get_neighbors(self,row,col):
        dx=[-1,1,0,0]
        dy=[0,0,-1,1]
        neighbors=[]
        for i in range(0,4):
            target_row=row+dx[i]
            target_col=col+dy[i]
            dot=(target_row,target_col)
            neighbors.append(dot)
        return neighbors


    def get_candidates(self,piece):
        candidates=set()

        for row,col in piece:
            neighbors=self.get_neighbors(row,col)
            for neighbor in neighbors:
                if neighbor not in piece:
                    candidates.add(neighbor)

        return candidates


    def generate_piece(self,target_size):
        #第一阶段：创建初始情况
        piece={(0,0)}
        # 第二阶段：不断生长，直到数量达到 target_size

        while len(piece)<target_size:

            # 步骤 1：找到所有相邻且未占用的格子
            candidates=self.get_candidates(piece)

            # 步骤 2：从候选格子中筛选出不会超限的位置
            valid_candidates=set()
            for candidate in candidates:
                if  self.is_within_bounds(piece,candidate,self.max_span) :
                    valid_candidates.add(candidate)

            #把候选的合法方块排序同时转化为一个列表，随机选择一个生长
            selected_dot=self.rng.choice(sorted(valid_candidates))

            piece.add(selected_dot)

        #归一化piece
        return self.normalize_piece(piece)




    def generate_random_piece(self):

        target_size=self.rng.randint(self.min_size,self.max_size)

        piece=self.generate_piece(target_size)
        return sorted(piece)

    def normalize_piece(self,piece):
        #归一化所有的piece
        min_row=100
        min_col=100
        for row,col in piece:
            min_row=min(min_row,row)
            min_col=min(min_col,col)
        normalized=set()
        for dot in piece:
            new_row=dot[0]-min_row
            new_col=dot[1]-min_col
            normalized.add((new_row,new_col))

        return normalized


    def is_within_bounds(self,piece,candidate,max_size=4):
        new_price=piece.copy()
        new_price.add(candidate)
        max_row=-100
        min_row=100
        max_col=-100
        min_col=100
        for row,col in new_price:
            max_row=max(max_row,row)
            min_row=min(min_row,row)
            max_col=max(max_col,col)
            min_col=min(min_col,col)

        height=max_row-min_row+1
        width=max_col-min_col+1
        if height>max_size or width>max_size:
            return False
        return True


    def generate_batch(self,count=3):
        pieces=[]

        for i in range(0,count):
            piece=self.generate_random_piece()
            pieces.append(piece)
        return pieces

if __name__=="__main":

    generator = PieceGenerator(seed=42)
    for i in range(1000):
        piece =generator. generate_random_piece()

        rows = [row for row, col in piece]
        cols = [col for row, col in piece]

        height = max(rows) - min(rows) + 1
        width = max(cols) - min(cols) + 1

        # 1. 格子数量合法
        assert 1 <= len(piece) <= 6

        # 2. 不允许重复格子
        assert len(piece) == len(set(piece))

        # 3. 最大宽高不超过 4×4
        assert height <= 4
        assert width <= 4

        # 4. 坐标已归一化
        assert min(rows) == 0
        assert min(cols) == 0

    print("1000 次随机方块基础测试通过！")
    generator1 = PieceGenerator(seed=42)
    generator2 = PieceGenerator(seed=42)

    for i in range(10):
        piece1 = generator1.generate_random_piece()
        piece2 = generator2.generate_random_piece()

        assert piece1 == piece2

    print("随机种子可复现测试通过")
    generator = PieceGenerator(seed=42)
    pieces = generator.generate_batch(3)

    assert len(pieces) == 3
    print(pieces)