# 읽담

북스윙 개인 독서 기록을 보존하고 책장·독서 노트·타이머·공유·통계와 초대형 소그룹 인증을 제공하는 Streamlit 앱.
도서비서 폴더는 독립 Git 저장소이며 상위 동하비서에서 제외된다. 서브모듈 관계가 없다.

- 숫자 activity kind는 원본과 호환한다. 원본 생명주기 의미 정정은 `SOURCE_AUDIT.md` 참고.
- `reading_chunks`는 기존 `activities`와 별도인 additive 조각 보관 표다. 읽담 화면에서 만든 조각은 `source_app=readdam`이며, UUID·스냅샷 책 정보·태그·콘텐츠 타입·소프트 삭제를 가진다. 기존 책·기록·통계에는 연결하거나 변환하지 않는다.
- 실제 DB/사진/백업은 Git에서 제외한다. 테스트는 별도 임시 DB만 쓴다.
- Supabase Auth 계정이 개인 서재와 소그룹을 분리한다. 기존 705권 서재는 Cloud Secret `READDAM_OWNER_EMAIL`과 일치하는 계정만 소유자로 연결하며, 소그룹에는 사용자가 선택한 인용구·사진 스냅샷과 일일 인증·반응·댓글만 공유한다. 전체공개 피드·뱃지는 구현하지 않는다.
- `migration/load_db.py`는 초기 적재 전용이며 기존 DB를 재생성하므로 사용 중인 DB에 실행하지 않는다.
- 영속 데이터는 Supabase Postgres(`bookbutler-prod`, 서울 리전)에 저장한다. 로컬 개발/테스트는 SQLite를 유지하며, `BOOK_BUTLER_DATABASE_URL` 또는 Supabase DB 환경변수가 있으면 Postgres로 연결한다.
- 사진은 비공개 Supabase Storage `book-photos` 버킷에 저장하고 서버가 짧은 만료의 서명 URL을 발급한다. 서비스 키는 `.env` 또는 Streamlit secrets에만 둔다.
- 공개 Streamlit Community Cloud 앱은 배포 전용 공개 미러 `srapdle-collab/book-butler-deploy`에서 제공한다. 앱 시작 비밀번호와 Supabase 접속 정보는 Cloud Secrets에만 두며, 원본 저장소 `srapdle-collab/book-butler`는 비공개로 유지한다. 배포 미러는 검증된 `main` 변경을 `git push deploy main`으로 수동 동기화한다.

## 공동작업 기록 체계
- 작업자 규칙: `AGENTS.md`(정본), `CLAUDE.md`(Claude 진입점). 여러 작업자가 번갈아 작업하므로 항상 공동작업으로 간주한다.
- 현재 상태·다음 행동은 `docs/HANDOFF.md`(최신 항목 맨 위), 상세 역사는 `docs/WORKLOG.md`, 프로젝트 간 계약은 동하비서 최상위 `CROSS_PROJECT_HANDOFF.md`에 둔다.

## Reading Chunk 공동작업 (오늘의 서재 연동)
- 공통 결정·책임 범위·규격·진행상태의 정본은 `../CROSS_PROJECT_HANDOFF.md` 1절이다. 세부 설계는 `오늘의 서재/docs/READING_CHUNK_DESIGN.md`에 있다.
- 읽담이 reading chunk의 최종 Source of Truth다. txt·예화창고는 파생 사본이다. 기존 activities 5,666건은 migration하지 않는다.
- 1차-A(읽담 단독)는 `aeecb7f`에 구현됐고, txt 출력의 ISBN·읽은 시간·sourceApp 코드 보완 `cbcf0b4`까지 main·origin/main에 반영됐다(2026-09-26). 사용자 승인에 따라 별도 worktree에서 fast-forward했고 반영 후 전체 테스트 65개가 통과했다. 원본 작업트리의 사용자 소유 미커밋 기획문서 2개는 보존 중이다.
- 운영 배포와 Supabase 적용은 보류 상태이며 `deploy/main`은 `51e5b0c`다. origin push만으로 배포 미러를 동기화하지 않는다. **1차-A는 운영 검증 전으로 완전 완료가 아니며 1차-B(오늘의 서재 API 연동)와 2차(예화 카테고리별 분류 export)는 미착수**다.
- txt 보관 루트는 `/Users/donghakim/Library/Mobile Documents/com~apple~CloudDocs/예화창고`로 확정됐다. 1차-A는 그 아래 `독서조각/`만 관리한다. 합성 임시 SQLite의 검증용 chunk 1건으로 실제 txt 생성·동일 항목 재export·내용 갱신·index 일치를 2026-09-26 확인했다. 기존 690개 항목의 전후 메타데이터 변경·삭제는 없었다. 운영 DB 기반 export와 iCloud 기기간 동기화는 아직 검증하지 않았다.
