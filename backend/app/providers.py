"""大模型厂商注册表。

新增厂商只需在此添加条目并在 .env 配置对应 Key：
    "厂商ID": {
        "name": "显示名",
        "base_url": "OpenAI 兼容接口地址",
        "key_env": "读取的环境变量名",
        "signup_url": "申请 Key 的入口网址（接入弹窗里展示）",
        "text_model": "文本模型（文案/故事/讲解）",
        "vision_model": "多模态识图模型，None=该厂商不支持",
        "img_model": "文生图模型（海报底图），None=不支持",
        "note": "一句话说明",
    }
"""

PROVIDERS = {
    "glm": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "key_env": "GLM_API_KEY",
        "signup_url": "https://open.bigmodel.cn/usercenter/apikeys",
        "text_model": "glm-4-flash",
        "vision_model": "glm-4v-flash",
        "img_model": "cogview-3-flash",
        "img_size": "768x1344",
        "note": "文本/识图/生图三个模型全部免费，学生团队推荐",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "key_env": "DEEPSEEK_API_KEY",
        "signup_url": "https://platform.deepseek.com/api_keys",
        "text_model": "deepseek-chat",
        "vision_model": None,
        "img_model": None,
        "note": "文案与故事质量出色；暂不支持识图与生图，海报走本地模板",
    },
    "qwen": {
        "name": "通义千问",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "key_env": "QWEN_API_KEY",
        "signup_url": "https://bailian.console.aliyun.com",
        "text_model": "qwen-plus",
        "vision_model": "qwen-vl-plus",
        "img_model": None,
        "note": "支持识图；生图走万相原生协议暂未接入，海报走本地模板",
    },
    "moonshot": {
        "name": "Kimi 月之暗面",
        "base_url": "https://api.moonshot.cn/v1",
        "key_env": "MOONSHOT_API_KEY",
        "signup_url": "https://platform.moonshot.cn/console/api-keys",
        "text_model": "moonshot-v1-8k",
        "vision_model": "moonshot-v1-8k-vision-preview",
        "img_model": None,
        "note": "长文本理解强，支持识图；生图暂不支持",
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "key_env": "OPENAI_API_KEY",
        "signup_url": "https://platform.openai.com/api-keys",
        "text_model": "gpt-4o-mini",
        "vision_model": "gpt-4o-mini",
        "img_model": "dall-e-3",
        "img_size": "1024x1792",
        "note": "能力全面，需海外网络环境",
    },
}
