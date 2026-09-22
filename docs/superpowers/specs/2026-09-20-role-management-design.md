# 客户问题工单系统 — 角色管理设计（Phase 1）

**日期：** 2026-09-20  
**状态：** 待用户审阅  
**范围：** 仅角色 / 权限 / 用户赋权；完整工单闭环见「后续阶段」

---

## 1. 背景与分期

### 1.1 产品目标（完整版，后续实现）

为企业提供客户问题登记、工单分派、处理、升级、回访和关闭能力，形成完整闭环。

| 角色 | 职责（产品） |
|------|----------------|
| 管理员 | 管理客户、分类、优先级和工单规则 |
| 客服人员 | 创建工单、补充信息和跟进客户 |
| 技术人员 | 处理技术问题和更新解决方案 |
| 客户 | 查看问题进度并补充信息 |

完整功能（客户管理、工单创建/分派/状态/处理、SLA、关闭回访及核心业务规则）已记录在需求文档中，**不在本 Phase 实现**，但权限码在本 Phase **预置**，避免下期大改模型。

### 1.2 本 Phase 目标（今天）

1. 用 OpenSpec 管理变更（`role-management`）。
2. 在 `super-campus/server/` 建立 FastAPI + MySQL 后端。
3. 实现经典 RBAC：角色 CRUD、权限勾选、用户分配角色。
4. 自建 JWT 登录；Vite 本地代理指向本后端。
5. 前端角色管理页 + 用户赋权页；种子四类角色与账号可演示。

### 1.3 已确认决策

| 项 | 选择 |
|----|------|
| 后端位置 | `super-campus/server/` |
| 框架 | FastAPI |
| 认证 | 自建登录 + JWT（`Authorization` 头，兼容现有前端写法） |
| 数据库 | MySQL（需建库，建议库名 `ticket_support`） |
| 权限模型 | 经典 RBAC（用户→角色→权限码） |
| 交付 | 后端 API + 前端页面 + 种子数据 |
| 403 | `msg` 中文，如「当前没有权限执行此操作」 |

---

## 2. 架构

```
super-campus/
├── openspec/                      # OpenSpec 根
│   └── changes/role-management/   # 本变更
├── server/                        # FastAPI
│   ├── app/
│   │   ├── api/                   # auth, roles, users, permissions
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── core/                  # config, security, deps
│   │   └── main.py
│   ├── scripts/                   # 建库、迁移、seed
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── CONTRACT.md
├── src/api/…                      # 前端 API 封装
├── src/views/system/…             # 角色 / 用户赋权页
├── vite.config.js                 # /api → http://127.0.0.1:8000（devLocal）
└── docs/superpowers/specs/        # 本文档
```

**运行时：** 前端 `:90` → Vite 代理 `/api` → FastAPI `:8000` → MySQL。  
**响应格式：** `{ code: 200|4xx, data, msg }`，对齐现有前端约定。

---

## 3. 数据模型

### 3.1 表

| 表 | 字段要点 |
|----|----------|
| `users` | id, username, password_hash, display_name, status, created_at |
| `roles` | id, code, name, description, is_system, created_at |
| `permissions` | id, code, name, module, description |
| `user_roles` | user_id, role_id（联合唯一） |
| `role_permissions` | role_id, permission_id（联合唯一） |

### 3.2 预置权限

| module | code |
|--------|------|
| system | `role:read`, `role:write`, `user:read`, `user:assign_role` |
| ticket | `ticket:create`, `ticket:assign`, `ticket:handle`, `ticket:escalate`, `ticket:followup`, `ticket:close`, `ticket:view_own`, `ticket:view_all` |
| meta | `customer:manage`, `category:manage`, `priority:manage`, `rule:manage` |

### 3.3 系统角色（`is_system=true`，可改权限不可删）

| code | 默认权限 |
|------|----------|
| `admin` | 全部 |
| `cs` | 建单、跟进、分派、回访、`ticket:view_all` 等客服向权限 |
| `tech` | 处理、升级、方案相关；查看分派相关（实现期与 `ticket:handle` / `ticket:escalate` 对齐） |
| `customer` | `ticket:view_own` 及后续「补充信息」所需码 |

### 3.4 种子账号

密码统一：`Admin@123`（仅本地演示）

| username | 角色 |
|----------|------|
| `admin` | admin |
| `cs01` | cs |
| `tech01` | tech |
| `customer01` | customer |

---

## 4. API

**前缀：** `/api`  
**鉴权：** JWT；`Authorization` 支持裸 token 或 `Bearer <token>`。

| Method | Path | 权限 | 说明 |
|--------|------|------|------|
| POST | `/api/auth/login` | 公开 | → token + 用户摘要 |
| GET | `/api/auth/me` | 登录 | 角色 + 权限码列表 |
| GET | `/api/permissions` | `role:read` | 按 module 分组 |
| GET | `/api/roles` | `role:read` | 分页列表 |
| GET | `/api/roles/{id}` | `role:read` | 含权限 id 列表 |
| POST | `/api/roles` | `role:write` | 新建 |
| PUT | `/api/roles/{id}` | `role:write` | 更新含权限 |
| DELETE | `/api/roles/{id}` | `role:write` | 系统角色拒绝 |
| GET | `/api/users` | `user:read` | 含角色 |
| PUT | `/api/users/{id}/roles` | `user:assign_role` | 分配角色 |

**依赖：** `require_permissions("role:write")`；权限以 DB 为准，`/auth/me` 实时查询。

### 4.1 错误约定

| code | 场景 | msg |
|------|------|-----|
| 401 | 未登录 / token 无效 | `请先登录` |
| 403 | 缺权限 | `当前没有权限执行此操作`（可附简短说明） |
| 400 | 参数错误、删系统角色等 | 具体中文原因 |
| 404 | 资源不存在 | 如 `角色不存在` |
| 200 | 成功 | `ok` 或业务文案 |

---

## 5. 前端与代理

- **代理：** `.env.devLocal` 配置本地后端；devLocal 下 `/api` 指向 `http://127.0.0.1:8000`。
- **API 模块：** `src/api/role/`、`src/api/user/`、登录对接 `/api/auth/login`。
- **页面：**
  1. 角色列表（`ele-page` + `ele-pro-table`）
  2. 新建/编辑抽屉（基本信息 + 按 module 权限勾选）
  3. 用户列表 + 分配角色
- **路由：** 静态 `/system/role`、`/system/user-role`（本阶段不做远程菜单动态下发）。
- **交互：** 403 用 `ElMessage.error(msg)`；按钮按 `/auth/me` 权限码显隐。

遵循现有 `CONTRACT.md`（axios 封装、禁止 views 裸调、`code === 200` 才 resolve）。

---

## 6. OpenSpec

1. `openspec init`（若不存在）。
2. Change id：`role-management`。
3. 产物：`proposal`、`design`、`specs`（auth / rbac）、`tasks`。
4. 新增 `server/CONTRACT.md`。

---

## 7. 验证

- **后端 pytest：** 登录成功、无权限 403 中文、系统角色不可删、赋权后权限变化。
- **前端手动：** 四类种子账号登录；角色 CRUD；按钮显隐与 403 提示。
- **联调：** `uvicorn` + `npm run dev`，代理日志命中本地 8000。

---

## 8. 明确不做（本 Phase）

- 客户管理、工单创建/分派/处理/SLA/关闭回访及全部工单业务规则。
- 对接远程 `uber/campus/usercenter`。
- 动态菜单下发、线上部署包（可演示以本地联调为准；完整演示包随后续工单 Phase）。

---

## 9. 后续阶段索引（完整 PRD）

评估维度备忘：UI/交互、功能闭环、需求理解、业务规则合理性；技术栈与库已选定本栈；演示优先本地可跑，后续再考虑静态包或线上。

| 能力 | 要点 |
|------|------|
| 客户管理 | CRUD；名称/联系人/电话/邮箱/行业；历史工单；按名称/联系人/状态搜索 |
| 工单创建 | 标题/描述/分类/优先级；关联客户/产品/订单/服务；附件；期望完成时间 |
| 分派 | 指定处理人/组；重新分派；协作者；待处理量；操作日志 |
| 状态 | 待分派、待处理、处理中、等待客户、已解决、已关闭、已重新打开；变更时间与负责人 |
| 处理 | 处理记录/内部备注；方案附件；预计/实际解决时间；解决结果 |
| SLA | 按优先级时限；临近提醒；超时标记；升级 |
| 关闭回访 | 客户确认→关闭；不认可→重开；评价/回访 |
| 规则 | 有处理人才能处理中；已关闭不可直接改须重开；等待客户不计入内部处理时间；已解决超时未反馈可自动关闭；仅管理员或当前处理人改状态；状态变更必留痕 |

这些在独立 OpenSpec change（如 `ticket-lifecycle`）中实现，继续复用本 Phase 的 RBAC 与四类角色。
