# 《山货有话说》—— AI 助农数字文创平台

> 拍一张山货照片，AI 为它**识别建档、写卖点文案、画文创海报、配语音介绍、生成短视频脚本**；再用 **AI 数字讲解员**带你云游乡村。
>
> 对应竞赛指定命题：**"乡村振兴·科创赋能"**（融合 AIGC 数字创意）
> 全国大学生数字媒体科技作品及创意竞赛参赛作品 v0.1

---

## 一、作品亮点（写进作品说明书的创新点）

1. **一条照片流，四件套产出**：单张农产品照片 → 多模态大模型识别 → 大模型文案 + AIGC 海报 + 智能语音 + 分镜脚本，全流程 ≤ 30 秒。
2. **"助农 + 文旅"双场景**：山货四件套解决"卖难"，AI 数字讲解员（29 个村落 · 覆盖 24 省区，支持省份筛选）解决"游难"，一个产品讲两个乡村振兴故事。
3. **多厂商模型引擎，一键切换**：内置智谱 GLM / DeepSeek / 通义千问 / Kimi / OpenAI 五家适配，支持网页"接入大模型"按钮在线接 Key；识图/生图能力随厂商自动适配，调用失败自动降级演示数据。
4. **用户系统 + 生成历史**：注册/登录（PBKDF2 加密存储、令牌会话），登录后每次创作自动存档，可随时回看与删除。
5. **低成本可复制**：全部基于开放 API（OpenAI 兼容接口 + Edge-TTS + SQLite），不依赖自训练模型，任何县域都能零门槛使用；未配置 Key 时自动进入演示模式，开箱即用。
6. **中文海报可靠排版**：AI 生成底图 + 本地精确文字排版合成，解决文生图模型中文乱码的行业痛点。

## 二、技术架构

```
┌─────────────┐   HTTP    ┌──────────────────────────────┐
│  前端 H5     │ ────────▶ │  FastAPI 后端                 │
│  Vue3+Vite  │           │  ├─ /api/recognize 多模态识图  │
│  +Tailwind  │ ◀──────── │  ├─ /api/generate  文案+脚本   │
└─────────────┘           │  ├─ /api/poster    海报合成    │
                          │  ├─ /api/tts       语音合成    │
                          │  └─ /api/guide    数字讲解员  │
                          └──────────────────────────────┘
                                    │
        ┌───────────────┬───────────┼──────────────┬──────────┐
        ▼               ▼           ▼              ▼          ▼
   多模态大模型      文本大模型    文生图 API      Edge-TTS   本地PIL模板
  (glm-4v-flash)  (glm-4-flash) (cogview-3-flash)  (免费)    (离线兜底)
```

- **后端** `backend/`：Python 3.13 + FastAPI，OpenAI 兼容接口统一封装（可一键切换智谱/DeepSeek/通义），Pillow 海报合成，edge-tts 语音
- **前端** `frontend/`：Vue 3 + Vite + Tailwind CSS 4，移动端优先响应式，`npm run build` 后由 FastAPI 统一托管
- **演示模式**：`backend/.env` 不填 Key 时，识图/文案走内置演示数据、海报走本地模板合成、TTS 正常可用——**无 Key 也能完整演示**

## 三、快速启动

> **微信小程序版**：`miniprogram/` 目录，用微信开发者工具导入即可运行（游客模式免 AppID），详见 `miniprogram/README.md`。
>
> **Windows 日常使用：直接双击项目根目录的 `启动.bat`（自动开浏览器），详见 `使用说明.md`——支持一键开机自启，重启电脑后无需任何操作。**
> 以下命令行方式适合开发调试：

```bash
# 1. 后端（首次）
cd backend
pip install -r requirements.txt
copy .env.example .env        # 想启用真实 AI：编辑 .env 填入 API Key
python run.py                 # 服务跑在 http://127.0.0.1:8000

# 2. 前端（开发时）
cd ../frontend
npm install
npm run dev                   # http://127.0.0.1:5173（已代理 /api 与 /static）

# 3. 前端（演示/交付：构建后由后端统一托管，只需跑后端）
cd ../frontend
npm run build
# 访问 http://127.0.0.1:8000 即可
```

**获取免费 API Key（可选）**：最方便的方式是直接在网页上点 **"＋ 接入大模型"** 按钮——选厂商、粘贴 Key、验证连接，一步到位（Key 保存在本机 `backend/.env`，重启后仍生效）。也可以手动注册 [智谱开放平台](https://open.bigmodel.cn) 后把 Key 填入 `backend/.env` 的 `GLM_API_KEY`。
`glm-4-flash`、`glm-4v-flash`、`cogview-3-flash` 三个模型**全部免费**，整套真实 AI 能力零成本。
也支持 DeepSeek / 通义千问 / Kimi / OpenAI——同样通过按钮或 `.env` 接入，之后在"模型引擎"栏一键切换（默认 `auto` 自动选用第一个有 Key 的厂商）。

## 四、API 一览

| 方法 | 路径 | 功能 | 关键参数 |
|---|---|---|---|
| POST | `/api/recognize` | 农产品识图建档 | `image`: base64/dataURL |
| POST | `/api/generate` | 卖点文案 + 短视频脚本 | `name/category/origin/highlights` |
| POST | `/api/poster` | AIGC 文创海报 | `image/name/tagline/origin` |
| POST | `/api/tts` | 语音介绍（mp3） | `text` |
| GET | `/api/villages` | 内置村落列表（29 个，覆盖 24 省区） | — |
| POST | `/api/guide` | 数字讲解员讲解/问答 | `village_id`, `question?` |
| GET | `/api/providers` | 模型厂商列表与当前状态 | — |
| POST | `/api/providers/switch` | 切换模型厂商（需已配置对应 Key） | `provider_id` |
| POST | `/api/providers/connect` | 在线接入厂商（验证 Key → 存 .env → 立即生效） | `provider_id`, `api_key` |
| POST | `/api/auth/register` | 注册（成功自动登录，返回令牌） | `username`, `password`, `nickname?` |
| POST | `/api/auth/login` | 登录，返回令牌 | `username`, `password` |
| POST | `/api/auth/logout` | 登出（令牌作废） | — |
| GET | `/api/auth/me` | 当前用户信息 | Authorization: Bearer 令牌 |
| GET/POST/DELETE | `/api/auth/history` | 每用户生成历史（登录后自动存档四件套） | — |
| GET | `/api/health` | 健康检查（含演示模式状态） | — |

交互式文档：启动后访问 <http://127.0.0.1:8000/docs>

## 五、目录结构

```
比赛2/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口（托管前端构建产物）
│   │   ├── config.py          # .env 配置（演示模式自动判定）
│   │   ├── schemas.py         # Pydantic 数据模型
│   │   ├── demo_data.py       # 演示数据（6 种山货 + 4 个村落）
│   │   ├── routers/           # recognize / generate / poster / tts / guide
│   │   └── services/          # llm / vision / poster / tts 封装
│   ├── generated/             # 生成的海报与语音（运行时产生）
│   ├── requirements.txt
│   ├── .env.example           # 配置模板（含免费模型说明）
│   └── run.py
├── frontend/
│   ├── src/
│   │   ├── App.vue            # 主流程编排
│   │   ├── api.js             # 接口封装
│   │   └── components/        # UploadPanel / ResultsPanel / GuidePanel
│   └── dist/                  # 构建产物（后端托管）
├── test_images/               # 测试照片
└── README.md
```

## 六、参赛交付清单（对照竞赛要求）

| 交付物 | 状态 | 位置/说明 |
|---|---|---|
| 可运行作品（H5） | ✅ 已完成 | 后端启动后访问 <http://127.0.0.1:8000> |
| 演示视频（1080P/16:9/MP4/≤5min） | ⬜ 待录制 | 按"创意阐述 1min + 功能演示 3min + 价值总结 1min"脚本录制 |
| 作品说明书 | ✅ 已完成 | `交付物/作品说明书-山货有话说.docx`（补全【】占位的团队信息即可提交） |
| 素材拍摄清单 | ✅ 已完成 | `素材/拍摄清单.md`（含品类、构图、光线要求） |
| 演示视频录制脚本 | ✅ 已完成 | `交付物/演示视频录制脚本.md`（分镜+口播词，照做 10 分钟录完） |
| 源码与运行说明 | ✅ 已完成 | 本仓库 |
| 校内报名 | ⬜ 待办理 | 向教务处/竞赛负责人提交（确认 2026 指定命题文件与《竞赛指南》） |

### 四周冲刺计划

- **第 1 周**：✅ 架构搭建 + 全链路 API 跑通（本周已完成原型）
- **第 2 周**：真实 Key 全量联调、prompt 调优、准备 5~8 个真实农产品素材
- **第 3 周**：UI 打磨、移动端实测、云端部署备份、数据可视化加分项
- **第 4 周**：演示视频录制、作品说明书、报名提交

## 七、风险与对策

| 风险 | 对策 |
|---|---|
| 2026 指定命题文件尚未发布 | 作品同时覆盖"乡村振兴 + AIGC"两个命题关键词，可灵活对口 |
| AI 生成质量不稳定 | 提示词模板已内置产品营销专家角色；演示数据兜底 |
| 评审现场网络故障 | 演示模式完全离线可用（本地模板海报 + 内置文案 + 缓存音频） |
