"""DB 초기화 + 샘플 데이터 삽입 (최초 1회 실행)"""
import pathlib
import sqlite3

DB_PATH = pathlib.Path(__file__).parent / "dut.db"
SCHEMA_PATH = pathlib.Path(__file__).parent / "schema.sql"


def init():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    # 샘플 모델
    models = [
        ("Galaxy S24",),
        ("Galaxy S24 Ultra",),
        ("Pixel 9 Pro",),
        ("iPhone 16",),
        ("iPhone 16 Pro",),
        ("iPad Pro 13",),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO models(name) VALUES(?)", models
    )

    # 샘플 팀
    teams = [("Alpha팀",), ("Beta팀",), ("Gamma팀",), ("Delta팀",)]
    conn.executemany("INSERT OR IGNORE INTO teams(name) VALUES(?)", teams)

    conn.commit()

    # 샘플 단말 (모델·팀 ID 참조)
    cur = conn.cursor()
    model_ids = {r[1]: r[0] for r in cur.execute("SELECT id, name FROM models")}
    team_ids = {r[1]: r[0] for r in cur.execute("SELECT id, name FROM teams")}

    equipment = [
        # (model_name, serial_no, owner, registered_at, status, team_name)
        ("Galaxy S24", "SN-S24-001", "홍길동", "2025-01-10", "available", "Alpha팀"),
        ("Galaxy S24", "SN-S24-002", "이순신", "2025-01-11", "available", "Alpha팀"),
        ("Galaxy S24", "SN-S24-003", "강감찬", "2025-01-12", "available", "Beta팀"),
        ("Galaxy S24 Ultra", "SN-S24U-001", "유관순", "2025-02-01", "available", "Beta팀"),
        ("Galaxy S24 Ultra", "SN-S24U-002", "김유신", "2025-02-02", "broken", "Beta팀"),
        ("Pixel 9 Pro", "SN-PX9-001", "세종대왕", "2025-03-05", "available", "Gamma팀"),
        ("Pixel 9 Pro", "SN-PX9-002", "을지문덕", "2025-03-06", "available", "Gamma팀"),
        ("Pixel 9 Pro", "SN-PX9-003", "장보고", "2025-03-07", "available", "Alpha팀"),
        ("iPhone 16", "SN-IP16-001", "신사임당", "2025-04-01", "available", "Delta팀"),
        ("iPhone 16", "SN-IP16-002", "이황", "2025-04-02", "available", "Delta팀"),
        ("iPhone 16", "SN-IP16-003", "이이", "2025-04-03", "available", "Alpha팀"),
        ("iPhone 16 Pro", "SN-IP16P-001", "정약용", "2025-05-10", "available", "Beta팀"),
        ("iPhone 16 Pro", "SN-IP16P-002", "김정호", "2025-05-11", "available", "Gamma팀"),
        ("iPad Pro 13", "SN-IPAD-001", "허준", "2025-06-01", "available", "Delta팀"),
        ("iPad Pro 13", "SN-IPAD-002", "최무선", "2025-06-02", "available", "Gamma팀"),
    ]
    conn.executemany(
        "INSERT OR IGNORE INTO equipment"
        "(model_id, serial_no, owner, registered_at, status, team_id) VALUES(?,?,?,?,?,?)",
        [
            (model_ids[m], sn, owner, reg_dt, status, team_ids[t])
            for m, sn, owner, reg_dt, status, t in equipment
        ],
    )

    # 샘플 대여 기록
    rentals = [
        # (serial_no, borrower_team, borrower_name, borrowed_at, expected_return)
        ("SN-S24-002", "Alpha팀", "홍길동", "2026-03-20 09:00", "2026-04-05"),
        ("SN-S24U-001", "Beta팀", "이순신", "2026-03-25 10:00", "2026-04-10"),
        ("SN-PX9-002", "Gamma팀", "강감찬", "2026-03-28 13:00", "2026-04-07"),
        ("SN-IP16-002", "Delta팀", "유관순", "2026-03-30 14:00", "2026-04-08"),
        ("SN-IP16P-001", "Beta팀", "김유신", "2026-03-31 09:30", "2026-04-15"),
        ("SN-IPAD-002", "Gamma팀", "세종대왕", "2026-04-01 08:00", "2026-04-14"),
    ]
    eq_ids = {
        r[0]: r[1]
        for r in cur.execute("SELECT serial_no, id FROM equipment")
    }
    conn.executemany(
        "INSERT OR IGNORE INTO rentals"
        "(equipment_id, borrower_team, borrower_name, borrowed_at, expected_return)"
        " VALUES(?,?,?,?,?)",
        [
            (eq_ids[sn], team_ids[t], name, ba, er)
            for sn, t, name, ba, er in rentals
        ],
    )

    # 샘플 멤버
    members = [
        ("홍길동",), ("이순신",), ("강감찬",), ("유관순",), ("김유신",),
        ("세종대왕",), ("을지문덕",), ("장보고",), ("신사임당",), ("이황",),
        ("이이",), ("정약용",), ("김정호",), ("허준",), ("최무선",),
    ]
    conn.executemany("INSERT OR IGNORE INTO members(name) VALUES(?)", members)

    conn.commit()
    conn.close()
    print("DB 초기화 완료:", DB_PATH)


if __name__ == "__main__":
    init()
