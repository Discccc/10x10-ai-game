from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
api_key=os.getenv("DEEPSEEK_API_KEY")
base_url=os.getenv("BASE_URL")
print("API Key 是否读取成功：", bool(api_key))
print("Base URL：", repr(base_url))
if not api_key:
    raise ValueError("环境变量中未找到API_KEY,请检查")



class LLMClient:
    def __init__(self,api_key,base_url,model,timeout=30):
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

if __name__=="__main__":
    messages=[
        {"role":"user",
        "content":"你好"
        }
        ]
    model="deepseek-flash"
    llm=LLMClient(api_key,base_url,model,10)
    response=llm.chat(messages)
    print(response.choices[0].message.content)
