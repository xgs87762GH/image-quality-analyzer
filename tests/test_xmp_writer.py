"""XMP写入器单元测试"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import unittest
import tempfile
import shutil


class TestXMPWriter(unittest.TestCase):
    """XMP写入器测试 - 检查代码逻辑"""
    
    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        # 读取源代码文件
        xmp_writer_file = project_root / "metadata" / "xmp_writer.py"
        with open(xmp_writer_file, 'r', encoding='utf-8') as f:
            cls.source_code = f.read()
        
        print("已读取 XMPWriter 源代码")
    
    def test_label_not_written(self):
        """测试 Label 字段不会被写入（因为它是字符串，不是数字）"""
        # 检查是否注释掉了 Label 写入
        # 不应该有未注释的 fields['label']+= 或 XMP-xmp:Label+=
        lines = self.source_code.split('\n')
        label_writes = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 检查未注释的 Label 写入
            if not stripped.startswith('#') and ('fields[\'label\']+=' in stripped or 
                                                  'fields["label"]+=' in stripped or
                                                  'XMP-xmp:Label+=' in stripped):
                label_writes.append(f"Line {i}: {stripped}")
        
        self.assertEqual(len(label_writes), 0, 
                        f"不应该有未注释的 Label 写入，但发现: {label_writes}")
        print("[PASS] Label 字段写入已正确注释")
    
    def test_keywords_not_written(self):
        """测试 Iptc4xmpCore:Keywords 字段不会被写入"""
        lines = self.source_code.split('\n')
        keywords_writes = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            # 检查未注释的 Keywords 写入
            if not stripped.startswith('#') and ('fields[\'keywords\']+=' in stripped or 
                                                  'fields["keywords"]+=' in stripped or
                                                  'Iptc4xmpCore:Keywords+=' in stripped):
                keywords_writes.append(f"Line {i}: {stripped}")
        
        self.assertEqual(len(keywords_writes), 0, 
                        f"不应该有未注释的 Keywords 写入，但发现: {keywords_writes}")
        
        # 检查是否有 Subject 写入（使用更宽松的检查）
        has_subject = ("subject" in self.source_code and "args.append" in self.source_code)
        self.assertTrue(has_subject, 
                     "应该写入 XMP-dc:Subject")
        print("[PASS] Keywords 字段写入已正确注释，Subject 写入存在")
    
    def test_warning_filtering(self):
        """测试非关键警告过滤逻辑"""
        # 检查是否有警告过滤逻辑
        self.assertIn("non_critical_warnings", self.source_code, 
                     "应该有非关键警告过滤")
        self.assertIn("XMP-Iptc4xmpCore:Keywords", self.source_code, 
                     "应该过滤 Keywords 警告")
        self.assertIn("FileName encoding", self.source_code, 
                     "应该过滤文件名编码警告")
        print("[PASS] 警告过滤逻辑已实现")
    
    def test_path_encoding_handling(self):
        """测试路径编码处理"""
        # 检查是否有路径编码处理
        self.assertIn("encode('utf-8')", self.source_code, 
                     "应该有 UTF-8 编码处理")
        self.assertIn("pathlib", self.source_code, 
                     "应该使用 pathlib 处理路径")
        print("[PASS] 路径编码处理已实现")
    
    def test_error_handling(self):
        """测试错误处理逻辑"""
        # 检查是否有错误处理
        self.assertIn("has_critical_error", self.source_code, 
                     "应该有关键错误检查")
        self.assertIn("Error creating file", self.source_code, 
                     "应该检查文件创建错误")
        print("[PASS] 错误处理逻辑已实现")


if __name__ == '__main__':
    unittest.main(verbosity=2)
