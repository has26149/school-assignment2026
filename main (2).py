import json
from pathlib import Path
from typing import Any

import streamlit as st

# ------------------------------------------------------------
# Cafe Seat & Outlet Finder
# Streamlit Cloud entry point: main.py
# Data is shared by sessions on the same running app instance.
# For durable storage across app restarts, connect a database.
# ------------------------------------------------------------

st.set_page_config(
    page_title="카페 자리·콘센트 찾기",
    page_icon="☕",
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("cafe_data.json")
ROWS = 6
COLS = 6

SAMPLE_DATA = {
    "카페 온도": {
        "tables": {
            "T1": {"row": 1, "col": 2, "occupied": True},
            "T2": {"row": 1, "col": 5, "occupied": False},
            "T3": {"row": 3, "col": 2, "occupied": False},
            "T4": {"row": 4, "col": 5, "occupied": True},
            "T5": {"row": 6, "col": 3, "occupied": False},
        },
        "outlets": [{"row": 1, "col": 1}, {"row": 3, "col": 6}, {"row": 6, "col": 5}],
    },
    "커피 정원": {
        "tables": {
            "A": {"row": 2, "col": 2, "occupied": False},
            "B": {"row": 2, "col": 5, "occupied": True},
            "C": {"row": 5, "col": 2, "occupied": False},
        },
        "outlets": [{"row": 1, "col": 3}, {"row": 4, "col": 4}],
    },
}


def load_data() -> dict[str, Any]:
    if not DATA_FILE.exists():
        save_data(SAMPLE_DATA)
        return json.loads(json.dumps(SAMPLE_DATA))
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return json.loads(json.dumps(SAMPLE_DATA))


def save_data(data: dict[str, Any]) -> None:
    temp_file = DATA_FILE.with_suffix(".tmp")
    with temp_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    temp_file.replace(DATA_FILE)


def valid_position(row: int, col: int) -> bool:
    return 1 <= row <= ROWS and 1 <= col <= COLS


if "cafes" not in st.session_state:
    st.session_state.cafes = load_data()
if "selected_table" not in st.session_state:
    st.session_state.selected_table = None
if "admin_unlocked" not in st.session_state:
    st.session_state.admin_unlocked = False


def persist() -> None:
    save_data(st.session_state.cafes)


def render_floor_plan(cafe_name: str, cafe: dict[str, Any], admin: bool = False) -> None:
    tables = cafe.get("tables", {})
    outlets = cafe.get("outlets", [])

    st.caption("🪑 좌석/테이블   ⚡ 콘센트   🟢 이용 가능   🔴 이용 중")
    st.caption("좌석을 누르면 해당 좌석의 이용 상태를 확인할 수 있어요.")

    for r in range(1, ROWS + 1):
        cells = st.columns(COLS, gap="small")
        for c in range(1, COLS + 1):
            with cells[c - 1]:
                table_items = [
                    (table_id, info)
                    for table_id, info in tables.items()
                    if info.get("row") == r and info.get("col") == c
                ]
                has_outlet = any(
                    outlet.get("row") == r and outlet.get("col") == c
                    for outlet in outlets
                )

                if table_items:
                    table_id, info = table_items[0]
                    occupied = bool(info.get("occupied", False))
                    status = "🔴 이용 중" if occupied else "🟢 이용 가능"
                    label = f"🪑 {table_id}" + (" ⚡" if has_outlet else "") + f"\n{status}"
                    clicked = st.button(
                        label,
                        key=f"{'admin' if admin else 'guest'}_{cafe_name}_{table_id}_{r}_{c}",
                        use_container_width=True,
                        type="primary" if occupied else "secondary",
                    )
                    if clicked and not admin:
                        st.session_state.selected_table = (cafe_name, table_id)
                    if (
                        not admin
                        and st.session_state.selected_table == (cafe_name, table_id)
                    ):
                        if occupied:
                            st.error("자리가 없습니다ㅠㅠ", icon="❌")
                        else:
                            st.success("이 자리는 이용할 수 있어요!", icon="✅")
                elif has_outlet:
                    st.markdown(
                        "<div style='height:68px;display:flex;align-items:center;"
                        "justify-content:center;border:1px dashed #D6A84F;"
                        "border-radius:10px;background:#FFF8E8;font-size:25px;'>⚡</div>",
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        "<div style='height:68px;border:1px solid #E8E8E8;"
                        "border-radius:10px;background:#FAFAFA;'></div>",
                        unsafe_allow_html=True,
                    )


st.title("☕ 카페 자리·콘센트 찾기")
st.write("방문하기 전에 카페의 좌석 현황과 콘센트 위치를 확인해 보세요.")

cafes = st.session_state.cafes
if not cafes:
    st.info("등록된 카페가 없습니다. 직원 관리 화면에서 카페를 추가해 주세요.")

tab_customer, tab_staff = st.tabs(["🙋 소비자 화면", "🧑‍💼 직원 관리 화면"])

with tab_customer:
    st.subheader("카페 선택")
    if cafes:
        cafe_names = list(cafes.keys())
        selected_cafe = st.selectbox(
            "확인할 카페를 선택하세요.",
            cafe_names,
            key="customer_cafe_select",
        )
        st.markdown(f"### {selected_cafe}")
        cafe = cafes[selected_cafe]
        available_count = sum(
            1 for info in cafe.get("tables", {}).values()
            if not info.get("occupied", False)
        )
        occupied_count = len(cafe.get("tables", {})) - available_count
        m1, m2, m3 = st.columns(3)
        m1.metric("전체 테이블", len(cafe.get("tables", {})))
        m2.metric("이용 가능", available_count)
        m3.metric("이용 중", occupied_count)
        st.markdown("#### 매장 좌석 배치도")
        render_floor_plan(selected_cafe, cafe, admin=False)
        st.caption("※ 배치도는 직원이 입력한 정보를 바탕으로 표시됩니다.")
    else:
        st.info("먼저 직원이 카페와 좌석 정보를 등록해야 합니다.")

with tab_staff:
    st.subheader("매장 정보 관리")
    required_password = st.secrets.get("ADMIN_PASSWORD", "") if hasattr(st, "secrets") else ""
    if required_password:
        if not st.session_state.admin_unlocked:
            with st.form("admin_login"):
                password = st.text_input("직원 비밀번호", type="password")
                login = st.form_submit_button("로그인")
                if login:
                    if password == required_password:
                        st.session_state.admin_unlocked = True
                        st.rerun()
                    else:
                        st.error("비밀번호가 올바르지 않습니다.")
            st.info("관리자 비밀번호는 Streamlit Cloud의 App settings → Secrets에 ADMIN_PASSWORD로 설정하세요.")
            st.stop()
    else:
        st.warning(
            "현재 직원 관리 화면에 비밀번호가 설정되어 있지 않습니다. "
            "배포 전 Streamlit Cloud Secrets에 ADMIN_PASSWORD를 설정하세요."
        )

    if st.button("직원 로그아웃"):
        st.session_state.admin_unlocked = False
        st.rerun()

    with st.expander("➕ 새 카페 추가", expanded=False):
        with st.form("add_cafe_form"):
            new_cafe = st.text_input("카페 이름", placeholder="예: 햇살 카페")
            add_cafe = st.form_submit_button("카페 추가")
            if add_cafe:
                name = new_cafe.strip()
                if not name:
                    st.error("카페 이름을 입력해 주세요.")
                elif name in st.session_state.cafes:
                    st.error("이미 등록된 카페입니다.")
                else:
                    st.session_state.cafes[name] = {"tables": {}, "outlets": []}
                    persist()
                    st.success(f"'{name}' 카페를 추가했습니다.")
                    st.rerun()

    if st.session_state.cafes:
        staff_cafe = st.selectbox(
            "관리할 카페",
            list(st.session_state.cafes.keys()),
            key="staff_cafe_select",
        )
        cafe = st.session_state.cafes[staff_cafe]
        st.markdown("#### 1. 테이블 등록")
        with st.form("add_table_form"):
            a, b, c = st.columns(3)
            table_id = a.text_input("테이블 이름", placeholder="예: T6")
            table_row = b.number_input("세로 위치 (1~6)", min_value=1, max_value=ROWS, value=1)
            table_col = c.number_input("가로 위치 (1~6)", min_value=1, max_value=COLS, value=1)
            add_table = st.form_submit_button("테이블 추가")
            if add_table:
                table_id = table_id.strip()
                if not table_id:
                    st.error("테이블 이름을 입력해 주세요.")
                elif table_id in cafe["tables"]:
                    st.error("이미 존재하는 테이블 이름입니다.")
                elif any(
                    t.get("row") == table_row and t.get("col") == table_col
                    for t in cafe["tables"].values()
                ):
                    st.error("해당 위치에 이미 테이블이 있습니다.")
                else:
                    cafe["tables"][table_id] = {
                        "row": int(table_row),
                        "col": int(table_col),
                        "occupied": False,
                    }
                    persist()
                    st.success(f"{table_id} 테이블을 추가했습니다.")
                    st.rerun()

        st.markdown("#### 2. 테이블 이용 상태 변경")
        if cafe["tables"]:
            table_ids = list(cafe["tables"].keys())
            chosen_table = st.selectbox("테이블 선택", table_ids, key="status_table_select")
            current = bool(cafe["tables"][chosen_table].get("occupied", False))
            new_status = st.radio(
                "현재 상태",
                ["이용 가능", "이용 중"],
                index=1 if current else 0,
                horizontal=True,
                key=f"status_{staff_cafe}_{chosen_table}",
            )
            if st.button("이용 상태 저장", key="save_status"):
                cafe["tables"][chosen_table]["occupied"] = new_status == "이용 중"
                persist()
                st.success(f"{chosen_table} 상태를 저장했습니다.")
                st.rerun()

            with st.expander("테이블 삭제"):
                delete_table = st.selectbox("삭제할 테이블", table_ids, key="delete_table_select")
                if st.button("선택한 테이블 삭제", type="secondary"):
                    del cafe["tables"][delete_table]
                    persist()
                    st.success("테이블을 삭제했습니다.")
                    st.rerun()
        else:
            st.info("등록된 테이블이 없습니다.")

        st.markdown("#### 3. 콘센트 위치 등록")
        with st.form("add_outlet_form"):
            x, y = st.columns(2)
            outlet_row = x.number_input("콘센트 세로 위치 (1~6)", min_value=1, max_value=ROWS, value=1, key="outlet_row")
            outlet_col = y.number_input("콘센트 가로 위치 (1~6)", min_value=1, max_value=COLS, value=1, key="outlet_col")
            add_outlet = st.form_submit_button("콘센트 위치 추가")
            if add_outlet:
                pos = {"row": int(outlet_row), "col": int(outlet_col)}
                if pos in cafe["outlets"]:
                    st.error("이미 등록된 콘센트 위치입니다.")
                else:
                    cafe["outlets"].append(pos)
                    persist()
                    st.success("콘센트 위치를 추가했습니다.")
                    st.rerun()

        if cafe["outlets"]:
            outlet_labels = [
                f"{i + 1}. {o['row']}행 {o['col']}열"
                for i, o in enumerate(cafe["outlets"])
            ]
            outlet_to_remove = st.selectbox(
                "삭제할 콘센트 위치",
                range(len(outlet_labels)),
                format_func=lambda i: outlet_labels[i],
                key="remove_outlet_select",
            )
            if st.button("선택한 콘센트 삭제"):
                cafe["outlets"].pop(outlet_to_remove)
                persist()
                st.success("콘센트 위치를 삭제했습니다.")
                st.rerun()

        st.markdown("#### 4. 현재 배치도 미리보기")
        render_floor_plan(staff_cafe, cafe, admin=True)

        st.markdown("#### 5. 카페 삭제")
        with st.expander("카페 삭제"):
            st.warning("카페를 삭제하면 해당 카페의 테이블과 콘센트 정보도 함께 삭제됩니다.")
            confirm_delete = st.checkbox(f"'{staff_cafe}' 카페를 삭제하는 데 동의합니다.")
            if st.button("이 카페 삭제", disabled=not confirm_delete):
                del st.session_state.cafes[staff_cafe]
                persist()
                st.success("카페를 삭제했습니다.")
                st.rerun()

st.divider()
st.caption("좌석 배치도는 6×6 격자 기준입니다. 직원이 실제 매장 구조에 맞게 테이블과 콘센트 위치를 입력해 주세요.")
