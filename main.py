import os
import importlib
import inspect
import sys
from mcp.server.fastmcp import FastMCP
# 引入 logging 模块，用来“静音”
import logging 

# 初始化 MCP Server
mcp = FastMCP("My Assistant Server")

logging.getLogger('mcp').setLevel(logging.CRITICAL)

def load_tools_dynamic():
    """
    动态扫描 tools 文件夹下的所有 .py 文件
    """
    tools_dir = os.path.join(os.path.dirname(__file__), "tools")
    
    if not os.path.exists(tools_dir):
        # ⚠️ 外部日志仍需保留，但要用 file=sys.stderr 输出
        print(f"⚠️ Warning: {tools_dir} directory not found.", file=sys.stderr)
        return

    for filename in os.listdir(tools_dir):
        if filename.endswith(".py") and not filename.startswith("__"):
            module_name = filename[:-3]
            try:
                # 确保当前目录在 sys.path 中，以便导入 tools.xxx
                if os.path.dirname(__file__) not in sys.path:
                    sys.path.append(os.path.dirname(__file__))
                    
                module = importlib.import_module(f"tools.{module_name}")
                
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if func.__module__ == module.__name__ and not name.startswith("_"):
                        mcp.tool()(func)
            except Exception as e:
                print(f"  ❌ Error loading {filename}: {e}", file=sys.stderr)

# 执行加载
load_tools_dynamic()

if __name__ == "__main__":
    # 🟢 运行 Stdio 模式
    # 进程会挂起，等待来自 stdin 的指令。
    mcp.run(transport="stdio")