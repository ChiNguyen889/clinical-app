from datetime import datetime
import sqlite3
import streamlit as st

# --- 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE ---
def init_db():
  conn = sqlite3.connect("clinical_notes.db")
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            patient_name TEXT,
            age TEXT,
            gender TEXT,
            symptoms TEXT,
            diagnosis TEXT,
            prescription TEXT,
            notes TEXT
        )
    """)
  conn.commit()
  conn.close()


init_db()

# --- 2. GIAO DIỆN STREAMLIT (TIẾNG TRUNG) ---
st.set_page_config(
    page_title="中醫臨床記事簿", page_icon="🌿", layout="wide"
)

st.title("🌿 中醫臨床個案管理與知識庫")
st.markdown("記錄患者病案、辨證論治及累積個人臨床經驗的智慧系統。")

# Thanh điều hướng bên trái (Sidebar)
menu = st.sidebar.selectbox(
    "選擇功能", ["📚 臨床個案檢索", "✍️ 記錄新個案", "🔍 搜尋與複習"]
)

# --- CHỨC NĂNG 1: THÊM CA LÂM SÀNG MỚI ---
if menu == "✍️ 記錄新個案":
  st.header("✍️ 臨床望聞問切與診療記錄")

  with st.form("clinical_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
      patient_name = st.text_input("患者姓名 (或代號)")
    with col2:
      age = st.text_input("年齡")
    with col3:
      gender = st.selectbox("性別", ["男", "女"])

    date = st.date_input("就診日期", datetime.now())

    symptoms = st.text_area(
        "四診記錄 (望、聞、問、切：主訴、舌象、脈象...)"
    )
    diagnosis = st.text_area("辨證論治 (病機分析、八綱/臟腑/六經辨證)")
    prescription = st.text_area("方藥 (治法、方劑名稱與加減)")
    notes = st.text_area("醫囑與心得筆記 (療效追蹤、心得體會)")

    submitted = st.form_submit_button("💾 儲存個案")

    if submitted:
      if patient_name and symptoms:
        conn = sqlite3.connect("clinical_notes.db")
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO cases (date, patient_name, age, gender,"
            " symptoms, diagnosis, prescription, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
            (
                str(date),
                patient_name,
                age,
                gender,
                symptoms,
                diagnosis,
                prescription,
                notes,
            ),
        )
        conn.commit()
        conn.close()
        st.success("✅ 個案儲存成功！")
      else:
        st.warning("⚠️ 請至少填寫「患者姓名」與「四診記錄」。")

# --- CHỨC NĂNG 2: TRA CỨU & XEM DANH SÁCH ---
elif menu == "📚 臨床個案檢索":
  st.header("📚 歷史個案列表")

  conn = sqlite3.connect("clinical_notes.db")
  cursor = conn.cursor()
  cursor.execute(
      "SELECT id, date, patient_name, age, gender, diagnosis FROM cases ORDER"
      " BY id DESC"
  )
  cases = cursor.fetchall()
  conn.close()

  if not cases:
    st.info("目前尚無記錄任何個案，請先前往「記錄新個案」新增。")
  else:
    for row in cases:
      case_id, c_date, c_name, c_age, c_gender, c_diag = row
      with st.expander(
          f"📅 {c_date} | 👤 {c_name} ({c_age}歲, {c_gender}) - 診斷: {c_diag[:30]}..."
      ):
        # Lấy thông tin chi tiết
        conn = sqlite3.connect("clinical_notes.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        details = cursor.fetchone()
        conn.close()

        st.markdown(f"**就診日期：** {details[1]}")
        st.markdown(f"**患者資訊：** {details[2]} | {details[3]}歲 | {details[4]}")
        st.markdown(f"**四診記錄：**\n> {details[5]}")
        st.markdown(f"**辨證論治：**\n> {details[6]}")
        st.markdown(f"**方藥處方：**\n> {details[7]}")
        st.markdown(f"**醫囑筆記：**\n> {details[8]}")

        if st.button(f"🗑️ 刪除此個案 (ID: {case_id})", key=f"del_{case_id}"):
          conn = sqlite3.connect("clinical_notes.db")
          cursor = conn.cursor()
          cursor.execute("DELETE FROM cases WHERE id = ?", (case_id,))
          conn.commit()
          conn.close()
          st.rerun()

# --- CHỨC NĂNG 3: TÌM KIẾM ---
elif menu == "🔍 搜尋與複習":
  st.header("🔍 智能關鍵字檢索")
  keyword = st.text_input(
      "輸入關鍵字 (例如：柴胡、脈弦滑、頭痛、失眠...)"
  )

  if keyword:
    conn = sqlite3.connect("clinical_notes.db")
    cursor = conn.cursor()
    query = """
            SELECT id, date, patient_name, symptoms, diagnosis, prescription 
            FROM cases 
            WHERE symptoms LIKE ? OR diagnosis LIKE ? OR prescription LIKE ? OR notes LIKE ?
        """
    like_kw = f"%{keyword}%"
    cursor.execute(query, (like_kw, like_kw, like_kw, like_kw))
    results = cursor.fetchall()
    conn.close()

    st.subheader(f"找到 {len筆 := len(results)} 筆相關個案：")
    for row in results:
      c_id, c_date, c_name, c_sym, c_diag, c_pres = row
      st.markdown(f"---")
      st.markdown(f"**日期：** {c_date} | **患者：** {c_name}")
      st.markdown(f"**主訴/四診：** {c_sym}")
      st.markdown(f"**辨證：** {c_diag}")
      st.markdown(f"**方劑：** {c_pres}")