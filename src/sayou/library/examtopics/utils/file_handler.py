"""
파일 핸들러 모듈

CSV 및 TXT 파일 입출력을 담당하는 클래스들을 제공합니다.
"""

import csv
import glob
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO, List, Tuple

from .models import ExamTopic


class CSVHeaders:
    """CSV 파일 헤더 상수"""
    FIELDS = ["Index", "Provider", "Exam", "Question", "Topic", "Date", "Status", "Count", "Url", "All"]


class FileHandler:
    """파일 입출력을 담당하는 클래스"""
    
    def __init__(self):
        self.csv_file: Optional[TextIO] = None
        self.csv_writer: Optional[csv.DictWriter] = None
        self.txt_file: Optional[TextIO] = None
        self.txt_other_file: Optional[TextIO] = None
        self.extracted_lines: List[str] = []

    def setup_csv_writer(self, file_path: str, write_header: bool = False):
        """
        CSV writer를 설정합니다.

        Args:
            file_path: CSV 파일 경로
            write_header: 헤더를 쓸지 여부
        """
        self.csv_file = open(file_path, 'a', newline='', encoding='utf-8')
        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=CSVHeaders.FIELDS)
        if write_header:
            self.csv_writer.writeheader()

    def setup_txt_writers(
        self,
        txt_file_path: str,
        other_file_path: Optional[str] = None,
        extracted_lines: Optional[List[str]] = None
    ):
        """
        TXT writer를 설정합니다.

        Args:
            txt_file_path: TXT 파일 경로
            other_file_path: 기타 TXT 파일 경로 (선택)
            extracted_lines: 이미 추출된 URL 목록 (선택)
        """
        self.txt_file = open(txt_file_path, 'a', newline='', encoding='utf-8')
        if other_file_path:
            self.txt_other_file = open(other_file_path, 'a', newline='', encoding='utf-8')
        if extracted_lines:
            self.extracted_lines = extracted_lines

    def write_topic_to_csv(self, topic: ExamTopic):
        """토픽 정보를 CSV에 씁니다."""
        if self.csv_writer:
            self.csv_writer.writerow(topic.to_csv_row())
            if self.csv_file:
                self.csv_file.flush()

    def write_duplicate_marker(self):
        """중복 마커를 CSV에 씁니다."""
        if self.csv_writer:
            duplicate_row = {field: "중복" for field in CSVHeaders.FIELDS}
            self.csv_writer.writerow(duplicate_row)
            if self.csv_file:
                self.csv_file.flush()

    def write_topic_to_txt(self, topic: ExamTopic, target_providers: List[str]):
        """
        토픽 정보를 TXT 파일에 씁니다.

        Args:
            topic: ExamTopic 객체
            target_providers: 대상 제공자 목록 (예: ['Google', 'Microsoft'])
        """
        full_text = topic.format_exam_content()
        
        if self.txt_file and topic.provider in target_providers:
            self.txt_file.write(full_text)
            self.txt_file.flush()
        elif self.txt_file:
            # 대상이 아닌 경우 [X] 표시 추가
            full_text = full_text.replace(topic.provider, f"{topic.provider} [X]")
            self.txt_file.write(full_text)
            self.txt_file.flush()
        elif self.txt_other_file:
            self.txt_other_file.write(full_text)
            self.txt_other_file.flush()

    def is_url_extracted(self, url: str) -> bool:
        """URL이 이미 추출되었는지 확인합니다."""
        return url in self.extracted_lines

    def close(self):
        """모든 파일을 닫습니다."""
        if self.csv_file:
            self.csv_file.close()
        if self.txt_file:
            self.txt_file.close()
        if self.txt_other_file:
            self.txt_other_file.close()


class CSVReader:
    """CSV 파일 읽기를 담당하는 클래스"""

    @staticmethod
    def get_last_info(file_path: str) -> Tuple[int, Optional[str], Optional[str]]:
        """
        CSV 파일에서 마지막 정보를 가져옵니다.

        Args:
            file_path: CSV 파일 경로

        Returns:
            Tuple[int, Optional[str], Optional[str]]: (마지막 인덱스, 제공자, URL)
        """
        last_index = 0
        last_url = None
        last_provider = None

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                list_csv = list(csv_reader)

                index = -1
                while True:
                    if abs(index) > len(list_csv):
                        break
                    
                    last = list_csv[index]
                    if len(last) == len(CSVHeaders.FIELDS):
                        try:
                            last_index = int(last[0])
                            last_provider = last[1]
                            last_url = last[8]
                            break
                        except ValueError:
                            index -= 1
                    else:
                        break
        except FileNotFoundError:
            pass

        return last_index, last_provider, last_url

    @staticmethod
    def read_items(file_path: str) -> List[List[str]]:
        """
        CSV 파일에서 아이템 목록을 읽습니다.

        Args:
            file_path: CSV 파일 경로

        Returns:
            List[List[str]]: 아이템 목록
        """
        items = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',')
                items = list(csv_reader)
        except FileNotFoundError:
            pass
        return items


def find_latest_csv_file(base_dir: str = "exams", prefix: str = "exams_") -> Optional[str]:
    """
    가장 최신 CSV 파일을 찾습니다.

    Args:
        base_dir: 기본 디렉토리
        prefix: 파일 이름 접두사

    Returns:
        Optional[str]: 찾은 파일 경로 또는 None
    """
    month = datetime.now().strftime("%y%m")
    files = glob.glob(f"{base_dir}/{prefix}{month}*.csv")
    files.sort(reverse=True)
    return files[0] if files else None


def create_output_paths(csv_file_path: str) -> dict:
    """
    출력 파일 경로들을 생성합니다.

    Args:
        csv_file_path: CSV 파일 경로

    Returns:
        dict: 파일 경로들을 담은 딕셔너리
    """
    base_path = Path(csv_file_path)
    return {
        'csv': csv_file_path,
        'txt': str(base_path.with_suffix('.txt')),
        'txt_others': str(base_path.with_name(base_path.stem + '_others.txt'))
    }