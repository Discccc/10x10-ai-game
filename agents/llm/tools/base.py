from abc import ABC,abstractmethod
from typing import Any
from pydantic import BaseModel

class BaseTool(ABC):
    name:str
    description:str
    args_schema:type[BaseModel]


    def validate_args(self,unvalidated_arguments:dict[str,Any])->BaseModel:
        return self.args_schema.model_validate(unvalidated_arguments)

    @abstractmethod
    def execute(self,validated_args:BaseModel)->Any:
        pass



    def build_openai_tool_definition(self)->dict[str,Any]:
        result={
            "type":"function",
            "function":{
                "name":self.name,
                "description":self.description,
                "parameters":self.args_schema.model_json_schema()
            }
        }
        return result