# 第九阶段：可视化修改与局部编辑能力 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 在现有 AI 应用生成平台的对话式修改能力之上，新增“可视化修改”功能，让用户能够直接在预览页面中选择要修改的网页元素，再结合自然语言描述局部修改需求，从而让 AI 更准确地修改目标区域，降低“描述不清”“改错位置”“整体被误改”的风险。

**Architecture:** 第九阶段采用“轻量可视化选区 + 提示词增强 + 模式化后端修改策略”的方案，而不是走完整低代码 DSL 编辑器路线。前端在预览 iframe 中注入可视化选区脚本，通过 hover / selected 高亮、元素信息采集和 `postMessage` 与主站通信，把用户选中的元素上下文拼接进对话输入。后端按生成模式分流处理：`SINGLE_FILE` 与 `MULTI_FILE` 通过提示词约束执行“只改指定区域但完整返回代码块”的全量改写；`VUE_PROJECT` 则依赖一组文件工具完成读目录、读文件、改文件、删文件、写文件的增量修改。再配合工具结果结构化展示、聊天记忆回放和更精细的提示词约束，形成真正可用的局部修改链路。

**Tech Stack:** Vue 3, Ant Design Vue, iframe + `postMessage`, Vite dev proxy, Spring Boot 3.5.5, Java 21, LangChain4j, Reactor, Chat Memory, 自定义工具集（读目录 / 读文件 / 改文件 / 删文件 / 写文件）。

---

## 1. 阶段定位

第七阶段解决的是“生成工程项目”，第八阶段解决的是“平台能力补全”，而第九阶段解决的是另一个非常关键的问题：

**用户已经生成出网站后，如何精准地改它。**

在纯对话模式下，用户通常会这样描述修改需求：

- “把这里改成红色”
- “把这个标题换一下”
- “把中间那张卡片文字改掉”

这些表达对人类来说勉强能猜，但对模型并不稳定。因为 AI 只看到代码，不直接知道用户嘴里的“这里”“这个”“中间那张”到底对应哪个元素。

所以第九阶段的目标不是把编辑器做成专业设计工具，而是做一层成本可控、效果明显的增强：

- 用户直接在网页上点击目标元素。
- 平台把元素信息结构化传给 AI。
- AI 在这个更明确的上下文里修改代码。

换句话说，第九阶段是在对话式编程和可视化编辑之间做折中：

- 不做全量拖拽低代码。
- 不做复杂 DSL 设计器。
- 不做浏览器里完整源码 IDE。
- 只做“选中目标 + 精准修改”。

这也是第九阶段最核心的产品定位。

## 2. 需求分析

## 2.1 当前问题

目前平台已经支持基于对话历史继续修改网站，这是很好的基础。但只靠文本描述修改需求仍然有明显问题：

- 用户描述经常不精确。
- 同一页面存在多个相似组件时，AI 可能改错地方。
- 用户只想改一小处，AI 却可能重写大片区域。
- 对多文件 / 工程项目来说，模型更容易因为上下文不足而误改。

举例：

如果用户生成了一个包含多个卡片的网站，现在只想修改其中第二张卡片的标题。用户如果说“修改卡片标题”，AI 可能不知道是哪个卡片。即使用户补一句“改第二个卡片的标题”，在复杂页面结构下，模型仍然未必稳定找到准确位置。

所以平台需要引入一个“元素选择”动作，帮助用户把修改目标说清楚。

## 2.2 用户真正需要的不是完整低代码，而是高命中率的修改

这一点很重要。很多团队一看到“可视化修改”，第一反应是：

- 做一个画布编辑器
- 做一个组件树
- 做一个属性面板
- 做一套页面 DSL

但这些事情都非常重，而且它们的本质已经不是“AI 修改生成网站”，而是在做另一套低代码平台。

第九阶段不应该直接跳到那个层级。用户当前最需要的，其实只是：

- 我点中哪个元素，AI 就知道我要改谁。
- 我说“改红”“换文案”“换图片”，AI 别再改错地方。

所以第九阶段的价值，不是“让用户像设计师一样拖组件”，而是“让修改目标的指向更清晰”。

## 3. 竞品调研与方案取舍

## 3.1 美团 NoCode 的启发

图片里展示了美团 NoCode 的做法。它有两个特点很值得参考：

- 用户可以直接在页面上选中元素。
- 系统会把选中元素的信息与修改需求拼接后再发给 AI。

通过抓包可以看到，请求中会包含：

- 文件路径
- 代码行信息
- tagName
- 选中区域信息
- 甚至完整文件内容

这说明它并不是把“视觉点击”直接映射成浏览器即时改样式，而是仍然走代码修改链路，只不过在前端帮用户完成了“目标定位”这一步。

这对第九阶段非常有启发：

- 真正的核心不是画布本身。
- 真正的核心是“把用户选中的元素上下文喂给后端”。

## 3.2 百度秒哒的启发

图片里还展示了百度秒哒的编辑方式。它和美团相比，有两个特点：

- 更偏 DSL 结构化页面编辑。
- 有些修改动作并不直接对应源码行，而是对应 DSL 片段。

这种方式的优点是：

- 更容易做结构化操作。
- 参数可以更清晰地与页面结构绑定。

但它的前提是：

- 平台本身必须围绕 DSL 搭建。
- 页面结构不是任意 HTML / 任意 Vue 工程，而是受控模型。

当前项目显然不在这个阶段。我们面对的是 AI 生成出来的真实代码项目，不是 DSL 页面树。

所以：

- 可以学习它“传递结构化参数”的思路。
- 但不能照搬它“基于 DSL 的编辑机制”。

## 3.3 为什么不做完整低代码 DSL 编辑器

结合竞品调研，第九阶段明确做出这个结论：

**不做完整可视化低代码编辑器。**

原因有 4 个：

- 开发成本太高。
- 需要定义并长期维护页面 DSL 规范。
- 需要页面渲染层、编辑层、存储层一起重构。
- 与当前“代码生成平台”的阶段目标不匹配。

第九阶段更合理的方案是：

- 保持代码生成体系不变。
- 新增可视化选区能力。
- 把选中的元素上下文加入提示词。
- 后端仍然以代码修改为主。

## 3.4 最终方案结论

第九阶段最终选型为：

- **前端负责选中元素与可视化高亮。**
- **前后端通过 iframe + `postMessage` 通信。**
- **后端基于不同代码生成模式，采用不同修改策略。**

这是一条“成本最低但收益明显”的路线。

## 4. 总体架构

## 4.1 可视化修改主链路

第九阶段建议的完整链路如下：

1. 用户进入应用对话页。
2. 用户点击“编辑模式”。
3. 预览区 iframe 中的网页进入选区模式。
4. 用户在网页中 hover 元素，页面显示悬浮高亮。
5. 用户点击某个元素后，该元素变为选中状态。
6. iframe 将元素信息通过 `postMessage` 发送给主页面。
7. 主页面展示“当前选中的元素信息”。
8. 用户输入修改需求。
9. 前端把元素信息自动拼接到提示词中。
10. 后端收到增强后的提示词。
11. 后端根据 `codeGenType` 选择修改方案：
    - `SINGLE_FILE`
    - `MULTI_FILE`
    - `VUE_PROJECT`
12. AI 产出修改结果。
13. 平台保存修改结果并刷新预览。
14. 前端退出编辑模式或清空当前选区。

## 4.2 三种模式的核心差异

第九阶段最关键的工程决策，就是不能把三种模式当成同一件事处理。

### `SINGLE_FILE`

特点：

- 只有一个 HTML 文件。
- AI 通常直接返回完整 HTML。
- 没有文件工具依赖。

修改策略：

- 提示词中明确“只修改选中区域”。
- 但返回结果仍然是完整 HTML 文件。

### `MULTI_FILE`

特点：

- 有 `index.html`、`style.css`、`script.js` 三个核心文件。
- AI 返回多个代码块。

修改策略：

- 提示词中明确选中元素与限制范围。
- 要求只修改必要代码块，保持其余内容稳定。
- 仍返回完整多文件代码块，而不是局部 patch。

### `VUE_PROJECT`

特点：

- 工程目录复杂。
- 文件数量多。
- 每次全量返回全部文件极不现实。

修改策略：

- 不能再靠“整项目完整返回”。
- 必须依赖工具做增量修改。
- AI 先读取相关文件，再选择修改 / 新增 / 删除。

所以第九阶段本质上是一套“同一交互入口，不同后端执行策略”的方案。

## 5. 前端方案设计

## 5.1 为什么使用 iframe 作为预览载体

当前项目的预览区已经是基于 iframe 实现的，这是第九阶段最重要的现成基础。

iframe 的好处是：

- 预览内容与主站隔离。
- 可以直接运行真实生成网站。
- 不需要把预览页面改造成组件化渲染树。
- 适合后续注入少量脚本实现编辑模式。

所以第九阶段不需要重写预览体系，只需要在 iframe 之上加一层选区逻辑。

## 5.2 为什么选择 `postMessage`

主页面和 iframe 页面要通信，最自然的方式就是 `window.postMessage`。

第九阶段这里的通信需求并不复杂：

- iframe 通知父页面“当前 hover / selected 的元素是谁”
- 父页面通知 iframe“开启编辑模式 / 清除选中 / 退出编辑模式”

这个需求与 `postMessage` 完全匹配。

推荐消息类型至少包括：

- `ELEMENT_HOVER`
- `ELEMENT_SELECTED`
- `TOGGLE_EDIT_MODE`
- `CLEAR_SELECTION`
- `CLEAR_ALL_EFFECTS`

## 5.3 同源问题与最终决策

这里有一个必须写透的技术点：**iframe 注入脚本与 DOM 访问依赖同源。**

浏览器同源策略要求协议、域名、端口都一致，否则：

- 父页面不能直接访问 iframe 的 DOM
- 也不能安全地注入脚本

图片中给出了两个方案：

### 方案 A：提前在生成代码里植入 `postMessage` 逻辑

优点：

- 不依赖后续动态注入。

缺点：

- 必须在 AI 生成阶段就写入额外代码。
- 会污染所有生成网站。
- 下载源码时会把这些编辑辅助代码一起带走，影响纯净性。

结论：不推荐。

### 方案 B：编辑时动态注入脚本

优点：

- 不污染生成代码。
- 编辑功能只在需要时启用。
- 更适合平台编辑场景。

缺点：

- 要求父页面与 iframe 页面同源。

结论：选择这个方案。

## 5.4 为了满足同源，需要修改前端开发配置

当前仓库 `ac-ai-code-free-fronted/.env.development` 中：

- `VITE_API_BASE_URL=http://localhost:8700/api`
- `VITE_APP_DEPLOY_URL_PREFIX=http://localhost:8700/api/static`

这意味着前端运行在 `5173`，预览运行在 `8700`，天然不同源。

第九阶段本地开发阶段建议这样改：

- `VITE_API_BASE_URL=/api`
- `VITE_DEPLOY_DOMAIN=http://localhost`

同时在 `vite.config.ts` 中加代理：

```ts
export default defineConfig({
  plugins: [vue(), vueDevTools()],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8700',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
```

这样前端通过 `5173/api/...` 访问后端，同时 iframe 也可通过相同前缀访问预览资源，从而达到同源效果。

这一点是第九阶段落地的前提条件，不是可选优化。

## 5.5 选区脚本需要采集哪些信息

当用户点击元素后，前端至少要采集这些信息：

- `tagName`
- `id`
- `className`
- `textContent`
- `selector`
- `pagePath`
- `rect`

其中最关键的是：

- `selector`
- `textContent`
- `pagePath`

因为它们最适合被拼进提示词，帮助 AI 锁定位置。

推荐的结构大致如下：

```ts
export interface ElementInfo {
  tagName: string
  id: string
  className: string
  textContent: string
  selector: string
  pagePath: string
  rect: {
    top: number
    left: number
    width: number
    height: number
  }
}
```

## 5.6 高亮交互设计

图片中的实现有两个视觉层级，这是合理的：

- hover 态：蓝色虚线 / 浅色背景
- selected 态：更明显的绿色或更粗边框

这两个层级都应该保留，因为它们分别承担不同任务：

- hover 帮助用户扫视页面
- selected 帮助用户确认“当前我要改谁”

另外还建议在 iframe 页面右上角加一个短暂提示条，例如：

- “编辑模式已开启，悬浮查看元素，点击选中元素”

这个提示非常便宜，但对交互理解帮助很大。

## 5.7 事件监听原则

选区脚本需要监听：

- `mouseover`
- `mouseout`
- `click`
- `message`

设计原则：

- 使用捕获阶段监听，优先拦截页面自身 click 逻辑。
- 在编辑模式中，点击元素时必须 `preventDefault()` 和 `stopPropagation()`。
- 跳过 `body`、`html`、`script`、`style` 等无意义节点。

否则用户点选元素时，可能会直接触发页面本身的导航或按钮逻辑。

## 5.8 选择器生成策略

图片中给出的选择器生成方式是“从当前元素向上回溯，拼接 tag / id / class / nth-child”。这个思路可用，但要注意第九阶段的定位不是“给程序精确执行 CSS 查询”，而是“给 AI 提供足够可理解的上下文”。

因此建议把选择器设计成：

- 足够表达位置
- 不必追求百分之百稳定重放
- 可读性比机械精确性更重要

例如：

```text
div.app:nth-child(1) > div.resume:nth-child(2) > div.section:nth-child(2) > p:nth-child(2)
```

这类字符串对 AI 是有用的，因为它携带了层级关系。

## 5.9 `visualEditor.ts` 的职责边界

图片中已经把可视化编辑逻辑提取到 `visualEditor.ts`，这是非常合理的。

这个文件应该承担这些职责：

- 管理 iframe 引用
- 开关编辑模式
- 注入脚本
- 向 iframe 发消息
- 处理来自 iframe 的消息

但它不应该承担：

- 对话页状态管理
- 最终消息发送逻辑
- SSE 处理
- 业务数据加载

这些仍然应该留在 `AppGeneratorPage.vue` 中。

## 5.10 对话页需要增加哪些 UI

第九阶段前端至少要增加 3 处 UI：

### 1. 编辑模式切换按钮

位置建议放在预览区顶部操作栏，与“刷新”“桌面端 / 移动端”并列。

按钮状态：

- 进入编辑模式
- 退出编辑模式

### 2. 当前选中元素信息区

建议放在消息区和输入框之间，使用 `a-alert` 或轻量信息卡片展示：

- 选中元素标签
- 选中元素文本内容摘要
- 选中元素所在页面路径
- 选中元素 selector
- 手动关闭按钮

### 3. 输入提示变化

当已经选中元素时，输入框 placeholder 也应该变化，比如：

- 未选中：`描述具体的需求，例如：修改配色为深色模式...`
- 已选中：`已选择页面元素，请描述要修改的内容...`

这会显著降低用户困惑。

## 5.11 提示词拼接策略

第九阶段不是把 `ElementInfo` 原样 JSON 扔给后端，而是要拼成可读上下文。

推荐拼接格式：

```text
选中元素信息：
- 页面路径：/
- 标签：h1
- 选择器：div.app > section.hero > h1
- 当前内容：你好，我是张三
```

然后再拼接用户原始修改需求：

```text
修改需求：把标题改成“你好，我是李鱼皮”
```

之所以推荐自然语言结构，而不是裸 JSON，是因为：

- 当前后端主要仍是 prompt 驱动，不是结构化参数执行器。
- 自然语言结构对不同模型兼容性更好。

## 6. 原生应用全量修改策略

## 6.1 为什么原生模式不适合做工具级局部 patch

`SINGLE_FILE` 和 `MULTI_FILE` 看似也能引入工具，但第九阶段不建议这么做，原因是：

- 它们的代码量本来就不大。
- 直接全量返回完整文件更简单。
- 当前解析与保存链路已经围绕完整代码块建立。

所以原生模式下，局部修改更适合靠“提示词强约束”，而不是额外引入复杂工具链。

## 6.2 当前最大问题：提示词不够强调“只改指定区域”

图片里演示了一个典型问题：

- 用户只想改标题
- 后端提示词解释错了第一个代码块
- 整个页面被错误替换或误改

这说明：

- 原生模式不是不能做局部修改。
- 问题主要出在提示词约束不够强。

## 6.3 原生 HTML 提示词应新增的约束

在现有 `codegen-single-file-system-prompt.txt` 基础上，第九阶段建议新增一段专门用于可视化修改的附加约束：

```text
特别注意：在本轮对话中，用户可能会提供“选中元素信息”和“修改需求”。

你的任务不是重新设计整个页面，而是在保持其他内容不变的前提下，只修改与选中元素相关的部分。

要求：
1. 你必须优先根据“选中元素信息”判断要修改的位置。
2. 你只能修改满足用户需求的最小必要代码。
3. 你必须返回完整 HTML 文件内容，而不是只返回被修改片段。
4. 你不得删除与本次修改无关的代码。
5. 如果用户只修改文案、颜色、图片、尺寸等局部内容，页面结构应尽量保持不变。
```

## 6.4 原生多文件提示词应新增的约束

在 `codegen-multi-file-system-prompt.txt` 基础上，也要增加类似约束：

```text
特别注意：用户可能会提供“选中元素信息”和“修改需求”。

你需要根据选中元素定位修改范围，只修改必要的文件和必要的内容。

要求：
1. 不要改动与目标元素无关的内容。
2. 若修改仅影响 HTML，则不要改 CSS/JS。
3. 若修改仅影响样式，则尽量只改 style.css。
4. 你必须返回完整的相关代码块，而不是局部片段。
```

这两段约束，是第九阶段原生模式改动成功率提升的关键。

## 6.5 原生模式的执行规则

最终建议：

- `SINGLE_FILE`：始终返回完整 HTML。
- `MULTI_FILE`：返回被影响文件的完整代码块，未影响文件尽量不返回或原样返回。

关键点是：

- “局部修改”发生在语义层面。
- “完整返回”发生在交付层面。

## 7. Vue 工程项目增量修改策略

## 7.1 为什么 Vue 工程必须使用工具

`VUE_PROJECT` 与前两种模式完全不同。它的文件数量多、层级深、变更可能跨多个组件与配置文件。

如果每次修改都要求模型完整返回整个项目，问题会非常严重：

- token 爆炸
- 易截断
- 易误删文件
- 用户只改一个字，也要重吐整个项目

所以第九阶段在 Vue 工程模式下必须走“工具化增量修改”。

## 7.2 第九阶段所需工具集合

结合图片内容，第九阶段建议为 `VUE_PROJECT` 增加以下工具：

- `writeFile`
- `readFile`
- `modifyFile`
- `deleteFile`
- `readDir`

它们分别承担：

- 写文件
- 读文件
- 修改文件
- 删文件
- 查看目录结构

## 7.3 为什么 `readDir` 很关键

很多人会先想到 `readFile` / `writeFile`，但第九阶段里 `readDir` 其实同样关键。因为 AI 修改工程代码前，需要先知道项目结构，否则它可能：

- 猜错文件路径
- 误以为某个组件不存在
- 重复创建已有文件

所以 `readDir` 是让模型先建立项目结构认知的关键工具。

## 7.4 为什么 `modifyFile` 不能简单等价于 `writeFile`

理论上，模型可以：

1. `readFile`
2. 自己计算新内容
3. `writeFile` 覆盖

但第九阶段仍建议单独提供 `modifyFile`，原因是：

- 更贴近“只改一段内容”的语义。
- 能帮助提示词更明确地表达修改意图。
- 更适合在流式输出中向用户展示“替换前 / 替换后”的结果。

## 7.5 `deleteFile` 的安全边界

图片中明确提出：删除工具必须保护关键文件。这一点非常重要。

建议至少禁止删除这些文件：

- `package.json`
- `vite.config.js` / `vite.config.ts`
- `vue.config.js`
- `tsconfig.json`
- `main.js` / `main.ts`
- `App.vue`
- `README.md`
- `.gitignore`
- 锁文件

原因很简单：

- 这些文件往往是项目骨架核心。
- 一旦被误删，整个项目很容易立即不可运行。

所以 `deleteFile` 必须是“受限删除”，不是任意删除。

## 7.6 `readDir` 的输出形式建议

`readDir` 不需要返回超复杂 JSON。第九阶段建议它返回缩进结构化字符串即可，例如：

```text
src
  pages
    Resume.vue
  components
    HeroBanner.vue
```

这种输出对 AI 足够友好，而且比 JSON 更省 token。

## 7.7 `modifyFile` 的参数设计

建议参数保持简单：

- `relativeFilePath`
- `oldContent`
- `newContent`

执行规则：

- 文件不存在 -> 失败
- 文件存在但 `oldContent` 未命中 -> 返回提示，不直接强写
- 命中后做字符串替换并保存

这样做比按“行号替换”更稳，因为 AI 传行号经常不稳定。

## 7.8 `readFile` 与 `writeFile` 的职责边界

- `readFile`：返回完整文件内容
- `writeFile`：覆盖式写入完整文件

这两个仍然是最基础能力，尤其在以下情况仍有用：

- 需要创建新文件
- 需要重写整个文件
- `modifyFile` 不适合处理结构性改造时

## 8. 工具结果信息优化

## 8.1 为什么需要统一工具输出

仅仅让工具能执行还不够。第九阶段已经不再只是“后台完成修改”，还要让用户能看懂 AI 在做什么。

如果工具输出只是：

- 成功
- 失败

那前端体验仍然很差。

用户更关心的是：

- 改了哪个文件
- 替换了什么内容
- 新增了什么内容
- 删除了什么文件

所以第九阶段建议对每个工具增加“面向用户展示的结果生成器”。

## 8.2 `BaseTool` 基类设计

图片里提出了一个很好的优化：定义 `BaseTool` 基类，把所有工具的可视化输出收敛到统一接口。

建议基类至少包含：

- `getToolName()`
- `getDisplayName()`
- `generateToolRequestResponse()`
- `generateToolExecutedResult(JSONObject arguments)`

这能解决两个问题：

- 每个工具都有统一展示入口。
- 流处理器不需要写一堆 `if-else` 拼输出。

## 8.3 为什么这里建议把工具做成 Spring Bean

图片里建议每个工具都是一个独立 Bean，这个方向是对的。原因：

- 便于自动注入与收集。
- 便于通过 `ToolManager` 统一管理。
- 可读性比手工 new 一长串工具对象更强。

## 8.4 `ToolManager` 的职责

`ToolManager` 本质上不是业务层，而是工具注册中心。它负责：

- 收集所有 `BaseTool` Bean
- 根据工具名查找工具实例
- 返回全部工具数组给 AI Service 工厂

这里有一个图片中提到的细节必须写清楚：

- 返回全部工具时，建议返回数组而不是集合

原因是 LangChain4j 的 `tools(...)` 注入在某些场景下对数组更直观，且与自动注入 `BaseTool[]` 的形式天然匹配。

## 8.5 流处理器也要接入 `ToolManager`

有了 `ToolManager` 之后，第九阶段的流处理器就不该再手写每个工具的展示逻辑，而应该：

1. 从工具请求 / 工具执行结果中取出 `toolName`
2. `toolManager.getTool(toolName)`
3. 调用对应工具的展示方法生成用户可读输出

这样每新增一个工具，只需要：

- 实现工具本身
- 实现展示方法

而不用再改一次流处理器。

## 9. 后端方案总设计

## 9.1 为什么第九阶段建议“创建”和“修改”分离

图片最后的扩展思路里提到：创建和修改最好分开。这一点我建议直接写进正式计划，而不是只放到扩展项里。

原因：

- 创建应用与修改应用使用的提示词不同。
- 创建应用与修改应用依赖的工具集也不同。
- 修改场景更强调“限制范围”和“只改必要内容”。

因此第九阶段建议至少在设计层面拆分：

- Create Service / Prompt
- Modify Service / Prompt

即使第一版代码暂时不完全拆干净，也要让文档先把边界写清楚。

## 9.2 修改专用提示词应该强调什么

无论是原生模式还是 Vue 工程模式，修改类提示词都必须比创建类提示词更“保守”。

建议强调：

- 只修改用户明确指定的元素或相关区域
- 保持其余内容不变
- 不要擅自重构不相关代码
- 如果是 Vue 工程模式，优先使用工具了解现有结构再修改
- 如果只需小改，禁止整项目重写

## 9.3 为什么不推荐继续优化“工具流式参数解析”

图片里明确写了一个观点：不推荐继续深挖把所有工具流参数实时拆到极致。这一点我认同。

原因是：

- 每个工具参数结构都不一样。
- 前后端都要写解析逻辑，复杂度迅速上升。
- 收益有限。

第九阶段更务实的做法是：

- 保留工具请求与工具执行结果两个关键事件
- 把执行结果做得足够好看
- 不在实时碎片流里过度追求逐字符解析

## 9.4 对原生模式与 Vue 模式的统一抽象

虽然底层实现不同，但第九阶段在 API 与前端交互层面最好统一成：

- 用户先选元素
- 用户再发需求
- 后端返回修改过程与结果

统一的是交互范式，不统一的是执行策略。

## 10. 多媒体上传与更高级编辑的扩展方向

图片里提到了两个很有价值但不应塞进第九阶段主交付的扩展方向：

### 1. 支持多媒体上传

思路是：

- 前端先把图片上传
- 返回图片 URL
- 再把图片 URL 及描述拼进提示词发给后端

这对“替换图片”场景很实用，且不需要模型直接识别二进制文件。

### 2. `contentEditable=true` 的直接编辑

这是一条更激进的路线：

- 用户直接在网页上修改文本
- 平台再把修改映射回代码

这个方向很有吸引力，但第九阶段不建议正式纳入主计划。原因：

- 文本映射回源码并不总是稳定。
- 样式和结构改动远比文案改动复杂。
- 很容易引出另一套编辑状态同步问题。

所以第九阶段把它列为后续优化即可。

## 11. 与当前仓库的集成差距

基于当前代码仓库，现状非常明确：

- 前端 `AppGeneratorPage.vue` 还没有编辑模式按钮。
- 还没有 `visualEditor.ts`。
- 还没有 iframe 注入脚本与 `postMessage` 通信。
- 当前 Vite 没有 `/api` 代理配置。
- `.env.development` 还是绝对地址模式，不利于同源。
- 后端 `AiCodeGeneratorService` 仍只有创建类接口，没有修改专用接口。
- `AiCodeGenServiceFactory` 还是简单的全局工厂，没有任何工具集扩展。
- `CodeGenTypeEnum` 当前还只有 `SINGLE_FILE` 与 `MULTI_FILE`，连阶段七的 `VUE_PROJECT` 也尚未在当前主分支出现。

这意味着第九阶段文档必须明确说明一个前置条件：

**第九阶段依赖第七阶段的 Vue 工程工具化能力先落地。**

否则 Vue 工程模式下的可视化修改没有基础。

## 12. 建议修改与新增文件

## 12.1 前端

- Modify: `ac-ai-code-free-fronted/vite.config.ts`
- Modify: `ac-ai-code-free-fronted/.env.development`
- Modify: `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`
- Create: `ac-ai-code-free-fronted/src/utils/visualEditor.ts`

如果需要把元素信息展示和提示词拼接继续拆分，还可以新增：

- `ac-ai-code-free-fronted/src/utils/selectedElementPrompt.ts`

## 12.2 后端

- Modify: `src/main/resources/prompt/codegen-single-file-system-prompt.txt`
- Modify: `src/main/resources/prompt/codegen-multi-file-system-prompt.txt`
- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`
- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`

若第七阶段基础已落地，则还建议新增或修改：

- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/BaseTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/ToolManager.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/tools/FileDeleteTool.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/tools/FileDirReadTool.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/tools/FileModifyTool.java`
- Create: `src/main/java/com/adcage/acaicodefree/ai/tools/FileReadTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`
- Modify: `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`

## 13. 实施任务拆分

### Task 1：补齐前端同源开发环境

**Files:**

- Modify: `ac-ai-code-free-fronted/vite.config.ts`
- Modify: `ac-ai-code-free-fronted/.env.development`

**目标：**

- 增加 `/api` 代理。
- 把开发环境 API 改为相对路径。
- 为 iframe 脚本注入创造同源条件。

**关键决策：**

- 采用动态注入脚本方案，而不是在生成代码里提前埋编辑脚本。

**验证：**

- 本地前端与 iframe 预览页面同源可访问。

### Task 2：实现前端可视化选区核心工具

**Files:**

- Create: `ac-ai-code-free-fronted/src/utils/visualEditor.ts`

**目标：**

- 管理 iframe 编辑模式。
- 注入脚本。
- 监听元素 hover / selected。
- 通过 `postMessage` 收发消息。

**关键决策：**

- 选区逻辑从页面组件中抽离。
- 不在组件中直接拼大量注入脚本字符串。

**验证：**

- 进入编辑模式后，hover 和 selected 高亮正确工作。

### Task 3：改造 AppGeneratorPage 承接选区信息

**Files:**

- Modify: `ac-ai-code-free-fronted/src/pages/app/AppGeneratorPage.vue`

**目标：**

- 增加编辑模式开关。
- 展示选中元素信息。
- 在发送消息时自动拼接元素上下文。
- 支持清除选区与退出编辑模式。

**关键决策：**

- 输入提示语动态变化。
- 元素信息展示用轻量 `Alert` 或信息卡片。

**验证：**

- 用户选中元素并发送消息时，请求中包含增强后的元素上下文。

### Task 4：优化原生模式提示词

**Files:**

- Modify: `src/main/resources/prompt/codegen-single-file-system-prompt.txt`
- Modify: `src/main/resources/prompt/codegen-multi-file-system-prompt.txt`

**目标：**

- 强化“只修改选中区域”的约束。
- 保持完整返回规则。

**关键决策：**

- 原生模式不引入复杂工具，优先靠提示词解决局部修改精度。

**验证：**

- 标题、文案、颜色等局部修改能稳定命中，不误改全页。

### Task 5：为 Vue 工程模式补齐增量修改工具集

**Files:**

- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/FileDeleteTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/FileDirReadTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/FileModifyTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/FileReadTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/FileWriteTool.java`

**目标：**

- 支持 Vue 工程模式在修改场景中读目录、读文件、改文件、删文件、写文件。

**关键决策：**

- 删除工具必须保护关键文件。
- `modifyFile` 优先基于字符串替换，而不是行号替换。

**验证：**

- Vue 工程项目能完成文本、样式、图片链接等增量修改。

### Task 6：引入 BaseTool 与 ToolManager

**Files:**

- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/BaseTool.java`
- Create/Modify: `src/main/java/com/adcage/acaicodefree/ai/tools/ToolManager.java`

**目标：**

- 统一所有工具的显示名称、请求展示、执行结果展示。
- 统一注册与查找工具。

**关键决策：**

- 工具全部注册为 Spring Bean。
- ToolManager 返回全部工具数组。

**验证：**

- 新增任意一个工具后，AI Service 与流处理器都能自动接入。

### Task 7：改造 AI Service 工厂与流处理器

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGenServiceFactory.java`
- Modify: `src/main/java/com/adcage/acaicodefree/core/handler/JsonMessageStreamHandler.java`

**目标：**

- Vue 工程模式通过 ToolManager 注入全部工具。
- 流处理器基于 ToolManager 生成工具展示文本。

**关键决策：**

- 不在流处理器里硬编码每个工具的展示逻辑。

**验证：**

- 工具请求与执行结果在前端展示更清晰，包含文件名、替换前后内容等摘要。

### Task 8：引入修改专用 Service / Prompt 分层

**Files:**

- Modify: `src/main/java/com/adcage/acaicodefree/ai/AiCodeGeneratorService.java`
- Create/Modify: 修改专用 prompt 资源

**目标：**

- 创建与修改分离。
- 修改模式下使用更保守的提示词与工具集。

**关键决策：**

- 修改类 prompt 强调“只改必要内容”。

**验证：**

- 修改场景的误改范围明显收缩。

### Task 9：补齐测试与手工回归场景

**Files:**

- Create: `src/test/java/.../VisualEditPromptAssemblyTest.java`
- Create: `src/test/java/.../ToolManagerTest.java`
- Create: `src/test/java/.../FileModifyToolTest.java`
- Create: `src/test/java/.../FileDeleteToolTest.java`

**目标：**

- 覆盖元素上下文拼接。
- 覆盖工具注册与查找。
- 覆盖文件修改与关键文件保护。

**关键决策：**

- 前端交互效果需要手工回归，自动化测试只覆盖核心逻辑。

**验证：**

- 本地手工验证：
  - 选中文案改文字
  - 选中标题改颜色
  - 选中图片替换链接
  - Vue 工程模式下局部修改成功

## 14. 验收标准

第九阶段完成后，至少要满足：

- 用户可进入编辑模式并在预览页面中选择元素。
- hover 与 selected 高亮效果明显可用。
- 选中元素信息能展示在对话页。
- 发送修改消息时，元素上下文会自动拼接进提示词。
- `SINGLE_FILE` 模式可稳定完成局部修改，且返回完整 HTML。
- `MULTI_FILE` 模式可稳定完成局部修改，且只改必要文件。
- `VUE_PROJECT` 模式支持增量修改，不需要整项目完整返回。
- Vue 工程模式工具结果在前端展示清晰，不再只有生硬的“成功 / 失败”。
- 删除工具不会误删关键文件。
- 编辑功能不会污染最终下载源码，不会把编辑脚本固化到生成网站中。

## 15. 风险与注意事项

### 15.1 第九阶段依赖前置阶段能力

如果第七阶段尚未落地 Vue 工程工具化修改链路，第九阶段的 `VUE_PROJECT` 可视化修改无法完整实现。这个依赖必须在计划里明确说明。

### 15.2 同源问题是落地的第一前提

如果前端开发环境和预览 iframe 无法做到同源，动态注入脚本方案就无法真正可用。不要在这个问题没解决前先写大段可视化代码。

### 15.3 不要让编辑脚本污染生成结果

编辑模式代码必须是临时注入，不应被持久保存进用户项目，否则下载源码就会夹带平台编辑逻辑。

### 15.4 不要把“轻量可视化修改”做成“半吊子低代码”

第九阶段目标很明确：帮助用户更准确地局部修改。不要为了追求看起来更炫而引入拖拽面板、属性系统、DSL 编辑树等重型内容。

### 15.5 图片与文件上传不是第九阶段主链路

虽然扩展方向里提到了多媒体上传，但第九阶段主交付应先聚焦文本、样式、图片 URL 替换等基础能力，避免范围膨胀。

## 16. 最后结论

如果说前几个阶段让平台学会了“生成”，那第九阶段让平台开始学会“精准修改”。

它的关键不在于把平台做成完整低代码编辑器，而在于用最低成本补上一个非常高价值的能力：

**用户能明确告诉 AI：我要改的是这里。**

一旦这一步完成，整个平台的修改体验会明显提升：

- 修改命中率更高
- 用户心智负担更低
- 误改范围更小
- Vue 工程模式不再只能靠整项目重写

第九阶段真正建立起来的，不只是一个“网页点选功能”，而是一套从视觉选区到代码局部修改的完整闭环。
