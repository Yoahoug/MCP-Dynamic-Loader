# MCP 服务自动注册架构使用说明

## 📋 概述

本项目实现了一个基于 FastMCP 的工具自动注册架构。通过简单的约定，您只需编写符合规范的函数，运行 `main.py` 即可自动将函数注册为 MCP 工具。

## 🏗️ 架构说明

### 核心组件

- **main.py**: MCP 服务主入口，负责动态扫描和注册工具
- **tools/**: 工具函数目录，所有需要暴露的工具函数放在此目录下
- **core/**: 核心模块目录（可选），用于放置辅助函数和共享逻辑

### 工作原理

1. 启动时，`main.py` 自动扫描 `tools/` 目录下所有 `.py` 文件
2. 检测每个模块中的公共函数（不以 `_` 开头）
3. 自动将这些函数注册为 MCP 工具
4. 通过 stdio 协议与客户端通信

## 📝 编写工具函数规范

### 1. 文件位置

所有工具函数必须放在 `tools/` 目录下：

```
MCP_server/
├── main.py
├── tools/
│   ├── calculator.py
│   ├── file_operations.py
│   └── web_search.py
└── core/
    └── helpers.py
```

### 2. 函数可见性

**必须是公共函数**（不以下划线开头）：

```python
# ✅ 正确：公共函数，会被自动注册
def search_web(query: str):
    pass

# ❌ 错误：私有函数，不会被注册
def _internal_helper():
    pass
```

### 3. MCP 标准注释格式

每个工具函数必须包含完整的文档字符串，说明功能、参数和返回值：

```python
def function_name(param1: type, param2: type) -> return_type:
    """
    工具功能的简短描述（必需）
    
    更详细的功能说明（可选）
    
    Args:
        param1: 参数1的说明
        param2: 参数2的说明
    
    Returns:
        返回值的说明
        
    Raises:
        可能抛出的异常说明（可选）
    """
    # 实现代码
    pass
```

### 4. 类型注解

**强烈建议**使用类型注解，帮助 MCP 客户端理解参数类型：

```python
from typing import List, Dict, Optional

def process_data(
    text: str,
    options: Optional[Dict[str, str]] = None,
    max_results: int = 10
) -> List[str]:
    """处理文本数据并返回结果列表"""
    pass
```

## 💡 完整示例

### 示例 1: 简单计算器工具

创建 `tools/calculator.py`：

```python
def add(a: float, b: float) -> float:
    """
    计算两个数字的和
    
    Args:
        a: 第一个数字
        b: 第二个数字
    
    Returns:
        两数之和
    """
    return a + b


def multiply(x: float, y: float) -> float:
    """
    计算两个数字的乘积
    
    Args:
        x: 第一个数字
        y: 第二个数字
    
    Returns:
        两数之积
    """
    return x * y


def _validate_input(value):
    """
    私有辅助函数，用于验证输入
    注意：以 _ 开头，不会被注册为工具
    """
    return isinstance(value, (int, float))
```

### 示例 2: 文件操作工具

创建 `tools/file_operations.py`：

```python
import os
from typing import List

def list_files(directory: str, extension: str = "") -> List[str]:
    """
    列出目录中的文件
    
    Args:
        directory: 目录路径
        extension: 文件扩展名过滤（例如: ".txt"），为空则返回所有文件
    
    Returns:
        文件名列表
    
    Raises:
        FileNotFoundError: 当目录不存在时
    """
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")
    
    files = os.listdir(directory)
    
    if extension:
        files = [f for f in files if f.endswith(extension)]
    
    return files


def read_file_content(filepath: str) -> str:
    """
    读取文件内容
    
    Args:
        filepath: 文件路径
    
    Returns:
        文件内容字符串
    
    Raises:
        FileNotFoundError: 当文件不存在时
        PermissionError: 当没有读取权限时
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()
```

### 示例 3: 使用 core 模块的辅助函数

创建 `core/helpers.py`：

```python
"""
核心辅助函数模块
此处的函数不会被自动注册为工具
"""

def format_response(data: dict) -> str:
    """格式化响应数据"""
    return str(data)


def validate_url(url: str) -> bool:
    """验证 URL 格式"""
    return url.startswith(('http://', 'https://'))
```

创建 `tools/web_tools.py`：

```python
from core.helpers import validate_url, format_response

def fetch_url(url: str) -> str:
    """
    获取指定 URL 的内容
    
    Args:
        url: 要访问的 URL 地址
    
    Returns:
        网页内容或错误信息
    """
    if not validate_url(url):
        return "Invalid URL format"
    
    # 实际的网络请求逻辑
    result = {"status": "success", "url": url}
    return format_response(result)
```

## 🚀 运行服务

### 1. 安装依赖

```bash
pip install mcp
```

### 2. 启动服务

```bash
python main.py
```

服务将通过 stdio 模式运行，等待来自客户端的指令。

### 3. 配置 MCP 客户端

在 Claude Desktop 或其他 MCP 客户端的配置文件中添加：

```json
{
  "mcpServers": {
    "my-assistant": {
      "command": "python",
      "args": ["/path/to/your/MCP_server/main.py"]
    }
  }
}
```

## ✅ 最佳实践

### 1. 函数命名

- 使用清晰、描述性的函数名
- 采用 snake_case 命名风格
- 避免使用缩写，除非是通用缩写

```python
# ✅ 好的命名
def search_documents(query: str, max_results: int):
    pass

# ❌ 不好的命名
def srch_doc(q, mr):
    pass
```

### 2. 错误处理

在函数中妥善处理异常：

```python
def safe_divide(a: float, b: float) -> float:
    """
    安全地进行除法运算
    
    Args:
        a: 被除数
        b: 除数
    
    Returns:
        除法结果
    
    Raises:
        ValueError: 当除数为零时
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### 3. 参数验证

在函数开始时验证输入参数：

```python
def process_text(text: str, min_length: int = 1) -> str:
    """
    处理文本内容
    
    Args:
        text: 输入文本
        min_length: 最小文本长度
    
    Returns:
        处理后的文本
    """
    if not isinstance(text, str):
        raise TypeError("text must be a string")
    
    if len(text) < min_length:
        raise ValueError(f"text length must be at least {min_length}")
    
    return text.strip()
```

### 4. 返回值清晰

确保返回值格式一致且易于理解：

```python
from typing import Dict

def analyze_text(text: str) -> Dict[str, int]:
    """
    分析文本统计信息
    
    Args:
        text: 输入文本
    
    Returns:
        包含统计信息的字典，包含以下键：
        - word_count: 单词数量
        - char_count: 字符数量
        - line_count: 行数
    """
    return {
        "word_count": len(text.split()),
        "char_count": len(text),
        "line_count": text.count('\n') + 1
    }
```

## 🔧 目录结构建议

```
MCP_server/
├── README.md                    # 本文档
├── main.py                      # 服务主入口
├── requirements.txt             # 依赖列表
├── tools/                       # 工具函数目录
│   ├── __init__.py
│   ├── calculator.py            # 计算相关工具
│   ├── file_operations.py       # 文件操作工具
│   ├── text_processing.py       # 文本处理工具
│   └── web_tools.py             # 网络相关工具
├── core/                        # 核心模块（私有）
│   ├── __init__.py
│   ├── helpers.py               # 辅助函数
│   └── config.py                # 配置管理
└── tests/                       # 测试文件（可选）
    ├── test_calculator.py
    └── test_file_operations.py
```

## 📋 检查清单

在添加新工具前，确保：

- [ ] 函数放在 `tools/` 目录下
- [ ] 函数名不以 `_` 开头（公共函数）
- [ ] 包含完整的文档字符串（docstring）
- [ ] 添加了类型注解
- [ ] 描述了所有参数和返回值
- [ ] 处理了可能的异常
- [ ] 测试函数正常工作

## 🐛 调试技巧

### 查看已注册的工具

修改 `main.py` 添加调试输出：

```python
def load_tools_dynamic():
    """动态扫描 tools 文件夹下的所有 .py 文件"""
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    
    if not os.path.exists(tools_dir):
        print(f"⚠️ Warning: {tools_dir} directory not found.", file=sys.stderr)
        return

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            try:
                if os.path.dirname(__file__) not in sys.path:
                    sys.path.append(os.path.dirname(__file__))
                    
                module = importlib.import_module(f"tools.{module_name}")
                
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if func.__module__ == module.__name__ and not name.startswith("_"):
                        mcp.tool()(func)
                        # 添加调试输出
                        print(f"✅ Registered tool: {name}", file=sys.stderr)
            except Exception as e:
                print(f"❌ Error loading {filename}: {e}", file=sys.stderr)
```

## 🤝 贡献指南

添加新工具时，请遵循以下步骤：

1. 在 `tools/` 目录创建新的 `.py` 文件
2. 按照规范编写函数和文档
3. 运行服务验证工具是否正确注册
4. 测试工具功能是否正常

**最后更新**: 2025-12-25
[![MCP Badge](https://lobehub.com/badge/mcp/yoahoug-mcp-dynamic-loader)](https://lobehub.com/mcp/yoahoug-mcp-dynamic-loader)
