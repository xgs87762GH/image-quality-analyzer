"""数据库查询工具"""
import argparse
import json
from pathlib import Path

from utils.encoding import setup_console_encoding
from database.connection import get_db
from services.quality_service import QualityService
from services.image_service import ImageService

setup_console_encoding()


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="查询图像质量数据库",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 查询评级<=2的图像
  python -m cli.query --rating-max 2

  # 查询低质量图像
  python -m cli.query --label LowQuality

  # 查询质量分数范围
  python -m cli.query --quality-min 0 --quality-max 50

  # 显示统计信息
  python -m cli.query --stats

  # 查找重复图像
  python -m cli.query --duplicates
        """
    )
    
    parser.add_argument(
        "--rating-min",
        type=int,
        help="最低评级（1-5）"
    )
    
    parser.add_argument(
        "--rating-max",
        type=int,
        help="最高评级（1-5）"
    )
    
    parser.add_argument(
        "--label",
        help="质量标签（如 LowQuality, MediumQuality）"
    )
    
    parser.add_argument(
        "--quality-min",
        type=float,
        help="最低质量分数"
    )
    
    parser.add_argument(
        "--quality-max",
        type=float,
        help="最高质量分数"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="显示统计信息"
    )
    
    parser.add_argument(
        "--duplicates",
        action="store_true",
        help="查找重复图像"
    )
    
    parser.add_argument(
        "--output",
        help="输出结果到JSON文件"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        help="限制结果数量"
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    quality_service = QualityService()
    image_service = ImageService()
    
    results = []
    
    # 统计信息
    if args.stats:
        stats = quality_service.get_statistics()
        image_stats = image_service.get_statistics()
        print("\n=== 统计信息 ===")
        print(f"总图像数: {image_stats.get('total_images', 0)}")
        print(f"已评估数: {stats.get('total', 0)}")
        if stats.get('total', 0) > 0:
            print(f"平均质量分数: {stats.get('avg_score', 0):.2f}")
            print(f"最低质量分数: {stats.get('min_score', 0):.2f}")
            print(f"最高质量分数: {stats.get('max_score', 0):.2f}")
            print(f"平均评级: {stats.get('avg_rating', 0):.2f}")
        return
    
    # 查找重复图像
    if args.duplicates:
        duplicates = image_service.find_duplicates()
        print(f"\n找到 {len(duplicates)} 组重复图像:")
        for dup in duplicates:
            print(f"\n哈希: {dup['hash']} (共 {dup['count']} 个)")
            for img in dup['images']:
                print(f"  - {img['file_path']}")
        results = duplicates
    # 按评级查询
    elif args.rating_min or args.rating_max:
        min_rating = args.rating_min or 1
        max_rating = args.rating_max or 5
        results = quality_service.find_by_rating(min_rating, max_rating)
        print(f"\n找到 {len(results)} 个图像 (评级: {min_rating}-{max_rating})")
    # 按标签查询
    elif args.label:
        results = quality_service.find_by_label(args.label)
        print(f"\n找到 {len(results)} 个图像 (标签: {args.label})")
    # 按质量分数范围查询
    elif args.quality_min or args.quality_max:
        min_score = args.quality_min or 0.0
        max_score = args.quality_max or 100.0
        results = quality_service.find_by_quality_range(min_score, max_score)
        print(f"\n找到 {len(results)} 个图像 (质量分数: {min_score}-{max_score})")
    else:
        print("请指定查询条件（--rating-max, --label, --quality-min等）或使用 --stats 查看统计信息")
        return
    
    # 限制结果数量
    if args.limit and len(results) > args.limit:
        results = results[:args.limit]
        print(f"（仅显示前 {args.limit} 个结果）")
    
    # 显示结果
    if not args.duplicates:
        print("\n=== 查询结果 ===")
        for i, result in enumerate(results, 1):
            img = result.get('image', {})
            quality = result.get('quality', {})
            print(f"\n[{i}] {Path(img.get('file_path', '')).name}")
            print(f"    路径: {img.get('file_path', '')}")
            print(f"    质量分数: {quality.get('quality_score', 0):.2f}")
            print(f"    评级: {quality.get('rating', 0)} 星")
            print(f"    标签: {quality.get('label', '')}")
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"\n结果已保存到: {args.output}")


if __name__ == "__main__":
    main()
