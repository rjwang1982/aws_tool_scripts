"""
author: RJ.Wang
Date: 2025-03-13
email: wangrenjun@gmail.com
Description: This tool helps users automatically calculate and output detailed information for each subnet based on a given CIDR network address and the required number of subnets. The details include the subnet’s CIDR address, IP address count, network address, gateway address, and broadcast address. Users simply need to enter the CIDR address and subnet number on the web page, and the tool will perform the subnet division and display the results. If the subnet number is not a power of 2 or exceeds the maximum number of subnets that can be divided, the tool will prompt an error message.
"""
from flask import Flask, render_template, request, redirect, url_for
import ipaddress

app = Flask(__name__)

def subnet_division(cidr, subnets):
    """
    该函数接受 CIDR 和子网数量，计算出所有子网的 CIDR、IP 数量、网络地址、网关地址和广播地址。
    
    参数:
    cidr (str): 原始的网络地址，采用 CIDR 格式（如 192.168.123.0/24）
    subnets (int): 需要划分的子网数量
    
    返回:
    list: 包含每个子网详细信息的列表，包括子网 CIDR、IP 数量、网络地址、网关地址和广播地址。
    
    异常:
    ValueError: 如果请求的子网数目超过了可以划分的最大子网数，或子网数目不是 2 的幂次方，抛出此异常。
    """
    # 检查子网数量是否是 2 的幂次方
    if (subnets & (subnets - 1)) != 0:
        raise ValueError("子网数量必须是 2 的幂次方。")

    # 将 CIDR 转换为网络对象
    network = ipaddress.IPv4Network(cidr, strict=False)

    # 计算最大可以划分的子网数
    max_subnets = 2 ** (32 - network.prefixlen)

    # 检查请求的子网数是否超过了最大子网数
    if subnets > max_subnets:
        raise ValueError(f"子网数量需求太大。最多可划分 {max_subnets} 个子网。")

    # 计算每个子网的大小（子网数目）
    new_prefix = network.prefixlen + (subnets.bit_length() - 1)  # 计算新的子网前缀长度
    
    # 划分子网
    subnets_list = list(network.subnets(new_prefix=new_prefix))

    # 输出每个子网的详细信息
    subnet_details = []
    for i, subnet in enumerate(subnets_list, 1):  # 给每个子网加上序号
        subnet_info = {
            'subnet_index': i,
            'subnet_cidr': subnet.with_prefixlen,
            'ip_count': subnet.num_addresses,
            'network_address': subnet.network_address,
            'gateway_address': str(subnet.network_address + 1),
            'broadcast_address': subnet.broadcast_address
        }
        subnet_details.append(subnet_info)
    
    return subnet_details

@app.route("/", methods=["GET", "POST"])
def index():
    """
    主页路由，处理用户输入和展示计算结果。
    用户可以输入 CIDR 和子网数量，提交后进行子网划分计算，结果将展示在新页面中。
    """
    if request.method == "POST":
        cidr = request.form["cidr"]  # 获取用户输入的 CIDR 地址
        subnets = int(request.form["subnets"])  # 获取用户输入的子网数量

        try:
            # 调用子网划分函数进行计算
            subnet_details = subnet_division(cidr, subnets)
            return render_template("result.html", subnet_details=subnet_details)
        except ValueError as e:
            # 如果计算出错（如子网数量过多或不是 2 的幂次方），显示错误信息
            return render_template("index.html", error=str(e))

    # 如果是 GET 请求，返回首页，用户可以输入 CIDR 和子网数量
    return render_template("index.html")

if __name__ == "__main__":
    """
    启动 Flask 应用：
    1. 默认情况下，Flask 运行在 http://127.0.0.1:5000/ 上。
    2. 使用此开发服务器进行测试和调试，适合开发环境，不适合生产环境。
    3. 若在生产环境中运行，请使用 WSGI 服务器（如 Gunicorn）和反向代理服务器（如 Nginx）。
    """
    app.run(debug=True)