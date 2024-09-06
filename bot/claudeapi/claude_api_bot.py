# encoding:utf-8

import time

from openai import OpenAI
from openai import OpenAIError
import anthropic

from bot.openai.open_ai_bot import OpenAIBot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.gemini.google_gemini_bot import GoogleGeminiBot
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from config import conf

user_session = dict()


# OpenAI对话模型API (可用)
class ClaudeAPIBot(OpenAIBot):
    def __init__(self):
        super().__init__()
        self.claudeClient = anthropic.Anthropic(
            api_key=conf().get("claude_api_key")
        )

        self.args = {
            "model": conf().get("model") or "claude-3-5-sonnet",  # 对话模型的名称
            # "temperature": conf().get("temperature", 0.7),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # # "max_tokens":4096,  # 回复最大的字符数
            # "top_p": conf().get("top_p", 1),
            # "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            # "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }

    def reply_text(self, session: ChatGPTSession, args=None, retry_count=0):
        self.searchmode = False
        try:
            actual_model = self._model_mapping(conf().get("model"))
            response = self.claudeClient.messages.create(
                model=actual_model,
                max_tokens=1024,
                # system=conf().get("system"),
                messages=GoogleGeminiBot.filter_messages(session.messages)
            )
            # response = openai.Completion.create(prompt=str(session), **self.args)
            res_content = response.content[0].text.strip().replace("<|endoftext|>", "")
            total_tokens = response.usage.input_tokens+response.usage.output_tokens
            completion_tokens = response.usage.output_tokens
            logger.info("[CLAUDE_API] reply={}".format(res_content))
            return {
                "total_tokens": total_tokens,
                "completion_tokens": completion_tokens,
                "content": res_content,
            }
        except Exception as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, OpenAIError.RateLimitError):
                logger.warn("[CLAUDE_API] RateLimitError: {}".format(e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, OpenAIError.Timeout):
                logger.warn("[CLAUDE_API] Timeout: {}".format(e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, OpenAIError.APIConnectionError):
                logger.warn("[CLAUDE_API] APIConnectionError: {}".format(e))
                need_retry = False
                result["content"] = "我连接不到你的网络"
            else:
                logger.warn("[CLAUDE_API] Exception: {}".format(e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[CLAUDE_API] 第{}次重试".format(retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result

    def _model_mapping(self, model) -> str:
        if model == "claude-3-opus":
            return "claude-3-opus-20240229"
        elif model == "claude-3-sonnet":
            return "claude-3-sonnet-20240229"
        elif model == "claude-3-haiku":
            return "claude-3-haiku-20240307"
        elif model == "claude-3.5-sonnet":
            return "claude-3-5-sonnet-20240620"
        return model
