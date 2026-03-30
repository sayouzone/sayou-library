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
ExamTopics 데이터 모델 클래스들

이 모듈은 ExamTopics 크롤링에서 사용되는 데이터 클래스들을 정의합니다.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import IntEnum


class TopicStatus(IntEnum):
    """토픽 상태 코드"""
    PAGE_NOT_FOUND = -1      # 404 에러 (페이지 없음)
    SUCCESS = 0              # 정상
    EXAM_OFFLINE = 1         # "This exam page is currently offline"
    DISCUSSION_MOVED = 2     # "This discussion was moved"
    BLOCKED = 3              # "Sorry, you have been blocked"
    HEADER_NOT_FOUND = -1    # 시험 문제 헤더를 찾을 수 없음
    SERVER_ERROR = 9         # "General Server Error" (Error Code: 1006 or 1002)
    INVALID_INPUT = -9       # 유효하지 않은 입력


@dataclass
class MediaBody:
    """사용자 댓글 정보를 담는 데이터 클래스"""
    username: Optional[str] = None
    date: Optional[str] = None
    selected_answers: Optional[str] = None
    content: Optional[str] = None
    upvote_text: Optional[str] = None
    badge_primary: Optional[str] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return {
            'username': self.username,
            'date': self.date,
            'selected_answers': self.selected_answers,
            'content': self.content,
            'upvote_text': self.upvote_text,
            'badge_primary': self.badge_primary
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'MediaBody':
        """딕셔너리에서 객체 생성"""
        return cls(
            username=data.get('username'),
            date=data.get('date'),
            selected_answers=data.get('selected_answers'),
            content=data.get('content'),
            upvote_text=data.get('upvote_text'),
            badge_primary=data.get('badge_primary')
        )


@dataclass
class ExamContent:
    """시험 문제 내용을 담는 데이터 클래스"""
    card_text: Optional[str] = None          # 문제 질문
    choices: Optional[str] = None            # 선택지
    suggested_answer: Optional[str] = None   # 제안된 정답
    suggested_answer_images: list[str] = field(default_factory=list)  # 제안된 정답 이미지 URL 목록
    vote_answers: list[str] = field(default_factory=list)             # 사용자 투표 결과
    media_bodies: list[MediaBody] = field(default_factory=list)       # 사용자 댓글 정보


@dataclass
class ExamTopic:
    """
    ExamTopics 시험 문제 정보를 담는 데이터 클래스
    
    Attributes:
        url: 토픽 URL
        response_code: HTTP 응답 코드
        index: 토픽 인덱스 번호
        provider: 시험 제공자 (예: 'Google', 'Microsoft')
        exam: 시험 이름 (예: 'Professional Data Engineer')
        question: 문제 번호
        topic: 주제 번호
        all_questions: 모든 문제 페이지 URL
        publisher: 게시자
        publish_date: 게시일
        status: 상태 코드
        count: 카운트
        description: 설명
        content: 시험 문제 내용 (ExamContent)
    """
    url: Optional[str] = None
    response_code: int = 200
    index: int = 0
    provider: Optional[str] = None
    exam: Optional[str] = None
    question: Optional[str] = None
    topic: Optional[str] = None
    all_questions: Optional[str] = None
    publisher: Optional[str] = None
    publish_date: Optional[str] = None
    status: int = -1
    count: int = 1
    description: Optional[str] = None
    content: ExamContent = field(default_factory=ExamContent)

    # 기존 호환성을 위한 프로퍼티들
    @property
    def card_text(self) -> Optional[str]:
        return self.content.card_text

    @card_text.setter
    def card_text(self, value: Optional[str]):
        self.content.card_text = value

    @property
    def choices(self) -> Optional[str]:
        return self.content.choices

    @choices.setter
    def choices(self, value: Optional[str]):
        self.content.choices = value

    @property
    def suggested_answer(self) -> Optional[str]:
        return self.content.suggested_answer

    @suggested_answer.setter
    def suggested_answer(self, value: Optional[str]):
        self.content.suggested_answer = value

    @property
    def suggested_answer_images(self) -> list[str]:
        return self.content.suggested_answer_images

    @suggested_answer_images.setter
    def suggested_answer_images(self, value: list[str]):
        self.content.suggested_answer_images = value

    @property
    def vote_answers(self) -> list[str]:
        return self.content.vote_answers

    @vote_answers.setter
    def vote_answers(self, value: list[str]):
        self.content.vote_answers = value

    @property
    def media_bodies(self) -> list:
        return self.content.media_bodies

    @media_bodies.setter
    def media_bodies(self, value: list):
        self.content.media_bodies = value

    def format_exam_content(self) -> str:
        """
        시험 문제 정보를 텍스트 형식으로 포맷팅합니다.
        
        Returns:
            str: 포맷팅된 텍스트
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"Provider: {self.provider}")
        lines.append(f"Exam: {self.exam}")
        lines.append(f"Question #: {self.question}")
        lines.append(f"Topic #: {self.topic}")
        lines.append(f"Publisher: {self.publisher}")
        lines.append(f"Date: {self.publish_date}")
        lines.append(f"URL: {self.url}")
        lines.append("-" * 80)
        
        if self.content.card_text:
            lines.append("Question:")
            lines.append(self.content.card_text)
            lines.append("")
        
        if self.content.choices:
            lines.append("Choices:")
            lines.append(self.content.choices)
            lines.append("")
        
        if self.content.suggested_answer:
            lines.append(f"Suggested Answer: {self.content.suggested_answer}")
        
        if self.content.suggested_answer_images:
            lines.append("Answer Images:")
            for img in self.content.suggested_answer_images:
                lines.append(f"  - {img}")
        
        if self.content.vote_answers:
            lines.append(f"Vote Answers: {', '.join(self.content.vote_answers)}")
        
        if self.content.media_bodies:
            lines.append("-" * 40)
            lines.append("Comments:")
            for idx, body in enumerate(self.content.media_bodies, 1):
                if isinstance(body, MediaBody):
                    lines.append(f"  [{idx}] {body.username} ({body.date})")
                    if body.selected_answers:
                        lines.append(f"      {body.selected_answers}")
                    if body.content:
                        lines.append(f"      {body.content[:200]}...")
                    if body.upvote_text:
                        lines.append(f"      {body.upvote_text}")
                elif isinstance(body, dict):
                    lines.append(f"  [{idx}] {body.get('username')} ({body.get('date')})")
                    if body.get('selected_answers'):
                        lines.append(f"      {body.get('selected_answers')}")
                    if body.get('content'):
                        lines.append(f"      {body.get('content', '')[:200]}...")
                    if body.get('upvote_text'):
                        lines.append(f"      {body.get('upvote_text')}")
        
        lines.append("=" * 80)
        lines.append("")
        
        return "\n".join(lines)

    def to_csv_row(self) -> dict:
        """CSV 행으로 변환"""
        return {
            "Index": self.index,
            "Provider": self.provider,
            "Exam": self.exam,
            "Question": self.question,
            "Topic": self.topic,
            "Date": self.publish_date,
            "Status": self.status,
            "Count": self.count,
            "Url": self.url,
            "All": self.all_questions
        }

    def is_error(self) -> bool:
        """에러 상태인지 확인"""
        return (
            self.response_code == 404 or
            self.response_code == 502 or
            self.response_code == 503 or
            (self.response_code == 200 and self.status == TopicStatus.PAGE_NOT_FOUND) or
            (self.response_code == 200 and self.status == TopicStatus.BLOCKED)
        )

    def is_blocked(self) -> bool:
        """차단 상태인지 확인"""
        return self.status == TopicStatus.BLOCKED

    def is_server_error(self) -> bool:
        """서버 에러 상태인지 확인"""
        return self.status == TopicStatus.SERVER_ERROR


@dataclass
class CrawlerConfig:
    """크롤러 설정을 담는 데이터 클래스"""
    max_404_error_count: int = 5
    log_file: str = "crawler.log"
    max_random_num: int = 10
    base_url: str = "https://www.examtopics.com"
    min_waiting_time: int = 10
    headless: bool = False

    @classmethod
    def from_json(cls, config_dict: dict) -> 'CrawlerConfig':
        """JSON 딕셔너리에서 설정 객체 생성"""
        return cls(
            max_404_error_count=config_dict.get('max_404_error_count', 5),
            log_file=config_dict.get('log_file', 'crawler.log'),
            max_random_num=config_dict.get('max_random_num', 10),
            base_url=config_dict.get('base_url', 'https://www.examtopics.com'),
            min_waiting_time=config_dict.get('min_waiting_time', 10),
            headless=config_dict.get('headless', False)
        )


# 기존 ExamTopics 클래스와의 호환성을 위한 별칭
ExamTopics = ExamTopic