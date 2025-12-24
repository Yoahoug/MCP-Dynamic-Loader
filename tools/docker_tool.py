import docker
import json
import ast
import os
import io
import tarfile


# 初始化 Docker 客户端
# 使用 _ 开头变量，防止被 main.py 误扫描
try:
    _client = docker.from_env()
except Exception as e:
    _client = None

# ================= 辅助函数 =================

def _check_client() -> str:
    if not _client:
        return "❌ Docker 服务未连接，请检查是否挂载了 /var/run/docker.sock"
    return ""

# ================= 容器生命周期管理 =================

def docker_list_containers(all: bool = True) -> str:
    """
    列出所有容器。
    Args:
        all: 是否显示已停止的容器 (默认 True)。
    """
    err = _check_client()
    if err: return err

    try:
        containers = _client.containers.list(all=all)
        if not containers:
            return "📭 暂无容器。"
        
        result = f"📦 **容器列表 ({len(containers)})**:\n"
        for c in containers:
            status_icon = "🟢" if c.status == 'running' else "🔴"
            ports = ", ".join([f"{k}->{v[0]['HostPort']}" for k, v in c.ports.items() if v]) if c.ports else "-"
            # 简化输出，避免刷屏
            result += f"{status_icon} **{c.name}**\n   ID: {c.short_id} | Stat: {c.status} | img: {c.image.tags[0] if c.image.tags else 'none'}\n"
        return result
    except Exception as e:
        return f"❌ 查询失败: {str(e)}"

def docker_container_action(container_name: str, action: str) -> str:
    """
    对容器执行操作：启动、停止、重启、删除。
    
    Args:
        container_name: 容器名称或 ID。
        action: 可选值 'start', 'stop', 'restart', 'remove' (删除)。
    """
    err = _check_client()
    if err: return err

    try:
        container = _client.containers.get(container_name)
        
        if action == "start":
            container.start()
            return f"▶️ 容器 `{container.name}` 已启动。"
        elif action == "stop":
            container.stop()
            return f"ww⏹️ 容器 `{container.name}` 已停止。"
        elif action == "restart":
            container.restart()
            return f"🔄 容器 `{container.name}` 已重启。"
        elif action == "remove":
            # 删除前先尝试停止
            try: container.stop() 
            except: pass
            container.remove()
            return f"🗑️ 容器 `{container.name}` 已删除。"
        else:
            return f"❌ 未知操作: {action}"
    except Exception as e:
        return f"❌ 操作失败: {str(e)}"

def docker_run_container(image: str, name: str = None, ports: str = None, command: str = None) -> str:
    """
    运行一个新的容器 (docker run)。
    
    Args:
        image: 镜像名称 (如 'nginx:latest')。
        name: (可选) 容器名称。
        ports: (可选) 端口映射字符串，格式为字典字符串。例如 '{"80/tcp": 8080}' 表示将容器80映射到宿主机8080。
        command: (可选) 启动命令。
    """
    err = _check_client()
    if err: return err

    try:
        # 处理端口映射参数
        ports_dict = {}
        if ports:
            try:
                # 尝试安全解析字符串为字典
                ports_dict = ast.literal_eval(ports)
            except:
                return "❌ 端口格式错误，请使用 JSON 格式，例如: {'80/tcp': 8080}"

        container = _client.containers.run(
            image,
            name=name,
            ports=ports_dict,
            command=command,
            detach=True # 后台运行
        )
        return f"✅ 容器创建并启动成功！\nName: {container.name}\nID: {container.short_id}"
    except Exception as e:
        return f"❌ 创建容器失败: {str(e)}"

def docker_inspect_container(container_name: str) -> str:
    """
    查看容器的详细信息（IP、挂载、环境变量等）。
    """
    err = _check_client()
    if err: return err

    try:
        c = _client.containers.get(container_name)
        # 提取关键信息
        info = {
            "ID": c.short_id,
            "Image": c.attrs['Config']['Image'],
            "Status": c.status,
            "Created": c.attrs['Created'],
            "IP": c.attrs['NetworkSettings']['IPAddress'],
            "MacAddress": c.attrs['NetworkSettings']['MacAddress'],
            "Mounts": [m['Source'] + ":" + m['Destination'] for m in c.attrs['Mounts']],
            "Env": c.attrs['Config']['Env'][:5] # 只显示前5个环境变量防止刷屏
        }
        return f"🔍 **容器详情 ({c.name})**:\n```json\n{json.dumps(info, indent=2)}\n```"
    except Exception as e:
        return f"❌ 获取详情失败: {str(e)}"

def docker_get_logs(container_name: str, lines: int = 50) -> str:
    """获取容器日志 (后 N 行)"""
    err = _check_client()
    if err: return err
    try:
        c = _client.containers.get(container_name)
        logs = c.logs(tail=lines).decode('utf-8', errors='ignore')
        return f"📜 **{c.name} Logs**:\n```\n{logs}\n```"
    except Exception as e:
        return f"❌ Log Error: {str(e)}"

# ================= 镜像管理 =================

def docker_list_images() -> str:
    """列出本地镜像"""
    err = _check_client()
    if err: return err
    try:
        images = _client.images.list()
        if not images: return "📭 无本地镜像。"
        res = "💿 **镜像列表**:\n"
        for img in images:
            tags = img.tags[0] if img.tags else '<none>'
            size = round(img.attrs['Size'] / (1024*1024), 1)
            res += f"- {tags} ({size}MB)\n"
        return res
    except Exception as e: return f"❌ Error: {str(e)}"

def docker_pull_image(image_name: str) -> str:
    """拉取/下载镜像"""
    err = _check_client()
    if err: return err
    try:
        img = _client.images.pull(image_name)
        return f"✅ 拉取成功: {img.tags[0]}"
    except Exception as e: return f"❌ 拉取失败: {str(e)}"

def docker_delete_image(image_name: str, force: bool = False) -> str:
    """删除镜像"""
    err = _check_client()
    if err: return err
    try:
        _client.images.remove(image_name, force=force)
        return f"🗑️ 镜像已删除: {image_name}"
    except Exception as e: return f"❌ 删除失败: {str(e)}"

def docker_reset_image(image_name: str) -> str:
    """
    重置镜像（强制更新到最新版并清理旧缓存）。
    """
    err = _check_client()
    if err: return err
    try:
        _client.images.pull(image_name)
        try: _client.images.prune(filters={'dangling': True})
        except: pass
        return f"🔄 镜像 {image_name} 已重置为最新版。"
    except Exception as e: return f"❌ 重置失败: {str(e)}"

def docker_copy_from_container(container_name: str, src_path: str) -> str:
    """
    从容器内部复制文件到 AstrBot 本地存储。
    用于提取代码沙箱生成的结果（图片、文档等）。
    
    Args:
        container_name: 容器名称或 ID。
        src_path: 容器内的文件绝对路径 (如 /workspace/plot.png)。
    """
    err = _check_client()
    if err: return err

    try:
        container = _client.containers.get(container_name)
        
        # 1. 准备本地接收目录
        # 建议存放在 data 下的临时目录，方便清理
        local_dir = "/AstrBot/data/data_temp"
        if not os.path.exists(local_dir):
            os.makedirs(local_dir, exist_ok=True)
            
        # 2. 从容器获取文件 (Docker API 返回的是 tar 数据流)
        try:
            bits, stat = container.get_archive(src_path)
        except docker.errors.NotFound:
            return f"❌ 容器内未找到文件: {src_path}"

        # 3. 在内存中解压 tar
        file_obj = io.BytesIO()
        for chunk in bits:
            file_obj.write(chunk)
        file_obj.seek(0)
        
        with tarfile.open(fileobj=file_obj) as tar:
            # 提取到本地目录
            tar.extractall(path=local_dir)
            # 获取文件名
            extracted_filename = os.path.basename(src_path)
            local_file_path = os.path.join(local_dir, extracted_filename)
            
        return f"✅ 文件已提取到本地: {local_file_path}"

    except Exception as e:
        return f"❌ 提取文件失败: {str(e)}"

# ================= 容器内执行与依赖管理 (新增) =================

def docker_exec_run(container_name: str, command: str, workdir: str = None) -> str:
    """
    在运行中的容器内执行命令 (相当于 docker exec)。
    
    Args:
        container_name: 容器名称或 ID。
        command: 要执行的 Shell 命令 (如 'ls -la /app', 'cat /etc/os-release')。
        workdir: (可选) 执行命令的工作目录。
    """
    err = _check_client()
    if err: return err

    try:
        container = _client.containers.get(container_name)
        if container.status != 'running':
            return f"❌ 容器 `{container.name}` 未运行，无法执行命令。"
            
        # 执行命令
        exit_code, output = container.exec_run(
            command, 
            workdir=workdir,
            demux=True # 分离 stdout 和 stderr
        )
        
        # 处理输出 (output 是 tuple: (stdout, stderr))
        stdout = output[0].decode('utf-8') if output[0] else ""
        stderr = output[1].decode('utf-8') if output[1] else ""
        
        result = f"💻 **执行结果 (Exit Code: {exit_code})**:\n"
        if stdout:
            result += f"--- Stdout ---\n{stdout}\n"
        if stderr:
            result += f"--- Stderr ---\n{stderr}\n"
            
        if not stdout and not stderr:
            result += "(无输出)"
            
        return result.strip()

    except Exception as e:
        return f"❌ 执行失败: {str(e)}"

def docker_pip_install(container_name: str, packages: str) -> str:
    """
    在指定容器内快速安装 Python 依赖库 (自动使用清华源加速)。
    
    Args:
        container_name: 容器名称。
        packages: 包名列表，用空格分隔 (如 'pandas numpy scipy')。
    """
    err = _check_client()
    if err: return err
    
    # 使用清华源，并增加超时时间，信任主机防止 SSL 报错
    pip_cmd = (
        f"pip install {packages} "
        "-i https://pypi.tuna.tsinghua.edu.cn/simple "
        "--default-timeout=100 "
        "--trusted-host pypi.tuna.tsinghua.edu.cn"
    )
    
    return docker_exec_run(container_name, pip_cmd)