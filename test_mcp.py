#!/usr/bin/env python3
"""测试 MCP 服务器"""

import subprocess
import json

def list_mcp_servers():
    """列出当前配置的 MCP 服务器"""
    
    print("当前配置的 MCP 服务器:")
    print("=" * 40)
    
    # 从 VSCode 配置读取
    try:
        with open('.vscode/settings.json', 'r') as f:
            vscode_config = json.load(f)
            servers = vscode_config.get('mcp.servers', {})
            
        for name, config in servers.items():
            print(f"服务器名称: {name}")
            print(f"命令: {config['command']} {' '.join(config['args'])}")
            print(f"工作目录: {config['cwd']}")
            
            # 测试服务器是否可运行
            try:
                result = subprocess.run([config['command'], '--version'], 
                                      capture_output=True, text=True, timeout=5)
                print(f"状态: ✅ Python 可用")
            except:
                print(f"状态: ❌ 无法运行")
            
            print("-" * 30)
            
    except FileNotFoundError:
        print("未找到 VSCode MCP 配置文件")
    
    # 从独立配置读取
    try:
        with open('mcp_config.json', 'r') as f:
            mcp_config = json.load(f)
            servers = mcp_config.get('mcpServers', {})
            
        print("\n独立 MCP 配置:")
        for name, config in servers.items():
            print(f"- {name}: {config['command']} {' '.join(config['args'])}")
            
    except FileNotFoundError:
        print("未找到独立 MCP 配置文件")

if __name__ == "__main__":
    list_mcp_servers()