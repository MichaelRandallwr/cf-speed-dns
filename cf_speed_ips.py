#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cloudflare 优选 IP：优先读仓库内的 cf_speed_ips.txt，缺失或无效时再请求网络。"""

import os
import traceback
from typing import List, Optional

import requests

try:
    _speed_ip_max = int(os.environ.get("SPEED_IP_MAX", "5"))
except ValueError:
    _speed_ip_max = 5
SPEED_IP_MAX = min(max(_speed_ip_max, 1), 50)

CF_SPEED_IP_URL = os.environ.get("CF_SPEED_IP_URL", "https://ip.164746.xyz/ipTop10.html")
CF_SPEED_IP_FILE = os.environ.get("CF_SPEED_IP_FILE", "cf_speed_ips.txt")


def parse_cf_speed_ips(raw: str, limit: int) -> List[str]:
    """从正文中解析优选 IP（逗号分隔；支持多行、去重、最多 limit 条）。"""
    out: List[str] = []
    seen: set[str] = set()
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        for chunk in line.split(","):
            s = chunk.strip()
            if s and s not in seen:
                seen.add(s)
                out.append(s)
                if len(out) >= limit:
                    return out
    return out


def _fetch_cf_speed_ips_from_network(timeout: int = 10, max_retries: int = 5) -> Optional[List[str]]:
    for attempt in range(max_retries):
        try:
            response = requests.get(CF_SPEED_IP_URL, timeout=timeout)
            if response.status_code == 200:
                ips = parse_cf_speed_ips(response.text, SPEED_IP_MAX)
                return ips if ips else None
        except Exception as e:
            print(f"获取优选 IP 失败 (尝试 {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                traceback.print_exc()
    return None


def load_cf_speed_ips(timeout: int = 10, max_retries: int = 5) -> Optional[List[str]]:
    """
    获取优选 IP 列表（TOP N）：先读本地文件，再走网络。
    文件内容可为 Top10；解析时仍会按 SPEED_IP_MAX 截取前 N 条。
    """
    path = CF_SPEED_IP_FILE
    if os.path.isfile(path):
        try:
            with open(path, encoding="utf-8") as f:
                raw = f.read()
            ips = parse_cf_speed_ips(raw, SPEED_IP_MAX)
            if ips:
                print(f"优选 IP 来自本地文件 {path}，共 {len(ips)} 条")
                return ips
            print(f"本地文件 {path} 解析无有效 IP，改为请求网络")
        except OSError as e:
            print(f"读取本地文件失败: {e}，改为请求网络")

    ips = _fetch_cf_speed_ips_from_network(timeout=timeout, max_retries=max_retries)
    return ips if ips else None
