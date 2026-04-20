# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

이 파일은 Claude Code (claude.ai/code)가 이 저장소에서 작업할 때 참고하는 가이드입니다.

## 명령어

```bash
# 의존성 설치
pip install -r requirements.txt

# 앱 실행
streamlit run app.py

# DB 초기화 (삭제 후 샘플 데이터로 재생성)
python db/init_db.py
```

테스트 및 린트 설정은 없습니다.

## 아키텍처

단말 장비의 재고, 대여, 폐기를 관리하는 **Streamlit 멀티페이지 앱**입니다.

### 진입점 및 네비게이션

`app.py`가 유일한 진입점입니다. 시작 시 `ensure_db()`를 호출하고 `st.navigation()`으로 6개 항목(home + 5개 데이터 페이지)을 등록합니다. `home.py`는 안내 페이지입니다.

### 데이터 레이어

- **`db/database.py`** — SQLite 연결 관리자. `get_conn()`은 모든 쿼리에서 사용하는 컨텍스트 매니저입니다. `ensure_db()`는 앱 시작 시 DB를 자동 초기화하거나 마이그레이션합니다. 마이그레이션은 `db/schema.sql`을 읽어 기존 컬럼과 비교 후 누락된 컬럼에 `ALTER TABLE`을 실행합니다.
- **`db/schema.sql`** — DB 스키마의 원본. `_iter_missing_columns()`가 이 파일을 파싱해 스키마 차이를 감지합니다.
- **`db/dut.db`** — SQLite DB 파일. 최초 실행 시 생성됩니다 (git에 커밋되지 않음).
- **`db/init_db.py`** — 스키마로 DB를 생성하고 샘플 데이터를 삽입합니다. 직접 실행(`python db/init_db.py`)하면 초기화됩니다.

### 쿼리 레이어

- **`queries/equipment.py`** — 단말 CRUD 및 조회 쿼리 전담. `@st.cache_data(ttl=300)` 사용. 쓰기 작업 후 `_clear_equipment_cache()`로 관련 캐시를 모두 무효화합니다.
- **`queries/rentals.py`** — 대여 CRUD. `add_rental`과 `return_rental`은 `equipment.status`를 `'rented'` / `'available'`로 갱신하고 `_clear_equipment_cache()`를 호출합니다.

### UI 레이어

- **`pages/`** — 페이지당 파일 1개. 각 페이지는 `queries/`와 `components/`에서 직접 임포트합니다.
- **`components/charts.py`** — Plotly 차트 팩토리 함수 모음. DataFrame을 받아 Plotly figure를 반환합니다.
- **`pages/3_part.py`** — 파트별 현황 페이지. 단말 추가(개별/CSV 일괄), 이관·미사용·고장 처리, 폐기 예정 확인을 모두 담당하는 가장 복잡한 페이지입니다.

### 단말 상태 생명주기

```
available → rented    (add_rental)
rented    → available (return_rental)
available → available (remove_equipment reason='이관' — team_id만 변경)
available → broken    (remove_equipment reason='고장')
available → retired   (remove_equipment reason='미사용')
broken/retired → disposed=1 (dispose_equipment)
disposed=1 → disposed=0    (restore_equipment — 폐기 대기로 복원)
```

`status IN ('broken', 'retired')` 이고 `disposed=0`인 단말이 폐기 대기 목록(`pages/5_disposal.py`)에 표시됩니다.

### 모델 명명 규칙

`pages/3_part.py`의 모델 생성 다이얼로그 기준:
- **E단말**: `{A종류}_{W종류}` — A종류: A/B/C, W종류: R/V (예: `A_R`, `C_V`)
- **M단말**: `{단말타입}_{단말구분}` — 타입: S620A/A455A/A465A, 구분: OV1/OV2/CV1/CV2 (예: `S620A_OV1`)

### 캐시 무효화 패턴

모든 `@st.cache_data` 함수는 쓰기 후 `.clear()`를 직접 호출해 무효화합니다. `queries/equipment.py`의 `_clear_equipment_cache()`가 공통 헬퍼 역할을 합니다. 캐시 클리어 후 페이지에서 `st.rerun()`을 호출해 UI를 갱신합니다.
