"""
author: RJ.Wang
Date: 2025-03-13
email: wangrenjun@gmail.com
Description: A Python tool for subnetting a given CIDR and number of subnets, outputting relevant details like CIDR, IP count, gateway, and broadcast address.
"""
import ipaddress
import argparse
import sys

def subnet_division(cidr, subnets):
    # 将 CIDR 转换为网络对象
    network = ipaddress.IPv4Network(cidr, strict=False)

    # 计算最大可以划分的子网数
    max_subnets = 2 ** (32 - network.prefixlen)

    # 检查请求的子网数是否超过了最大子网数
    if subnets > max_subnets:
        raise ValueError(f"子网数量需求太大。最多可划分 {max_subnets} 个子网。")
    
    # 检查子网数量是否是 2 的幂
    if (subnets & (subnets - 1)) != 0:
        raise ValueError("子网数量必须是 2 的幂（例如 1, 2, 4, 8, 16 等）。")

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
def main():
    # 设置命令行参数解析
    parser = argparse.ArgumentParser(description="根据 CIDR 和子网数量划分子网")
    parser.add_argument("cidr", help="CIDR 地址 (例如：192.168.123.0/24)")
    parser.add_argument("subnets", type=int, help="需要划分的子网数量")
    
    # 检查是否需要显示帮助信息
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)
    
    # 解析命令行参数
    args = parser.parse_args()
    
    try:
        # 调用 subnet_division 函数
        subnet_details = subnet_division(args.cidr, args.subnets)

        # 打印输出
        for detail in subnet_details:
            print(f"子网 {detail['subnet_index']}: {detail['subnet_cidr']}")
            print(f"  包含 IP 数量: {detail['ip_count']}")
            print(f"  网络地址: {detail['network_address']}")
            print(f"  默认网关: {detail['gateway_address']}")
            print(f"  广播地址: {detail['broadcast_address']}")
            print()
    
    except ValueError as e:
        # 输出错误信息
        print(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()