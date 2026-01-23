# Conda环境设置脚本（Windows PowerShell）

$ENV_NAME = "image_quality"
$PYTHON_VERSION = "3.10"

Write-Host "正在创建conda环境: $ENV_NAME (Python $PYTHON_VERSION)" -ForegroundColor Green
conda create -n $ENV_NAME python=$PYTHON_VERSION -y

Write-Host "激活环境并安装依赖..." -ForegroundColor Green
conda activate $ENV_NAME

pip install -r requirements.txt

Write-Host "初始化数据库..." -ForegroundColor Green
python scripts/init_database.py

Write-Host "`n环境设置完成！" -ForegroundColor Green
Write-Host "使用以下命令激活环境：" -ForegroundColor Yellow
Write-Host "  conda activate $ENV_NAME" -ForegroundColor Cyan
Write-Host "启动Web界面：" -ForegroundColor Yellow
Write-Host "  python scripts/run_web.py" -ForegroundColor Cyan
