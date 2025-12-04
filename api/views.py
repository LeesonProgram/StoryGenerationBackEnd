from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import requests
import json
import time

# Ollama 本地 API 配置
OLLAMA_API_URL = "http://localhost:18001/api/generate"  # Ollama 默认地址
TEXT_TO_IMAGE_API_URL = "http://localhost:18002/api/generate_image"  # Text to Image 模型地址


@csrf_exempt
def receive_content(request):
    if request.method != "POST":
        return JsonResponse({"error": "只支持POST请求"}, status=405)

    try:
        # ----------------------------
        # 1. 解析前端 JSON 请求
        # ----------------------------
        data = json.loads(request.body)
        user_prompt = data.get("prompt", "").strip()
        user_style = data.get("style", "").strip()

        print(">>> 前端 prompt:", user_prompt)
        print(">>> 前端 style:", user_style)

        # ----------------------------
        # 2. 构建 system prompt
        # ----------------------------
        system_prompt = f"""
你是一个专业的故事场景拆分助手，请根据用户提供的故事 prompt，将故事拆分成多个场景。
无论用户输入什么语言，你都必须 **完全使用中文输出**！

每个场景需要包含以下字段：
- scence_title: 场景标题
- prompt: 适合用于图像生成的场景描述（风格需为：{user_style}）
- narration: 场景旁白
- bgm_suggestion: 适合该场景的背景音乐

⚠️ 以下内容必须严格遵守：
1. 所有字段（scence_title、prompt、narration、bgm_suggestion）必须使用中文描述。
2. prompt 字段必须是 **中文的图像描述**，不能出现英文句子。
3. narration 必须是中文叙述。
4. 请严格输出一个 JSON 数组，每个元素是一个场景对象。
5. 不要输出解释，不要输出自然语言，只输出 JSON。
"""

        full_prompt = f"{system_prompt}\n\n故事内容如下：\n{user_prompt}"

        payload = {
            "model": "qwen2.5-coder:3b",
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": 0.4,
                "num_predict": 1500,
            }
        }

        print(">>> 调用 Ollama ...")

        response = requests.post(OLLAMA_API_URL, json=payload, timeout=60)
        print(">>> Ollama 状态码:", response.status_code)

        if response.status_code != 200:
            return JsonResponse({
                "code": 500,
                "msg": "大模型调用失败",
                "data": response.text,
                "time": int(time.time() * 1000)
            })

        res = response.json()
        model_text = res.get("response", "").strip()

        print(">>> 模型原始输出：")
        print(model_text)

        # ----------------------------
        # 3. 尝试提取 JSON 数组
        # ----------------------------
        cleaned = model_text

        # 去掉 ```json ``` 包裹
        if "```" in cleaned:
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()

        json_start = cleaned.find("[")
        json_end = cleaned.rfind("]") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("模型未返回有效 JSON")

        cleaned_json = cleaned[json_start:json_end]

        shot_list = json.loads(cleaned_json)

        print(">>> 解析后的 JSON：")
        print(json.dumps(shot_list, ensure_ascii=False, indent=2))

        # ----------------------------
        # 4. 构造最终返回格式
        # ----------------------------
        return JsonResponse({
            "code": 200,
            "msg": "操作成功",
            "data": {
                "shotList": shot_list
            },
            "time": int(time.time() * 1000)
        })

    except Exception as e:
        print(">>> ❌ 错误:", str(e))
        return JsonResponse({
            "code": 500,
            "msg": "服务器异常",
            "data": str(e),
            "time": int(time.time() * 1000)
        })


@csrf_exempt
def generate_image(request):
    if request.method != "POST":
        return JsonResponse({"error": "只支持POST请求"}, status=405)

    try:
        # ----------------------------
        # 1. 解析前端 JSON 请求
        # ----------------------------
        data = json.loads(request.body)
        user_prompt = data.get("prompt", "").strip()
        user_style = data.get("style", "").strip()

        print(">>> 前端 prompt:", user_prompt)
        print(">>> 前端 style:", user_style)

        # ----------------------------
        # 2. 构建完整的提示词
        # ----------------------------
        full_prompt = f"风格:{user_style}\n\n场景描述:{user_prompt}"

        payload = {
            "prompt": full_prompt,
            "stream": False
        }

        print(">>> 调用 Text to Image 模型 ...")

        response = requests.post(TEXT_TO_IMAGE_API_URL, json=payload, timeout=60)
        print(">>> Text to Image 模型状态码:", response.status_code)

        if response.status_code != 200:
            return JsonResponse({
                "code": 500,
                "msg": "图像生成模型调用失败",
                "data": response.text,
                "time": int(time.time() * 1000)
            })

        res = response.json()
        image_base64 = res.get("image_base64", "")
        saved_path = res.get("saved_path", "")

        print(">>> 图像生成成功")

        # ----------------------------
        # 3. 构造最终返回格式
        # ----------------------------
        return JsonResponse({
            "code": 200,
            "msg": "操作成功",
            "data": {
                "image_base64": image_base64,
                "saved_path": saved_path
            },
            "time": int(time.time() * 1000)
        })

    except Exception as e:
        print(">>> ❌ 错误:", str(e))
        return JsonResponse({
            "code": 500,
            "msg": "服务器异常",
            "data": str(e),
            "time": int(time.time() * 1000)
        })