# 启动项目脚本（Windows PowerShell）

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Image Quality Analyzer - 启动脚本" -ForegroundColor Cyan
Write-Host "  图像质量分析器" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查conda是否安装
$condaExists = Get-Command conda -ErrorAction SilentlyContinue
if (-not $condaExists) {
    Write-Host "错误: 未找到conda，请先安装Anaconda或Miniconda" -ForegroundColor Red
    exit 1
}

$ENV_NAME = "image_quality"

# 检查环境是否存在
Write-Host "检查conda环境..." -ForegroundColor Yellow
$envExists = conda env list | Select-String $ENV_NAME

if (-not $envExists) {
    Write-Host "环境不存在，正在创建..." -ForegroundColor Yellow
    Write-Host "执行: scripts/setup_env.ps1" -ForegroundColor Yellow
    & "scripts/setup_env.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "环境创建失败！" -ForegroundColor Red
        exit 1
    }
}

# 激活环境
Write-Host "激活conda环境: $ENV_NAME" -ForegroundColor Green
conda activate $ENV_NAME

if ($LASTEXITCODE -ne 0) {
    Write-Host "环境激活失败！" -ForegroundColor Red
    exit 1
}

# 检查依赖
Write-Host "检查依赖..." -ForegroundColor Yellow
$flaskExists = python -c "import flask" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "安装依赖..." -ForegroundColor Yellow
    pip install -r requirements.txt
}

# 检查数据库
Write-Host "检查数据库..." -ForegroundColor Yellow
if (-not (Test-Path "data/image_quality.db")) {
    Write-Host "初始化数据库..." -ForegroundColor Yellow
    python scripts/init_database.py
}

# 执行数据库迁移（如果需要）
Write-Host "检查数据库迁移..." -ForegroundColor Yellow
python -c "from database.connection import get_db; db = get_db(); conn = db.get_connection(); cursor = conn.execute('PRAGMA table_info(images)'); cols = [row[1] for row in cursor.fetchall()]; exit(0 if 'deleted_at' in cols and 'thumbnail_path' in cols else 1)" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "执行数据库迁移..." -ForegroundColor Yellow
    python -c "from database.connection import get_db; db = get_db(); conn = db.get_connection(); conn.execute('ALTER TABLE images ADD COLUMN thumbnail_path TEXT'); conn.execute('ALTER TABLE images ADD COLUMN deleted_at TIMESTAMP'); conn.execute('CREATE INDEX IF NOT EXISTS idx_deleted_at ON images(deleted_at)'); conn.commit(); print('迁移完成')"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  启动Web服务器..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "访问地址: http://localhost:5000" -ForegroundColor Cyan
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 启动Web服务器
python scripts/run_web.py
