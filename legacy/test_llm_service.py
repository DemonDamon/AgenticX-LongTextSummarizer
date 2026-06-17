# Date    : 2024/9/26 22:35
# File    : test_llm_service.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


import requests
import json

"""
可能需要执行下面语句：
export http_proxy=http://10.0.0.5:3128; export https_proxy=http://10.0.0.5:3128
"""

# url = "http://192.168.32.113:7820/aibox/v1/llm/chat/completions"
url = 'http://192.168.32.151:6821/aibox/v1/openai/chat/completions'

payload = json.dumps({
   "request_id": "test-jbjsax-89ujwbjdq-dbjdh8",
   # "model": "Qwen1.5-32B-Chat-GPTQ-Int4",
   "model": "Qwen2.5-72B-Instruct-GPTQ-Int4",
   "messages": [
      {
         "role": "system",
         "content": "你是文员，负责提取客户提供的信息中的地址，地址输出要求按照以下格式，不要输出多余内容：xx省xx市xx区，成功：xx。如果提取到信息，请不要虚构，提示未找到地址"
      },
      {
         "role": "user",
         "content": "我的地址是广东省广州市天河区，可以办理宽带吗"
      }
   ],
   "stream": False,
   "max_tokens": 52
})
headers = {
   'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
   'Content-Type': 'application/json'
}

response = requests.request("POST", url, headers=headers, data=payload)

print(response.text)
