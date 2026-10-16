from datetime import datetime
import os
import sqlite3
import streamlit as st

# --- XÁC ĐỊNH ĐƯỜNG DẪN DATABASE AN TOÀN ---
if os.path.exists("/mount/src"):
  DB_PATH = "/tmp/clinical_notes.db"
else:
  DB_PATH = "clinical_notes.db"


# --- 1. KHỞI TẠO CƠ SỞ DỮ LIỆU SQLITE ---
def init_db():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  # Bảng lưu ca lâm sàng
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

  # Bảng mới: Lưu sách / Y văn kinh điển / Điều khoản
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS classical_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT,
            clause_info TEXT,
            content TEXT,
            application TEXT
        )
    """)

  # Bảng mới: Lưu ghi chú Dược liệu
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS herbs_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            herb_name TEXT,
            properties TEXT,
            channels TEXT,
            clinical_notes TEXT
        )
    """)

  conn.commit()
  conn.close()


init_db()

# --- 2. GIAO DIỆN STREAMLIT (TIẾNG TRUNG) ---
st.set_page_config(
    page_title="中醫臨床記事簿與知識庫", page_icon="🌿", layout="wide"
)

st.title("🌿 中醫臨床個案管理與知識庫")
st.markdown("記錄患者病案、辨證論治及積累個人臨床經驗的智慧系統。")

# 側邊欄導航
menu = st.sidebar.selectbox(
    "選擇功能",
    ["📚 臨床知識與目錄", "✍️ 記錄新個案", "🔍 臨床個案檢索"],
)

# --- CHỨC NĂNG 1: THÊM CA LÂM SÀNG MỚI ---
if menu == "✍️ 記錄新個案":
  st.header("✍️ 記錄臨床實時個案")

  with st.form("clinical_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
      patient_name = st.text_input("患者姓名 (或病歷號)")
    with col2:
      age = st.text_input("年齡")
    with col3:
      gender = st.selectbox("性別", ["男", "女"])

    date = st.date_input("就診日期", datetime.now())

    symptoms = st.text_area("四診合參 (望、聞、問、切：症狀、脈象、舌苔等)")
    diagnosis = st.text_area("辨證論治 (八綱、臟腑 / 六經辨證)")
    prescription = st.text_area("方藥 (主方及加減藥味)")
    notes = st.text_area("跟診心得 / 醫案按語 (個人臨床筆記)")

    submitted = st.form_submit_button("儲存病案")

    if submitted:
      if patient_name and symptoms:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
                    INSERT INTO cases (date, patient_name, age, gender, symptoms, diagnosis, prescription, notes)
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
        st.success("已成功儲存臨床個案！")
      else:
        st.warning("請至少填寫患者姓名與四診症狀。")

# --- CHỨC NĂNG 2: TÌM KIẾM & ÔN TẬP CA BỆNH ---
elif menu == "🔍 臨床個案檢索":
  st.header("🔍 歷史個案列表與檢索")

  search_keyword = st.text_input(
      "輸入關鍵字搜尋 (患者姓名、症狀、方劑、按語...):"
  )

  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()

  if search_keyword:
    cursor.execute(
        """
            SELECT * FROM cases 
            WHERE patient_name LIKE ? OR symptoms LIKE ? OR prescription LIKE ? OR notes LIKE ?
            ORDER BY date DESC
        """,
        (
            f"%{search_keyword}%",
            f"%{search_keyword}%",
            f"%{search_keyword}%",
            f"%{search_keyword}%",
        ),
    )
  else:
    cursor.execute("SELECT * FROM cases ORDER BY date DESC")

  rows = cursor.fetchall()
  conn.close()

  st.write(f"共找到 **{len(rows)}** 筆符合的臨床個案。")

  for row in rows:
    with st.expander(
        f"📅 {row[1]} | 患者: {row[2]} (年齡: {row[3]}, 性別: {row[4]})"
    ):
      st.markdown(f"**四診記錄：** {row[5]}")
      st.markdown(f"**辨證論治：** {row[6]}")
      st.markdown(f"**處方加減：** {row[7]}")
      st.markdown(f"**心得按語：** {row[8]}")

# --- CHỨC NĂNG 3: KHO TRI THỨC, SÁCH & DƯỢC LIỆU ---
elif menu == "📚 臨床知識與目錄":
  st.header("📚 醫文經典與中藥知識庫")

  tab1, tab2 = st.tabs(["📖 經方與古典條文", "🌿 中藥性味歸經"])

  # --- TAB 1: THÊM VÀ TRA CỨU SÁCH / KINH ĐIỂN ---
  with tab1:
    st.subheader("📖 新增與檢索經典條文 / 醫書筆記")

    # Form thêm sách / điều khoản mới
    with st.form("book_form"):
      st.markdown("##### ➕ 新增條文 / 書籍筆記")
      b_name = st.text_input(
          "書名 / 篇名 (例如：《傷寒論》、《金匱要略》、溫病學)"
      )
      b_clause = st.text_input("條文編號 / 專題 (例如：第 96 條、柴歸湯體質)")
      b_content = st.text_area("經文原文 / 核心內容")
      b_app = st.text_area("個人臨床應用體會 / 老師傳授心得")

      book_submitted = st.form_submit_button("儲存經典筆記")

      if book_submitted:
        if b_name and b_content:
          conn = sqlite3.connect(DB_PATH)
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO classical_books (book_name, clause_info, content, application)
                        VALUES (?, ?, ?, ?)
                    """,
              (b_name, b_clause, b_content, b_app),
          )
          conn.commit()
          conn.close()
          st.success("已成功儲存經典筆記！")
        else:
          st.warning("請填寫書名與經文內容。")

    st.markdown("---")
    st.subheader("🔍 已儲存的經典條文列表")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classical_books ORDER BY id DESC")
    books = cursor.fetchall()
    conn.close()

    for b in books:
      with st.expander(
          f"📖 書名: {b[1]} | 標籤/條文: {b[2] if b[2] else '一般筆記'}"
      ):
        st.markdown(f"**原文/內容：** {b[3]}")
        st.markdown(f"**臨床應用體會：** {b[4]}")

  # --- TAB 2: THÊM VÀ TRA CỨU DƯỢC LIỆU ---
  with tab2:
    st.subheader("🌿 新增與檢索中藥 / 科學中藥筆記")

    with st.form("herb_form"):
      st.markdown("##### ➕ 新增藥物心得")
      h_name = st.text_input(
          "藥名 (例如：柴胡、黃芩、科學中藥荊防敗毒散)"
      )
      h_props = st.text_input("性味 (例如：苦、微寒)")
      h_channels = st.text_input("歸經 (例如：肝、膽經)")
      h_notes = st.text_area("功效與臨床使用心得 / 劑量經驗")

      herb_submitted = st.form_submit_button("儲存藥物筆記")

      if herb_submitted:
        if h_name:
          conn = sqlite3.connect(DB_PATH)
          cursor = conn.cursor()
          cursor.execute(
              """
                        INSERT INTO herbs_notes (herb_name, properties, channels, clinical_notes)
                        VALUES (?, ?, ?, ?)
                    """,
              (h_name, h_props, h_channels, h_notes),
          )
          conn.commit()
          conn.close()
          st.success("已成功儲存藥物筆記！")
        else:
          st.warning("請填寫藥名。")

    st.markdown("---")
    st.subheader("🔍 已儲存的中藥筆記列表")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM herbs_notes ORDER BY id DESC")
    herbs = cursor.fetchall()
    conn.close()

    for h in herbs:
      with st.expander(f"🌿 藥名: {h[1]} (性味: {h[2]} | 歸經: {h[3]})"):
        st.markdown(f"**臨床應用與心得：** {h[4]}")
