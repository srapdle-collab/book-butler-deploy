# 읽담

북스윙 개인 독서 기록을 보존하고 책장·독서 노트·타이머·공유·통계와 초대형 소그룹 인증을 제공하는 Streamlit 앱.
도서비서 폴더는 독립 Git 저장소이며 상위 동하비서에서 제외된다. 서브모듈 관계가 없다.

- 숫자 activity kind는 원본과 호환한다. 원본 생명주기 의미 정정은 `SOURCE_AUDIT.md` 참고.
- 실제 DB/사진/백업은 Git에서 제외한다. 테스트는 별도 임시 DB만 쓴다.
- Supabase Auth 계정이 개인 서재와 소그룹을 분리한다. 기존 705권 서재는 Cloud Secret `READDAM_OWNER_EMAIL`과 일치하는 계정만 소유자로 연결하며, 소그룹에는 사용자가 선택한 인용구·사진 스냅샷과 일일 인증·반응·댓글만 공유한다. 전체공개 피드·뱃지는 구현하지 않는다.
- `migration/load_db.py`는 초기 적재 전용이며 기존 DB를 재생성하므로 사용 중인 DB에 실행하지 않는다.
- 영속 데이터는 Supabase Postgres(`bookbutler-prod`, 서울 리전)에 저장한다. 로컬 개발/테스트는 SQLite를 유지하며, `BOOK_BUTLER_DATABASE_URL` 또는 Supabase DB 환경변수가 있으면 Postgres로 연결한다.
- 사진은 비공개 Supabase Storage `book-photos` 버킷에 저장하고 서버가 짧은 만료의 서명 URL을 발급한다. 서비스 키는 `.env` 또는 Streamlit secrets에만 둔다.
- 공개 Streamlit Community Cloud 앱은 배포 전용 공개 미러 `srapdle-collab/book-butler-deploy`에서 제공한다. 앱 시작 비밀번호와 Supabase 접속 정보는 Cloud Secrets에만 두며, 원본 저장소 `srapdle-collab/book-butler`는 비공개로 유지한다. 배포 미러는 검증된 `main` 변경을 `git push deploy main`으로 수동 동기화한다.
