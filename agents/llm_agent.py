
from .llm_client import LLMClient
from .tools.place_piece import PlacePieceTool
from game.environment import GameEnvironment
from .observation import format_observation
from .prompts import build_messages
import json


class LLMAgent:

    def __init__(
        self,
        llmclient: LLMClient,
        env: GameEnvironment
    ):
        self.llmclient = llmclient
        self.placepiecetool = PlacePieceTool(env)
        self.env = env


    def decide(self, error_feedback: str | None = None):
        snapshot = self.env.get_state_snapshot()
        observation = format_observation(snapshot)
        messages = build_messages(observation, error_feedback)
        tools = []
        tools.append(self.placepiecetool.build_openai_tool_definition())

        response = self.llmclient.chat(
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        choice = response.choices[0]

        if choice.finish_reason != "tool_calls":
            raise RuntimeError("模型未返回工具调用")

        tool_calls = choice.message.tool_calls

        if tool_calls is None or len(tool_calls) != 1:
            raise RuntimeError("本次决策需要恰好一个工具调用")

        tool_call = tool_calls[0]

        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        if tool_name != "place_piece":
            raise RuntimeError("该工具不存在")

        tool_args = json.loads(arguments)
        validated_args = self.placepiecetool.validate_args(tool_args)
        result = self.placepiecetool.execute(validated_args)

        return result, validated_args


    def run_game(self):
        # 保存整局游戏的执行结果：
        # 包含所有成功的 StepResult，以及至多一个最终失败的 StepResult
        step_results = []

        # 单次落子任务最多允许尝试三次
        max_attempts = 3

        # 定义允许重新请求 LLM 进行决策的错误类型
        # 只有这些错误才会触发有限重试
        retryable_error_codes = {
            "invalid_position",
            "invalid_piece_index"
        }

        # 获取游戏初始状态，用于判断整局游戏是否结束
        snapshot = self.env.get_state_snapshot()

        # 外层循环：负责持续运行整局游戏，直到游戏自然结束或 Agent 提前终止
        while snapshot.game_over is False:

            # 当前落子任务的错误反馈，每次开始新的落子任务时清空
            retry_feedback = None

            # 标记当前落子任务是否成功，默认尚未成功
            placement_succeeded = False

            # 内层循环：负责当前落子任务的有限重试，最多尝试 max_attempts 次
            for attempt in range(1, max_attempts + 1):

                # 请求 LLM 决策并执行放置动作
                # 如果上一次动作失败，会将错误反馈一并传给 LLM
                result, validated_args = self.decide(retry_feedback)

                # 第一层判断：检查本次放置是否成功
                if result.success:
                    placement_succeeded = True
                    break  # 成功后退出内层 for，结束当前落子任务

                # 动作失败时必须存在错误信息，否则说明环境返回结果异常
                if result.error is None:
                    raise RuntimeError("动作失败，但是未提供错误信息")

                # 第二层判断：检查错误是否允许重试
                if result.error.code not in retryable_error_codes:
                    # 非白名单错误不允许重试，立即退出内层 for
                    break

                # 动作失败且错误允许重试：
                # 将本次动作参数和失败原因整理成字符串，
                # 下一次调用 decide() 时反馈给 LLM，帮助其修正决策
                retry_feedback = (
                    f"上一次放置 action：{validated_args.model_dump()}\n\n"
                    f"错误代码：{result.error.code}\n"
                    f"错误原因：{result.error.message}"
                )

            # 内层循环结束后，统一保存本次任务的最终执行结果
            # 成功时保存成功结果；失败时保存最后一次失败结果
            step_results.append(result)

            if placement_succeeded:
                # 当前落子成功，更新游戏状态，进入下一次落子任务
                snapshot = result.state
            else:
                # 当前落子任务最终失败：
                # 可能是三次尝试全部失败，也可能遇到了不可重试错误
                # 停止整局 Agent 运行，保留此前成绩和最后一次失败信息
                break

        # 返回整局游戏的执行记录
        return step_results
