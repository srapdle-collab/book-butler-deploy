# Reading Chunk → 예화창고 자동 export 준비

`tools/export_pipeline.py`는 DB의 **해당 소유자 전체 Chunk**(soft delete 포함)를 읽기 전용으로 조회한다. 매번 전체 목록을 확인하지만 receipt와 manifest를 비교해 실제로 바뀐 파일만 반영한다. 수동 `chunk-id` 입력은 필요 없다.

흐름: 1차-A txt 계획 → 기존 카테고리의 `읽담/` 분류 계획 → 충돌/미매핑 사전 차단 → 1차-A 실행 → DB 변경 재확인 → 분류 실행. 내용 수정, 태그 변경, soft delete가 다음 실행에 반영된다. 한 실행 중 두 단계는 단일 트랜잭션이 아니므로 중단 후 같은 명령을 다시 실행하면 각 단계의 pending 기록부터 복구한다. 사람이 만든 파일과 관리 영역 밖 파일은 수정하지 않는다. 기존 카테고리 폴더가 없으면 새로 만들지 않는다.

CLI 기본값은 **dry-run**이며 파일과 DB를 쓰지 않는다. `--apply`는 파일을 실제로 쓰므로 운영 승인·read-only 사전 점검 뒤에만 사용한다. 오늘 밤 실제 iCloud `--apply`는 실행하지 않았다.

```text
python tools/export_pipeline.py --output-root <기존 예화창고 루트>
python tools/export_pipeline.py --output-root <기존 예화창고 루트> --apply
```

일반 실행의 소유자 ID는 기존 `READDAM_OWNER_EMAIL`과 정확히 일치하는 `profiles` 한 건에서 확인한다. 계정이 없거나 중복이면 중단한다. `--owner-id`는 합성/관리자 검증용이다. 비밀값과 Chunk 본문은 CLI 결과에 출력하지 않는다. `CONFLICT` 또는 `UNMAPPED`가 있으면 `--apply`는 파일을 쓰기 전에 중단한다. DB에서 사라졌으나 index에 남은 **소유** ID는 자동 삭제하지 않는다. 과거 합성 검증처럼 DB에 없고 receipt·분류 manifest·파생 경로도 없는 index 행은 기존 파일이 있을 때만 보존하며, 그 파일을 읽담 소유로 주장하거나 수정하지 않는다. DB 연결 실패나 데이터 변경이 실행 중 발생하면 다음 실행에서 다시 검증한다.

`config/launchd/readdam-export.plist.template`는 **설치되지 않은 템플릿**이다. 절대 경로 세 곳을 실제 Mac 환경에 맞추고, 한 Mac만 exporter로 지정하고, dry-run과 실제 iCloud 사전 검증을 마친 다음 별도 승인으로 활성화한다. `.env`/Secrets는 plist에 넣지 않는다. launchd가 설정된 Python/작업 디렉터리에서 읽을 수 있어야 한다. `StartInterval=300`은 변경을 5분 간격으로 확인하는 구조이며 실시간 DB 이벤트 구독은 아니다. 중복 실행은 로컬 잠금으로 거부한다. iCloud 장치 간 동시 exporter 잠금은 제공하지 않는다.

현재 미완료: 운영 DB READ ONLY 접근, 실제 사용자 승인 태그가 있는 Chunk의 운영 dry-run, 실제 iCloud write와 launchd 설치 승인·검증. 이 문서는 운영 활성화 승인이 아니다.
