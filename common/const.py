# bot_type
OPEN_AI = "openAI"
# CHATGPT = "chatGPT"
BAIDU = "baidu"  # 百度文心一言模型
XUNFEI = "xunfei"
CHATGPTONAZURE = "chatGPTOnAzure"
LINKAI = "linkai"
CLAUDEAI = "claude"  # 使用cookie的历史模型
CLAUDEAPI= "claudeAPI"  # 通过Claude api调用模型
QWEN = "qwen"  # 旧版通义模型
QWEN_DASHSCOPE = "dashscope"  # 通义新版sdk和api key


GEMINI = "gemini"  # gemini-1.0-pro
ZHIPU_AI = "glm-4"
MOONSHOT = "moonshot"
MiniMax = "minimax"


# model
CLAUDE3 = "claude-3-opus-20240229"
GPT35 = "gpt-3.5-turbo"
GPT35_0125 = "gpt-3.5-turbo-0125"
GPT35_1106 = "gpt-3.5-turbo-1106"

GPT_4o = "gpt-4o"
GPT_4o_05_13 = "gpt-4o-2024-05-13"
GPT_4o_08_06 = "gpt-4o-2024-08-06"
chatgpt_4o_latest = "chatgpt-4o-latest"
GPT4_TURBO = "gpt-4-turbo"
GPT4_TURBO_PREVIEW = "gpt-4-turbo-preview"
GPT4_TURBO_04_09 = "gpt-4-turbo-2024-04-09"
GPT4_TURBO_01_25 = "gpt-4-0125-preview"
GPT4_TURBO_11_06 = "gpt-4-1106-preview"
GPT4_VISION_PREVIEW = "gpt-4-vision-preview"

GPT4 = "gpt-4"
GPT_4o_MINI = "gpt-4o-mini"
GPT4_32k = "gpt-4-32k"
GPT4_06_13 = "gpt-4-0613"
GPT4_32k_06_13 = "gpt-4-32k-0613"

WHISPER_1 = "whisper-1"
TTS_1 = "tts-1"
TTS_1_HD = "tts-1-hd"

WEN_XIN = "wenxin"
WEN_XIN_4 = "wenxin-4"

QWEN_TURBO = "qwen-turbo"
QWEN_PLUS = "qwen-plus"
QWEN_MAX = "qwen-max"

LINKAI_35 = "linkai-3.5"
LINKAI_4_TURBO = "linkai-4-turbo"
LINKAI_4o = "linkai-4o"

GEMINI_PRO = "gemini-1.0-pro"
GEMINI_15_flash = "gemini-1.5-flash"
GEMINI_15_PRO = "gemini-1.5-pro"

MODEL_LIST = [
              GPT35, GPT35_0125, GPT35_1106, "gpt-3.5-turbo-16k",
              GPT_4o, GPT_4o_MINI, GPT4_TURBO, GPT4_TURBO_PREVIEW, GPT4_TURBO_01_25, GPT4_TURBO_11_06, GPT4, GPT4_32k, GPT4_06_13, GPT4_32k_06_13,
              WEN_XIN, WEN_XIN_4,
              XUNFEI, ZHIPU_AI, MOONSHOT, MiniMax,
              GEMINI, GEMINI_PRO, GEMINI_15_flash, GEMINI_15_PRO,
              "claude", "claude-3-haiku", "claude-3-sonnet", "claude-3-opus", "claude-3-opus-20240229", "claude-3.5-sonnet",
              "moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k",
              QWEN, QWEN_TURBO, QWEN_PLUS, QWEN_MAX,
              LINKAI_35, LINKAI_4_TURBO, LINKAI_4o
            ]

# channel
FEISHU = "feishu"
DINGTALK = "dingtalk"

VISION_MODEL_SYSTEM_PROMPT = "你是一个专业的图像分析师，请用中文详细描述图片内容。"
PDF_MODEL_SYSTEM_PROMPT = '''您将收到一个PDF页面或幻灯片的图像。您的目标是以技术术语讨论您所看到的内容，就像您正在进行演示一样。

如果有图表，请描述图表并解释其含义。
例如：如果有一个描述流程的图表，可以这样说："流程从X开始，然后我们有Y和Z..."

如果有表格，请逻辑地描述表格中的内容。
例如：如果有一个列出项目和价格的表格，可以这样说："价格如下：A的价格是X，B的价格是Y..."

不要包含涉及内容格式的术语。
不要提及内容类型 - 请专注于内容本身。
例如：如果图像中有图表/图形和文本，请描述两者，但不要提及一个是图表，另一个是文本。
只需描述您在图表中看到的内容以及您从文本中理解的内容。

您应该保持简洁，但请记住您的听众无法看到图像，所以要详尽地描述内容。

排除与内容无关的元素：
不要提及页码或图像上元素的位置。

------

如果有可识别的标题，请识别标题并按以下格式给出输出：

{标题}

{内容描述}

如果没有明确的标题，只需返回内容描述。
'''

SUPPORT_FILE_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx', '.csv','.xls', '.xlsx', '.ppt', '.pptx']

HELP_TEXT_SUFFIX = f'''
普通指令：
提问：直接提问，例如：
什么是勾股定理？

可以使用的特殊指令包括：

1. 画图指令：
可使用 “画” 开头的指令来绘图，例如：
画一个卡通人物
画一个苹果

2. 搜索指令：
可使用“搜索”开头的指令来搜索信息，例如：
搜索南京的天气预报
搜索今年的诺贝尔奖获得者

3. 上传文件分析：
支持的文件类型包括：
{SUPPORT_FILE_EXTENSIONS}
'''