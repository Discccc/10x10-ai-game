
import numpy as np

from agents.q_learning.feature_extractor import FeatureExtractor


class LinearQAgent:

    def __init__(
        self,
        epsilon_start=1.0,
        epsilon_min=0.05,
        epsilon_decay_steps=10000,
        gamma=0.9,
        learning_rate=0.01
    ):
        self.feature_extractor = FeatureExtractor()

        # Epsilon 参数
        self.epsilon_start = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay_steps = epsilon_decay_steps


        # 计算指数衰减系数
        self.epsilon_decay_rate = (
            self.epsilon_min / self.epsilon_start
        ) ** (1 / self.epsilon_decay_steps)

        # 初始化权重
        self.weights = np.zeros(
            len(self.feature_extractor.FEATURE_NAMES),
            dtype=float
        )

        # 折扣因子
        self.gamma = gamma

        #学习率
        self.learning_rate=learning_rate

    def get_q_value(self, state, action):
        features = self.feature_extractor.extract_features(
            state, action
        )
        q = np.dot(self.weights, features)
        return q

    def get_greedy_action(self, state, legal_actions):
        if not legal_actions:
            return None

        best_action = None
        best_q_value = float("-inf")

        for action in legal_actions:
            q_value = self.get_q_value(state, action)

            if q_value > best_q_value:
                best_action = action
                best_q_value = q_value

        return best_action

    def get_epsilon(self, total_steps):
        if total_steps < 0:
            raise ValueError("步数不能小于0")

        epsilon = (
            self.epsilon_start
            * self.epsilon_decay_rate ** total_steps
        )

        epsilon = max(epsilon, self.epsilon_min)

        return epsilon

    def select_action(self, state, legal_actions, epsilon):
        if not legal_actions:
            return None

        random_value = np.random.random()

        if random_value < epsilon:
            # 探索：随机选择合法动作
            random_index = np.random.randint(
                len(legal_actions)
            )
            action = legal_actions[random_index]

        else:
            # 利用：选择 Q 值最大的动作
            action = self.get_greedy_action(
                state, legal_actions
            )

        return action

    def calculate_td_target(
        self,
        reward,
        next_state,
        next_legal_actions,
        done
    ):
        # 判断游戏是否结束
        if done:
            return reward

        next_q_valueMax = float("-inf")

        for action in next_legal_actions:
            q_value = self.get_q_value(next_state, action)

            if q_value > next_q_valueMax:

                next_q_valueMax = q_value

        td_target=reward+self.gamma*next_q_valueMax
        return td_target


    def calculate_td_error(self,current_q,td_target):
       return td_target-current_q

    def update_weights(self,features,td_error):
        new_weights=self.weights+self.learning_rate*td_error*features

        if not np.isfinite(new_weights).all():
            raise FloatingPointError("权重出现异常")

        self.weights=new_weights

    def learn(self,
              state,
              action,
              reward,
              next_state,
              next_legal_actions,
              done):

        features=self.feature_extractor.extract_features(state,action)
        #获得当前动作的特征

        current_q=self.get_q_value(state,action)
        td_target=self.calculate_td_target(reward,next_state,next_legal_actions,done)
        td_error=self.calculate_td_error(current_q,td_target)
        weights_before=self.weights.copy()
        self.update_weights(features,td_error)
        weights_after=self.weights.copy()

        return{
            "features":features,
            "current_q":current_q,
            "td_target":td_target,
            "td_error":td_error,
            "weights_before":weights_before,
            "weights_after":weights_after
        }