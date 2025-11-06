# 羽毛球计分系统 (badminton-count)

一个开箱即用的羽毛球比赛记录与统计系统，包含：

- ✅ FastAPI + SQLite 的后端 API（内置管理员、4 个测试账号以及 5 场样例比赛）
- ✅ 移动端优先的纯静态前端页面（无需构建，可直接放到 Nginx 静态目录）
- ✅ Excel 导出、胜率排行榜、个人统计、日历标记、权限控制等功能
- ✅ 完整部署指南与测试脚本

---

## 目录结构总览

```
badminton-count/
├── backend/
│   ├── app/
│   │   ├── auth/                # 登录与 Token 逻辑
│   │   ├── exports/             # Excel 导出服务
│   │   ├── matches/             # 比赛录入与查询
│   │   ├── stats/               # 胜率、统计分析
│   │   ├── users/               # 用户管理
│   │   ├── config.py            # 环境配置
│   │   ├── db.py                # 数据库会话管理
│   │   ├── main.py              # FastAPI 入口
│   │   ├── models.py            # SQLAlchemy 模型
│   │   └── seed.py              # 初始数据（账号 & 比赛）
│   ├── requirements.txt         # 后端依赖
│   └── tests/                   # Pytest 自动化测试
├── frontend/
│   ├── index.html               # 前端入口页面
│   ├── styles.css               # 样式
│   └── app.js                   # 业务逻辑（调用后端 API）
├── deployment/
│   └── nginx.conf               # 示例 Nginx 配置
└── README.md                    # 本说明文件
```

---

## 一、快速开始

### 1. 后端准备

> **环境要求**：Python 3.11+，无需安装数据库，项目默认使用 SQLite。

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

首次启动会自动在 `backend/badminton.db` 中写入：

- 管理员账号 `admin`（同时拥有 root 权限）
- 4 个测试选手账号：`alice`、`bob`、`carol`、`dave`
- 5 条涵盖单打、双打、1v2 的样例比赛数据

**默认密码**：所有测试账号密码均为 `password123`，管理员密码为 `admin123`。

### 2. 前端准备

前端是纯静态页面，不需要打包编译，直接将整个 `frontend/` 目录拷贝到任意静态服务器即可。开发阶段可直接用浏览器打开 `frontend/index.html`，或者用 Nginx/VSCode Live Server 等静态服务托管。

前端会默认请求同源下的 `/api` 路径，如果后端运行在其他主机，请参考下方部署章节中的反向代理示例。

### 3. 立即体验

1. 访问 `http://localhost:8000` 时，FastAPI 会返回 JSON 提示。前端需要单独打开 `frontend/index.html`。
2. 登录页面输入管理员账号 `admin` / `admin123` 即可进入系统。
3. 体验以下功能：
   - 切换「比赛」标签页查看样例数据、过滤“仅看我参与”。
   - 点击某场比赛卡片查看详细数据。
   - 若拥有录入权限（管理员或选手 Alice/Bob），可点击右上角「新增比赛」进行录入。
   - 在「选手」标签页查看胜率排行榜、单击选手查看详细统计与打球日历。
   - 「设置」标签页可导出 Excel、查看个人信息；管理员可创建新用户，root 用户拥有导出全部比赛的按钮。

---

## 二、运行测试

项目内置了一套端到端测试用例，覆盖登录、比赛列表、录入比赛、排行榜以及导出接口。

```bash
cd backend
pytest
```

测试会自动使用临时数据库文件，运行结束后会清理数据。

---

## 三、部署说明

### 1. 生产环境推荐

- 使用 `uvicorn` 或 `gunicorn` + `uvicorn.workers.UvicornWorker` 启动 FastAPI：

  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

- 将 `frontend/` 目录复制到服务器的静态目录，例如 `/var/www/badminton-count/frontend`。
- 使用 Nginx 作为前端与后端之间的反向代理。

### 2. 示例 Nginx 配置

`deployment/nginx.conf` 提供了一个可直接套用的配置片段：

```nginx
server {
    listen 80;
    server_name _;

    root /var/www/badminton-count/frontend;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        expires 30d;
    }
}
```

根据实际部署情况，将 `proxy_pass` 中的地址改成 FastAPI 服务所在主机/端口即可。

### 3. 常见问题

| 问题 | 解决方案 |
| ---- | -------- |
| 前端提示“登录已过期” | 检查浏览器是否能访问 `/api/health`，确认反向代理是否正确指向后端。 |
| Excel 导出乱码 | Excel 文件采用 UTF-8 编码，使用新版 Office/金山文档可直接打开。 |
| 想清空数据 | 删除 `backend/badminton.db` 文件后重新启动服务即可重新生成初始数据。 |

---

## 四、API 概览

| 路径 | 方法 | 权限 | 说明 |
| ---- | ---- | ---- | ---- |
| `/api/auth/token` | POST | 匿名 | 密码登录，返回 JWT Token |
| `/api/users/me` | GET | 登录 | 获取当前用户信息 |
| `/api/users/` | GET | 登录 | 获取所有注册用户列表 |
| `/api/users/` | POST | 管理员 | 新增用户（可配置录入权限、管理员身份） |
| `/api/matches/` | GET | 登录 | 获取比赛列表，可加 `only_mine=true` 查询本人参与的比赛 |
| `/api/matches/` | POST | 具备录入权限 | 录入新的比赛成绩 |
| `/api/stats/rankings` | GET | 登录 | 胜率排行榜 |
| `/api/stats/players/{id}` | GET | 登录 | 某位选手的详细统计 |
| `/api/exports/me/*` | GET | 登录 | 导出个人比赛/统计 Excel |
| `/api/exports/players/{id}/*` | GET | 管理员 | 为指定选手导出比赛或统计 |
| `/api/exports/all` | GET | root | 导出全部比赛记录 |

更多字段示例可在 `backend/tests/test_api.py` 中查看。

---

## 五、示例账号 & 权限一览

| 用户名 | 密码 | 角色 | 说明 |
| ------ | ---- | ---- | ---- |
| `admin` | `admin123` | root + 管理员 + 录入权限 | 可管理用户、导出所有比赛 |
| `alice` | `password123` | 普通用户 + 录入权限 | 有比赛录入权限 |
| `bob` | `password123` | 普通用户 + 录入权限 | 有比赛录入权限 |
| `carol` | `password123` | 普通用户 | 仅查看数据 |
| `dave` | `password123` | 普通用户 | 仅查看数据 |

登录后可以使用设置页中的「新增用户」为同事添加账号，并勾选“允许录入比赛”来赋予录入权限。

---

## 六、更多提示

- 修改默认密码：登录后可在数据库中手动更新，或通过管理员更新用户密码（`PATCH /api/users/{id}`）。
- Excel 导出依赖 `openpyxl`，若部署环境较精简，请提前确认依赖已安装。
- 若希望自定义 Token 有效期或数据库位置，可通过设置环境变量：
  - `BADMINTON_SECRET_KEY`
  - `BADMINTON_ACCESS_TOKEN_EXPIRE`（单位：分钟）
  - `BADMINTON_DATABASE_URL`

祝使用愉快！
