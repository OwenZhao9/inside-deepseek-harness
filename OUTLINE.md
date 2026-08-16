# 《DeepSeek Harness 从 0 到 1》完整章节大纲

> 素材基线：dsh 仓库 `v0.1.0-rc.5`，`packages/` 下 219 个包 + `vendor/` 里 9 个连源码搬进来的框架包 + 2 个 app + 6 个 example；`.agents/notes` 683 篇双语设计笔记（proposed 25 / implemented 505 / rejected 11 / archived 142），`docs/postmortem` 4 篇事故复盘。全书所有代码引用均以该版本仓库相对路径给出。

---

## 全书结构总览

| 章 | 标题 | 难度 | 字数 |
|---|---|---|---|
| 1 | 十分钟：`npx` 跑起来，然后看懂你刚启动了什么 | 入门 | 12,000 |
| 2 | 主循环：turn、step 和 inbox——从 50 行长到 496 行 | 入门 | 20,000 |
| 3 | 工具：写你的第一个 `defineTool`，读懂那 51 个工具的目录 | 入门 | 18,000 |
| 4 | 会话即日志：事件溯源、surface 投影、fork/resume/replay | 入门→进阶 | 22,000 |
| 5 | 提示词是拼出来的：有序段落注册表与两条上下文通道 | 进阶 | 18,000 |
| 6 | 上下文经济学：四道防线、spill、skill，以及 KV cache 的账 | 进阶 | 20,000 |
| 7 | 组装层：Cordis 插件树与四层 patch——`dsh` 启动时到底发生了什么 | 进阶 | 22,000 |
| 8 | 权限：工具七段流水线、两条审批路径、Code Mode | 进阶 | 24,000 |
| 9 | 能力 seam：三角色拆包，与 4 行 YAML 把执行世界搬到远程 | 进阶→硬核 | 20,000 |
| 10 | 多智能体：subagent / workflow / jobs / goal / plan / schedule | 硬核 | 24,000 |
| 11 | 持久化：双后端、崩溃恢复、格式版本，与"模型可见即已记录"的执法机器 | 硬核 | 20,000 |
| 12 | 683 篇设计笔记与 4 篇事故复盘：一个仓库怎么记住自己为什么这么做 | 硬核（元层） | 16,000 |
| 13 | 让模型给自己写插件：运行时自修改、双半沙箱、以及一页迁移清单 | 最硬核 | 22,000 |

**正文合计 ≈ 258,000 字**，加前言、附录（工具目录速查表 / 事件词汇表 / seam 总表 / 术语中英对照）约 8,000 字，**全书约 26.5 万字**。

---

# 第 1 章　十分钟：`npx` 跑起来，然后看懂你刚启动了什么

**钩子**：你的机器上根本不存在一份完整的 dsh 配置文件——你看到的那棵插件树，是每次启动时当场算出来的。

## 小节

**1.1 三条命令**
`npx @deepseek-ai/dsh web`（README.zh.md:20 的原句）、`dsh --profile headless`、以及源码模式下的 `pnpm install && pnpm dsh web`。目标只有一个：让读者在 10 分钟内看到一个能跑的 agent，并知道自己刚才起的是哪一套。

**1.2 第一课不是读代码，是 `dsh --profile web --dump-config`**
让读者亲手打印出那棵"离线合成、和真实挂载完全一致"的树，重点看每段行前面的 `# == <来源文件>, patched by <哪些层>` 注释。建立全书第一个正确心智：磁盘上没有完整配置，里面出现的任何一行，你都可以用自己的 patch 换掉。配合 `apps/cli/composition.md`（自动生成的 mermaid 组合图）看 `dsh-base` 那 78 行插件都是什么。

**1.3 profile、bundle、patch：三个名词一次讲完**
profile = 声明了 `dsh.profile` 的目录；bundle = 声明了 `dsh.bundle` 的 npm 包；patch = 一个只有两种动作（按 `id` 改一行 / `insert` 加新行）的 YAML 文件。先给结论，机制留到第 7 章。

**1.4 第一个练习：写一条 home 级 patch**
在 `$DSH_HOME/cordis.patch.yml` 里改掉 `agent-default-model` 的模型名，重启，再 `--dump-config` 验证它确实压在了 bundle 层之上。三个必须提前警告的坑：改 `config` 是**整体替换不是深合并**（该行的每个键都要重抄）；空文件或只有注释的 patch 会抛错，想禁用这一层要写 `[]`；home 级优先级**高于** profile 级（这是刻意的：home 级代表"这台机器的偏好"）。

**1.5 出错了怎么读日志**
提前给三张"启动失败的脸"：模块解析失败（`plugin(s) failed to load: <名字>`）、插件 apply 抛异常（FAILED fiber 的原始 stack）、以及最难懂的第三种——插件既不报错也不干活，卡在 PENDING 等一个没人提供的服务。教读者遇到"我的插件没输出"先去找 `pending (waiting for services: xxx)` 这句话，而不是加 `console.log`。

## 关键文件

- `README.zh.md`
- `apps/cli/src/profile-boot.ts`
- `apps/cli/composition.md`
- `packages/bundle/base/cordis.patch.yml`
- `packages/boot/app-boot/README.zh.md`
- `docs/user/develop/basic/publish.zh.md`

**读者收益**：跑起来，并且第一天就装上"配置是算出来的、任何一行都可覆盖"这个正确心智，而不是去满硬盘找那个不存在的配置文件。

**字数**：12,000

---

# 第 2 章　主循环：turn、step 和 inbox——从 50 行长到 496 行

**钩子**：先写一个 50 行的 `while(true)` agent 循环，然后我问你五个问题；这五个问题的答案，就是 dsh 那 496 行里多出来的 446 行。

## 小节

**2.1 先写那 50 行**
`while(true) { const resp = await llm(messages); if (!resp.toolCalls) break; messages.push(...await runTools(resp.toolCalls)) }`。跑通它，然后依次追问：用户中途插话怎么办？怎么取消？崩溃后怎么恢复？插件怎么在发请求前改提示词？工具能不能并行？

**2.2 turn 与 step：为什么必须是两级**
一个 step = 一次模型请求 + 这次请求触发的工具执行；一个 turn = 0 到多个 step。"用户说一句话"和"模型调一次工具"是两种不同的续跑理由。先看 `docs/architecture.zh.md` 的 Turn flow 伪代码，再对照 `agent.ts` 的 `turn()` 逐行讲——伪代码和真代码几乎一一对应。特别讲清楚：一个 turn 可以有 **0 个 step**（被 pre-step 拒了），而这个空轮次仍然要写进日志。

**2.3 inbox：两条队列，三个 API 其实是一个原语**
`send(message, target, wakeup)` 是唯一原语，`followup=('next-turn', true)`、`steer=('next-step', true)`、`inject=('next-step', false)`。用一张 2×2 表讲完。`claim()` 在轮次边界取"全部 next-step + 一条 next-turn"，在步骤边界只取 next-step——这就是"一条排队 prompt 独占一个 turn，但 steering 和注入的上下文可以搭同一趟车"的全部实现。`inbox.ts` 这 20 行代码可以整段贴进书里。

**2.4 pre-step waterfall：插件在哪里拍板**
`claim → systemPrompt.assemble → 渲染上下文 → 才 dispatch agent/pre-step`。监听器的三种写法：不调 `next()` 直接 reject（我说了算）、`await next()` 后在结果上叠加、直接 `return next()`（只观察）。这里埋一个第 5 章的伏笔：**系统提示词的组装发生在 waterfall 之前**，所以你在这里改提示词片段，最快下一步才生效。

**2.5 取消：signal、inbox、记账**
`cancel()` 只做两件事——清 inbox、abort signal。停止本身是协作式的，靠循环里十几处 `signal.throwIfAborted()`。真正复杂的是记账：未分发的工具调用要补一对合成的 `tool/call` + `tool/result`（这是 Anthropic/OpenAI 消息格式对 tool_call 必须配对的硬性要求，所有 harness 都得做）；**真正的设计选择是它的反面**——调度器自身内部故障（不是取消）走另一条路：停止新分发、等已启动的落地、把第一个错误抛到轮次边界，**绝不编造工具结果**。

**2.6 唤醒锁存：abort 到 idle 之间那个窗口**
abort 同步返回，driver 异步收敛。这个窗口里进来的消息靠 `wakeRequested` 锁存在当前 phase 上，`kick` 的 finally 在切回 idle 后自动重放。三个边界条件：`disposed` 原因从不锁存、不带 `keepInbox` 的 cancel 会连锁存一起清掉、消息被 remove 后不开空轮次。`tests/cancel.spec.ts` 里 27 个测试的**测试名本身就是一份竞态规格清单**，直接当小标题列出来。

> 注脚：`ReactLoopAgent` 这个类名与 ReAct 论文的提示词范式无关——和 LangGraph 的 `create_react_agent` 一样，"react" 只是 tool-calling 循环这个形状的行业历史命名。

## 关键文件

- `packages/core/agent-loop/src/agent.ts`（496 行，本章主战场）
- `packages/core/agent/src/inbox.ts`
- `packages/core/agent/src/runtime-types.ts`（`agent/*` 事件签名与 mode 的权威清单）
- `packages/core/agent-loop/tests/cancel.spec.ts`
- `docs/agent-lifecycle.zh.md`（官方中文时序图，可直接改编成插图）
- `docs/architecture.zh.md`

**读者收益**：从此能看懂任何一个 agent 框架的主循环，并且知道自己那 50 行缺了哪五件事。

**字数**：20,000

---

# 第 3 章　工具：写你的第一个 `defineTool`，读懂那 51 个工具的目录

**钩子**：`execute()` 返回的不是给模型看的文本，是一个规范 JSON 值——文本是注册表按你声明的 `output` 投影出来的。这一个区别，决定了后面所有策略层能不能存在。

## 小节

**3.1 四件套：name / description / parameters / output + execute**
从 `packages/core/tools/README.zh.md` 的 `read_file` 例子开场。三个入门必踩的点：返回值是值不是文本；`args` 已被按 `parameters` 校验过（缺必填、类型错、枚举非法都变成 `INVALID_ARGS`，根本进不了工具体）；`exec.signal` 必填只读，异步工具必须观测或转发它。演示 `register()` 返回的 disposer 随 fiber 自动释放——这是全仓的资源管理惯例。

**3.2 schema 是怎么变成 prompt 里那段文字的**
一条线读到底：`ToolRuntime` 构造函数里那行 `ctx.systemPrompt.tools(...)` → `wireSchemas` → `schemaOf` 白名单三字段（只有 `name`/`description`/`parameters` 进模型请求，`timeoutMs`、并发分类器、`output.schema` 一律不给模型看）→ `orderTools` 排序。工具顺序默认按 code-unit 字典序，这是提供方前缀缓存对稳定字节的通行要求；**本仓库超出常规的是把它做成了强制项**：`toolOrder` 配置里必须恰好出现一次保留标记 `<unlisted-tools>`，缺了或重复了，配置加载期就抛。

**3.3 读一遍 51 个工具的目录**
按 `docs/tool-catalog.zh.md` 的映射表过一遍：Shell 与终端、文件系统、代码智能（lsp）、传输（run_code）、计划与任务、子 agent、后台任务、定时、Web、会话自省、人机交互、自举扩展。让读者自己发现规律：**工具本身几乎不实现能力**——bash 背后是 `ctx.shell`，read/write 背后是 `ctx.fs`，web_search 背后是 `ctx.web`，lsp 背后是 `ctx.lsp`。这是第 9 章的直觉预埋。

**3.4 工具自己拥有 UI：presentCall / presentResult**
纯函数返回带 `card` 标签的联合类型（generic / terminal / diff / search / read / web），让 UI 不用写 `if (toolName === 'bash')`。为什么必须是纯函数：实时流式和日志回放两种场景都会调它们。search 卡片带 `truncated` 与 `total`，让 UI 在类型层面就没法把截断结果画成完整结果。

**3.5 并发分类是 fail-closed 的**
`isConcurrencySafe(args)` 只有精确返回 `true` 才并行；未知工具、被遮蔽、没声明分类器、分类器抛异常、返回任何非 `true` 的值，一律判为独占。调度侧：连续 parallel 归进有界滚动池（默认上限 10），每个 exclusive 是顺序屏障，**只有分发和工具体重叠**，post-execute、`tool/result` 写入、additionalContexts 全部严格按模型给出的顺序提交。

**3.6 动手：把你的工具发布成一个 bundle**
在 `package.json` 里写 `"dsh": { "bundle": { "patch": "./cordis.patch.yml" } }`，patch 里用包名引用自己的插件行，`dsh plugin --profile demo add <你的包>`。讲清 `dsh plugin` 只是 pnpm 转发器，层列表按"安装后的实际状态"重新对账。

## 关键文件

- `packages/core/tools/src/schema.ts`（`defineTool` / `validateArgs`）
- `packages/core/tools/src/index.ts`（1946 行，本章只读注册与 schema 部分）
- `packages/core/tools/src/presentation.ts`
- `packages/core/tools/README.zh.md`
- `docs/tool-catalog.zh.md`
- `packages/core/agent-loop/src/tool-calls.ts`（调度侧）

**读者收益**：能写出一个在真实 harness 里挂得住、被策略层管得住、UI 画得出来的工具，而不只是一个 `async function`。

**字数**：18,000

---

# 第 4 章　会话即日志：事件溯源、surface 投影、fork/resume/replay

**钩子**：这个循环里没有 `this.messages` 这个字段。每次发请求前都从仅追加的事件日志里**现算**模型历史——而且有一条运行时不变量会把两者逐字节比对，不一致就抛。

## 小节

**4.1 为什么不能只维护一个 messages 数组**
从最朴素的实现出发，展示它在崩溃恢复、fork、审计、压缩四个场景同时失效。然后引入答案：一条仅追加日志是唯一真源，消息历史是投影。第一条要背下来的契约：**`seq` 恒等于数组下标**（append 时 `seq` 直接取 `log.length`）。这条等式后面被 fork 切片、持久化游标、崩溃修复续号反复直接使用。动手：写一个 30 行的 append-only Session 并加上这条断言。

**4.2 一条事件长什么样，什么东西故意不在日志里**
信封 `{type, seq, time, data}` + 三个可选字段 `surfaceOp` / `sourceEventSeqs` / `ignorable`。对照讲 `SessionHeader`（version、id、createdAt、cwd、parentSession、seedLength、delegationDepth、agentPreset）为什么故意不在事件表里——它是存储关注点，永远到不了 `deriveMessages()`。再讲 `SessionEventMap` 可声明合并：插件能加自己的事件类型，但插件事件一律 log-only。

**4.3 20 行读懂 deriveMessages**
44 种事件类型里只有 3 种会变成 LLM 消息：`user/message`、`assistant/message`、`tool/result`。而且这是**编译期强制**的——`append` 的第三个参数是条件元组类型，surface 事件必须传 `SurfaceIntent`，非 surface 事件传了就编译不过。带读者手写一遍 `deriveEventMessage`，埋两个坑：空内容的 `assistant/message` 要返回 null（它只是为了保住 usage 才写日志）；`assistant/chunk` 一律跳过。

**4.4 surface：给仅追加的日志加一层可重写的视图**
`append` 与 `replace` 两种操作、被遮蔽范围、`replaceGeneration` 如何驱动缓存失效。校验极严：`start`/`end` 必须是当前 surface 上真实存在的节点，且 `sourceEventSeqs` 必须覆盖每一个被遮蔽的节点——**想删历史而不留引用做不到**。`tool/result` 的替换更被钉死为"只允许改 content"：把两边的 `content[0].content` 置空后深比较，任何 turn / step / callId / error / meta 的差异都拒绝。

**4.5 人类 transcript 与模型 transcript 会分叉**
压缩不删除任何东西，只遮蔽。所以给人看的 transcript 必须读"追加来源"的事件（仓库为此导出了 `isAppendSurfaceEvent`），照抄 surface 会让用户眼睁睁看着自己刚读过的对话被抹掉。

**4.6 fork、resume、replay 是同一个原语的三种用法**
全都是"用一段已有事件当构造种子"。fork 从活跃会话切前缀并记 `parentSession`/`seedLength`，且拒绝停在开放轮次里（抛 `OPEN_TURN` 而不是静默截断）。resume 的种子是磁盘上的完整日志。配合讲 `session/end-seed`——一个 payload 是空对象的事件，**位置和时间戳承载全部含义**；以及一个产品级细节：种子已经以它结尾时不重复打标记，因为"接手一个会话不算工作"，不能让每次打开会话都把它顶到列表最前面。

## 关键文件

- `packages/core/session/src/index.ts`（1157 行）
- `packages/core/session/src/surface.ts`
- `packages/core/session/src/types.ts`
- `packages/core/agent-loop/src/invariant.ts`
- `docs/subsystems/session.zh.md`

**读者收益**：拿到一套可以直接搬进任何 agent 项目的"日志优先"架构，以及一条能让偷偷改请求的做法当场爆炸的断言。

**字数**：22,000

---

# 第 5 章　提示词是拼出来的：有序段落注册表与两条上下文通道

**钩子**：没有任何一个文件里躺着完整的 system prompt。我们从一份真实的提示词快照倒推回去，一行一行标注它来自哪个包的哪次 `section()` 调用。

## 小节

**5.1 从快照倒推**
把 `examples/acp-agent/tests/snapshots/text-turn/system-prompt.expected.md` 整份贴出来逐行标注：第 1 行来自服务构造函数硬编码的 `harness:identity`（order −100），第 3–5 行来自配置里的 `persona` 字段（order 0），第 8 行起是各工具包注册的 order 100–116 段落。这是让读者第一次意识到"提示词是拼出来的、不是写出来的"最有效的一页。

**5.2 order 号段与作用域遮蔽**
号段约定：−100 身份 / 0 persona / 100–199 工具引导 / 150 SDK / 190 交付物。`order` 是 `number` 不是整数——`SUBAGENT_SECTION_ORDER = 116.5` 就是用小数插队。作用域分层：`agent.ctx` 上注册的同名段遮蔽全局段，这是子 agent 换 persona 的实现方式（名字必须一样才构成替换而不是并列）。再讲 `complete: true`：组装照跑完、waterfall 照跑，之后这一段还原成唯一的提示词段。

**5.3 变量插值是彻底 fail-loud 的**
未注册的名字抛、注册了但本次无值抛、`{{{model}}}` 也抛；查变量用 `Object.hasOwn`，所以 `{{constructor}}` 算未知。孤立的 `{{` 才按字面量放行，替换进去的值绝不二次扫描。设计取向写在注释里：明确失败胜过交付一个格式错误的提示词。对比常见做法（渲染成空串或原样保留）讲清为什么在 agent 场景里静默降级更危险——少了 cwd 的提示词不报错，只会让模型在错误的目录下操作半小时。

**5.4 上下文注入的两条通道，怎么选**
**通道一** `systemPrompt.context()`：注册表托管、有 order、有去重投影，拼成一条 user 角色的 runtime-context 快照，开头固定为 `Current runtime context. This snapshot supersedes earlier runtime-context snapshots.`。当前仅有三个使用者：`sandbox:policy`(110)、`approval:policy`(115)、`subagent:delegation`(120)。**通道二** 插件自己监听 `agent/pre-step` 往 decision.messages 里追加：`time-context`、`agent-instructions`、`tool-skill` 的目录与 `/` 手势都走这条。判据：能被一句"当前值"完整表达的幂等事实用通道一；必须保留轨迹的增量事件用通道二。
> 两条通道的**去重机制完全不同**：通道一比对渲染文本（不变就一条都不写，全空时发 CLEARED 标记）；`time-context` 走的是 `refreshIntervalMs` 时间节流——它每次渲染都含当前时间戳，结构上不可能"内容没变"。顺带提一句：`system-prompt/README.zh.md` 把 git 状态列为**未来可能的**变量提供方举例，当前仓库里并不存在这个提供方，别照着文档去 grep。

**5.5 AGENTS.md 链与提示词注入防御**
从 `$DSH_HOME/AGENTS.md` 到 cwd 一路上的 AGENTS.md / CLAUDE.md 按从宽泛到具体排好，超预算时先整份丢弃更宽泛的，最后对最具体那份做二分截断（按 UTF-8 字节，回退到 lead byte），并在正文里明确告知模型省略了什么。安全点：正文里所有 `</system-reminder>` 字面量被转义成 `<\/system-reminder>`——仓库里的 AGENTS.md 是不可信内容，不能让它提前闭合框架标签。

**5.6 动手：20 行写一个自己的提示词段插件**
`inject: ['systemPrompt']` + `ctx.systemPrompt.section({...})` + 注册一个 `{{branch}}` 变量。踩坑清单：变量名必须匹配 `^[a-z][a-z0-9_]*$`；provider 返回 undefined 而段里引用了它会在渲染时抛；同名重复注册会抛，per-agent 覆盖必须通过 `agent.ctx` 注册。

## 关键文件

- `packages/core/system-prompt/src/index.ts`
- `packages/core/agent-loop/src/runtime-context.ts`
- `packages/context/time-context/src/index.ts`
- `packages/context/agent-instructions/src/render.ts`
- `examples/acp-agent/tests/snapshots/text-turn/system-prompt.expected.md`

**读者收益**：学会把"提示词"从一个大字符串重构成一张可组合、可遮蔽、可 fail-loud 校验的注册表。

**字数**：18,000

---

# 第 6 章　上下文经济学：四道防线、spill、skill，以及 KV cache 的账

**钩子**：动态事实为什么不能进 system prompt？因为 system prompt 在请求最前面，改一个字节，从那个 token 起后面全部缓存作废。这一章讲的每个决策，最后都能折算成钱。

## 小节

**6.1 先算账：前缀缓存的物理规则**
提供方按请求起始 token 序列做缓存。由此推出三条工程规则：动态事实一律追加在历史尾部（只追加、前缀永远稳定）；用一句"本快照取代先前的快照"做语义失效，而不是回去删旧消息；工具顺序确定性生成。

**6.2 四道防线，按代价从低到高**
① 工具自己的输出截断（bash 的 stdout/stderr 在 subprocess 层就有每流上限，溢出写临时文件）→ ② `spill-policy`：超过 `maxInlineBytes` 的纯文本结果整个落盘，只留头尾预览 + 定位符 → ③ `tool-result-pruner`：对历史里已有的超大工具结果做**无模型**的头/中/尾确定性剪枝（按 Unicode code point 切，不切断代理对）→ ④ 才是花钱的 LLM 摘要压缩。顺序写死在代码里：pressure 触发后先跑剪枝、重新计量，还超阈值才摘要。

**6.3 spill 的两个可以直接抄走的工程细节**
**字节预算**：先用"省略字节数 = 全部字节数"这个最坏情况算出告知语的长度上界，从 cap 里扣掉，剩下的才是预览预算——否则"刚好越线的结果被 spill 之后反而变长"。**文件系统安全**：0700 私有 root（mkdtemp 拿不可预测后缀）+ `session-<sha256前12>` 子目录 + 6 字节随机前缀文件名 + `open(path, 'wx', 0o600)` 排他写（预先种植的符号链接改不了写入目标）。再讲策略为什么跳过 `read`（防 read→spill→再 read 死循环），以及为什么在 code-mode 的 dispatch-log 分支上**反而不跳过**。

**6.4 压缩：追加一条 replace，而不是删**
`compaction/start` 这条持久事件本身就是锁，摘要（异步、可能很久）之后校验区间没变，再写 `compaction/summary` + 一条带 `surfaceOp: replace` 的 `user/message`，最后才写 `compaction/end`。**锁最后释放**意味着中途崩溃留下一个可检测的孤儿 start，而不是一个谎称完成的 end。区间选法：从尾部倒着攒够 `retainTokens`，再往前退到工具调用/结果配对平衡的边界。压缩指令要求固定的八段 Markdown 结构，空段也要写 `(none)`。

**6.5 摘要请求为什么长成"上一次请求的前缀"**
不用独立的 summarizer system prompt，而是复用会话最后一次真实请求的 `system` 和 `tools`，接上被压缩区间的消息，把压缩指令作为**最后一条 user 消息**追加。这样这次辅助调用在字节层面是上次请求的真前缀。三个被否决的替代方案是最好的习题：保留摘要器 system 提示词但复用其余（否，system 正是缓存最先命中的区域）、只发被遮蔽区域不带 header（否，第一个 token 就分叉）、**省略 tools schema**（否——摘要器从不调工具也必须带上，因为工具 schema 是缓存 token 序列的一部分；这一条是超出通行做法的地方）。

**6.6 SKILL.md：按需加载的第三种上下文**
六个发现根 + rank（100 `.dsh/skills` / 200 `.agents/skills` / 300 custom / 400 `$DSH_HOME/skills` / 500 `$DSH_AGENTS_HOME/skills` / 600 bundled），目录型与扁平 `.md` 两种形态，frontmatter 坏了只 warn 跳过不炸整个目录。目录以 `<system-reminder>` user 消息发布、按 SHA-256 digest 决定要不要重发（发的是**完整替换目录**，措辞明确要求"只用这份替换目录里的名字"）。用户打 `/skill-name` 时模型完全不参与决策——正则只扫 `source.kind === 'user'` 的消息，工具输出伪造不了这个手势；带 `disable-model-invocation` 的 skill 只能从这条路进入。

**6.7 上下文溢出的恢复路径**
`agent/request-error` 上的监听器只在 `CONTEXT_WINDOW_EXCEEDED` 时介入，**绕过阈值和保留尾部策略**强行压出一次有效缩减；而且即使后续摘要抛异常，只要无模型剪枝已经让 surface 前进了，也照样返回 `{kind:'retry'}`。

## 关键文件

- `packages/compaction/compaction-basic/src/summarizer.ts`
- `packages/compaction/compaction-basic/src/region.ts`
- `packages/compaction/compaction-basic/src/index.ts`
- `packages/compaction/compaction-tool-result-pruner/src/index.ts`
- `packages/spill/spill-policy/src/index.ts`、`packages/spill/spill-local/src/store.ts`
- `packages/skill/skill-filesystem/src/index.ts`、`packages/skill/tool-skill/src/index.ts`

**读者收益**：把"上下文管理"从玄学变成一张有先后顺序、有单价、有失败模式的成本表。

**字数**：20,000

---

# 第 7 章　组装层：Cordis 插件树与四层 patch——`dsh` 启动时到底发生了什么

**钩子**：`$DSH_HOME/profiles/<name>/cordis.yml` 的内容永远是 `[]` 加三行注释，而且每次启动都被无条件覆写。这不是偷懒——是在对抗框架自己的持久化行为。

## 小节

**7.1 Cordis 五个概念一次讲完**
插件 = 带可选 `inject` 和 `apply(ctx)` 的函数（或 Service 子类）；Context = 服务容器；`inject` = 声明依赖，服务没齐就一直 PENDING（所以 YAML 里行顺序不影响加载顺序）；事件四种分发模式（emit / waterfall / parallel / serial，模式是事件公开约定的一部分）；`effect` = 注册即可逆副作用（`ctx.on`、`ctx.plugin`、服务注册本身已经是 effect，只有框架不管的资源才需要手写）。配 `docs/cordis-tutorial` 的 01–03 章做实操。

**7.2 四层 patch：顺序写死在一行数组字面量里**
`composeEntries([bundlePatches, profile.patches, homePatches, overlays])`。逐层讲清来源，重申 home 级压在 profile 级之上的设计意图。再讲 `applyEntryPatches` 的循环体：带 `insert` 的把行 push 进列表，不带 insert 的必须有 `id`，找到后 `target[key] = value` **浅覆盖顶层键**——而 `config` 就是一个顶层键，所以写了 config 就等于整个 config 被换掉。`id` 找不到只是一条 warn。

**7.3 撑着整套设计的那五行本地修改**
上游 cordis 的 patch 实现在循环开始前只建一次 id 索引，结果是"A 层 insert 的行，B 层永远 patch 不到"。dsh 在 insert 分支末尾补了一句 `buildMap(insert)`（vendor/README.md 本地修改第 11 条）。没有这一句，整套"base 全量 insert、mode bundle 和用户层按 id 覆盖"的设计根本不成立——因为所有行都是 base insert 进来的。同一条修改还把私有方法提成导出的纯函数，让 `--dump-config` 复用同一份算法。

**7.4 `!!js` 与 inject 的排队关系：命令行 flag 是怎么进配置的**
`!!js` 方言与 `with (ctx) { eval(expr) }` 求值器**来自 vendored 的上游 cordis loader/include，不是 dsh 的发明**；而"求值推迟到该行 inject 的服务全部激活之后"是 dsh 移植的上游 PR `cordiverse/cordis#41`（vendor/README.md 本地修改第 15 条）。dsh 自己的原创增量是**第 18 条：让 `disabled` 成为唯一被插值的元数据字段**——`dsh-base` 靠这一个能力在同一份 patch 里塞进两套 shell 栈（bash 一对带 `!!js process.platform === 'win32'`，pwsh 一对带取反表达式）。由此讲透惯用法：app 自己的 provider 插件解析 flag 并 provide 成普通服务，配置行写 `inject: [webStartup]` + `port: !!js ctx.webStartup.port ?? 3080`，启动器压根不认识 `--port`。反面：用户 patch 整体替换掉这行的 config，表达式就一起没了。

**7.5 `boot()` 的时序与两级审计**
`baseUrl → provide dshHomePath → plugin(Loader) → prepare(ctx) → mountRootInclude → loader.await() → 两级审计`。`prepare` 是唯一能在任何配置行挂载之前注入宿主事实的窗口。`assertEntriesLoaded` 找"启用了但没有 fiber"的行；`assertEntriesActivated` 再遍历一遍，FAILED 的 fiber 会被 await 出私有 rejection，PENDING 的则列出它 inject 了但至今拿不到的服务名。把第 1 章那三张"失败的脸"在这里补齐机制。

**7.6 热的用户 patch，与 `installFailLoud` 的 2 秒**
两个 watcher（profile 的和 home 的）每代都重新读取两个文件；`composeLive` 外面那层 `structuredClone` 是必须的——include 把 insert 行**按引用**推进已挂载的树，后续 id patch 会原地 mutate 它们，复用同一份解析结果会把用户覆盖烤进 bundle 的内存行。最后讲 `installFailLoud`：致命失败先写诊断，再 race 一个 release 回调和 2 秒超时（定时器保持引用防止 Node 因事件循环空了而 exit 0），最后才 `exit(1)`——因为 Loader 并发挂载，某个 TUI 可能已经拿走了终端，直接退会把 raw 模式、bracketed paste 和键盘协议残留在用户 shell 上。

**7.7 为什么整棵树必须是 patch，而不能是一份文件**
三条约束共同逼出这个设计，串起来讲：Loader 有树写回（插件自毁会把 `disabled: true` 写回配置文件，所以任何被 include 的真实文件都不可信）；patch 不跨 include 边界（所以所有层必须压在同一个 include 层级，这又要求 insert 进来的行能被后续层索引到）；insert 行按引用入树（所以每代重组必须 structuredClone）。

## 关键文件

- `apps/cli/src/profile-boot.ts`、`apps/cli/src/args.ts`
- `packages/boot/app-boot/src/index.ts`、`packages/boot/app-boot/src/profile.ts`
- `vendor/include/src/index.ts`、`vendor/cordis/src/fiber.ts`
- `vendor/loader/src/config/entry.ts`、`vendor/loader/src/config/utils.ts`
- `vendor/README.md`（18 条本地修改日志，全仓最值钱的一份"为什么"文档）
- `packages/bundle/base/cordis.patch.yml`、`packages/bundle/web-app/cordis.patch.yml`

**读者收益**：看懂一个真实产品的"组合层"长什么样，以及为什么它不是 YAML 拼接那么轻。

**字数**：22,000

---

# 第 8 章　权限：工具七段流水线、两条审批路径、Code Mode

**钩子**：这个 harness 里没有一个叫 `permission` 的中心模块。权限是七段流水线上的三个不同座位，加上两条互不相通的审批路径。

## 小节

**8.1 七段流水线，每段能干什么、不能干什么**
`pre-execute`（可重排的 allow/deny/ask，**故意不给改参数**——一旦允许改写，日志记录的、UI 呈现的和实际执行的就会脱钩）→ 审批 ask（一次性，缺 seam 就退化为拒绝）→ 单调 guards（同步、只能拒、不可翻案）→ `tools/execute`（环绕包装，唯一能替换的字段是 `signal`）→ 工具体 → `post-execute`（accept 换 content 或换 value 二选一 / block / 附加上下文）→ `finalizeContent`（同步、只能改 content、**连流水线失败也要过**）→ `tools/result`（结果先冻结、只观测、观察者失败被隔离）。每段配一个真实消费者。核心教学点：可重排的扩展点和不可翻案的所有者策略必须是两种东西。

**8.2 值与呈现的拆分**
工具体返回规范 JSON 值 → 按声明的 `output.schema` 校验 → deepFreeze → 纯函数 `render(args, value)` 得到 `ContentBlock[]` → 顶层调用再派生可回放的 `presentationMeta`。规范值只活在执行局部、永不入日志。所以 post-execute 换 value 会触发重新校验与重新渲染，换 content 则保留原值和元数据。**警告**：换 content 不是保密边界——值不能让下游程序拿到时必须 block 或替换 value。

**8.3 审批的两条路，以及它们上面的两层策略**
**路径 A（注册表级）**：某个 pre-execute 监听器返回 ask → `ctx.approval.request` → 只有 `allowed-once` 放行，且审批发生在 guards **之前**（人点了同意，guards 仍可一票否决）。**路径 B（工具级）**：沙箱提权由 bash / fs 的工具体自己发起，模型在同一次调用里带 `sandbox_permissions` 和 `justification`；"请求的模式是否严格更宽"是**执行期检查而非 schema 约束**，因为 schema 是注册表全局的、而生效模式是每次调用的真相。上面还有两层不问也能定的策略：会话级 `approval/policy`（`'never'` 在 waterfall 分发之前就确定性返回 rejected）和把 sandbox mode 与 approval policy 打包的 permission-presets。

**8.4 沙箱：一个函数、三种后端、三套拒绝方言**
整个 sandbox seam 只有 `confine(argv, policy) → ConfinedArgv`——它自己不 spawn 任何东西，且禁止"静默无隔离透传"（拿不到后端必须抛 `SANDBOX_UNAVAILABLE`）。三种 profile 对照读（58 行的 `profiles.ts` 是最好的教材）：bwrap 的 `--ro-bind / /` 挂载、Landlock 的允许清单、Seatbelt 现拼的 SBPL 文本。后端选择：先按平台定链，多候选才**真的跑一遍**功能探测（`--version` 式检查会漏掉"有 syscall 但拒绝强制执行"的内核）。

**8.5 "被拦住"和"根本没跑起来"必须分开**
`ConfinedArgv` 把拒绝方言随 argv 带回来（EROFS→`read-only file system` / EACCES→`permission denied` / EPERM→`operation not permitted`），类型注释明令禁止跨后端取并集。`RunnerFailureRule` 三段式：允许退出码门控 + 逐行致命签名 + 按整行精确相等排除的信息行。Landlock 的规则最典型——退出码必须恰好 125，致命前缀是 `landlock-run: `，但必须先剔除 `landlock-run: partial enforcement (older Landlock ABI)` 这一行。判别顺序：runner 失败优先于 denial。（这一节是第 12 章复盘 0004 的技术前置。）

**8.6 Code Mode：把 N 个 schema 换成 1 个传输 + 一份生成的 SDK**
`view()` 在能力层之外追加保留的 `run_code`；两段提示词（`tools:code-only` order 99、`tools:sdk` order 150）；绑定调用带 parent token 重入完整流水线；子调用池复用 native 并发约定；写 `tool/code-dispatch-start` 和 `tool/code-dispatch` 两条日志事件。最精彩的安全细节：塌缩判定发生在**策略流水线之前**——一个 code 模式的 agent 直接发 native 调用，会在 createExecution 阶段就返回 `UNKNOWN_TOOL`，钩子和审批 UI 根本看不到，注释原话是不能让任何一方"观察到、更糟的是批准"一个注定失败的调用。而拒绝文案写的是"请从 run_code 程序里调 `<name>`"，不是干巴巴的 unknown tool——因为同一份提示词刚刚声明过那个工具。

**8.7 有一个不变式插件在真的看着这条流水线**
挂在 `internal/dispatch` 上，用 WeakMap 记录 stage：pre-execute 重复分发 fail、execute 必须跟在 pre 之后、post 必须跟在 pre 或 execute 之后、`tools/result` 时校验 exec / result / content 全部冻结，并校验 code-dispatch 事件的 root/parent/sub 三级 callId 血缘且必须落在未结束的 turn 内。教学点：在插件化架构里，跨插件的顺序约定光靠文档守不住，得有一个运行时的类型系统。

## 关键文件

- `packages/core/tools/src/index.ts`（流水线主体）、`src/code-mode.ts`、`src/invariant.ts`
- `packages/sandbox/sandbox/src/index.ts`、`src/escalation.ts`
- `packages/sandbox/sandbox-local/src/index.ts`、`src/profiles.ts`
- `packages/sandbox/sandbox-policy/src/index.ts`
- `packages/shell/bash-sandbox/src/helpers.ts`、`packages/shell/tool-bash/src/index.ts`
- `docs/tool-execution-pipeline.zh.md`（Mermaid 全景图）

**读者收益**：拿到一套"能拒绝、能审批、能包装、能观测、且顺序不会被插件搅乱"的权限模型，而不是散落各处的 `if (dangerous)`。

**字数**：24,000

---

# 第 9 章　能力 seam：三角色拆包，与 4 行 YAML 把执行世界搬到远程

**钩子**：`examples/headless-agent/e2b.cordis.yml` 只做了四件事——禁两个本地 provider、插三个 E2B 包、改一行策略。然后 Bash、PTY、LSP 整套跑到了远程机器上，而 `bash-local`、`terminal-bash`、`lsp-stdio`、三个工具包**一行代码都没改**。

## 小节

**9.1 三角色是写进 Agent Note 的硬规范**
Service Definition（拥有 `ctx.<key>` 的 Cordis Service 和词汇类型，"可以是抽象类，也可以是具体的注册表服务；绝不是 TypeScript interface"）/ Service Provider（注册实现的插件）/ Consumer（注入服务键，从不导入 provider 特有类型）。术语纪律：seam 严格指三者合体，单独一个角色不叫 seam。同一份笔记明确**反对预防性拆分**——只有一种可设想 provider 和一个 consumer 时就保持一个包。用 `packages/shell` 的五个包（shell / bash-local / bash-sandbox / tool-bash / shell-env）当第一课。

**9.2 Service Definition 的物理形态**
一个文件同时做三件事：`declare module` 声明合并给出全仓类型、`super(ctx, 'sandbox')` 运行时占键、抽象方法定义契约。运行时约束是"一个 context 只能有一个实现，装第二个直接抛"——所以平台差异不是运行时 `if`，而是在 YAML 里用 `disabled` 开关二选一（回扣第 7 章）。再讲一个命名细节：`ctx.shell` 的 settings 命名空间叫 `shell` 而不是 `bash`——"命名空间命名的是能力，不是实现"，所以 mac 上写的 settings 带到 Windows 上仍能解析。

**9.3 执行世界 = `ctx.fs` + `ctx.subprocess`**
决策原文：共同挂载的提供方必须描述**相同的**路径命名空间、可执行文件、进程和终端会话。为此 fs seam 在不透明的 `targetKey` 之外额外暴露三个"路径事实"：`processPath`、`fileUrl`（后端拥有 URI 编码，因为宿主平台可能不同于执行平台）、`contains`。这也是 `fs-e2b` 全程用 posix 命名空间的原因。再讲 `spawnTerminal` 为什么必须是深原语而不是管道组合（管道无法分配控制终端、无法确定前台进程组、无法证明会话树已清理），以及代价：node-pty 下沉进 `subprocess-local`。

**9.4 跟着 e2b.cordis.yml 走一遍**
逐行讲那 4 行 patch，加上文件头注释里的 one-world invariant（`e2b.cwd`、`sandbox-policy.workspaceRoot`、`bash-local` 默认 workdir 必须指向同一个远程目录）。然后让读者去 grep 确认几个消费方里没有任何一处 import 了 `subprocess-local` 或 `fs-local`。**顺带纠正一个常见误解**：E2B 远程沙箱不是 `ctx.sandbox` 的一个 provider——sandbox seam 的文档第一句就划界"容器、microVM 和远程执行替换的是外层的整个能力 seam"，所以 e2b overlay 里 sandbox-policy 干脆设成 `danger-full-access`。

**9.5 Provider 变体用继承实现**
`SandboxBashExecutor extends LocalBashExecutor`，只 override `resolve/run/start`，在 argv 层插入 `confine`；`fs-sandbox extends LocalFileSystem`，只 override `writeText/editText`。两者都**没有自己的 Config**（沙箱默认值归 `ctx.sandboxPolicy`，runner 选择归 `ctx.sandbox`）。再讲两种沙箱的定位差：fs-sandbox 的模块文档自认"不是内核边界"（操作是 seam 自己的 open/rename，只有目标路径不可信，canonicalize-then-contain 就够了），但它必须和 Seatbelt profile **共用同一份 `writableRoots()`**，否则会出现"bash 能写 /tmp、Write 工具不能"的裂缝。

**9.6 能力事实回流：让工具 schema 跟着 provider 走**
`ShellExecutor` / `FileSystem` 基类上的 `get sandboxMode()` 默认返回 undefined，沙箱实现 override 成部署默认模式。`tool-bash` 据此决定要不要向模型公开 `sandbox_permissions` / `justification` 两个参数，以及要不要在工具描述里追加提权指导段落。原则：Consumer 不能 import provider 类型，但可以通过 seam 上定义的能力事实读到实现的性质。

**9.7 第四个角色：只挂事件、不注册服务的配套插件**
fs seam 声明了 `fs/write-intent`、`fs/edit-intent`（waterfall 单槽决策）和 `fs/observed`（emit，监听器必须同步）。`fs-observation-policy` 只挂这三个事件、不注册任何服务，实现了"编辑前必须先读过这个文件"——不挂它，工具就退回裸 provider 的无条件写。结论：跨切面策略不必污染 Consumer，也不必污染 Provider。

**9.8 那张从代码里长出来的 seam 总表**
`docs/capability-seams.zh.md` 列了 **55 个 `ctx` 服务键（56 行表格）**，每行标注角色（seam / core / bundle）、所属包、已知实现、直接消费方、配套插件。维护模式是混合的：服务从 Cordis 声明中发现，角色分类在 `scripts/gen-doc-graphs.ts` 里，并设有完整性守卫——新增一个 provider 忘了归类会被守卫拦住。

**9.9 加餐：为一个还不存在的 provider 预付兼容账**
`ctx.codeRuntime` 目前只有一个 TypeScript worker 后端，却已经在 seam 层强制 ECMAScript ∪ Python 保留字的并集。最硬核的是 `__debug__`：CPython 把裸引用编译成常量 True 并在编译期拒绝赋值，所以以该名注入的全局在程序里根本不可达——"校验通过、在 Python 后端不可用"正是这份共享清单要防的裂缝。

## 关键文件

- `.agents/notes/implemented/architecture/2026-06-13-capability-seams.zh.md`
- `.agents/notes/implemented/architecture/2026-07-28-portable-execution-world-consumers.zh.md`
- `packages/fs/fs/src/index.ts`、`packages/subprocess/subprocess/src/index.ts`
- `packages/fs/fs-sandbox/src/index.ts`、`packages/shell/bash-sandbox/src/index.ts`
- `packages/lsp/lsp/src/index.ts`、`packages/lsp/lsp-stdio/src/index.ts`
- `packages/code-runtime/code-runtime/src/index.ts`
- `examples/headless-agent/e2b.cordis.yml`
- `docs/capability-seams.zh.md`

**读者收益**：学会把"能力"切成三个包，从此换后端不用改工具，也不用改模型看到的任何一个字。

**字数**：20,000

---

# 第 10 章　多智能体：subagent / workflow / jobs / goal / plan / schedule

**钩子**：ralph 这个"自主迭代直到完成"的工作流，它的全部编排逻辑是一段**写死在 TS 源码里的 JS 字符串**——模型能提供的只有 objective 和 maxRounds 两个数字。

## 小节

**10.1 六个包，一句话对照**
subagent = 让别的 agent 替我干；workflow = 让模型写一段 JS 编排一批 agent；jobs = 让长跑工具在后台跑并被回收；goal = 让同一会话自己给自己续轮次；plan = 软性的"先规划后动手"模式；schedule = 让会话在未来某个时刻给自己发提醒。两组关键对照：goal 与 ralph 都是"迭代到完成"，但 goal 在同一会话里滚（省 token、有上下文）、ralph 每轮换新 agent（干净、靠工作区当记忆）；schedule 与 jobs 都是"以后再说"，但一个墙钟触发、一个工作完成触发。

**10.2 one-shot 与 continuable：第一个分岔**
one-shot 有 run 句柄、有 result、await 完必须 dispose，没有 steering、没有恢复。continuable 根本没有 run，你拿到的是一个持久 `childId`，之后所有交互通过 `send_message` 进它的 inbox 排队。**可继续子 agent 根本不经过 `provider.start()`**——由续跑管理器自己组装，provider 只被问"要不要用父级历史做种子"。能力检测方式也不同：不是 flag，而是"provider 上有没有 `prepareContinuable` 这个可选方法"。

**10.3 Activation：三态是推导出来的，不是第二套状态机**
一份持久子会话最多挂一个 Activation。`stateOf()` 只看 Agent.status、已准入未出队的消息 id 集合、以及 ownedChildren 集合——running / waiting / settled 全部推导。讲清 `accepted` 集合为什么必须存在（followup 到消息真正准入之间有一个微任务窗口，同步观察者会误判成已结算）。再讲三条生命周期硬纪律：ChildLock 串行链、child-first 释放、记忆化 disposal 作为准入截止线。

**10.4 委派边界会把策略固化进子会话日志**
只要组合了 approval 服务，每个进程内子 agent 都被无条件写入 `approval/policy = 'never'`，**不管父级自己是什么策略**。理由是"无人可问"：交互式父级下的后台子 agent 会挂在一个任何界面都不展示的问题上，而被拦住的子 agent 从外面看和正常干活的没有区别。这条作为 `source: 'delegation'` 的持久事件写进子日志，冷恢复会重放它，fork 种子里陈旧的父级策略也会输给它。配套还有一段固定的运行时上下文告诉模型"你的权限范围在启动时就定死了，需要审批的操作会被自动拒绝，别重试，把限制写进回复里"。深度用 `SessionHeader.delegationDepth` 做单调下界——一个被恢复的父级不能假装自己是顶层。

**10.5 workflow：worker + node:vm，以及它到底隔离了什么**
`start()` 先在宿主侧做 meta 校验和脚本预解析（为了保住"同步抛 SCRIPT_PARSE"这个约定），再创建 Worker 并清空 env。ready/go 握手让"刚 start 就被取消"也能阻止脚本的同步前缀。五个钩子：`agent` / `parallel` / `pipeline` / `phase` / `log`；错误纪律分两档——普通子 agent 失败降级为 null，fatal 的 `WorkflowError` 原样重抛（致命性用**宿主 realm 的 instanceof** 判定，脚本里造的对象永远伪造不出来；反过来工作流作者在脚本里 `instanceof Error` 是失效的）。取消是两段式：脚本侧钩子抛 CANCELLED，宿主侧 `disposeGraceMs` 到期强制结算 + 补合成 agent-end + terminate。README 写得非常诚实：worker 内的 `node:vm` 是**塑造 API 的机制，不是安全边界**，信任前提对齐到"模型已经有 bash 权限"。

**10.6 ralph：固定工作流这个模式**
读一遍 `RALPH_SCRIPT`：一个 for 循环，每轮起全新子 agent，要求按 `{status, summary, evidence, nextSteps, blocker}` 的结构化 schema 返回，脚本内自己做语义校验和交接长度校验。provider 路由和总量上限走 `WorkflowStartRequest` 字段传，脚本连看都看不到；ralph 还会拒绝 `inheritsParentContext` 为 true 的 provider——它的整个前提就是每轮干净上下文、共享工作区才是长期记忆。诚实地讲清已知限制：**"完成"是 worker 自己声明的，没有独立评估器**，Native 渲染器的标签会明确写"结果由 worker 报告，而非独立认证"。

**10.7 后台通知怎么送才不会烧钱**
owner busy → inject（多个通知合并成一个 step）；owner idle → followup（开一个新轮次，要花一次模型请求）；父级正在拆卸 → 一律降级为 inject。再叠一层预算：`maxConsecutiveWakes` 默认 3，专门挡"被唤醒的轮次起了个任务、任务完成又唤醒它"这条自激链，任何人类输入重置。jobs 的两道准入：没有 controller 服务这个 owner 就不许开工；每 owner 并发上限默认 10，超限的错误消息直接教模型怎么办。

**10.8 goal / plan / schedule：三种"自己给自己派活"**
goal 是事件溯源的（持久 phase 回答"目标发生了什么"，**进程本地的 activation 从不持久化**，所以重启后不会自动续跑，必须用户明确 resume）；驱动器在 idle 时先 flush 持久化、再预留 round、再 followup。plan mode 是**纯软性指引**，只贡献一段提示词，真正的限制归沙箱和审批，且 `exit_plan_mode` 工具在非 plan 模式下也保持注册（进出 plan 不改变工具目录，不破坏 KV cache 前缀）。schedule 只在 live 根 agent 上装 timer、只往会话流追加事件、到期工作走普通 follow-up；every 类最小间隔 5 分钟，错过多次只补最近一次。

**10.9 一个必须讲的现场矛盾**
`packages/bundle/base/cordis.patch.yml` 里 `subagent_fork` 明确写 `one-shot` 并附了长注释解释原因（可继续 child 的 report 工具和提示词段落排在继承历史之前，会把 fork 唯一的收益——提供方侧前缀复用——全部吃掉），两个 example 也是 one-shot；**但 CLI 随附的三个 agent preset（standard / code / cordis）把 `subagent` 和 `subagent_fork` 都设成了 `continuable`**。对应的 Agent Note 把这件事写成了"已接受的风险"：限制只存在于三个配置文件和一处代码注释里，不在门禁里。同时 `subagent-fork-in-process` 源码里的 TODO 还写着"没有随附组合调用 prepareContinuable"——注释和配置已经对不上了。这是全书最好的"配置约定为什么必须有门禁"的活教材，也是第 12 章的引子。

## 关键文件

- `packages/subagent/subagent/src/index.ts`、`src/continuation.ts`（1483 行）、`src/child-agent.ts`
- `packages/subagent/tool-subagent/src/index.ts`、`packages/subagent/subagent-fork-in-process/src/index.ts`
- `packages/workflow/workflow-worker-thread/src/index.ts:58-72`（meta 校验与同步 SCRIPT_PARSE）
- `packages/workflow/workflow-worker-thread/src/host.ts:45-57`（worker env 清空、tsx/TMP 补丁）+ `src/runtime.ts`、`src/session.ts`
- `packages/workflow/tool-ralph/src/index.ts`
- `packages/jobs/jobs-local/src/index.ts`、`packages/jobs/tool-jobs/src/index.ts`
- `packages/goal/goal-round-driver/src/index.ts`、`packages/plan/plan-mode/src/index.ts`、`packages/schedule/schedule/src/runtime.ts`
- `apps/cli/config/agent-presets/standard/agent.cordis.yml`、`packages/bundle/base/cordis.patch.yml`
- `docs/subsystems/subagent.zh.md`

**读者收益**：搞清"多智能体"到底是六种不同的东西，以及每一种在生命周期、权限、计费上的真实代价。

**字数**：24,000

---

# 第 11 章　持久化：双后端、崩溃恢复、格式版本，与"模型可见即已记录"的执法机器

**钩子**：架构文档里那句口号，要么在代码里有一个会抛异常的执行体，要么它只是口号。这一章讲那台执法机器。

## 小节

**11.1 双重强制的"模型可见即已记录"**
**第一重**：在 `llm/stream` 上 **prepend** 一个全局监听器（prepend 是为了防止会短路的回放监听器把检查静音掉），断言 options 和 messages 都被冻结、sessionId 指向活会话，然后 `JSON.stringify(options.messages)` 必须严格等于 `JSON.stringify(session.deriveMessages())`，之后再比 `foldRequestHeader` 折出来的 model/system/temperature/maxTokens/stop/tools。**第二重**：checkpoint policy 在模型请求、顶层工具执行、每次 pre-step 之前强制 flush，失败就不调适配器、不执行工具体（fail-closed）。于是"模型看到的"和"磁盘上有的"之间不存在时间窗口。

**11.2 无损 JSON 的边界比你以为的窄得多**
逐条讲 `json.ts` 拒绝的东西：`-0`（JSON 会写成 0）、非有限数、稀疏数组、数组上的额外自有属性、非枚举或 symbol 键、跨 realm 伪造的 `Array.prototype`、循环引用。两个工程点：**一趟遍历同时完成校验和复制**（否则一个有状态的 getter 可以在校验和存储之间换值）；遍历是显式任务栈而不是递归（合法的深层嵌套受限于内存而不是调用栈）。这是一个可以直接抄进任何持久化项目的模块。

**11.3 存储编码不等于数据模型：chunk 打包行**
日志必须逐条无损保存流式分片且 seq 连续，于是磁盘上绝大多数行是 token 级 delta（源码注释给了实测数字：分片的 JSON 信封开销约 56 倍，打包后日志小约 60%）。打包器把连续同块的 delta 合成一行、时间戳存差值。三个决策要讲透：打包行用**不带斜杠的 tag** 且不在 `SessionEventMap` 里（读者不可能把它误当事件）；编码器只白名单它完全认识的形状，认不出就原样存（丢压缩不丢数据）；解码器遇到坏的打包行必须**抛**而不能当普通事件（否则静默吞掉整段流）。`MIN_RUN` 被声明为格式常量而非可调参数——两种布局解码结果相同，改它不作废已有日志。

**11.4 崩溃恢复：补边界，而不是截断**
一个长任务的单个轮次可能有几万条已落盘事件，截掉等于毁掉真实工作。正确做法：扫出悬空 tool-call、按 Map 插入顺序合成 `tool/result`、补 `step/end`、补 `turn/end{interrupted}`（合成事件的 time 复用最后一条真实事件的时间戳以保证确定性）。重点讲两段**给模型看的恢复文案是设计资产**：已记录过 tool/call 的明确说"结果未知，只有只读或幂等的操作才该重试；可能有副作用就先核对外部状态或问用户，不要盲目重试"。`interrupted` 是唯一一个 agent loop 永远不会发出的 TurnEndReason。

**11.5 怎么设计一个能换后端的持久化 seam**
三层：抽象服务（直接在领域类型 `SessionEvent` 上定义接口，**不发明平行的持久化事件类型**）、协调器（缓冲、按 id 串行、领养、修复时序、dispose 排空——所有难做对的编排只写一次）、后端字节原语（loadStored / appendBatch / commitRepair / readStoredRevision / list）。撕裂尾用泛型 `TornMarker` 表达，协调器只判断它在不在再原样交回，完全不知道它是字节偏移（JSONL）还是起始 seq（SQLite）。最后指向那份 432 行、memory/jsonl/sqlite 三个后端共跑的 contract 测试。

**11.6 崩溃安全的文件写：JSONL 后端逐步拆解**
临时文件 fsync → 用 `link()` 而不是 `rename()` 发布（link 遇到同名会 EEXIST，rename 会静默覆盖掉另一份同 id 日志）→ fsync 父目录 → 追加失败 truncate 回原大小（避免半条记录造成 seq 重复）→ zstd 模式下 header 单独成帧使 `list()` 只解一帧。配合讲 SessionId 是**未校验的 branded string**，进文件系统前必须逐 code unit 转义（`.` 和 `..` 特判）。对照 SQLite 后端：一个事件一行、列与信封 1:1、整批在一个事务里、能按 seq 寻址所以额外实现 `loadStoredFrom`。

**11.7 日志格式版本该由谁来决定 bump**
罕见清晰的规则：**是否 bump 由写入方发出的内容决定，而不是由读取方能不能解析决定**；"能解析不报错"不等于正确。只有结构性变化才够格（header 形状、事件信封、核心事件语义、surface 机制），加一个普通事件类型不 bump，靠 per-event 的 `ignorable` 兜底——而 `ignorable` **默认为 false（必需）**，理由白纸黑字：忘记打标记导致过度拒绝只是不方便，静默跳过会恢复出一个被掏空的会话。失败时的用户体验也分方向：更新的 harness 写的请升级，更旧的说明本构建没有升级路径。

**11.8 修订号、领养与"同一个方法对冷热状态给出不同语义"**
后端给每份日志一个不透明 revision，冷会话连同 revision 放进有界 LRU，一致就复用整份已解析已冻结的对象图。HMR / 活跃前缀领养故意绕开冷路径的崩溃修复——活跃 Session 仍是权威，可能稍后补上真正的 step/turn end，所以只截断撕裂尾、绝不合成 interrupted 闭合；同一个 `load()` 对冷会话做修复、对活跃且轮次未闭合的会话直接拒绝。这是这套设计里最容易读漏的地方。

## 关键文件

- `packages/core/agent-loop/src/invariant.ts`、`packages/session/session-checkpoint-policy/src/index.ts`
- `packages/core/session/src/json.ts`、`src/chunk-rows.ts`、`src/repair.ts`、`src/invariant.ts`
- `packages/session/session-persistence/src/coordinator.ts`（1361 行）、`src/write-behind.ts`
- `packages/session/session-persistence-jsonl/src/index.ts`、`src/format.ts`
- `packages/session/session-persistence-sqlite/src/schema.ts`
- `packages/session/session-persistence/tests/contract.ts`
- `.agents/notes/implemented/architecture/2026-08-10-session-log-version-mechanism.zh.md`

**读者收益**：拿到一套可以直接复用的持久化 seam 设计（抽象层 / 协调器 / 字节原语），以及一份"版本号什么时候该加"的可执行判据。

**字数**：20,000

---

# 第 12 章　683 篇设计笔记与 4 篇事故复盘：一个仓库怎么记住自己为什么这么做

**钩子**：这个开源仓库只有一个 commit——git 历史在压扁时消失了。那 683 篇按日期命名的设计笔记，是它唯一保留的开发时间线。而其中最值钱的部分，是写着"我们否掉了什么"的那 11 篇。

> **为什么这章放在第 12 而不是第 3**：读完前 11 章的源码之后，你才有资格读作者们当时的决策记录；否则那些笔记只是一堆你无法证伪的断言。

## 小节

**12.1 制度：路径即元数据的四态状态机**
`{生命周期}/{类别}/yyyy-mm-dd-标题.md`。生命周期 proposed / implemented / rejected / archived，笔记随状态**物理搬家**；类别 feature / bug-fix / simplification / architecture / process / testing 是代码里的封闭集合（定义在 `scripts/agent-note-tree.ts`，门禁拒绝任何别的目录名）。日期是"这个主题第一次被提出"的日期。笔记之间只能用相对 Markdown 链接互引——既能机械检查死链，也能在搬家时保持有效。实测分布：proposed 25 / implemented 505 / rejected 11 / archived 142 = **683**，跨度 2026-06-11 到 2026-08-13，共 64 天。

**12.2 硬性要求：每篇必须写"曾考虑的替代方案"**
README 原话：记录决策时不记录它击败了什么，就是在邀请反复争论。这一节由 `verify-agent-note-format` 机械校验；格式统一日之前的老笔记只允许用一行固定注释豁免，且门禁只对那之前的文件接受它。另一条更硬的规则：每个非平凡变更都必须在同一个 PR 里新增或更新至少一篇笔记，但这条边界**由人评审执行**——他们明确拒绝加"CI 差异分类门禁"，理由是机械检查判断不了语义变更是否平凡。再讲正文骨架按生命周期分：implemented 里出现 `## Proposal` / `## Plan` / `## Acceptance criteria` 会被门禁拒绝，因为那是提案语气混进了现状描述。

**12.3 归档区是密码学冻结的历史**
142 篇 × 3 个文件 = **426 条 SHA-256** 记在一份仅追加的 `manifest.json` 里，`--write` 模式必须先证明每条已有封存的内容没变才允许追加。归档动作只允许做四件事，之后永久冻结——哪怕包改名了、行为变了也不许动。根目录 `.rgignore` 把归档目录排除在默认搜索之外，防止陈旧事实凭字面匹配排到当前答案前面。顺带讲双语机制：每篇三个文件，`.i18n.yaml` 里存两侧在"最后一次确认一致"时各自的 **git blob hash**。

**12.4 rejected/ 的准入比 implemented 还严**
只有 11 篇，且规定"仅当其决策依据仍能避免一种诱人且影响重大的错误时保留，否则删除完整三文件组"。rejected 是唯一 Status 行带内容的状态（`rejected — <一行原因>`），因为"读者查阅被否决的笔记时，结论正是他们要找的"。rejected 笔记是**冻结的提案**：保留提案时的全部章节，只在 Status 行加原因；且绝不能进归档区。

**12.5 精读一：十路并行 NIH 审计**
2026-07-26 同一天做了两件相反的事——立下《优先选用持续维护的依赖》的政策，然后用覆盖每个包分组的十路并行审计逐条否掉 30 多个替换提案。理由全是具体证据：vscode-jsonrpc 只能删 255 行且表达不了 `maxMessageBytes`、反转了取消宽限期语义、在 ESM 仓库里是 CJS；p-retry "执行模型不对"（那个插件是返回决策的 waterfall 监听器，重新执行由 agent loop 依据持久日志负责）；shell-quote 是拿安全边界换 1 行代码；strip-ansi 只能替掉约 20 行内层，而 `stripVTControlCharacters` 被实证会泄漏未终止的 OSC 载荷。最锋利的一笔自省：`AGENTS.md` 其实从未写过任何依赖政策，**agent 只能从既有模式里自行推断出一条"不要加依赖"的规则，而这条推断出的规则比任何人实际决定过的都更严格**——这是 AI 参与开发时独有的失败模式。

**12.6 精读二：代码写完了才发现前提是假的**
《用 `node:timers/promises` 替代手写可取消休眠》论证完美、风险栏写着"基本没有风险"，PR #679 实现完毕后发现 vitest 的假时钟不拦截 `node:timers/promises`。整篇原样冻结，Status 行改成"实现证伪了行为等价前提"。

**12.7 精读三：项目第 9 天的"删除审计日"**
2026-06-20 产出 21 篇笔记，12 篇是 simplification，5 篇被自己否掉。这五篇揭示了事件溯源会话的核心不变量，逐条讲：《加载时截断被中断的最终轮次》（否：单个轮次可包含大量工具输出，静默丢弃代价太大）、《只持久化组装后的 assistant 消息，不存 chunk》（否：高保真回放、部分失败流、快照回放都依赖 `assistant/chunk`）、《删掉持久的 step 边界事件》（否：对称的 start/end 让崩溃修复、不变量、transcript 检查都比从相邻事件推断更清楚）、《把持久化接口折进 dsh-session》（否：独立的 Service Definition 包正是这个 seam 的角色划分）、《删掉 bash 输出的 spill 文件》。

**12.8 四篇复盘：准入门槛与逐篇拆解**
准入三条同时成立：隐蔽、系统性、重新发现代价高。逐篇讲：
- **0001**：178 个绿灯 + 100% 行覆盖，第一个真实编辑器连接就崩。一行 `export default apply` 让 Loader 的 `unwrapExports` 丢掉整个模块命名空间；叠加 Cordis 服务解析只沿祖先方向遍历。为什么测试没抓到——测试都用 `ctx.plugin({...})` 手动挂插件，而 `unwrapExports` 只被 Loader 调用；且顶层调用时代理会走绕过 fiber 遍历的全局直查路径。教训写死成规则：至少一个测试端到端驱动真实 Loader/export 路径，且因为不调模型，它属于 CI 而不是 key 门控之后。
- **0002**：快照刷新把 `UNKNOWN_TOOL` 洗成了"预期输出"。**一句话教训：快照刷新是 fixture 的生产过程，不是正确性审查。** 后续：2026-08-11 他们干脆改了 vendored Loader，让 `disabled` 成为唯一被插值的元数据字段——"隐患以求值而非禁止关闭"，顺带删掉整个 Windows 平台补丁层（回扣第 7 章）。
- **0003**：自家 web agent 改完 GUI 后去验收另一个端口上的另一个服务器，把裸 Vite 的白屏 HTTP 200 当成功。复盘用持久事件日志的 seq 号逐条取证，并声明"以这些事件为依据，而不是根据后续报告反推意图"。更狠的一笔：第一版回归测试本身也是假的（超时杀掉 Vite 后"非零退出"断言照样通过）。
- **0004**：用一个 stderr 前缀同时表示"信息"和"致命"，导致 ripgrep 无匹配被报成沙箱故障；叠加适配器把结构化 `SandboxUnavailableError` 换成了通用 `SEARCH_FAILED`。两条可迁移规则：进程归因需要多项独立证据同时成立；适配器必须保留下层 seam 拥有的结构化失败。

**12.9 五个到开源当天还停在 proposed/ 的项目**
API extractor 报告、架构一致性检查、供应链与 vendor 漂移、确定性与压力测试、变异测试——全是测试与流程严谨度，第一天就想清楚、最后也没做完。变异测试那篇写得尤其明白：逐文件 100% 覆盖率门禁只证明每行被执行过，"在 agent 编写测试的场景下，覆盖率压力可能产出执行但不断言的测试"。**他们两个月前就预判了复盘 0001 的根因，然后没来得及建这道防线。** 收尾再点出 `AGENTS.md` 第 5 行那节"预发布姿态：地基优先于爆炸半径"——里面写着"首个 tag 发布时删掉本节"，而它被留到了公开那一刻。

## 关键文件

- `.agents/notes/README.zh.md`、`scripts/agent-note-tree.ts`、`.agents/notes/archived/manifest.json`
- `docs/postmortem/README.zh.md` 及 0001–0004 四篇
- `.agents/notes/rejected/simplification/2026-07-26-dependency-swaps-rejected-by-nih-audit.zh.md`
- `.agents/notes/rejected/simplification/2026-07-26-builtin-timer-promises-for-hand-rolled-sleeps.zh.md`
- `.agents/notes/rejected/simplification/2026-06-20-*.zh.md`（五篇）
- `.agents/notes/implemented/process/2026-07-26-dependencies-over-hand-rolling.zh.md`
- `.agents/notes/implemented/feature/2026-08-10-subagent-approval-pinned-never.zh.md`
- `AGENTS.md`

**读者收益**：拿到一套可以明天就在自己团队落地的决策记录制度，以及四个"为什么每一道安全网都没拦住"的真实故事——这是全书唯一别人给不了的东西。

**字数**：16,000

---

# 第 13 章　让模型给自己写插件：运行时自修改、双半沙箱，与一页迁移清单

**钩子**：模型可以在一个正在跑的 harness 里现写一个插件、现挂上去。用户需要点头的那扇门，守的不是"要不要执行代码"——那件事在组合层已经被授权了；它守的是"要不要往我的页面里塞 UI"。

## 小节

**13.1 五个动词：inspect / define / run / stop / undefine**
先讲身份四件套：`pluginId`（可长期演进的插件）、`packageId`（不可变的一份源码版本）、`pluginRunId`（一次激活尝试）、`currentPackageId`（最近一次完全成功的版本）。改代码 = 在同一个 pluginId 上追加一个新 packageId，永不覆盖——这套"不可变版本 + 可变指针"是回滚和事后诊断的地基。再讲写代码之前先查真实契约：`cordis_inspect_list` / `cordis_inspect_query`，host 侧数据来自生成的 `api-catalog.ts`（与 `docs/subsystems` 出自同一次 AST 遍历，所以模型读到的和文档渲染的不可能偏离），client 侧是一次可取消的跨页面往返。

**13.2 host 半：node:vm 沙箱的工程细节**
`define` 只登记不执行，但用**运行时同一个编译器**做语法预检（刻意用 `new Script` 而不是 `new Function`，为了让预检和求值报出同一份行号与 caret；检测到出错行含 ` as ` 还会额外教一句"这里是纯 JS 不是 TypeScript"）。沙箱里 `require`/`fetch`/`setTimeout` 等被换成调用即抛的**教学陷阱**，错误文本直接告诉模型改用 `ctx.fs` / `ctx.web` / `inject:['timer']`；但 `process` 故意留成 `undefined`——一个会抛的 accessor 会在 `typeof process` 这种特征探测处就炸掉。还要给 vm 侧的 `Object`/`Array`/`Error`/`Promise`/`Map`/`Set` 打 `Symbol.hasInstance` 补丁，否则模型写的 `err instanceof Error`（err 来自 host 服务）静默返回 false。

**13.3 guard：把一个真 ctx 缩成一份可教的契约**
白名单动词表 + `ctx.get` 可选查找 + 属性访问必须在 `inject` 里声明过（两条不同的拒绝文案分别教"去声明它"和"它被刻意扣着"）。两条真正的安全规则：任何被注入服务的方法若返回一个 Cordis Context 一律拒绝（那是一个没被 guard 包过的、通回运行时的新句柄）；`tools.get` 只返回 schema 视图不返回活的 `ToolDefinition`（否则包代码拿到 `execute` 就能绕过第 8 章那整条流水线）。最后读那段 `jscpd:ignore` 注释：host 和浏览器两份 guard 是**有意的手抄孪生**，理由是两个面在不同的 `ts.Program` 里编译、Context 合并了不同的服务键，抽进共享包等于把一条安全不变量搬出执行它的那一半——这是罕见的"拒绝 DRY"的正当理由。

**13.4 浏览器半：闭包遮蔽与渲染崩溃的归因**
`new Function(...parameters, ...)` 的参数表就是模型能用的全部符号；`setTimeout`/`fetch`/`require` 作为**参数名遮蔽**同名全局，页面本身毫发无损。guard 在 `slots.register` 成功后把 component 对象本身 claim 进 WeakMap（注册表原样保存 component，用身份当键就够了），于是页面上任意一次 entry 崩溃都能精确映射回是哪个动态包注册的。一次观察分两个出口、两种寿命：上行给撰写它的会话（host 每包只留最后一条、跨页面）、落在本页面板（本页当前）；报告本身失败只 `console.error`，不让一次崩溃变成两次。`theme.overrideTokens` 的 source 参数被无条件替换成包 id，`slots.register` 的 priority 被无条件覆盖——签名保持不变只是为了和文档里的服务签名对得上，传进来的值从头到尾没被信任过。

**13.5 两半之间：启动图、一条 `/api`、两套协议**
`packages/host/webserver` 提供的 `ctx.webServer` 只有四类东西：具名路由表（exact 优先、再最长前缀）、**upgrade（WebSocket）路由注册表**、一个唯一的 fallback 席位、以及 `index.html` 的转换回调 `tapIndex`——它对 agent、session、工具一无所知。协议真源是注入到 `<head>` 第一个 script 的 `window.__DSH_BOOT__` 启动图（JSON 里的 `<` 会被转义）；裸跑 `apps/web` 的 Vite 只会白屏，这正是复盘 0003 的坑。`/api` 是一条路由跑两套协议，靠 interceptor 分流：两段式路径走 Typert Gateway，其余落回遗留 apiproxy。

**13.6 Typert：装饰器 + 编译期生成的类型化 RPC**
`@Remote` 本身不产生任何类型信息，只往模块私有 WeakMap 里记一笔；严格描述符、Zod schema、Client 的 `.d.ts` 全部由构建期 generator 从 Host 的 `ts.Program` 分析出来。规模数据：生产代码里一共 **24 个 `@Remote` 方法，分布在 5 个包**（cordis-host-runner 12、goal 6、message-feedback 3、commands 2、plugin-inventory 1）——也就是说**恰好一半属于运行时自修改这一个功能**，这套网关基本是被 `cordis_define`/`cordis_run` 逼出来的。三个设计点：复杂 host 对象靠 lookup 声明 `agent↔agentId` 映射、取消信号是带外 carrier signal 永不进 args、从源码跑时有一条 `Function.prototype.toString` 抠参数名的 SRC 回退——但 **Client 永远拒绝挂载没有严格 codec 的 SRC 描述符，且严格 endpoint 被撤回后不会降级回 SRC**：热卸载不能悄悄削弱校验强度。

**13.7 本地 HTTP API 的信任栅栏该绑什么**
绑 **Host 头，不是 Origin**：明文 HTTP 下浏览器的图片与导航读取既不带 Origin 也不带 Fetch-Metadata，而 Host 是 DNS rebinding 唯一伪造不了的头。`trustedHosts` 条目必须是 WHATWG 解析后逐字读回相同的裸 authority，否则插件加载期就大声失败（防 `harness.internal/path` 这类笔误静默授权 hostname、防补零端口把精确端口放大成任意端口）。特权方法集用空信任表过栅栏、钉死在回环。作者自己的免责声明也要照抄：**这是可达性策略，不是认证层**。

**13.8 失败怎么回到模型手里**
三条语义不同的通道：同步拒绝走工具错误；异步结算（run 最终成败、渲染崩溃、host handler 抛错）走 `agent.steer()`；用户手势导致的状态变化走 `agent.inject()`。运行期失败按 `平台\0类别\0消息` 去重，一个每秒抛一次的 handler 对模型的代价是**一段话**而不是一张越来越长的清单。每条 steer 文本都以可执行的下一步收尾——这是把"报错"升级成"可自愈"的关键。顺带讲一个诚实的观察：`lifecycle.ts` 的错误文案里还写着已改名的工具 `cordis_runtime_inspect`，preset 头注释还提着不存在的 `cordis_mount`——**给模型看的教学文案一旦写死在错误消息里，就和文档一样会腐坏，而且腐坏得更隐蔽**。

**13.9 尾声：一页迁移清单**
把全书能直接搬走的东西压成一张表：仅追加日志 + seq 恒等下标；surface 投影与 replace 遮蔽；waterfall/serial/guard 三种扩展点的区别；能力三角色拆包；per-call policy 而非 per-provider config；fail-loud 渲染与运行时不变量伴生插件；错误文案当产品设计；决策记录必须写"击败了什么"。每条给一句"在你的项目里最小落地形态是什么"。

## 关键文件

- `packages/extensions/cordis-host-runner/src/index.ts`、`src/sandbox.ts`、`src/guard.ts`、`src/lifecycle.ts`、`src/inspect-registry.ts`
- `packages/extensions/cordis-client-runner/src/client/evaluator.ts`、`guard.ts`、`orchestrator.ts`、`runtime.ts`
- `packages/extensions/tool-cordis/src/prompt.ts`、`src/api-catalog.ts`
- `packages/host/webserver/src/index.ts`、`packages/client/modules/src/index.ts`、`src/client/system.ts`
- `packages/client/connection/src/api-request-trust.ts`、`src/rpc-host.ts`
- `packages/api/gateway/src/index.ts`、`src/client/index.ts`、`packages/api/remotes/src/remote-events.ts`、`packages/typert/protocol/src/index.ts`
- `packages/bundle/web-app/src/index.ts`

**读者收益**：见识一个 agent 能安全地改写自身运行时的完整工程形态，并带走一张可以明天就用的迁移清单。

**字数**：22,000

---

# 附加交付

## 一、全书一句话卖点

> **市面上已经有书教你"怎么用"一个 agent harness；这本书带你把一个 219 个包、9 个连源码搬进来的框架包的真实生产级 harness，从 `npx` 一路拆到 `boot()` 的每一行——并且读完它 683 篇写着"我们否掉了什么"的设计笔记和 4 篇"为什么每一道安全网都没拦住"的事故复盘。**

副标题备选：《从装上到读懂：一本关于别人为什么这么写的书》

## 二、8 个短视频选题（每条 60–180 秒）

1. **《你电脑上根本没有那个配置文件》** —— `--dump-config` 现场演示：磁盘上永远是 `[]` 加三行注释，而且每次启动都被覆写。反转：这不是偷懒，是在对抗框架自己的"树写回"。（引流最强，第 1 章）

2. **《一行五个字符的补丁，撑着整套配置架构》** —— 上游 cordis 的 patch 实现只在循环开始前建一次 id 索引，于是"A 层 insert 的行，B 层永远改不到"。dsh 补了一句 `buildMap(insert)`。没有这一行，profile/bundle 整套设计不成立。（第 7 章）

3. **《178 个测试全绿、100% 行覆盖，第一个真实连接就崩了》** —— 一行 `export default` 引发的复盘 0001。金句直接打屏：覆盖率证明代码行被执行过，不能说明功能按交付方式正常工作。（第 12 章，最容易破圈）

4. **《快照测试骗了他们七个场景》** —— 复盘 0002：日志里躺着 `UNKNOWN_TOOL`，快照套件全绿，因为刷新后的期望输出和"通用失败卡片"完美匹配。金句：快照刷新是 fixture 的生产过程，不是正确性审查。（第 12 章）

5. **《他们自己的 AI 改完页面，跑去验收了另一个端口》** —— 复盘 0003，用会话日志的 seq 号逐条取证，连"第一版回归测试本身也是假的"这段都讲。（第 12 章，故事性最强）

6. **《十路并行审计，30 多个"换成成熟依赖"被逐条否掉》** —— 结尾抛出那句自省：这个仓库从来没写过依赖政策，是 AI 自己从代码风格里推断出了一条更严的规则，然后严格执行了两个月。（第 12 章，AI 协作开发独有议题）

7. **《你的子 agent 永远问不了人》** —— 被委派的子 agent 审批策略被钉死为 `never`，理由是"无人可问"；而这篇笔记明文推翻了 16 天前自己的相反决定。（第 10 章）

8. **《让模型自己给自己写一个插件挂上去》** —— `cordis_define` → `cordis_run` 全流程录屏。反转结尾：用户点头的那扇门守的不是"要不要执行代码"，而是"要不要往我页面里塞 UI"——纯 host 半的包能读写文件、跑命令，模型一句话就直接跑起来了。（第 13 章，话题度最高）

> 备用选题：《崩溃前先花 2 秒把终端还给你》（`installFailLoud`）、《ralph 的全部编排逻辑是一段写死在源码里的字符串》。

## 三、如果只写三章，先写哪三章

**答案：第 2 章、第 4 章、第 12 章。**

| 章 | 为什么是它 |
|---|---|
| **第 2 章 主循环** | 全书的地基，也是唯一能让读者立刻动手复现的一章。"从 50 行长到 496 行"这个叙事本身就是最好的样章——读者读完就能回自己项目里改代码。任何后续章节都要靠它建立的 turn/step/inbox 词汇。 |
| **第 4 章 会话即日志** | 最可迁移、最反直觉、最能证明"这本书讲的是架构不是 API"。事件溯源 + surface 投影 + 那条会逐字节比对的运行时不变量，三样东西任何做 agent 的人拿走就能用。它也是第 6、10、11 三章的公共前置。 |
| **第 12 章 设计笔记与复盘** | **唯一别人给不了的差异化**，也是最容易破圈、最适合先发出去验证市场的一章。它不依赖前面的代码细节也能独立成文（虽然放在书里必须靠后），四篇复盘天然自带传播性。先写它可以立刻拿去做付费专栏首篇 / 短视频 / 公众号连载，验证选题成立与否。 |

**执行建议**：这三章按 2 → 4 → 12 的顺序写，先写完 12 章拿去公开发一遍（它的传播性最好且不剧透核心技术内容），用读者反馈决定后面 10 章的详略配比。第 1 章此时压缩成一篇 3,000 字的《开始之前：把 dsh 跑起来》作为第 2 章的前置附录随发即可——它是必要的入口，但不构成任何人的购买理由。