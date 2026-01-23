#!/bin/bash
# Conda环境设置脚本（Linux/macOS）

ENV_NAME="image_quality"
PYTHON_VERSION="3.10"

echo "正在创建conda环境: $ENV_NAME (Python $PYTHON_VERSION)"
conda create -n $ENV_NAME python=$PYTHON_VERSION -y

echo "激活环境并安装依赖..."
source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate $ENV_NAME

pip install -r requirements.txt

echo "初始化数据库..."
python scripts/init_database.py

echo "环境设置完成！"
echo "使用以下命令激活环境："
echo "  conda activate $ENV_NAME"
echo "启动Web界面："
echo "  python scripts/run_web.py"
