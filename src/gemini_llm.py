import os
import time
import logging
import traceback
from pathlib import Path

from google import genai
from google.api_core import exceptions as google_exceptions
from google.genai import types

# 日志
logging.basicConfig(level=logging.INFO)

# 获取项目目录
project_dir = Path(__file__).parent.parent

# Gemini配置
gemini_config = {
    # 基础配置
    "project_id": "xxx",  # 和config中保持一致
    "location": "us-central1",
    "model": "gemini-2.5-pro",
    "credentials_path": os.path.join(project_dir, "config", "gemini_config.json"),  # 如果为None则使用默认路径
    # 超时和重试配置
    "timeout": 120,
    "max_retries": 3,
    # 生成参数配置
    "temperature": 0.1,
    "max_tokens": 8000,
    "thinking_budget": 8000,  # 修复为支持的范围内 (1-24576)
    # 安全设置
    "safety_settings": [
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "OFF"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "OFF"},
    ],
    # 计费标签
    "billing_name": "xxx",
}

class GeminiLLM:
    """
    Google Gemini LLM调用封装类
    """

    def __init__(self, config=None):
        """初始化Gemini配置"""
        
        self.logger = logging.getLogger(__name__)
        # 使用传入的config或默认的gemini_config
        config_to_use = config if config is not None else gemini_config
        self._init_gemini(config_to_use)       # 再调用初始化方法

    def _init_gemini(self, gemini_config):
        """初始化Gemini配置"""
        try:
            self.gemini_project_id = gemini_config["project_id"]
            self.gemini_location = gemini_config["location"]
            self.gemini_model_name = gemini_config["model"]
            self.gemini_timeout = gemini_config["timeout"]
            self.gemini_max_retries = gemini_config["max_retries"]
            self.gemini_billing_name = gemini_config["billing_name"]
            self.gemini_temperature = gemini_config["temperature"]
            self.gemini_max_tokens = gemini_config["max_tokens"]
            self.gemini_thinking_budget = gemini_config["thinking_budget"]
            self.gemini_safety_settings = gemini_config["safety_settings"]

            # 设置Google应用凭据
            credentials_path = gemini_config.get("credentials_path")
            self.logger.info(f"🔑 检查Gemini凭据文件: {credentials_path}")
            
            if credentials_path and os.path.exists(credentials_path):
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
                self.logger.info(f"✅ 找到凭据文件: {credentials_path}")
            else:
                self.logger.warning(f"❌ Gemini凭据文件不存在: {credentials_path}")
                self.logger.warning(f"💡 请确保配置文件存在并包含正确的Google Cloud凭据")

            # 初始化Gemini客户端
            self.gemini_client = genai.Client(
                vertexai=True,
                project=self.gemini_project_id,
                location=self.gemini_location,
            )
            self.logger.info(
                f"Initialized Gemini tool, project: {self.gemini_project_id}, model: {self.gemini_model_name}"
            )
        except Exception as e:
            self.logger.error(f"Failed to initialize Gemini client: {e}")
            traceback.print_exc()
            raise

    def _convert_messages_to_gemini_contents(self, messages):
        """
        将标准消息格式转换为Gemini的Content格式

        Args:
            messages: 标准消息列表，包含role和content

        Returns:
            (contents, system_instruction) 元组
        """
        contents = []
        system_instruction = None

        for message in messages:
            role = message.get("role", "user")
            content = message.get("content", "")

            if role == "system":
                # 系统消息作为system_instruction
                system_instruction = [types.Part.from_text(text=content)]
            elif role in ["user", "model", "assistant"]:
                # 将assistant角色映射为model
                if role == "assistant":
                    role = "model"

                contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content)]))

        return contents, system_instruction

    def call(
        self,
        message_list,
        temperature=None,
        max_tokens=None,
        timeout=None,
        thinking_budget=None,
        **kwargs,
    ):
        """
        调用Google Gemini API

        Args:
            message_list: 消息列表，包含role和content
            temperature: 温度参数，控制输出的随机性
            max_tokens: 最大输出token数
            timeout: 超时时间（秒）
            thinking_budget: 思考预算token数
            **kwargs: 其他参数（如response_mime_type等）

        Returns:
            (response, tokens_used, finish_reason): 返回内容、token使用量(整数)和结束原因
        """
        if not message_list:
            self.logger.warning("Message list is empty")
            return "", 0, "invalid_request"

        try:
            # 转换消息格式
            contents, system_instruction = self._convert_messages_to_gemini_contents(message_list)

            # 使用传入的参数或配置文件中的默认值
            request_timeout = timeout if timeout is not None else self.gemini_timeout
            request_temperature = temperature if temperature is not None else self.gemini_temperature
            request_max_tokens = max_tokens if max_tokens is not None else self.gemini_max_tokens
            request_thinking_budget = thinking_budget if thinking_budget is not None else self.gemini_thinking_budget

            # 从 kwargs 中获取 response_mime_type
            response_mime_type = kwargs.get("response_mime_type")

            # 设置默认labels
            labels = kwargs.get("labels", {"billing_name": self.gemini_billing_name})

            self.logger.info(f"Calling Gemini API, model: {self.gemini_model_name}, message count: {len(contents)}")

            # 配置生成参数
            config_params = {
                "temperature": request_temperature,
                "max_output_tokens": request_max_tokens,
                "safety_settings": [
                    types.SafetySetting(category=setting["category"], threshold=setting["threshold"])
                    for setting in self.gemini_safety_settings
                ],
                "thinking_config": types.ThinkingConfig(thinking_budget=request_thinking_budget),
                "labels": labels,
            }
            
            # 如果指定了response_mime_type，添加到配置中
            if response_mime_type:
                config_params["response_mime_type"] = response_mime_type
                self.logger.info(f"Setting response_mime_type to: {response_mime_type}")
            
            generate_content_config = types.GenerateContentConfig(**config_params)

            # 如果有系统指令，添加到配置中
            if system_instruction:
                generate_content_config.system_instruction = system_instruction

            start_time = time.time()

            # 调用API
            response = self.gemini_client.models.generate_content(
                model=self.gemini_model_name,
                contents=contents,
                config=generate_content_config,
            )

            # 处理响应
            end_time = time.time()
            response_time = end_time - start_time

            # 统计token使用情况
            usage = response.usage_metadata
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            thoughts_tokens = getattr(usage, "thoughts_token_count", 0) or 0
            total_tokens = input_tokens + output_tokens + thoughts_tokens

            self.logger.info(f"Gemini API call successful, time taken: {response_time:.2f} seconds")
            self.logger.info(f"Token usage: input={input_tokens}, output={output_tokens}, thoughts={thoughts_tokens}")

            if response and response.text:
                return response.text, total_tokens, "stop"
            else:
                self.logger.warning(f"Gemini API returned empty response")
                return "", 0, "empty_response"

        except google_exceptions.DeadlineExceeded:
            self.logger.error(f"Gemini API request timed out after {timeout or self.gemini_timeout} seconds")
            traceback.print_exc()
            return "", 0, "timeout"
        except google_exceptions.PermissionDenied as e:
            self.logger.error(f"Permission denied when calling Gemini API: {e}")
            traceback.print_exc()
            return "", 0, "permission_denied"
        except google_exceptions.InvalidArgument as e:
            self.logger.error(f"Invalid argument when calling Gemini API: {e}")
            traceback.print_exc()
            return "", 0, "invalid_argument"
        except google_exceptions.ResourceExhausted as e:
            self.logger.error(f"Resource exhausted when calling Gemini API: {e}")
            traceback.print_exc()
            return "", 0, "resource_exhausted"
        except Exception as e:
            self.logger.error(f"Unexpected error when calling Gemini API: {e}")
            traceback.print_exc()
            return "", 0, "error"
