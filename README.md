# 도서비서 (Book Butler)

개인 독서 기록(진도·타임라인·인용구·통계·스트릭)을 위한 1단계 앱. 이후 소셜 공유(2단계), 소그룹 커뮤니티(3단계)로 확장 예정.

전체 기획(로드맵, 데이터 구조, 마이그레이션 계획, 기술 스택)은 [도서비서_기획문서.md](./도서비서_기획문서.md)를 참고.

## 폴더 구조
```
도서비서/
├── data/
│   ├── bookswing_import/   # 북스윙 백업 원본 zip (git 추적 제외)
│   └── book_butler.db      # 적재된 SQLite DB (git 추적 제외)
├── migration/                # 북스윙 JSON → 새 DB 스키마 변환·적재 스크립트
├── lib/                       # DB 접근, 스트릭/뱃지 계산 등 공용 모듈
├── app.py                    # Streamlit 앱 (1단계: 책장/책 상세/통계/스트릭·뱃지)
├── requirements.txt
└── README.md
```

## 현재 상태
- 북스윙 백업 705권·활동 5,666건을 새 JSON 구조로 변환하는 스크립트가 준비됨.
- 변환 결과와 사진은 개인정보 보호를 위해 `migration/output/`에 생성되며 Git 추적에서 제외됨(단, `validation_report.md`는 예외적으로 추적).
- JSON → SQLite 적재 스크립트(`migration/load_db.py`)와 1단계 Streamlit 화면(책장, 책 상세, 통계, 스트릭/뱃지)을 구현함.
- 책 상세에서 진도·인용구·메모·사진 기록과 책 상태·정보 수정을 지원함.
- 활동 kind는 북스윙과 동일한 숫자 체계(0~7)를 사용함.

## 북스윙 데이터 변환

```bash
python3 migration/convert_bookswing.py \
  data/bookswing_import/BooksWing_backup.zip \
  migration/output
```

결과물은 `books.json`, `activities.json`, `photo_manifest.json`, `photos/`,
`parse_failures.json`, `validation_report.md`로 생성된다.

## DB 적재 및 앱 실행

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

python migration/load_db.py   # migration/output/*.json → data/book_butler.db
streamlit run app.py
```

`app.py`는 `data/book_butler.db`, `data/photos/`, `migration/output/photos/`를 읽어
책장·책 상세·통계·스트릭/뱃지 화면을 렌더링한다. 통계 화면의 "읽은 쪽수/시간"은
북스윙 원본 진행 로그(progress_log) 문장에서 역파싱한 값을 세션 단위로 합산한
것이며, 음수로 기록된 값은 0으로 처리한다.

## 테스트

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
```

AppTest는 임시 SQLite DB와 임시 사진 폴더를 사용하므로 실제 독서 데이터에 영향을 주지 않는다.
