# Date    : 2024/9/26 22:49
# File    : test_client.py
# Desc    : 
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com


# Date    : 2024/9/17 15:50
# File    : test_client.py
# Desc    :
# Author  : Damon
# E-mail  : bingzhenli@hotmail.com

import secrets
import requests
import json
import time


sender_id = secrets.token_urlsafe(16)  # 随机生成会话id
url = f"http://192.168.42.137:8282/aibox/richMail/v1.0/intelliAbstract?sid={sender_id}"


payload = json.dumps(
    {
        "email_content": "ai峰会在广州举办，需要确认是否需要提供发票，请确认。"},
    ensure_ascii=False
).encode(encoding="utf-8")


headers = {
    'Content-Type': 'application/json'
}


_start = time.time()
response = requests.request("POST", url, headers=headers, data=payload)
_end = time.time()
gap = round(_end - _start, 2)


if response.status_code == 200:
    resp_json = response.json()  # json.loads(response.text.encode('utf8'))  # dict类型
    print("时长={0} | 生成字数={1} | 推理速度={2}字/秒".format(gap, len(resp_json["text"]), round(len(resp_json["text"]) / gap, 2)))
    print(f"接口响应：{resp_json}")
else:
    print(response)
