import re
import fitz
from PyPDF2 import PdfReader, PdfWriter
from typing import List, Tuple, Union
import os

class PDFSplitter:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)
        self.pyreader = PdfReader(pdf_path)
    
    def _save_chunk(self, pages: List[int], output_path: str):
        """通用保存函数"""
        writer = PdfWriter()
        for p in pages:
            writer.add_page(self.pyreader.pages[p])
        with open(output_path, "wb") as f:
            writer.write(f)
        print(f"已保存到 {output_path}")

    # ----------------- 按章节拆分 -----------------
    def split_by_bookmarks(self, output_dir: str, level: int = 1):
        """基于书签层级拆分[1,5](@ref)"""
        toc = self.doc.get_toc()
        if not toc:
            raise ValueError("PDF 无书签目录")

        chapters = []
        current_chapter = []
        for entry in toc:
            if entry[0] == level:  # 根据层级判断章节
                if current_chapter:
                    chapters.append(current_chapter)
                current_chapter = [entry]
            else:
                current_chapter.append(entry)
        
        for i, chap in enumerate(chapters):
            lv = chap[0][0]
            page = chap[0][2]  # 页码从0开始
            title = chap[0][1]
            index_start = self.find_valid_page_in_chap(chap)
            start_page = chap[index_start][2] - 1  # 页码从0开始
            next_chap = chapters[i+1] if i+1 < len(chapters) else None
            if next_chap is None:
                end_page = len(self.doc)
            else:
                index_end = self.find_valid_page_in_chap(next_chap)
                end_page = next_chap[index_end][2]-1 if i+1 < len(chapters) else len(self.doc)
            # 创建以章节标题命名的目录
            chapter_dir = os.path.join(output_dir, title.replace(" ", "_").replace("/", "_"))
            os.makedirs(chapter_dir, exist_ok=True)
            self._save_chunk(
                pages=range(start_page, end_page),
                output_path=f"{output_dir}/{title}.pdf"
            )
    
    def split_by_chapter(self, output_dir: str, chapter: str, level: int = 1):
        """基于书签层级拆分[1,5](@ref)"""
        toc = self.doc.get_toc()
        if not toc:
            raise ValueError("PDF 无书签目录")
        chapters = []
        target_chapter = None
        current_chapter = []
        for entry in toc:
            lv = entry[0]
            ch = entry[1]
            if ch == chapter:  # 根据层级判断章节
                current_chapter = [entry]
                target_chapter = entry
            elif target_chapter and lv == level:
                current_chapter.append(entry)
            elif target_chapter and lv > level:
                current_chapter.append(entry)
                continue
            elif target_chapter and lv < level:
                if current_chapter:
                    chapters.append(current_chapter)
                break
        
        if len(chapters) > 0:
            target_chapter = chapters[0]
        else:
            raise ValueError("未找到指定章节")
        chapter_title = target_chapter[0][1]
        chapter_dir = os.path.join(output_dir, chapter_title.replace(" ", "_").replace("/", "_"))
        os.makedirs(chapter_dir, exist_ok=True)
        for i, subchap in enumerate(target_chapter):
            if subchap[0] != level:
                continue
            lv = subchap[0]
            title = subchap[1]
            page = subchap[2]    
            index_start = self.find_valid_page_in_subchap(target_chapter, i)
            start_page = target_chapter[index_start][2] - 1  # 页码从0开始
            next_sub_chap = None
            next_sub_chap_index = 0
            for j, sub_chap in enumerate(target_chapter[i+1:], start=i+1):
                if sub_chap[0] == level:
                    next_sub_chap_index = j
                    next_sub_chap = sub_chap
                    break
            if next_sub_chap is None:
                last_sub_chap_index = len(target_chapter) - 1
                end_page = target_chapter[last_sub_chap_index][2]
            else:
                index_end = self.find_valid_page_in_subchap(target_chapter, next_sub_chap_index)
                end_page = target_chapter[index_end][2]-1
            # 创建以章节标题命名的目录
            self._save_chunk(
            pages=range(start_page, end_page),
            output_path=f"{chapter_dir}/{title}.pdf"
            )

    def find_valid_page_in_chap(self, chap) -> int:
        index = 0
        while index < len(chap) and chap[index][2] < 0:
                index += 1
        return index
    
    def find_valid_page_in_subchap(self, chap, curr_index) -> int:
        index = curr_index
        while index < len(chap) and chap[index][2] < 0:
                index += 1
        return index
    # ----------------- 按内容分析拆分 -----------------
    def split_by_content(self, output_dir: str, pattern: str = r'^Chapter\s+\d+'):
        """基于正则表达式识别章节起始页[3](@ref)"""
        chapter_pages = []
        for pnum in range(len(self.doc)):
            text = self.doc.load_page(pnum).get_text("text")
            if re.search(pattern, text, flags=re.IGNORECASE):
                chapter_pages.append(pnum)
        
        for i, start in enumerate(chapter_pages):
            end = chapter_pages[i+1] if i+1 < len(chapter_pages) else len(self.doc)
            self._save_chunk(
                pages=range(start, end),
                output_path=f"{output_dir}/Section_{i+1}.pdf"
            )

    # ----------------- 按固定页数拆分 -----------------
    def split_by_pages(self, output_dir: str, chunk_size: int = 10):
        """每 N 页拆分为一个文件[5,6](@ref)"""
        total = len(self.doc)
        for i in range(0, total, chunk_size):
            self._save_chunk(
                pages=range(i, min(i+chunk_size, total)),
                output_path=f"{output_dir}/Part_{i//chunk_size + 1}.pdf"
            )

    # ----------------- 自定义范围拆分 -----------------
    def split_custom(self, ranges: List[Tuple[int, int]], output_dir: str):
        """指定页码范围拆分[2](@ref)"""
        for idx, (start, end) in enumerate(ranges):
            self._save_chunk(
                pages=range(start-1, end),
                output_path=f"{output_dir}/Custom_{idx+1}.pdf"
            )

# ----------------- 使用示例 -----------------
if __name__ == "__main__":
    splitter = PDFSplitter("azure-aks.pdf")
    #模式选择
    #splitter.split_by_bookmarks("output/") 
    #splitter.split_by_chapter("output/", "操作指南", 2) 
    splitter.split_by_chapter("output/", "安全性", 3) 