# 도서비서 작업 기록

## 2026-09-20 — Codex: 원본 의미 대조
- 사용자 승인 10항목 구현 시작. 브랜치 `codex/bookswing-stage1`. 기존 기획문서 수정/미추적 사본 보존.
- 705권/5,666건 원본 대조: 읽는 중35, 완독278, 미독320, 중단72. readingNow는 1권만1. readCount와 kind6 수 705권 모두 일치.
- 상태/생명주기 의미를 정정하되 숫자 kind·ID·본문·사진은 보존. 원본 의미와 새 앱 이벤트 의미 분리.
- SQLite 백업 `data/backups/before-stage1-20260920-151840.db` 후 원본에서 온 행만 보정. integrity_check=ok.
- 검증: 상태 판정과 멱등 보정 테스트. 근거/역추론 한계는 SOURCE_AUDIT.md.
- 남은 일: 독서 노트, 지속 타이머, 수정/삭제, 공유/책장/통계와 AppTest. 원격 push 없음.
