"""
날짜/시간 변환 유틸리티 모듈

ExamTopics 크롤링에서 사용되는 날짜/시간 변환 함수들을 제공합니다.
"""

import locale
import re
from datetime import datetime
from typing import Optional

import pytz


def date_to_date(date_string: str) -> str:
    """
    "Sun 07 Jan 2024 00:08" 형식을 "2024-01-07 00:08"으로 변환합니다.

    Args:
        date_string: "Sun 07 Jan 2024 00:08" 형식의 문자열

    Returns:
        str: "2024-01-07 00:08" 형식의 문자열
    """
    datetime_object = datetime.strptime(date_string, "%a %d %b %Y %H:%M")
    return datetime_object.strftime("%Y-%m-%d %H:%M")


def us_to_kr_datetime_with_timezone(
    date_string: str,
    input_format: Optional[str] = None
) -> str:
    """
    미국 날짜/시간을 한국 날짜/시간으로 변환 (시간대 포함)
    
    Args:
        date_string: 미국 형식 날짜/시간 문자열
        input_format: 입력 형식 (None이면 자동 감지 시도)
    
    Returns:
        한국 형식 날짜/시간 문자열 (YYYY년 MM월 DD일 HH:MM:SS)
    """
    us_tz = pytz.timezone('America/New_York')
    kr_tz = pytz.timezone('Asia/Seoul')
    
    us_formats = [
        '%m/%d/%Y %I:%M:%S %p',  # 12/07/2025 03:30:45 PM
        '%m/%d/%Y %I:%M %p',     # 12/07/2025 03:30 PM
        '%m/%d/%Y',              # 12/07/2025
        '%B %d, %Y %I:%M %p',    # December 07, 2025 03:30 PM
        '%b %d, %Y %I:%M %p',    # Dec 07, 2025 03:30 PM
        '%m-%d-%Y %H:%M:%S',     # 12-07-2025 15:30:45
        '%Y-%m-%d %H:%M:%S',     # 2025-12-07 15:30:45 (ISO)
    ]
    
    if input_format is None:
        dt = None
        for fmt in us_formats:
            try:
                dt = datetime.strptime(date_string, fmt)
                break
            except ValueError:
                continue
        
        if dt is None:
            raise ValueError(f"지원하지 않는 날짜 형식: {date_string}")
    else:
        dt = datetime.strptime(date_string, input_format)
    
    us_dt = us_tz.localize(dt)
    kr_dt = us_dt.astimezone(kr_tz)
    
    return kr_dt.strftime('%Y년 %m월 %d일 %H:%M:%S')


# 월 이름 매핑 테이블
MONTH_MAPPING = {
    "January": "Jan", "Jan.": "Jan", "Jan": "Jan",
    "February": "Feb", "Feb.": "Feb", "Feb": "Feb",
    "March": "Mar", "Mar.": "Mar", "Mar": "Mar",
    "April": "Apr", "Apr.": "Apr", "Apr": "Apr",
    "May": "May",
    "June": "Jun", "Jun.": "Jun", "Jun": "Jun",
    "July": "Jul", "Jul.": "Jul", "Jul": "Jul",
    "August": "Aug", "Aug.": "Aug", "Aug": "Aug",
    "September": "Sep", "Sept.": "Sep", "Sep.": "Sep", "Sep": "Sep",
    "October": "Oct", "Oct.": "Oct", "Oct": "Oct",
    "November": "Nov", "Nov.": "Nov", "Nov": "Nov",
    "December": "Dec", "Dec.": "Dec", "Dec": "Dec",
}


def _normalize_month_name(date_str: str) -> str:
    """월 이름을 표준 형식으로 정규화"""
    month_keys = sorted(MONTH_MAPPING.keys(), key=len, reverse=True)
    pattern = re.compile('|'.join(re.escape(key) for key in month_keys))
    return pattern.sub(lambda m: MONTH_MAPPING[m.group(0)], date_str)


def _normalize_time_indicators(date_str: str) -> str:
    """시간 표시자를 표준 형식으로 정규화"""
    result = date_str.replace('p.m.', 'PM').replace('a.m.', 'AM')
    result = result.replace('noon', '12:00 PM').replace('midnight', '12:00 AM')
    return result


def _set_english_locale():
    """영어 로케일 설정"""
    try:
        locale.setlocale(locale.LC_TIME, 'en_US.UTF-8')
    except locale.Error:
        locale.setlocale(locale.LC_TIME, 'English_United States.1252')


def us_to_kr_datetime(date_str: str) -> str:
    """
    미국 날짜/시간 문자열을 한국 형식으로 변환
    
    Args:
        date_str: 미국 형식 날짜/시간 문자열 (예: 'Sept. 26, 2025, 4:25 p.m.')
    
    Returns:
        한국 형식 날짜/시간 문자열 (YYYY.MM.DD HH:MM)
    """
    # 월 이름 정규화
    normalized_date = _normalize_month_name(date_str)
    # 시간 표시자 정규화
    normalized_date = _normalize_time_indicators(normalized_date)
    
    # 영어 로케일 설정
    _set_english_locale()
    
    datetime_formats = [
        '%b %d, %Y, %I:%M %p',  # Sep 26, 2025, 4:25 PM
        '%b %d, %Y, %I %p',     # Sep 26, 2025, 4 PM
    ]

    datetime_obj = None
    for datetime_format in datetime_formats:
        try:
            datetime_obj = datetime.strptime(normalized_date, datetime_format)
            break
        except ValueError:
            continue

    if datetime_obj is None:
        raise ValueError(f"지원하지 않는 날짜 형식: {normalized_date}")

    return datetime_obj.strftime('%Y.%m.%d %H:%M')


def extract_publish_info(input_string: str) -> dict:
    """
    'by {publisher} at {date_string}' 형식의 문자열에서
    publisher와 publish_date를 추출합니다.

    Args:
        input_string: 분석할 원본 문자열

    Returns:
        dict: 'publisher'와 'publish_date'를 포함하는 딕셔너리
    """
    pattern = re.compile(r"by\s+(.*?)\s+at\s+(.*)")
    match = pattern.search(input_string)

    if match:
        publisher = match.group(1)
        date_str = match.group(2)
    else:
        publisher = None
        date_str = input_string

    publish_date = us_to_kr_datetime(date_str)

    return {
        'publisher': publisher,
        'publish_date': publish_date
    }
