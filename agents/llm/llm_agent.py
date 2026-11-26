
from .llm_client import LLMClient
from .tools.place_piece import PlacePieceTool
from game.environment import GameEnvironment
from .observation import format_observation
from .prompts import build_messages
import json
from game.schemas import StepResult



class LLMAgent:

    def __init__(
        self,
        llmclient: LLMClient,
        env: GameEnvironment
    ):
        self.llmclient = llmclient
        self.placepiecetool = PlacePieceTool(env)
        self.env = env


    def _request_action(self, error_feedback: str | None = None):

        #构建Observation
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


        return  validated_args







    def decide(self):
        snapshot = self.env.get_state_snapshot()

        if snapshot.game_over:
            raise RuntimeError("游戏已经结束")

        max_attempts = 3

        retryable_error_codes = {
            "invalid_position",
            "invalid_piece_index"
        }

        retry_feedback = None

        for attempt in range(1, max_attempts + 1):

            validated_args = self._request_action(retry_feedback)
            action=(
                validated_args.piece_index,
                validated_args.anchor_row,
                validated_args.anchor_col
            )
            error=self.env.validate_action(action)


            if error is None:
                break

            if error.code not in retryable_error_codes:
                break

            retry_feedback = (
                f"上一次放置 action：{validated_args.model_dump()}\n\n"
                f"错误代码：{error.code}\n"
                f"错误原因：{error.message}"
            )

        return validated_args,error


    def execute(self,validated_args):
        return self.placepiecetool.execute(validated_args)






    def run_game(self,on_step=None):
        # 保存整局游戏的执行结果：
        # 包含所有成功的 StepResult，以及至多一个最终失败的 StepResult
        step_results = []


        # 获取游戏初始状态，用于判断整局游戏是否结束
        snapshot = self.env.get_state_snapshot()

        # 外层循环：负责持续运行整局游戏，直到游戏自然结束或 Agent 提前终止
        while snapshot.game_over is False:

            results=self.play_step()
            step_result=results["result"]
            step_results.append(step_result)

            if on_step is not None:
                on_step(
                    {
                        "action":results["action"],
                        "result":step_result.model_dump()
                    }
                )

            if step_result.success:
                # 当前落子成功，更新游戏状态，进入下一次落子任务
                snapshot = step_result.state
            else:
                # 当前落子任务最终失败：
                # 可能是三次尝试全部失败，也可能遇到了不可重试错误
                # 停止整局 Agent 运行，保留此前成绩和最后一次失败信息
                break

        # 返回整局游戏的执行记录
        return step_results


    def play_step(self):
        validated_args,error=self.decide()

        if error is not None:
            result= StepResult(
                success=False,
                error=error,
                score_gained=0,
                cleared_rows=[],
                cleared_cols=[],
                batch_refreshed=False,
                state=self.env.get_state_snapshot()
            )
        else:
            result= self.execute(validated_args)

        return{
            "action":validated_args.model_dump(),
            "result":result
        }