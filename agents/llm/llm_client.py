from openai import OpenAI
import os
from dotenv import load_dotenv



if not api_key:
    raise ValueError("环境变量中未找到API_KEY,请检查")



class LLMClient:
    def __init__(self,api_key=None,base_url=None,model="deepseek-flash",timeout=30):


        load_dotenv()
        if api_key is None:
            api_key = os.getenv("DEEPSEEK_API_KEY")

        if base_url is None:
            base_url = os.getenv("BASE_URL")

        if not api_key:
            raise ValueError("环境变量中未找到API_KEY,请检查")

        if not base_url:
            raise ValueError("未找到BASE_URL,请检查")

        self.timeout=timeout
        self.model=model
        self.client=OpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout

        )



    def chat(self,
             messages,
             tools=None,
             tool_choice=None
             ):
        response=self.client.chat.completions.create(
            messages=messages,
            model=self.model,
            timeout=self.timeout,
            tools=tools,
             extra_body={
            "thinking": {"type": "disabled"}
            },
            tool_choice=tool_choice

        )
        return response