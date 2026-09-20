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
- 독서 노트, 지속 타이머, 전체 타임라인, 기록 수정·휴지통·복원, 출처 포함 추억/내보내기, 실제 DB 책장 요약, 기간별 통계를 지원함.
- 원본 대조로 상태/생명주기 해석을 정정함. [판정 근거](docs/SOURCE_AUDIT.md) 및 [1단계 구현·검증 보고서](docs/STAGE1_REPORT.md) 참고.

## 북스윙 데이터 변환

```bash
python3 migration/convert_bookswing.py \
  data/bookswing_import/BooksWing_backup.zip \
  migration/output
```

결과물은 `books.json`, `activities.json`, `photo_manifest.json`, `photos/`,
`parse_failures.json`, `validation_report.md`로 생성된다.

## DB 적재 및 앱 실행

**기존 DB를 사용 중이면 `load_db.py`를 재실행하지 마세요. DB를 통째로 재생성합니다.**
기존 자료의 의미 보정은 백업을 만드는 `python -m migration.audit_source --apply`로 한 번만 적용합니다.

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

새 타이머는 시작/멈춤 상태와 초를 DB에 보존하며 새로고침 후 사이드바의
‘타이머 이어보기’로 복구합니다. 여러 기기를 사용하려면 동일한 서버/DB에 접속해야 합니다.
앱은 현재 개인용 단일 사용자 구조입니다. 종료 버튼을 누르기 전까지는 연결이 끊긴 시간도 경과 시간에 포함됩니다.

원본 kind=5는 독서 시작이고 kind=6은 별점이 함께 있는 완료 기록으로 판정합니다.
새 앱의 kind=5 완료와 구별하기 위해 `event_type`을 사용합니다. 기존 0/1/2/4 숫자 체계는 그대로입니다.

## 테스트

```bash
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/pytest -q
```

AppTest는 임시 SQLite DB와 임시 사진 폴더를 사용하므로 실제 독서 데이터에 영향을 주지 않는다.
