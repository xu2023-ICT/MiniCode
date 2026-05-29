"""Base class for all tools."""

from abc import ABC, abstractmethod

# 明天尝试写一个web search的工具看看需要哪些参数
class Tool(ABC):
    """Minimal tool interface. Subclass this to add new capabilities."""

    name: str
    description: str
    parameters: dict  # JSON Schema for the function args

    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Run the tool and return a text result."""
        ...

    def schema(self) -> dict:
        """OpenAI function-calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }
    
"""
  {
      "type": "function", 固定
      "function": {
          "name": "get_weather",
          "description": "获取指定城市的天气",
          "parameters": {
              "type": "object", @ 键值对
              "properties": {
                  "city": {
                      "type": "string",
                      "description": "城市名称，例如 Beijing"
                  },
                  "unit": {
                      "type": "string",
                      "enum": ["celsius", "fahrenheit"],
                      "description": "温度单位"
                  }
              },
              "required": ["city"],
              "additionalProperties": False
          },
          "strict": True
      }
"""