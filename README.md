# sayou-library
Sayouzone Libraries Crawler

도서 정보 크롤링 및 글로벌 자격증 시험 크로링<br/>

- Aladin 도서 조회
- 경기도 도서관 도서 조회
- 글로벌 자격증 시험 다운로드

## 패키지 구조

```
├── src/sayou/library/
│   ├── aladin/
│   │   ├──  parsers/
│   │   │    └── __init__.py
│   │   ├── __init__.py
│   │   ├── client.py            # 문서 API 파서
│   │   ├── crawler.py           # 문서 뷰어 API 파서
│   │   ├── models.py            # 공시정보 API 파서
│   │   ├── README.md            # 정기보고서 재무정보 API 파서
│   │   └── utils.py             # 주요사항보고서 주요정보 API 파서
│   ├── examtopics/
│   │   ├──  parsers/
│   │   │    ├── __init__.py     #
│   │   │    └── playwright.py   #
│   │   ├──  utils/
│   │   │    ├── data.py         #
│   │   │    ├── fkle_handler.py #
│   │   │    └── utils.py        #
│   │   ├── __init__.py
│   │   ├── client.py            # 문서 API 파서
│   │   ├── crawler.py           # 문서 뷰어 API 파서
│   │   ├── models.py            # 공시정보 API 파서
│   │   ├── playwright.py        # 정기보고서 재무정보 API 파서
│   │   └── README.md            # 주요사항보고서 주요정보 API 파서
│   └── hscitylib/
│       ├──  parsers/
│       │    └── __init__.py     #
│       ├── __init__.py          #
│       ├── client.py            # 문서 API 파서
│       ├── crawler.py           # 문서 뷰어 API 파서
│       ├── models.py            # 공시정보 API 파서
│       ├── README.md            # 정기보고서 재무정보 API 파서
│       └── utils.py             # 주요사항보고서 주요정보 API 파서
├── tests/
│   ├── test_aladin.py           # OpenDART 테스트 (로컬 소스)
│   └── test_examtopics.py       # OpenDART 테스트 (sayou-stock)
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Deployment


## Errors
