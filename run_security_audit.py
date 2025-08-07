#!/usr/bin/env python3
"""
AWS 安全审计工具启动器
自动设置工作目录并运行相关脚本
"""

import os
import sys
from pathlib import Path

def setup_environment():
    """设置工作环境"""
    # 获取脚本所在目录
    script_dir = Path(__file__).parent.absolute()
    
    # 切换到脚本目录
    os.chdir(script_dir)
    
    # 添加到 Python 路径
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    
    print(f"工作目录设置为: {script_dir}")
    return script_dir

def main():
    """主函数"""
    print("AWS 安全审计工具")
    print("=" * 50)
    
    # 设置环境
    work_dir = setup_environment()
    
    # 显示菜单
    print("请选择要执行的操作:")
    print("1. 导出开放的安全组规则（完整版）")
    print("2. 导出开放的安全组规则（简化版）")
    print("3. 查看输出文件列表")
    print("4. 退出")
    
    while True:
        choice = input("\n请输入选项 (1-4): ").strip()
        
        if choice == '1':
            print("\n正在运行完整版安全组导出...")
            try:
                import export_open_security_groups
                export_open_security_groups.main()
            except Exception as e:
                print(f"执行失败: {e}")
        
        elif choice == '2':
            print("\n正在运行简化版安全组导出...")
            try:
                import export_open_sg_simple
                export_open_sg_simple.export_open_security_groups()
            except Exception as e:
                print(f"执行失败: {e}")
        
        elif choice == '3':
            print("\n输出文件列表:")
            try:
                from file_utils import file_manager
                files = file_manager.list_output_files("*.csv")
                if files:
                    for i, file in enumerate(files, 1):
                        print(f"{i}. {os.path.basename(file)}")
                else:
                    print("没有找到输出文件")
            except Exception as e:
                print(f"查看文件失败: {e}")
        
        elif choice == '4':
            print("退出程序")
            break
        
        else:
            print("无效选项，请重新输入")

if __name__ == '__main__':
    main()