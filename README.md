# 도서비서 (Book Butler)

개인 독서 기록(진도·타임라인·인용구·통계·스트릭)을 위한 1단계 앱. 이후 소셜 공유(2단계), 소그룹 커뮤니티(3단계)로 확장 예정.

전체 기획(로드맵, 데이터 구조, 마이그레이션 계획, 기술 스택)은 [도서비서_기획문서.md](./도서비서_기획문서.md)를 참고.

## 폴더 구조
```
도서비서/
├── data/
│   └── bookswing_import/   # 북스윙 백업 원본 zip (git 추적 제외)
├── migration/                # 북스윙 JSON → 새 DB 스키마 변환 스크립트
├── app.py                    # Streamlit 앱 (1단계, 화면 구현 전)
└── README.md
```

## 현재 상태
- 북스윙 백업 705권·활동 5,666건을 새 JSON 구조로 변환하는 스크립트가 준비됨.
- 변환 결과와 사진은 개인정보 보호를 위해 `migration/output/`에 생성되며 Git 추적에서 제외됨.
- 화면 코드와 DB 스키마 구현은 아직 시작 전.

## 북스윙 데이터 변환

```bash
python3 migration/convert_bookswing.py \
  data/bookswing_import/BooksWing_backup.zip \
  migration/output
```

결과물은 `books.json`, `activities.json`, `photo_manifest.json`, `photos/`,
`parse_failures.json`, `validation_report.md`로 생성된다.
