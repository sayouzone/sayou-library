# Copyright (c) 2025-2026, Sayouzone
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ExamTopics Playwright 크롤러 모듈

Playwright를 사용하여 ExamTopics 웹사이트에서 시험 문제 정보를 크롤링합니다.
"""

import json
import math
import random
import re
import time
from typing import Optional, List
from urllib.parse import urlparse

from playwright.sync_api import Playwright, Page, BrowserContext, Browser
from playwright._impl._errors import TimeoutError

from .models import ExamTopic, CrawlerConfig, TopicStatus
from .parsers.playwright import PageParser
from .utils.file_handler import FileHandler


from .client import ExamtopicsClient

from .parsers import (
)

class ExamtopicsCrawler:
    """
    Examtopics Crawler
    """

    def __init__(self):
        self.client = ExamtopicsClient()



class PlaywrightCrawler:
    """
    ExamTopics 웹사이트에서 시험 문제 정보를 Playwright을 이용하여 크롤링하는 클래스입니다.
    """

    HOST_URL = 'https://www.examtopics.com'
    TARGET_PROVIDERS = ['Google', 'Microsoft', 'Amazon', 'Databricks', 'Snowflake']

    def __init__(
        self,
        playwright: Playwright,
        config: Optional[CrawlerConfig] = None,
        config_file: str = 'config.json'
    ):
        """
        초기화

        Args:
            playwright: Playwright 객체
            config: CrawlerConfig 설정 객체 (선택)
            config_file: 설정 파일 경로 (config가 None일 때 사용)
        """
        # 설정 로드
        if config:
            self.config = config
        else:
            self.config = self._load_config(config_file)

        # 브라우저 초기화
        self.browser: Browser = playwright.chromium.launch(headless=self.config.headless)
        self.context: BrowserContext = self.browser.new_context()
        self.page: Page = self.context.new_page()
        self.page.on("response", self._handle_response)

        # 상태 변수
        self.current_url: Optional[str] = None
        self.response_status: int = 200
        self.provider: str = 'microsoft'
        self.path: Optional[str] = None

        # 파서 초기화
        self.parser = PageParser()
        
        # 파일 핸들러 초기화
        self.file_handler = FileHandler()

        # 쿠키 정보 확인
        cookies = self.context.cookies()
        print('Cookies:', cookies)

    def _load_config(self, config_file: str) -> CrawlerConfig:
        """설정 파일에서 설정을 로드합니다."""
        try:
            with open(config_file, 'r') as f:
                config_dict = json.load(f)
                return CrawlerConfig.from_json(config_dict)
        except FileNotFoundError:
            print(f"Config file not found: {config_file}, using defaults")
            return CrawlerConfig()

    def close(self):
        """리소스를 정리합니다."""
        self.file_handler.close()
        self.context.close()
        self.browser.close()

    def set_provider(self, provider: str):
        """제공자를 설정합니다."""
        self.provider = provider

    def set_base_url(self, base_url: str):
        """
        기본 URL을 설정합니다.

        Args:
            base_url: 기본 URL
        """
        if not base_url:
            return
            
        parts = urlparse(base_url)
        # 토픽 번호 부분을 '##NUMBER##'로 치환하여 저장
        self.path = re.sub(r'/view/([0-9]+)\-exam', '/view/##NUMBER##-exam', parts.path)

    def set_csv_writer(self, csv_file, csv_writer):
        """CSV writer를 설정합니다 (레거시 호환성)."""
        self.file_handler.csv_file = csv_file
        self.file_handler.csv_writer = csv_writer

    def set_txt_writer(self, txt_file=None, txt_other_file=None, extracted_lines=None):
        """TXT writer를 설정합니다 (레거시 호환성)."""
        self.file_handler.txt_file = txt_file
        self.file_handler.txt_other_file = txt_other_file
        if extracted_lines:
            self.file_handler.extracted_lines = extracted_lines

    def _handle_response(self, response):
        """
        Playwright의 response 이벤트 핸들러입니다.
        """
        url = response.url
        content_type = response.header_value("content-type")
        
        if response.status >= 200 and content_type and "text/html" in content_type:
            print(f"Response URL: {url} {content_type}")
        
        if f"{self.HOST_URL}/discussions/" in url:
            self.current_url = url
            self.response_status = response.status
            print(f"Response Status: {self.response_status}")

    def get_examtopic(self, exam_no: int, url: str) -> ExamTopic:
        """
        주어진 URL에서 시험 문제 정보를 가져옵니다.

        Args:
            exam_no: 시험 번호
            url: 시험 문제 페이지 URL

        Returns:
            ExamTopic: ExamTopic 객체
        """
        topic = ExamTopic(url=url, index=exam_no)

        if not exam_no and not url:
            print("시험 번호 또는 URL이 제공되지 않았습니다.")
            topic.status = TopicStatus.INVALID_INPUT
            return topic

        # 페이지 로드
        try:
            self.page.goto(url, wait_until='domcontentloaded', timeout=60000)
        except TimeoutError as e:
            print(f"TimeoutError: Timeout error when trying to load: {url}")
            return topic

        # 에러 확인
        status = self.parser.get_error_status(self.page)
        print(f"status: {status}")
        
        if status != TopicStatus.SUCCESS:
            topic.status = status
            topic.url = self.current_url
            topic.description = "차단되었습니다" if status == TopicStatus.BLOCKED else None
            return topic

        # 토픽 정보 추출
        topic = self.parser.extract_topic(self.page, topic, self.current_url)

        return topic

    def extract_examtopics_by_urls(self, items: List[List[str]], sleep: int) -> List[ExamTopic]:
        """
        주어진 URL 목록에서 시험 문제 정보를 가져옵니다.

        Args:
            items: URL 목록 (CSV 행 형태)
            sleep: 기본 대기 시간 (초)

        Returns:
            list: ExamTopic 객체 목록
        """
        topics = []
        error_count = 0

        for idx, item in enumerate(items):
            # 빈 줄 건너뛰기
            if len(item) == 0:
                continue

            index = item[0]
            uri = item[8]

            # 이미 추출된 URL 건너뛰기
            if self.file_handler.is_url_extracted(uri):
                print(f"### Skipping {idx + 1}/{len(items)}")
                continue

            topic = self.get_examtopic(int(index), uri)

            if not topic:
                return topics

            # 에러 처리
            if topic.is_error():
                error_count += 1
                if error_count >= self.config.max_404_error_count:
                    print("### Finishing (404 Error) ###")
                    break

                waiting_time = self._calculate_error_wait_time(sleep, error_count)
                print(f"### Waiting {waiting_time}s (404 Error) ###")
                time.sleep(waiting_time)
                continue

            # TXT 파일에 저장
            self._write_topic_to_files(topic)

            # 정상 처리
            topic.index = int(index)
            topics.append(topic)

            if topic.is_blocked() or topic.is_server_error():
                print(f"description: {topic.description}")
                break

            if idx >= len(items) - 1:
                print("### Finishing ###")
                break

            # 대기
            waiting_time = self._calculate_normal_wait_time()
            print(f"### Waiting {waiting_time}s ### {idx + 1}/{len(items)}")
            time.sleep(waiting_time)

        return topics

    def get_examtopics(self, start: int, end: int, sleep: int) -> List[ExamTopic]:
        """
        주어진 범위의 토픽 번호에 해당하는 시험 문제 정보를 가져옵니다.

        Args:
            start: 시작 토픽 번호
            end: 끝 토픽 번호
            sleep: 대기 시간 (초)

        Returns:
            list: ExamTopic 객체 목록
        """
        topics = []
        error_count = 0
        uris = []

        path = self._build_initial_path(start)
        uri = f"https://{self.HOST_URL.replace('https://', '')}{path}"
        index = start

        while index <= end:
            # URL 변환 (특정 제공자 문제 대응)
            uri = self._transform_uri_for_crawling(uri)
            
            topic = self.get_examtopic(index, uri)

            if not topic:
                return topics

            # 에러 처리
            if topic.is_error():
                error_count += 1
                if error_count >= self.config.max_404_error_count:
                    print("### Finishing 404 Error ###")
                    break

                waiting_time = self._calculate_error_wait_time(sleep, error_count)
                print(f"### Waiting {waiting_time}s (404 Error) ###")
                time.sleep(waiting_time)
                continue

            topic.index = index
            topics.append(topic)

            if topic.is_blocked() or topic.is_server_error():
                print(f"description: {topic.description}")
                break

            # CSV 저장
            self.file_handler.write_topic_to_csv(topic)

            # TXT 저장
            self._write_topic_to_files(topic)

            # 중복 URL 체크
            uri = topic.url
            if uri in uris:
                self.file_handler.write_duplicate_marker()
                break
            uris.append(uri)

            # 다음 URL 준비
            uri = self._prepare_next_uri(uri, index)
            index += 1
            error_count = 0

            if index > end:
                print("### Finishing ###")
                break

            # 대기
            waiting_time = self._calculate_normal_wait_time()
            print(f"### Waiting {waiting_time}s ###")
            time.sleep(waiting_time)

        return topics

    def _build_initial_path(self, start: int) -> str:
        """초기 경로를 생성합니다."""
        if self.path:
            return self.path.replace("##NUMBER##", str(start))
        return f"/discussions/{self.provider}/view/{start}-exam-topic-1-discussion/"

    def _transform_uri_for_crawling(self, uri: str) -> str:
        """크롤링을 위해 URI를 변환합니다."""
        # 특정 제공자에서 발생하는 404 오류 대응
        uri = uri.replace("/cisco/", "/amazon/")
        uri = uri.replace("/microsoft/", "/amazon/")
        uri = uri.replace("/amazon/", "/oracle/")
        uri = uri.replace("/acams/", "/oracle/")
        return uri

    def _prepare_next_uri(self, uri: str, current_index: int) -> str:
        """다음 URI를 준비합니다."""
        uri = uri.replace("/acams/", "/amazon/")
        uri = uri.replace(f"/{current_index}", f"/{current_index + 1}")
        return uri

    def _calculate_error_wait_time(self, base_sleep: int, error_count: int) -> float:
        """에러 발생 시 대기 시간을 계산합니다."""
        waiting_time = base_sleep * random.randint(1, self.config.max_random_num)
        waiting_time += math.pow(2, error_count)
        return waiting_time

    def _calculate_normal_wait_time(self) -> int:
        """일반 대기 시간을 계산합니다."""
        return random.randint(5, self.config.min_waiting_time)

    def _write_topic_to_files(self, topic: ExamTopic):
        """토픽을 파일에 저장합니다."""
        if self.file_handler.txt_file:
            self.file_handler.write_topic_to_txt(topic, self.TARGET_PROVIDERS)