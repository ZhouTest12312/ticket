# Web 开发契约

> **适用范围：** `web/` 管理端（Vue 3 + Vite + Element Plus + Ele Admin Plus）。  
> **本文档：** 通用工程结构、请求封装、组件模式与开发约束；**不含**具体需求的页面清单、API 路径表、联调状态。  
> **需求级设计：** 写入 `openspec/changes/{change-id}/design.md`（页面↔API↔后端路径、字段映射、迁移策略等）。

---

## 1. 文档分工

| 文档 | 内容 |
|------|------|
| 根目录 `AGENTS.md` | OpenSpec 变更流程、测试目录 |
| `openspec/changes/{change-id}/specs/` | 业务能力、接口契约、Scenario |
| `openspec/changes/{change-id}/design.md` | 本变更的前端落位、API 模块、路径、与存量差异 |
| **本文档 `CONTRACT.md`** | 工程内长期有效的通用约束 |
| `server/CONTRACT.md` | 后端通用约束；前后端联调时 design.md 对齐两端 |

---

## 2. 技术栈（不可替换）

| 分类 | 选型 |
|------|------|
| 框架 | Vue 3 `<script setup>` |
| 构建 | Vite 5 |
| UI | Element Plus + Ele Admin Plus |
| 状态 | Pinia |
| 路由 | Vue Router 4（菜单多为后端动态下发） |
| HTTP | Axios（`src/utils/request.js` 唯一实例） |
| 样式 | SCSS |

---

## 3. 目录职责

```
src/
├── api/{domain}/index.js   # 按业务域封装接口，禁止在 views 裸调 axios
├── views/                  # 页面，按业务分子目录
├── components/             # 可复用组件
├── utils/request.js        # Axios 实例与拦截器
├── router/                 # 路由与守卫
├── store/                  # Pinia
└── config/setting.js       # API_BASE_URL 等
```

**环境变量：** `.env.*` 中 `VITE_API_URL`（开发默认 `/api`）；本地 dev 端口见 `vite.config.js`（当前 90）。

---

## 4. HTTP 约定

### 4.1 请求实例（`src/utils/request.js`）

- `baseURL` = `API_BASE_URL`
- Header：`Authorization: <token>`
- 部分网关前缀（如 `/sishu/`、`/peiyou/`）有额外 Header，按现有拦截器扩展
- 拦截器处理 401 等协议错误；**不**统一解包 `data`，由各 API 函数判断 `res.data.code`

### 4.2 API 模块写法

```javascript
import request from '@/utils/request';

/**
 * @param {Object} data 查询/提交参数（字段与 change spec / design.md 一致）
 */
export async function pageXxx(data) {
  const res = await request.get('/path/from/design.md', { params: data });
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}

export async function createXxx(data) {
  const res = await request.post('/path/from/design.md', data);
  if (res.data.code === 200) {
    return res.data.data;
  }
  return Promise.reject(new Error(res.data.msg || '请求失败'));
}
```

**规则：**

- 路径、Method、入参/出参结构以 **change 的 `design.md` + `specs`** 为准，不写死在本文档
- 与 uber-campus 后端联调时，Body **直接传 Dto 字段**（不用顶层 `request` 信封，与 `server/CONTRACT.md` 一致）
- 业务错误展示 `res.data.msg`；禁止在页面内重复实现业务规则

### 4.3 职责边界

| 前端允许 | 前端禁止 |
|----------|----------|
| 展示、交互、加载态、展示层格式化（日期等） | 根据业务状态推导按钮/权限（须用后端 `editable`、`*Label` 等） |
| 表单基础校验（必填、格式） | 业务规则计算、数据过滤、状态分支 |
| 将用户输入原样提交后端 | 在 `views` 内散落 `request.post` |

---

## 5. 页面模式

### 5.1 列表页

- 布局：`<ele-page>` + 搜索组件 + `<ele-pro-table>`
- 分页：通过 `:response="{ dataName, countName }"` 与后端分页字段对齐（在 design.md 约定）
- 批量操作：依赖后端返回的可选标识（如 `batchSelectable`），不在前端写业务过滤

### 5.2 表单 / 抽屉

- `ele-drawer` + `el-form` + `useFormData()`
- 新建/编辑字段可编辑性读详情接口返回，不做 `if (status === …)` 业务判断

### 5.3 字典与级联

- 复用 `DictSelect`、`@/api/dictionary`
- 级联清空、依赖关系按 PRD/spec；接口报错直接展示 `msg`

---

## 6. 路由

- 主路由由**后台菜单**注册；`component` 路径对应 `src/views/` 下文件
- 新增页面 path 与菜单配置保持一致；代码内 `router.push` 避免硬编码与菜单不一致的路径
- 静态路由补充见 `src/router/routes.js`

---

## 7. 文件上传（OSS）

- 依赖：`ali-oss`、`crypto-js`（项目已有 upload 工具）
- 流程：`getStsToken` → AES 解密 → 客户端直传 OSS → 业务表单只提交 **HTTPS URL**
- STS/OSS 接口路径在 change `design.md` 与后端 OSS Controller 对齐
- 禁止把 `File`/`Blob` 塞进业务 JSON

---

## 8. 测试

- 禁止根目录 `tests/`
- 前端相关用例跟随变更：`openspec/changes/{change-id}/tests/`（e2e 等按 AGENTS.md）

---

## 9. 提交前检查（通用）

- [ ] 接口封装在 `src/api/{domain}/`，views 无裸调 axios
- [ ] 路径与字段和对应 change 的 `design.md`、`specs` 一致
- [ ] `code === 200` 才 resolve；失败有用户可读提示
- [ ] 无前端业务规则分支；展示字段来自后端
- [ ] 文件字段为 OSS HTTPS URL
- [ ] 未引入与 Vue 栈冲突的 UI/状态库
