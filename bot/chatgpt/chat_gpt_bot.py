# encoding:utf-8
import openai
import requests
from bot.openai.open_ai_bot import OpenAIBot
from common.log import logger
from config import conf


class AzureChatGPTBot(OpenAIBot):
    def __init__(self):
        super().__init__()
        self.client = openai.AzureOpenAI(
            api_key=conf().get("open_ai_api_key"),
            api_version=conf().get("azure_api_version", "2023-07-01-preview"),
            azure_endpoint=conf().get("azure_openai_api_base")
        )
        self.args["model"] = conf().get("azure_deployment_id")

    def create_img(self, query, retry_count=0, api_key=None):
        text_to_image_model = conf().get("text_to_image")
        if text_to_image_model == "dall-e-2":
            api_version = "2023-06-01-preview"
            endpoint = conf().get("azure_openai_dalle_api_base", "open_ai_api_base")
            if not endpoint.endswith("/"):
                endpoint += "/"
            url = f"{endpoint}openai/images/generations:submit?api-version={api_version}"
            api_key = conf().get("azure_openai_dalle_api_key", "open_ai_api_key")
            headers = {"api-key": api_key, "Content-Type": "application/json"}
            try:
                body = {"prompt": query, "size": conf().get("image_create_size", "256x256"), "n": 1}
                submission = requests.post(url, headers=headers, json=body)
                operation_location = submission.headers['operation-location']
                status = ""
                while status != "succeeded":
                    if retry_count > 3:
                        return False, "图片生成失败"
                    response = requests.get(operation_location, headers=headers)
                    status = response.json()['status']
                    retry_count += 1
                image_url = response.json()['result']['data'][0]['url']
                return True, image_url
            except Exception as e:
                logger.error(f"create image error: {e}")
                return False, "图片生成失败"
        elif text_to_image_model == "dall-e-3":
            try:
                response = self.client.images.generate(
                    model=conf().get("azure_openai_dalle_deployment_id", "text_to_image"),
                    prompt=query,
                    size=conf().get("image_create_size", "1024x1024"),
                    quality=conf().get("dalle3_image_quality", "standard"),
                    n=1
                )
                if response.data and len(response.data) > 0:
                    image_url = response.data[0].url
                    return True, image_url
                else:
                    logger.error("响应中没有图像 URL")
                    return False, "图片生成失败"
            except openai.APIError as e:
                error_message = f"生成图像时发生API错误: {str(e)}"
                logger.error(error_message)
                return False, error_message
            except Exception as e:
                error_message = f"生成图像时发生错误: {str(e)}"
                logger.error(error_message)
                return False, "图片生成失败"
        else:
            return False, "图片生成失败，未配置text_to_image参数"
