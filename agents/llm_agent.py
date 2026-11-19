from .llm_client import LLMClient
from  .tools.place_piece import PlacePieceTool
from game.environment import GameEnvironment
from .observation import format_observation
from .prompts import build_messages
import json

class LLMAgent:

    def __init__(
        self,
        llmclient:LLMClient,
        env:GameEnvironment
        ):
        self.llmclient=llmclient
        self.placepiecetool=PlacePieceTool(env)
        self.env=env


    def decide(self):
        snapshot=self.env.get_state_snapshot()
        observation=format_observation(snapshot)
        messages=build_messages(observation)
        tools=[]
        tools.append(self.placepiecetool.build_openai_tool_definition())
        response=self.llmclient.chat(
            messages=messages,
            tools= tools,
            tool_choice="auto"
        )
        choice=response.choices[0]
        if choice.finish_reason!="tool_calls":
            raise RuntimeError("模型未返回工具调用")
        tool_calls=choice.message.tool_calls

        if tool_calls is None or len(tool_calls)!=1:
            raise RuntimeError("本次决策需要恰好一个工具调用")

        tool_call=tool_calls[0]

        tool_name=tool_call.function.name
        arguments=tool_call.function.arguments

        if tool_name !="place_piece":
            raise RuntimeError("该工具不存在")
        tool_args=json.loads(arguments)
        validated_args=self.placepiecetool.validate_args(tool_args)
        result=self.placepiecetool.execute(validated_args)
        return result




    def run_game(self, max_steps=None):
        snapshot = self.env.get_state_snapshot()
        step_results = []
        step_count = 0

        print("\n========== AI 游戏开始 ==========")

        while not snapshot.game_over:

            # 最大行动次数保护
            if max_steps is not None and step_count >= max_steps:
                print(f"\n达到最大行动次数 {max_steps}，测试停止。")
                break

            step_count += 1

            print(f"\n{'=' * 15}")
            print(f"第 {step_count} 次决策")
            print(f"{'=' * 15}", flush=True)

            # 执行一次决策
            result = self.decide()

            if result.success is False:
                raise RuntimeError(
                    f"第 {step_count} 次动作执行失败：{result.error}"
                )

            step_results.append(result)
            snapshot = result.state

            # 输出本次行动结果
            print("\n---------- 行动结果 ----------")
            print(f"执行成功：{result.success}")
            print(f"本次得分：{result.score_gained}")
            print(f"消除行：{result.cleared_rows}")
            print(f"消除列：{result.cleared_cols}")
            print(f"批次刷新：{result.batch_refreshed}")
            print(f"当前总分：{snapshot.score}")
            print(f"游戏结束：{snapshot.game_over}")

            # 输出最新棋盘
            print("\n---------- 当前棋盘 ----------")
            for row in snapshot.board:
                print(" ".join("■" if cell else "□" for cell in row))

        print("\n========== 本次运行结束 ==========")
        print(f"行动次数：{len(step_results)}")
        print(f"最终得分：{snapshot.score}")
        print(f"游戏是否结束：{snapshot.game_over}")

        return step_results
