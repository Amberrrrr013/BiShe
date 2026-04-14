# 项目现状巡检与开题报告差距分析（2026-04-14）

## 1) 当前项目主要功能（基于代码结构）

### 1.1 端到端流程
项目已经具备“文本 -> 语音 -> 头像驱动视频 -> 字幕烧录”的完整流水线能力，主流程由 `SpeechVideoWorkflow` 编排。对应节点包括：
- `generate_text`
- `process_image`
- `synthesize_speech`
- `generate_video`
- `add_subtitles`
- `finalize`

并且支持在条件分支下跳过图像或视频（纯音频、文本视频）模式。

### 1.2 三类使用模式
- 手动/半自动模式：由 `workflow.py` 主流程提供。
- Agent 模式：由 `ai_agent.py` 和 `agent_workflow.py` 提供，支持技能式调用（文本、语音、视频、评估）。
- Web 服务模式：`server.py` 提供 Flask API 和前端入口（`/frontend`, `/agent`）。

### 1.3 模块分层
项目在 `models/` 下已有较清晰分层：
- `models/text`：文本生成（用户文本、AI 生成、随机文本）
- `models/tts`：语音合成
- `models/image`：图像来源与处理
- `models/video`：Talking-head 视频生成
- `models/video_editor.py`：字幕与后处理

---

## 2) 代码中当前的主要问题（优先级从高到低）

### P0（必须先修）
1. **存在明文 API Key 泄露风险**
   - `server.py` 的 `MODEL_CONFIGS` 中出现明文 key。
   - `ai_agent.py` 中也有默认 fallback key。
   - 这会导致密钥泄露、账号被盗用、仓库污染历史。

2. **配置文件与导入关系不一致，导致可运行性脆弱**
   - 多处 `from config import API_CONFIG, PROJECT_ROOT, OUTPUT_DIR`，但仓库根目录只有 `config/` 包和 `config.example.py`，缺少可直接导入的 `config.py`。
   - `server.py` 还引用 `api_config.py`（`from api_config import api_manager`），该文件在仓库中不存在。

### P1（高优）
3. **跨平台路径硬编码严重（Windows 固定路径）**
   - 多个文件固定 `D:\_BiShe\...`，Linux/容器环境无法直接运行。
   - 也造成实验复现困难，不利于论文“可实现性/可复用性”论证。

4. **参数体系不统一（教学难度、风格标签冲突）**
   - 文本模块支持 `elementary/middle_school/high_school/college_cet/english_major/native`。
   - API/工作流又大量使用 `easy/intermediate/advanced`。
   - 这会导致 Prompt 约束失效或表现不稳定，难以做教学分层评估。

5. **Agent 仍偏“工具串联”，缺少显式“任务规划-质量反馈-重生成”闭环状态机**
   - 代码中已有质量评估技能，但在“质量阈值触发重生成”上的流程标准化还不够清晰。
   - 与开题报告中的“Task Planner -> Quality Checker -> Feedback Refinement”目标尚有差距。

### P2（中优）
6. **测试体系偏脚本化，缺少自动化基线评测**
   - 当前有大量 `test_*.py` 文件，但更像手工调试脚本。
   - 缺少统一的 smoke test、接口契约测试、质量指标回归记录。

7. **研究数据资产不足（语料模板库/评估问卷/结果记录）**
   - 开题报告强调 TED 结构模板与教学评估，但仓库未看到成体系的数据目录与标注规范。

---

## 3) 对照开题报告：建议的改造路线

### 阶段A（1周内）：先完成“可运行 + 安全 + 可复现”
1. 新建统一配置层：
   - 增加 `config.py`（本地私有，不入库）+ `.env` + `config/defaults.py`（入库）。
   - 所有 API key 改为环境变量注入。
2. 移除硬编码路径：
   - 统一使用 `Path(__file__).resolve().parent` 与环境变量 `MODEL_ROOT`。
3. 补齐缺失依赖文件：
   - 明确 `api_config.py` 是否弃用；若保留，补齐实现；若弃用，删除引用并改路由逻辑。

### 阶段B（2~3周）：对齐“单 Agent 调度架构”
1. 引入显式任务状态模型（建议 Pydantic）：
   - `InputSpec -> Plan -> Script -> TTS -> Video -> QC -> Retry/Accept`。
2. 统一参数本体（ontology）：
   - `difficulty` 统一到一套枚举（建议沿用开题报告中的 6 档）。
   - `style` 与模板库一一映射，并提供默认回退策略。
3. 增强质量闭环：
   - 至少实现 3 个阈值门控：文本长度偏差、语速/时长匹配、字幕时间轴一致性。

### 阶段C（论文支撑）：形成“可研究、可展示、可答辩”证据链
1. 构建教学模板库与语料标注：
   - 例如 `data/templates/` 下维护三段式、问题引入式等模板。
2. 建立评估管线：
   - 自动指标（WER、时长偏差、字幕对齐率）+ 主观问卷（教师/学生）。
3. 增加实验记录结构：
   - `experiments/YYYYMMDD_run_x/metadata.json` 保存输入参数、模型版本、评分结果。

---

## 4) 最小可执行重构清单（建议按此顺序）

1. `server.py` / `ai_agent.py`：删除明文 key，改 `os.getenv()`。
2. 新增 `config.py` 生成策略（或 `config_loader.py`），保证 `from config import ...` 可用。
3. 全局替换 `D:\_BiShe\...` 为相对路径+环境变量。
4. 在 `workflow.py` 增加统一 `validate_input_config()`，严格校验 `difficulty/style/method`。
5. 在 `QualityEvaluationSkill` 后增加自动重试策略（最多 N 次，写入原因日志）。
6. 增加 `tests/test_smoke_pipeline.py`：至少验证 text-only 与 full pipeline 两条路径。

---

## 5) 与开题目标的匹配结论

- **已具备基础**：模块化多模态流水线 + Agent 化雏形已经存在，作为本科毕设原型是可行的。
- **核心差距**：还缺“可复现、可评估、可闭环优化”的工程与研究支撑层。
- **建议策略**：不要继续扩模型种类，优先做“统一配置 + 参数体系 + 质量闭环 + 评估记录”。这最能直接支撑论文第四章“实现与结果分析”。

