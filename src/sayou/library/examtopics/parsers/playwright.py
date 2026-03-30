"""
ExamTopics 페이지 파서 모듈

Playwright를 사용하여 ExamTopics 페이지에서 정보를 추출하는 파서 클래스를 제공합니다.
"""

from typing import Optional, Tuple
from urllib.parse import urlparse

from playwright._impl._errors import TimeoutError

from .models import ExamTopic, ExamContent, MediaBody, TopicStatus
from .utils.date_utils import date_to_date, extract_publish_info


class PageParser:
    """ExamTopics 페이지 파싱을 담당하는 클래스"""
    
    HOST_URL = 'https://www.examtopics.com'
    
    def __init__(self):
        self.current_url: Optional[str] = None
        self.response_status: int = 200

    def get_error_status(self, locator) -> int:
        """
        페이지에서 에러 메시지를 찾아서 에러 코드를 반환합니다.

        Returns:
            int: 에러 코드
                -1: 404 에러 (페이지 없음)
                1: "This exam page is currently offline"
                2: "This discussion was moved"
                3: "Sorry, you have been blocked"
                9: "General Server Error" (Error Code: 1006 or 1002)
                0: 에러 없음
        """
        # Cloudflare 차단 확인
        if self._check_cloudflare_block(locator):
            return TopicStatus.BLOCKED

        # 일반 에러 페이지 확인
        error_status = self._check_error_page(locator)
        if error_status != 0:
            return error_status

        # 서버 에러 확인
        if self._check_server_error(locator):
            return TopicStatus.SERVER_ERROR

        # 404 이미지 확인
        if self._check_404_image(locator):
            return TopicStatus.PAGE_NOT_FOUND

        return TopicStatus.SUCCESS

    def _check_cloudflare_block(self, locator) -> bool:
        """Cloudflare 차단 여부 확인"""
        try:
            error_locator = locator.locator('div.cf-error-details-wrapper')
            error_text = error_locator.inner_text(timeout=1000)
            if "Sorry, you have been blocked" in error_text.strip():
                return True
        except TimeoutError:
            pass
        return False

    def _check_error_page(self, locator) -> int:
        """일반 에러 페이지 확인"""
        try:
            error_locator = locator.locator('div.error-page-area.sec-spacer')
            error_text = error_locator.inner_text(timeout=1000)
            if "This exam page is currently offline" in error_text:
                return TopicStatus.EXAM_OFFLINE
            elif "This discussion was moved" in error_text:
                return TopicStatus.DISCUSSION_MOVED
        except TimeoutError:
            pass
        return 0

    def _check_server_error(self, locator) -> bool:
        """서버 에러 확인"""
        try:
            error_locator = locator.locator('div.error-page-message div.error-page')
            error_text = error_locator.inner_text(timeout=1000)
            if "General Server Error" in error_text:
                if "Error Code: 1006" in error_text or "Error Code: 1002" in error_text:
                    return True
        except TimeoutError:
            pass
        return False

    def _check_404_image(self, locator) -> bool:
        """404 에러 이미지 확인"""
        image_locators = locator.locator('img')
        for image_locator in image_locators.all():
            src_url = image_locator.get_attribute("src")
            if src_url and "/assets/images/et/404robot.jpg" in src_url:
                return True
        return False

    def extract_exam_content(self, locator) -> ExamContent:
        """
        주어진 요소에서 시험 문제 정보를 추출합니다.

        Args:
            locator: Playwright Locator 객체

        Returns:
            ExamContent: 시험 문제 내용 데이터 클래스
        """
        content = ExamContent()
        
        body_locator = locator.locator('div.question-body')

        # Card Text (문제 질문)
        content.card_text = self._extract_card_text(body_locator)
        
        # Choices (문제 답변, 선택지)
        content.choices = self._extract_choices(body_locator)
        
        # 제안된 정답 및 사용자 투표 결과
        question_answer_locator = body_locator.locator('div.question-answer')
        
        # Suggested Answer (제안 답변)
        content.suggested_answer, content.suggested_answer_images = \
            self._extract_suggested_answer(question_answer_locator)
        
        # Vote Distribution
        content.vote_answers = self._extract_vote_answers(question_answer_locator)
        
        # 사용자 댓글 (media bodies)
        content.media_bodies = self._extract_media_bodies(locator)

        return content

    def _extract_card_text(self, body_locator) -> Optional[str]:
        """문제 질문 추출"""
        card_text_locator = body_locator.locator('p.card-text')
        card_text = card_text_locator.inner_text()
        
        # 이미지 URL 추가
        image_locators = card_text_locator.locator('img')
        for image_locator in image_locators.all():
            item_image = image_locator.get_attribute("src")
            card_text = card_text + "\n" + item_image
        
        return card_text

    def _extract_choices(self, body_locator) -> Optional[str]:
        """선택지 추출"""
        choices_locator = body_locator.locator('div.question-choices-container')
        image_locators = choices_locator.locator('img')
        
        if image_locators.count() == 0:
            try:
                return choices_locator.inner_text(timeout=1000)
            except TimeoutError:
                return None
        else:
            choices_arr = []
            choices_locators = choices_locator.locator('li')
            for choices_elem_locator in choices_locators.all():
                choice_text = choices_elem_locator.inner_text()
                image_locators = choices_elem_locator.locator('img')
                for image_locator in image_locators.all():
                    item_image = image_locator.get_attribute("src")
                    choice_text = choice_text + "\n" + item_image
                choices_arr.append(choice_text)
            return '\n'.join(choices_arr)

    def _extract_suggested_answer(self, question_answer_locator) -> Tuple[Optional[str], list]:
        """제안된 정답 추출"""
        suggested_answer_locator = question_answer_locator.locator('span.correct-answer')
        suggested_answer = suggested_answer_locator.inner_text()
        
        suggested_answer_images = []
        image_locators = suggested_answer_locator.locator('img')
        for image_locator in image_locators.all():
            answer_image = image_locator.get_attribute("src")
            suggested_answer_images.append(answer_image)
        
        return suggested_answer, suggested_answer_images

    def _extract_vote_answers(self, question_answer_locator) -> list:
        """투표 결과 추출"""
        vote_answers = []
        vote_distribution_locator = question_answer_locator.locator(
            '//div[@class="progress vote-distribution-bar"]'
        )
        vote_locators = vote_distribution_locator.locator("div[style*='display: flex']")
        for vote_locator in vote_locators.all():
            vote = vote_locator.inner_text()
            vote_answers.append(vote)
        return vote_answers

    def _extract_media_bodies(self, locator) -> list:
        """사용자 댓글 추출"""
        media_bodies = []
        media_body_locators = locator.locator('div.media-body')
        
        for media_body_locator in media_body_locators.all():
            media_body = self._extract_single_media_body(media_body_locator)
            media_bodies.append(media_body)
        
        return media_bodies

    def _extract_single_media_body(self, media_body_locator) -> dict:
        """단일 댓글 정보 추출"""
        media_body = {}

        # Username
        try:
            comment_username_locator = media_body_locator.locator("h5.comment-username").first
            media_body['username'] = comment_username_locator.inner_text(timeout=1000)
        except TimeoutError:
            pass
        
        # Date
        try:
            comment_date_locator = media_body_locator.locator("span.comment-date").first
            comment_date_title = comment_date_locator.get_attribute('title')
            comment_date_title = date_to_date(comment_date_title)
            comment_date_text = comment_date_locator.inner_text(timeout=1000)
            media_body['date'] = f"{comment_date_title} ({comment_date_text})"
        except TimeoutError:
            pass

        # Selected Answers
        try:
            comment_selected_answers = media_body_locator.locator("div.comment-selected-answers").first
            media_body['selected_answers'] = comment_selected_answers.inner_text(timeout=1000)
        except TimeoutError:
            pass
        
        # Content
        try:
            comment_content = media_body_locator.locator("div.comment-content").first
            media_body['content'] = comment_content.inner_text(timeout=1000)
        except TimeoutError:
            pass

        # Upvote Text
        try:
            upvote_text = media_body_locator.locator("span.upvote-text").first
            media_body['upvote_text'] = upvote_text.inner_text(timeout=1000)
        except TimeoutError:
            pass

        # Badge
        try:
            badge_primary = media_body_locator.locator("span.badge-primary").first
            media_body['badge_primary'] = badge_primary.inner_text(timeout=1000)
        except TimeoutError:
            pass
        
        return media_body

    def extract_topic(self, locator, topic: ExamTopic, current_url: str) -> ExamTopic:
        """
        페이지에서 전체 토픽 정보를 추출합니다.

        Args:
            locator: Playwright Locator 객체
            topic: ExamTopic 데이터 객체
            current_url: 현재 페이지 URL

        Returns:
            ExamTopic: 추출된 정보가 채워진 ExamTopic 객체
        """
        # 헤더 추출
        header_info = self._extract_header_info(locator, topic)
        if header_info is None:
            topic.status = TopicStatus.HEADER_NOT_FOUND
            topic.description = "시험 문제 헤더를 찾을 수 없습니다."
            return topic

        topic.provider = header_info['provider']
        topic.exam = header_info['exam']
        topic.question = header_info['question']
        topic.topic_num = header_info['topic_num']
        topic.all_questions = header_info['all_questions_url']

        # 시험 문제 내용 추출
        content = self.extract_exam_content(locator)
        topic.content = content

        # 메타데이터 추출
        meta_info = self._extract_meta_info(locator)
        if meta_info:
            topic.publisher = meta_info['publisher']
            topic.publish_date = meta_info['publish_date']

        topic.status = TopicStatus.SUCCESS

        # URL 정리
        topic.url = self._normalize_url(topic.all_questions, current_url)

        return topic

    def _extract_header_info(self, locator, topic: ExamTopic) -> Optional[dict]:
        """헤더 정보 추출"""
        try:
            header_locator = locator.locator('div.question-discussion-header')
            header_text = header_locator.inner_text(timeout=1000)
        except TimeoutError:
            return None

        exams = header_text.splitlines()
        provider = exams[0].replace("Actual exam question from ", "") if len(exams) >= 1 else ""
        provider = provider.replace("Exam question from ", "")

        # Discussion link에서 시험 이름 추출
        discussion_locator = header_locator.locator('a.discussion-link')
        exam_name = discussion_locator.inner_text()

        # Provider 이름 정리
        index = provider.find(f"'s {exam_name}")
        provider = provider[0:index].strip() if index > 0 else provider

        # 질문 및 주제 번호 추출
        question_locator = header_locator.locator("div")
        question_text = question_locator.inner_text()
        
        question_num = None
        topic_num = None
        for line in question_text.splitlines():
            if "Question #: " in line:
                question_num = line.replace("Question #: ", "").strip()
            elif "Topic #: " in line:
                topic_num = line.replace("Topic #: ", "").strip()

        # All questions URL
        link_locator = header_locator.locator('a.all-questions-link')
        all_questions_url = link_locator.get_attribute("href")
        if self.HOST_URL not in all_questions_url:
            all_questions_url = f"{self.HOST_URL}{all_questions_url}"

        return {
            'provider': provider,
            'exam': exam_name,
            'question': question_num,
            'topic_num': topic_num,
            'all_questions_url': all_questions_url
        }

    def _extract_meta_info(self, locator) -> Optional[dict]:
        """메타데이터 (게시자, 게시일) 추출"""
        try:
            meta_locator = locator.locator('div.discussion-meta-data')
            meta_text = meta_locator.inner_text()
        except TimeoutError:
            return None

        result = extract_publish_info(meta_text)
        
        if result['publisher'] is None:
            try:
                user_locator = meta_locator.locator('a.title-username')
                result['publisher'] = user_locator.inner_text().strip()
            except TimeoutError:
                index = meta_text.find(" at ")
                result['publisher'] = meta_text[0:index].replace("by ", "")

        return result

    def _normalize_url(self, all_questions_url: str, current_url: str) -> str:
        """URL 정규화"""
        uri = urlparse(all_questions_url)
        paths = uri.path.split("/")
        provider1 = paths[2] if len(paths) > 2 else ""

        uri = urlparse(current_url)
        paths = uri.path.split("/")
        if len(paths) > 2:
            current_url = current_url.replace("/" + paths[2] + "/", "/" + provider1 + "/")

        return current_url