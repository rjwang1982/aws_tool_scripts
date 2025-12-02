"""
author: RJ.Wang
Date: 2024-03-14
Description: 获取 AWS EKS 集群相关信息
"""

import boto3
import logging
from botocore.exceptions import ClientError
from typing import Dict, List, Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EKSClusterInfo:
    def __init__(self, region: str = None):
        """
        初始化 EKS 客户端
        :param region: AWS 区域，如果不指定则使用默认区域
        """
        self.eks_client = boto3.client('eks', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)

    def get_all_clusters(self) -> List[str]:
        """
        获取所有 EKS 集群名称
        :return: 集群名称列表
        """
        try:
            response = self.eks_client.list_clusters()
            clusters = response['clusters']
            logger.info(f"找到 {len(clusters)} 个 EKS 集群")
            return clusters
        except ClientError as e:
            logger.error(f"获取集群列表失败: {e}")
            return []

    def get_cluster_details(self, cluster_name: str) -> Dict[str, Any]:
        """
        获取指定集群的详细信息
        :param cluster_name: 集群名称
        :return: 集群详细信息
        """
        try:
            response = self.eks_client.describe_cluster(name=cluster_name)
            cluster = response['cluster']
            
            # 提取关键信息
            cluster_info = {
                '集群名称': cluster['name'],
                '状态': cluster['status'],
                'Kubernetes版本': cluster['version'],
                '平台版本': cluster['platformVersion'],
                'API地址': cluster['endpoint'],
                'VPC配置': {
                    'VPC_ID': cluster['resourcesVpcConfig']['vpcId'],
                    '子网IDs': cluster['resourcesVpcConfig']['subnetIds'],
                    '安全组IDs': cluster['resourcesVpcConfig']['securityGroupIds'],
                    '公网访问': cluster['resourcesVpcConfig']['endpointPublicAccess'],
                    '私网访问': cluster['resourcesVpcConfig']['endpointPrivateAccess']
                }
            }
            
            return cluster_info
        except ClientError as e:
            logger.error(f"获取集群 {cluster_name} 详细信息失败: {e}")
            return {}

    def get_nodegroups(self, cluster_name: str) -> Dict[str, Any]:
        """
        获取集群的节点组信息
        :param cluster_name: 集群名称
        :return: 节点组信息
        """
        try:
            # 获取节点组列表
            nodegroups = self.eks_client.list_nodegroups(clusterName=cluster_name)['nodegroups']
            nodegroup_details = {}

            for ng_name in nodegroups:
                ng_info = self.eks_client.describe_nodegroup(
                    clusterName=cluster_name,
                    nodegroupName=ng_name
                )['nodegroup']
                
                nodegroup_details[ng_name] = {
                    '状态': ng_info['status'],
                    '实例类型': ng_info['instanceTypes'],
                    '期望节点数': ng_info['scalingConfig']['desiredSize'],
                    '最小节点数': ng_info['scalingConfig']['minSize'],
                    '最大节点数': ng_info['scalingConfig']['maxSize'],
                    'AMI类型': ng_info['amiType'],
                    '容量类型': ng_info.get('capacityType', 'ON_DEMAND')
                }

            return nodegroup_details
        except ClientError as e:
            logger.error(f"获取集群 {cluster_name} 节点组信息失败: {e}")
            return {}

    def get_cluster_addons(self, cluster_name: str) -> Dict[str, Any]:
        """
        获取集群插件信息
        :param cluster_name: 集群名称
        :return: 插件信息
        """
        try:
            addons = self.eks_client.list_addons(clusterName=cluster_name)['addons']
            addon_details = {}

            for addon_name in addons:
                addon_info = self.eks_client.describe_addon(
                    clusterName=cluster_name,
                    addonName=addon_name
                )['addon']
                
                addon_details[addon_name] = {
                    '状态': addon_info['status'],
                    '版本': addon_info['addonVersion']
                }

            return addon_details
        except ClientError as e:
            logger.error(f"获取集群 {cluster_name} 插件信息失败: {e}")
            return {}

def main():
    """
    主函数
    """
    try:
        # 创建 EKS 信息获取器实例
        eks_info = EKSClusterInfo()
        
        # 获取所有集群
        clusters = eks_info.get_all_clusters()
        
        if not clusters:
            logger.info("未找到 EKS 集群")
            return

        # 遍历每个集群并获取详细信息
        for cluster_name in clusters:
            logger.info(f"\n{'='*50}")
            logger.info(f"集群: {cluster_name} 的详细信息")
            logger.info('='*50)

            # 获取集群详细信息
            cluster_details = eks_info.get_cluster_details(cluster_name)
            logger.info("\n集群基本信息:")
            for key, value in cluster_details.items():
                logger.info(f"{key}: {value}")

            # 获取节点组信息
            nodegroups = eks_info.get_nodegroups(cluster_name)
            logger.info("\n节点组信息:")
            for ng_name, ng_info in nodegroups.items():
                logger.info(f"\n节点组: {ng_name}")
                for key, value in ng_info.items():
                    logger.info(f"{key}: {value}")

            # 获取插件信息
            addons = eks_info.get_cluster_addons(cluster_name)
            logger.info("\n插件信息:")
            for addon_name, addon_info in addons.items():
                logger.info(f"\n插件: {addon_name}")
                for key, value in addon_info.items():
                    logger.info(f"{key}: {value}")

    except Exception as e:
        logger.error(f"程序执行出错: {e}")

if __name__ == "__main__":
    main()
