### 1. 安装 uv

如果你还没有安装 `uv`，请先执行以下命令安装：

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. 初始化与启动

在项目根目录下运行以下命令，即可自动同步环境并启动服务：

```bash
# 1. 同步依赖环境 (自动创建虚拟环境并安装依赖)
uv sync

# 2. 运行数据库迁移
uv run python manage.py migrate

# 3. 启动服务器
uv run python manage.py runserver
```
