#!/usr/bin/env python3
"""
ExamTopics 크롤러 메인 실행 스크립트

사용법:
    python main.py --start 100000 --end 100100
    python main.py --csv-file exams/exams_2501.csv --start 100000 --end 100100
"""

import argparse
from datetime import datetime

from playwright.sync_api import Playwright, sync_playwright

from crawler import PlaywrightCrawler
from utils.file_handler import CSVReader, find_latest_csv_file, create_output_paths, CSVHeaders


def parse_args() -> argparse.Namespace:
    """커맨드라인 인자를 파싱합니다."""
    parser = argparse.ArgumentParser(
        description='ExamTopics 웹사이트에서 시험 문제를 크롤링합니다.'
    )

    parser.add_argument(
        '--config',
        help='설정 파일 경로',
        default='config.json'
    )
    parser.add_argument(
        '--csv-file',
        required=False,
        help='히스토리 CSV 파일 경로'
    )
    parser.add_argument(
        '--start',
        type=int,
        help='시작 토픽 번호'
    )
    parser.add_argument(
        '--end',
        type=int,
        help='끝 토픽 번호',
        default=999999
    )
    parser.add_argument(
        '--module',
        help='크롤링 모듈 (playwright)',
        default='playwright',
        choices=['playwright']
    )
    parser.add_argument(
        '--process',
        help='프로세스 유형 (retrieve, retry, check, test)',
        default='retrieve',
        choices=['retrieve', 'retry', 'check', 'test']
    )

    return parser.parse_args()


def setup_files(csv_file_path: str, last_index: int) -> dict:
    """파일들을 설정합니다."""
    paths = create_output_paths(csv_file_path)
    
    # CSV 파일 열기
    csv_file = open(paths['csv'], 'a', newline='', encoding='utf-8')
    
    import csv
    csv_writer = csv.DictWriter(csv_file, fieldnames=CSVHeaders.FIELDS)
    if last_index <= 0:
        csv_writer.writeheader()

    # TXT 파일 열기
    question_file = open(paths['txt'], 'a', newline='', encoding='utf-8')
    other_question_file = open(paths['txt_others'], 'a', newline='', encoding='utf-8')

    return {
        'csv_file': csv_file,
        'csv_writer': csv_writer,
        'question_file': question_file,
        'other_question_file': other_question_file
    }


def run(playwright: Playwright, args: argparse.Namespace) -> None:
    """메인 실행 함수"""
    # 파라미터 설정
    start = args.start if args.start else 0
    end = args.end if args.end else 0
    csv_file_path = args.csv_file

    # CSV 파일 경로 결정
    if not csv_file_path:
        csv_file_path = find_latest_csv_file()
        if not csv_file_path:
            month = datetime.now().strftime("%y%m")
            csv_file_path = f"exams/exams_{month}.csv"

    # 마지막 정보 가져오기
    last_index, last_provider, last_url = CSVReader.get_last_info(csv_file_path)
    print(f"Last info - Index: {last_index}, Provider: {last_provider}, URL: {last_url}")

    # 시작 번호 설정
    start = start if start else (last_index + 1)
    last_provider = last_provider.lower() if last_provider else "cisco"

    # 파일 설정
    files = setup_files(csv_file_path, last_index)

    # Playwright 크롤러가 아닌 경우 종료
    if args.module != 'playwright':
        print("Only playwright module is supported")
        return

    # 크롤러 초기화 및 실행
    crawler = PlaywrightCrawler(playwright, config_file=args.config)
    
    try:
        crawler.set_provider(last_provider)
        crawler.set_base_url(last_url)
        crawler.set_csv_writer(files['csv_file'], files['csv_writer'])
        crawler.set_txt_writer(
            txt_file=files['question_file'],
            txt_other_file=files['other_question_file']
        )

        # 크롤링 실행
        topics = crawler.get_examtopics(start, end + 1, 10)
        print(f"Crawled {len(topics)} topics")

    finally:
        # 리소스 정리
        files['other_question_file'].close()
        files['question_file'].close()
        files['csv_file'].close()
        crawler.close()


def main():
    """엔트리 포인트"""
    args = parse_args()
    
    print(f"Arguments: {args}")
    print(f"  --config: {args.config}")
    print(f"  --csv-file: {args.csv_file}")
    print(f"  --start: {args.start}")
    print(f"  --end: {args.end}")
    print(f"  --module: {args.module}")
    print(f"  --process: {args.process}")

    with sync_playwright() as playwright:
        print("Starting Playwright...")
        run(playwright, args)


if __name__ == "__main__":
    main()
