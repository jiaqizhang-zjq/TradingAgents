# UV 包管理器使用指南

## 简介

本项目使用 [UV](https://github.com/astral-sh/uv) 作为 Python 包管理器。UV 是一个用 Rust 编写的极速 Python 包管理器，比 pip 快 10-100 倍。

## 安装 UV

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 或者使用 pip
pip install uv
```

## 快速开始

### 1. 创建虚拟环境

```bash
# 使用项目指定的 Python 版本（3.10）
uv venv --python 3.10

# 或者使用系统默认 Python
uv venv
```

### 2. 激活虚拟环境

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. 安装依赖

```bash
# 安装所有依赖（根据 pyproject.toml）
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"

# 安装特定依赖组（UV 支持）
uv pip install --group dev

# 同步依赖（根据 uv.lock）
uv sync
```

### 4. 添加新依赖

```bash
# 添加运行时依赖
uv add pandas numpy

# 添加开发依赖
uv add --dev pytest black

# 添加特定依赖组
uv add --group test pytest-cov
```

### 5. 更新依赖

```bash
# 更新所有依赖
uv lock --upgrade

# 更新特定包
uv lock --upgrade-package pandas

# 同步到虚拟环境
uv sync
```

## 常用命令

### 虚拟环境管理

```bash
# 创建虚拟环境
uv venv

# 指定 Python 版本创建
uv venv --python 3.11

# 使用特定 Python 解释器
uv venv --python /usr/local/bin/python3.10
```

### 依赖管理

```bash
# 安装依赖
uv pip install <package>

# 从 requirements.txt 安装
uv pip install -r requirements.txt

# 生成 requirements.txt
uv pip freeze > requirements.txt

# 锁定依赖
uv lock

# 同步依赖（根据 uv.lock）
uv sync

# 检查依赖冲突
uv pip check
```

### 运行 Python

```bash
# 在虚拟环境中运行
uv run python main.py

# 运行模块
uv run python -m tradingagents

# 运行脚本（自动使用虚拟环境）
uv run main.py
```

### 项目管理

```bash
# 初始化新项目
uv init

# 构建项目
uv build

# 发布到 PyPI
uv publish
```

## 项目配置

### pyproject.toml UV 配置

```toml
[tool.uv]
# UV 包管理器配置
python-preference = "only-system"  # 使用系统 Python
managed = true  # 允许 UV 管理虚拟环境

[tool.uv.pip]
# pip 兼容配置
generate-hashes = false
no-binary = false

[tool.uv.venv]
# 虚拟环境配置
name = ".venv"  # 虚拟环境目录名
prompt = "tradingagents"  # 虚拟环境提示符

# 依赖组配置
[dependency-groups]
dev = [
    "pytest>=7.0.0",
    "black>=23.0.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

### .python-version

项目使用 Python 3.10：

```
3.10
```

## 与 pip 的对比

| 功能 | UV | pip |
|------|-----|-----|
| 安装速度 | ⚡ 极快 | 🐌 较慢 |
| 依赖解析 | 内置 | 需要 pip-tools |
| 虚拟环境 | 内置 | 需要 venv |
| 锁定文件 | uv.lock | requirements.txt |
| 兼容性 | 完全兼容 pip | 标准 |

## 最佳实践

### 1. 使用 uv.lock

`uv.lock` 文件应该提交到版本控制，以确保所有开发者使用相同的依赖版本：

```bash
# 生成锁定文件
uv lock

# 提交到 git
git add uv.lock
git commit -m "Update dependencies"
```

### 2. 依赖分组

使用依赖组来管理不同环境的依赖：

```toml
[dependency-groups]
dev = ["pytest", "black", "mypy"]
test = ["pytest", "pytest-cov"]
docs = ["mkdocs", "mkdocs-material"]
```

安装时：

```bash
uv pip install --group dev
```

### 3. 使用 uv run

使用 `uv run` 自动在虚拟环境中运行命令：

```bash
# 不需要手动激活虚拟环境
uv run python main.py

# 运行测试
uv run pytest

# 运行 black
uv run black .
```

### 4. 迁移现有项目

从 pip/requirements.txt 迁移：

```bash
# 安装 UV
pip install uv

# 创建虚拟环境
uv venv

# 安装现有依赖
uv pip install -r requirements.txt

# 生成 uv.lock
uv lock
```

## 故障排除

### 1. Python 版本不匹配

```bash
# 检查 Python 版本
uv run python --version

# 重新创建虚拟环境
rm -rf .venv
uv venv --python 3.10
```

### 2. 依赖冲突

```bash
# 检查依赖冲突
uv pip check

# 查看依赖树
uv pip tree

# 强制重新锁定
uv lock --upgrade
```

### 3. 缓存问题

```bash
# 清除 UV 缓存
uv cache clean

# 清除特定包的缓存
uv cache clean pandas
```

### 4. 虚拟环境问题

```bash
# 重新创建虚拟环境
rm -rf .venv
uv venv
uv sync
```

## 完整工作流示例

```bash
# 1. 克隆项目
git clone https://github.com/TauricResearch/TradingAgents.git
cd TradingAgents

# 2. 创建虚拟环境
uv venv --python 3.10

# 3. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
# .venv\Scripts\activate  # Windows

# 4. 安装依赖
uv sync

# 5. 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 6. 运行项目
uv run python main.py

# 7. 运行测试
uv run pytest

# 8. 添加新依赖
uv add new-package

# 9. 更新锁定文件
uv lock

# 10. 提交更改
git add pyproject.toml uv.lock
git commit -m "Add new-package dependency"
```

## 参考

- [UV 官方文档](https://docs.astral.sh/uv/)
- [UV GitHub](https://github.com/astral-sh/uv)
- [迁移指南](https://docs.astral.sh/uv/pip/compatibility/)
