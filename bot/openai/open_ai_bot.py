# encoding:utf-8
import os
import time
from openai import OpenAI
from openai import OpenAIError

from bot.bot import Bot
from bot.chatgpt.chat_gpt_session import ChatGPTSession
from bot.session_manager import SessionManager
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from common.log import logger
from common.token_bucket import TokenBucket
from common.const import PDF_MODEL_SYSTEM_PROMPT, VISION_MODEL_SYSTEM_PROMPT
from config import conf, load_config
from common.utils import get_img_uri, encode_image

from pdf2image import convert_from_path
from pdfminer.high_level import extract_text
from openai import OpenAI        
import docx2txt
import pandas as pd
import io
import tempfile
import aspose.slides as slides
import aspose.pydrawing as drawing


user_session = dict()


# OpenAI对话模型API (可用)
class OpenAIBot(Bot):
    def __init__(self):
        super().__init__()
        self.client = OpenAI(
            api_key=conf().get("open_ai_api_key"),
            base_url=conf().get("open_ai_api_base")
        )
        self.perplexity_client = OpenAI(api_key=conf().get("perplexity_api_key"), base_url=conf().get("perplexity_base_url"))
        self.perplexity_model = conf().get("perplexity_model")
        self.sessions = SessionManager(ChatGPTSession, model=conf().get("model") or "gpt-4o")

        proxy = conf().get("proxy")
        if proxy:
            self.client.proxy = proxy
            self.perplexity_client.proxy = proxy

        if conf().get("rate_limit_chatgpt"):
            self.tb4chatgpt = TokenBucket(conf().get("rate_limit_chatgpt", 20))

        self.args = {
            "model": conf().get("model") or "gpt-4o",  # 对话模型的名称
            # "temperature": conf().get("temperature", 0.7),  # 值在[0,1]之间，越大表示回复越具有不确定性
            # # "max_tokens":4096,  # 回复最大的字符数
            # "top_p": conf().get("top_p", 1),
            # "frequency_penalty": conf().get("frequency_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            # "presence_penalty": conf().get("presence_penalty", 0.0),  # [-2,2]之间，该值越大则更倾向于产生不同的内容
            "timeout": conf().get("request_timeout", None),  # 重试超时时间，在这个时间内，将会自动重试
        }

    def file_analysis(self, session: ChatGPTSession, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        
        analysis_methods = {
            '.pdf': self.pdf_analysis,
            '.txt': self.text_analysis,
            '.doc': self.text_analysis,
            '.docx': self.text_analysis,
            '.csv': self.tabular_analysis,
            '.xls': self.tabular_analysis,
            '.xlsx': self.tabular_analysis,
            '.ppt': self.ppt_analysis,
            '.pptx': self.ppt_analysis
        }
        
        analysis_method = analysis_methods.get(file_extension)
        if analysis_method:
            return analysis_method(session, file_path)
        else:
            return {"content": "不支持的文件类型"}

    def text_analysis(self, session: ChatGPTSession, file_path):
        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".txt":
            with open(file_path, 'r', encoding='utf-8') as file:
                text = file.read()
        else:  # .txt
            text = docx2txt.process(file_path)
                  
        file_name = os.path.basename(file_path)
        session.add_query(f"读取以下文件: {file_name}")
        session.add_reply('文件内容如下：\n\n'+text)
        return {"content": f"文件读取已完成，如不需继续分析，请回复\n\n{conf().get('clear_memory_commands')[0]}"}

    def tabular_analysis(self, session: ChatGPTSession, file_path):


        file_extension = os.path.splitext(file_path)[1].lower()
        file_name = os.path.basename(file_path)
        session.add_query(f"读取以下{'Excel' if file_extension in ['.xls', '.xlsx'] else 'CSV'}文件: {file_name}")


        if file_extension == ".csv":  # .csv
            df = pd.read_csv(file_path)
            csv_text = df.to_csv(index=False)
            session.add_reply('文件内容如下：\n\n'+csv_text)
            return {"content": f"CSV文件读取已完成，如不需继续分析，请回复\n\n{conf().get('clear_memory_commands')[0]}"}
        else:
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            for sheet_name in sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                buffer = io.StringIO()
                df.to_csv(buffer, index=False)
                sheet_content = buffer.getvalue()
                session.add_query(f"读取Excel文件的Sheet: {sheet_name}")
                session.add_reply(f'Sheet名称: {sheet_name}\n\n文件内容如下：\n\n{sheet_content}')
                logger.info(f"Sheet名称: {sheet_name}\n\n文件内容如下：\n\n{sheet_content}")
            return {"content": f"Excel文件读取已完成，共处理了 {len(sheet_names)} 个工作表。\n\n如不需继续分析，请回复\n\n{conf().get('clear_memory_commands')[0]}"}
    
    
    def pdf_analysis(self, session: ChatGPTSession, file_path):
        
        try:
            # Convert PDF to images
            images = convert_from_path(file_path)
            
            # Extract text (optional)
            # text = extract_text(file_path)

            # Analyze images with GPT-4V
            for i in range(len(images)):  # Skip first page if it's just an intro
                img_uri = get_img_uri(images[i])
                session.add_query(f"分析{os.path.basename(file_path)}中的第{i+1}页")
                description = self.analyze_image(session, img_uri, prompt=PDF_MODEL_SYSTEM_PROMPT)
                logger.info(f"PDF分析结果: {description}")

            try:
                os.remove(file_path)
            except Exception as e:
                pass
            
            return {
                "content": f"文件读取已完成，如不需继续分析，请回复\n\n{conf().get('clear_memory_commands')[0]}",
            }
            # Store or process the results as needed
            # For example, you could save it to a database or send a summary to the user


        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {
                "content": "文件分析失败",
            }

            # logger.debug("[{}] response={}".format(self.args["model"], response))
            # logger.info("[{}] reply={}, total_tokens={}".format(self.args["model"], response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
        
    
    def ppt_analysis(self, session: ChatGPTSession, file_path):
        try:
            pdf_path = os.path.splitext(file_path)[0] + ".pdf"
            with slides.Presentation(file_path) as presentation:
                presentation.save(pdf_path, slides.export.SaveFormat.PDF)

            return self.pdf_analysis(session, pdf_path)
        
        except Exception as e:
            logger.error(f"Error processing PPT: {str(e)}")
            return {
                "content": "PPT文件分析失败",
            }

    def analyze_image(self, session: ChatGPTSession, img_url, prompt=VISION_MODEL_SYSTEM_PROMPT):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": 
                            {
                                "url": img_url
                            },
                    }
                    ],
                }
            ],
            max_tokens=300,
            top_p=0.1   
        )
        session.add_reply(response.choices[0].message.content)
        result = {
                "total_tokens": response.usage.total_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "content": response.choices[0].message.content,
            }
        return result

    def create_img(self, query, retry_count=0):
        try:
            if conf().get("rate_limit_dalle") and not self.tb4dalle.get_token():
                return False, "请求太快了，请休息一下再问我吧"
            logger.info("[{}] image_query={}".format(self.args["model"], query))
            response = self.client.images.generate(
                model=conf().get("text_to_image") or "dall-e-3",
                prompt=query,  # 图片描述
                n=1,  # 每次生成图片的数量
                size=conf().get("image_create_size", "1024x1024"),  # 图片大小,可选有 256x256, 512x512, 1024x1024
            )
            image_url = response.data[0].url
            logger.info("[{}] image_url={}".format(self.args["model"], image_url))
            return True, image_url
        except OpenAIError.RateLimitError as e:
            logger.warn(e)
            if retry_count < 1:
                time.sleep(5)
                logger.warn("[{}] ImgCreate RateLimit exceed, 第{}次重试".format(self.args["model"], retry_count + 1))
                return self.create_img(query, retry_count + 1)
            else:
                return False, "画图出现问题，请休息一下再问我吧"
        except Exception as e:
            logger.exception(e)
            return False, "画图出现问题，请休息一下再问我吧"

    def reply(self, query, context=None):
        session_id = context["session_id"]
        clear_memory_commands = conf().get("clear_memory_commands", ["#清除记忆"])

        if context.type == ContextType.TEXT:
            if query in clear_memory_commands:
                self.sessions.clear_session(session_id)
                return Reply(ReplyType.INFO, "记忆已清除")
            elif query == "#清除所有":
                self.sessions.clear_all_session()
                return Reply(ReplyType.INFO, "所有人记忆已清除")
            elif query == "#更新配置":
                load_config()
                return Reply(ReplyType.INFO, "配置已更新")

            session = self.sessions.session_query(query, session_id)
            logger.debug("[{}] session query={}".format(self.args["model"], session.messages))

            model = context.get("gpt_model")
            new_args = self.args.copy()
            if model:
                new_args["model"] = model
            # if context.get('stream'):
            #     # reply in stream
            #     return self.reply_text_stream(query, new_query, session_id)
            reply_content = self.reply_text(session, args=new_args)
            logger.debug(
                "[{}] new_query={}, session_id={}, reply_cont={}, completion_tokens={}".format(
                    self.args["model"],
                    session.messages,
                    session_id,
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], session_id, reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
                logger.debug("[{}] reply {} used 0 tokens.".format(self.args["model"], reply_content))
            return reply

        elif context.type == ContextType.SEARCH:
            logger.info("[{}] Handling search query: {}".format(self.args["model"], query))
            session = self.sessions.session_query(query, context["session_id"])
            new_args = self.args.copy()
            new_args["model"] = conf().get("perplexity_model")
            reply_content = self.reply_search(session, args=new_args)
            
            logger.debug(
                "[{}] search_query={}, session_id={}, reply_content={}, completion_tokens={}".format(
                    self.args["model"],
                    session.messages,
                    context["session_id"],
                    reply_content["content"],
                    reply_content["completion_tokens"],
                )
            )
       
            
            if reply_content["completion_tokens"] == 0 and len(reply_content["content"]) > 0:
                reply = Reply(ReplyType.ERROR, reply_content["content"])
            elif reply_content["completion_tokens"] > 0:
                self.sessions.session_reply(reply_content["content"], context["session_id"], reply_content["total_tokens"])
                reply = Reply(ReplyType.TEXT, reply_content["content"])
            else:
                reply = Reply(ReplyType.ERROR, "搜索查询未返回结果")
                logger.debug("[{}] Search query {} used 0 tokens.".format(self.args["model"], reply_content))
            
            return reply
        
        elif context.type == ContextType.FILE:
            cmsg = context["msg"]
            cmsg.prepare()
            session = self.sessions.build_session(context["session_id"])
            reply_content = self.file_analysis(session, context.content)
            reply = Reply(ReplyType.TEXT, reply_content["content"])
            return reply
            
        elif context.type == ContextType.IMAGE:
            cmsg = context["msg"]
            cmsg.prepare()
            session = self.sessions.build_session(context["session_id"])
            session.add_query("分析以下图片")
            image_url = encode_image(context.content)
            reply_content = self.analyze_image(session,image_url)
            reply = Reply(ReplyType.TEXT, reply_content["content"])
            return reply

        elif context.type == ContextType.IMAGE_CREATE:
            ok, retstring = self.create_img(query, 0)
            reply = None
            if ok:
                reply = Reply(ReplyType.IMAGE_URL, retstring)
            else:
                reply = Reply(ReplyType.ERROR, retstring)
            return reply
        else:
            reply = Reply(ReplyType.ERROR, "Bot不支持处理{}类型的消息".format(context.type))
            return reply

    def reply_search(self, session: ChatGPTSession, args=None, retry_count=0) -> dict:

        try:
            if args is None:
                args = self.args
            response = self.perplexity_client.chat.completions.create(messages=session.messages, **args)
            # logger.debug("[{}] response={}".format(self.args["model"], response))
            # logger.info("[{}] reply={}, total_tokens={}".format(self.args["model"], response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {
                "total_tokens": response.usage.total_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "content": response.choices[0].message.content,
            }
        except OpenAIError.APIError as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, OpenAIError.RateLimitError):
                logger.warn("[{}] RateLimitError: {}".format(self.args["model"], e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, OpenAIError.Timeout):
                logger.warn("[{}] Timeout: {}".format(self.args["model"], e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, OpenAIError.APIError):
                logger.warn("[{}] Bad Gateway: {}".format(self.args["model"], e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, OpenAIError.APIConnectionError):
                logger.warn("[{}] APIConnectionError: {}".format(self.args["model"], e))
                result["content"] = "我连接不到你的网络"
                if need_retry:
                    time.sleep(5)
            else:
                logger.exception("[{}] Exception: {}".format(self.args["model"], e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[{}] 第{}次重试".format(self.args["model"], retry_count + 1))
                return self.reply_search(session, retry_count + 1)
            else:
                return result


    def reply_text(self, session: ChatGPTSession, args=None, retry_count=0) -> dict:
        """
        call openai's ChatCompletion to get the answer
        :param session: a conversation session
        :param session_id: session id
        :param retry_count: retry count
        :return: {}
        """
        try:
            if conf().get("rate_limit_chatgpt") and not self.tb4chatgpt.get_token():
                raise OpenAIError.RateLimitError("RateLimitError: rate limit exceeded")
            if args is None:
                args = self.args
            response = self.client.chat.completions.create(messages=session.messages, **args)
            # logger.debug("[{}] response={}".format(self.args["model"], response))
            # logger.info("[{}] reply={}, total_tokens={}".format(self.args["model"], response.choices[0]['message']['content'], response["usage"]["total_tokens"]))
            return {
                "total_tokens": response.usage.total_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "content": response.choices[0].message.content,
            }
        except OpenAIError.APIError as e:
            need_retry = retry_count < 2
            result = {"completion_tokens": 0, "content": "我现在有点累了，等会再来吧"}
            if isinstance(e, OpenAIError.RateLimitError):
                logger.warn("[{}] RateLimitError: {}".format(self.args["model"], e))
                result["content"] = "提问太快啦，请休息一下再问我吧"
                if need_retry:
                    time.sleep(20)
            elif isinstance(e, OpenAIError.Timeout):
                logger.warn("[{}] Timeout: {}".format(self.args["model"], e))
                result["content"] = "我没有收到你的消息"
                if need_retry:
                    time.sleep(5)
            elif isinstance(e, OpenAIError.APIError):
                logger.warn("[{}] Bad Gateway: {}".format(self.args["model"], e))
                result["content"] = "请再问我一次"
                if need_retry:
                    time.sleep(10)
            elif isinstance(e, OpenAIError.APIConnectionError):
                logger.warn("[{}] APIConnectionError: {}".format(self.args["model"], e))
                result["content"] = "我连接不到你的网络"
                if need_retry:
                    time.sleep(5)
            else:
                logger.exception("[{}] Exception: {}".format(self.args["model"], e))
                need_retry = False
                self.sessions.clear_session(session.session_id)

            if need_retry:
                logger.warn("[{}] 第{}次重试".format(self.args["model"], retry_count + 1))
                return self.reply_text(session, retry_count + 1)
            else:
                return result
