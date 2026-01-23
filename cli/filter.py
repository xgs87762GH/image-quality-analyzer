"""根据元数据筛选图像的命令行工具"""
import argparse
import csv
from pathlib import Path
from typing import List

from metadata.xmp_reader import XMPReader


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="根据XMP元数据筛选图像",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 列出所有图像的元数据
  python -m cli.filter -i ./images --list

  # 查找评级<=2的图像
  python -m cli.filter -i ./images --max-rating 2

  # 查找低质量标签的图像
  python -m cli.filter -i ./images --label LowQuality VeryLowQuality

  # 查找包含"blurry"关键词的图像
  python -m cli.filter -i ./images --subject blurry

  # 删除低质量图像（危险操作！）
  python -m cli.filter -i ./images --max-rating 2 --delete
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="输入目录路径"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出所有图像及其元数据"
    )
    
    parser.add_argument(
        "--max-rating",
        type=int,
        help="查找评级<=指定值的图像（1-5）"
    )
    
    parser.add_argument(
        "--label",
        nargs="+",
        help="查找指定标签的图像（如 LowQuality VeryLowQuality）"
    )
    
    parser.add_argument(
        "--subject",
        nargs="+",
        help="查找包含指定关键词的图像（如 blurry brightness_issue）"
    )
    
    parser.add_argument(
        "--output",
        help="将结果保存到CSV文件"
    )
    
    parser.add_argument(
        "--delete",
        action="store_true",
        help="删除筛选出的图像（危险操作！）"
    )
    
    parser.add_argument(
        "--exiftool",
        default="exiftool",
        help="exiftool可执行文件路径"
    )
    
    return parser


def list_images(reader: XMPReader, directory: str, output_file: str = None):
    """列出所有图像及其元数据"""
    from utils.constants import DEFAULT_IMAGE_EXTENSIONS
    
    results = []
    for img_path in Path(directory).rglob("*"):
        if img_path.suffix.lower() in DEFAULT_IMAGE_EXTENSIONS:
            metadata = reader.read(str(img_path))
            results.append({
                "file": str(img_path),
                "rating": metadata.get("Rating", "N/A"),
                "label": metadata.get("Label", "N/A"),
                "subjects": metadata.get("Subject", "N/A")
            })
    
    # 打印结果
    print(f"\n找到 {len(results)} 个图像文件:\n")
    print(f"{'文件':<50} {'评级':<8} {'标签':<15} {'关键词'}")
    print("-" * 100)
    for r in results:
        subjects_str = str(r["subjects"])[:30] if r["subjects"] != "N/A" else "N/A"
        print(f"{Path(r['file']).name:<50} {str(r['rating']):<8} {str(r['label']):<15} {subjects_str}")
    
    # 保存到文件
    if output_file:
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
        print(f"\n结果已保存到: {output_file}")


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"错误: 目录不存在: {args.input}")
        return
    
    try:
        reader = XMPReader(exiftool_path=args.exiftool)
    except FileNotFoundError:
        return
    
    images = []
    
    if args.list:
        list_images(reader, args.input, args.output)
        return
    
    if args.max_rating:
        images = reader.find_by_rating(args.input, args.max_rating)
        print(f"\n找到 {len(images)} 个评级<={args.max_rating} 的图像")
    
    if args.label:
        label_images = reader.find_by_label(args.input, args.label)
        if images:
            images = list(set(images) & set(label_images))
        else:
            images = label_images
        print(f"找到 {len(images)} 个标签为 {args.label} 的图像")
    
    if args.subject:
        subject_images = reader.find_by_subject(args.input, args.subject)
        if images:
            images = list(set(images) & set(subject_images))
        else:
            images = subject_images
        print(f"找到 {len(images)} 个包含关键词 {args.subject} 的图像")
    
    if not images:
        print("\n未找到匹配的图像")
        return
    
    # 显示结果
    print(f"\n匹配的图像 ({len(images)} 个):")
    for img in images[:20]:
        print(f"  {img}")
    if len(images) > 20:
        print(f"  ... 还有 {len(images) - 20} 个")
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["file"])
            for img in images:
                writer.writerow([img])
        print(f"\n结果已保存到: {args.output}")
    
    # 删除操作
    if args.delete:
        print(f"\n警告: 即将删除 {len(images)} 个图像！")
        confirm = input("确认删除？(输入 'yes' 确认): ")
        if confirm.lower() == 'yes':
            deleted = 0
            for img in images:
                try:
                    Path(img).unlink()
                    deleted += 1
                    print(f"已删除: {img}")
                except Exception as e:
                    print(f"删除失败 {img}: {e}")
            print(f"\n删除完成: {deleted}/{len(images)} 个文件")
        else:
            print("操作已取消")


if __name__ == "__main__":
    main()
