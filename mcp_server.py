#!/usr/bin/env python3
"""
AWS Tools MCP Server
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import Resource, TextResourceContents

app = Server("aws-tools")

@app.list_resources()
async def list_resources() -> list[Resource]:
    """列出可用的 AWS 资源"""
    return [
        Resource(
            uri="aws://ec2/config",
            name="EC2 Configuration",
            description="EC2 实例配置信息"
        ),
        Resource(
            uri="aws://regions",
            name="AWS Regions",
            description="AWS 区域列表"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str:
    """读取指定的资源"""
    if uri == "aws://ec2/config":
        config = {
            "default_region": "us-east-1",
            "max_workers": 10,
            "timeout": 30
        }
        return TextResourceContents(
            uri=uri,
            text=json.dumps(config, indent=2)
        )
    
    elif uri == "aws://regions":
        regions = [
            "us-east-1", "us-west-2", "eu-west-1", 
            "ap-southeast-1", "ap-northeast-1"
        ]
        return TextResourceContents(
            uri=uri,
            text=json.dumps(regions, indent=2)
        )
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

if __name__ == "__main__":
    asyncio.run(app.run())