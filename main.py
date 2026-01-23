#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量图像质量/审美分析工具 - 主程序入口
"""
from utils.encoding import setup_console_encoding
from cli.main import main

# 设置控制台编码
setup_console_encoding()

if __name__ == "__main__":
    main()
