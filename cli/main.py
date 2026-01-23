"""主程序入口"""
import argparse
import sys
from pathlib import Path

from utils.encoding import setup_console_encoding
from database.connection import init_database
from processors.batch_processor import BatchProcessor
from config.settings import get_settings
from utils.constants import DEFAULT_IMAGE_EXTENSIONS

setup_console_encoding()


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="批量图像质量/审美分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础质量分析
  python -m cli.main -i ./images

  # 包含审美评分
  python -m cli.main -i ./images --aesthetic

  # 生成CSV报告
  python -m cli.main -i ./images -o report.csv

  # 指定exiftool路径
  python -m cli.main -i ./images --exiftool "C:/exiftool/exiftool.exe"
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        nargs="+",
        required=True,
        help="输入目录路径（可指定多个）"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="输出CSV报告路径（可选）"
    )
    
    parser.add_argument(
        "--aesthetic",
        action="store_true",
        help="启用审美评分（需要transformers和torch）"
    )
    
    parser.add_argument(
        "--exiftool",
        default="exiftool",
        help="exiftool可执行文件路径（默认: exiftool）"
    )
    
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="不创建备份文件（默认会创建）"
    )
    
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=DEFAULT_IMAGE_EXTENSIONS,
        help=f"要处理的图像扩展名（默认: {' '.join(DEFAULT_IMAGE_EXTENSIONS)}）"
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 初始化数据库
    try:
        init_database()
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)
    
    processor = BatchProcessor(use_aesthetic=args.aesthetic)
    
    # 支持多目录
    input_dirs = args.input if isinstance(args.input, list) else [args.input]
    
    processor.process(
        input_dir=None,
        input_dirs=input_dirs,
        output_csv=args.output,
        extensions=args.extensions,
        write_xmp=not args.no_xmp if hasattr(args, 'no_xmp') else None
    )


if __name__ == "__main__":
    main()
