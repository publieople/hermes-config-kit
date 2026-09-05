"""
DeepSeek ReAct Agent — 完整参考实现
展示 stop=["PAUSE"] 和中文冒号兼容的正确用法
"""

import json
import os
import re
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)

REACT_PROMPT = """
You run in a loop of Thought, Action, Action Input, PAUSE, Observation.
At the end of the loop you output an Answer
Use Thought to describe your thoughts about the question you have been asked.
Use Action to run one of the actions available to you
use Action Input to indicate the input to the Action- then return PAUSE.
Observation will be the result of running those actions.

Your available actions:
{tools}

Rules:
1- If the input is a greeting or a goodbye, respond directly without using the Thought-Action loop.
2- Otherwise, follow the Thought-Action Input loop to find the best answer.
3- If you already have the answer, use your knowledge without relying on external actions.
4- If you need to execute more than one Action, do it on separate calls.
5- At the end, provide a final answer.

Example:
Question: 今天北京天气怎么样？
Thought: 我需要调用 get_weather 工具获取天气
Action: get_weather
Action Input: {"city": "BeiJing"}

PAUSE

You will be called again with this:
Observation: 北京的气温是0度.

You then output:
Final Answer: 北京的气温是0度.

Begin!

New input: {input}"""


def send_messages(messages):
    """关键：stop=["PAUSE"] 防止模型一次性生成整个循环"""
    return client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        stop=["PAUSE"],
    )


def run_react_agent(tools_def, tool_functions, query):
    """通用 ReAct Agent 执行器"""
    prompt = REACT_PROMPT.replace("{tools}", json.dumps(tools_def))
    prompt = prompt.replace("{input}", query)
    messages = [{"role": "user", "content": prompt}]

    while True:
        response = send_messages(messages)
        text = response.choices[0].message.content

        # 兼容中英文冒号
        if re.search(r"Final Answer[:：]", text):
            return re.search(r"Final Answer[:：]\s*(.*)", text).group(1)

        messages.append(response.choices[0].message)

        # 解析 Action（兼容中英文冒号）
        action_m = re.search(r"Action[:：]\s*(\w+)", text)
        input_m = re.search(r"Action Input[:：]\s*(\{.*?\})", text, re.DOTALL)

        if action_m and input_m:
            tool_name = action_m.group(1)
            params = json.loads(input_m.group(1))
            observation = tool_functions[tool_name](**params)
            messages.append({"role": "user", "content": f"Observation: {observation}"})
        else:
            raise RuntimeError(f"无法解析 ReAct 输出:\n{text}")
