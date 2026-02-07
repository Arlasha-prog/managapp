import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import io

# --- 1. НАСТРОЙКИ ---
st.set_page_config(page_title="Teenage CRM Ultra", page_icon="🚀", layout="wide")


def init_db():
    conn = sqlite3.connect('teenage_crm.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (username TEXT PRIMARY KEY, password TEXT, role TEXT, name TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS deals 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, manager TEXT, client_phone TEXT, 
                  services TEXT, total_price TEXT, comments TEXT, status TEXT, history TEXT, date TEXT)''')

    # Создаем админа, если его еще нет
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute("INSERT INTO users VALUES ('admin', 'admin123', 'admin', 'Главный Босс')")
    conn.commit()
    return conn


# --- 2. УСЛУГИ И ЦЕНЫ ---
SERVICES_DATA = [
    {"id": "1a", "cat": "Клубы", "name": "🎓 Подростковый клуб (Базовый)", "age": (9, 13), "price": 330000, "unit": "₸"},
    {"id": "1b", "cat": "Клубы", "name": "🎓 Подростковый клуб (Расширенный)", "age": (9, 13), "price": 380000,
     "unit": "₸"},
    {"id": "2", "cat": "Обучение", "name": "👔 Школа инструкторов", "age": (16, 22), "price": 270000, "unit": "₸"},
    {"id": "3", "cat": "Лагеря", "name": "🐴 Весенний конный лагерь", "age": (9, 14), "price": 230000, "unit": "₸"},
    {"id": "4", "cat": "Лагеря", "name": "🏔️ Горный лагерь (10 дней)", "age": (13, 17), "price": 350000, "unit": "₸"},
    {"id": "5", "cat": "Лагеря", "name": "🌊 Алаколь 'Морские Волки'", "age": (10, 17), "price": 350000, "unit": "₸"},
    {"id": "6", "cat": "Тур", "name": "🇨🇾 Тур на КИПР (Программа)", "age": (10, 17), "price": 1500, "unit": "€"},
    {"id": "7", "cat": "Фест", "name": "🎣 Рыбалка (Отдых)", "age": (0, 99), "price": 15000, "unit": "₸"},
    {"id": "7.1", "cat": "Фест", "name": "🎣 Рыбалка (Профи со снастями)", "age": (0, 99), "price": 24000, "unit": "₸"},
    {"id": "7.2", "cat": "Фест", "name": "🎣 Рыбалка (+ Аренда удочек)", "age": (0, 99), "price": 30000, "unit": "₸"},
    {"id": "8", "cat": "Фест", "name": "🎈 Катание на баллонах", "age": (0, 99), "price": 25000, "unit": "₸"},
    {"id": "9", "cat": "Фест", "name": "🥾 Поход в Горы (Горельник)", "age": (0, 99), "price": 10000, "unit": "₸"},
    {"id": "10", "cat": "Фест", "name": "👨‍👩‍👧‍👦 Семейный пакет (Фест)", "age": (0, 99), "price": 15000, "unit": "₸"},
]


# --- 3. ФУНКЦИИ УПРАВЛЕНИЯ ---
def update_status(deal_id, new_status):
    conn = init_db()
    dt = datetime.now().strftime("%d.%m %H:%M")
    res = conn.execute("SELECT history FROM deals WHERE id=?", (deal_id,)).fetchone()
    curr_h = res[0] if res else ""
    new_h = curr_h + f"[{dt}] Статус: {new_status}\n"
    conn.execute("UPDATE deals SET status=?, history=? WHERE id=?", (new_status, new_h, deal_id))
    conn.commit()
    conn.close()


# --- 4. СТРАНИЦА СДЕЛКИ ---
def show_deal_page(deal_id):
    if st.button("⬅️ Назад к списку"):
        del st.session_state.active_deal_id
        st.rerun()

    conn = init_db()
    deal = pd.read_sql_query(f"SELECT * FROM deals WHERE id={deal_id}", conn).iloc[0]
    conn.close()

    st.title(f"Сделка #{deal_id}")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.info(f"Клиент: {deal['client_phone']}")
        st.write(f"**Услуги:** {deal['services']}")
        st.write(f"**Сумма:** {deal['total_price']}")
        st.text_area("История логов", deal['history'], height=200)
    with c2:
        st.subheader("Действие")
        ns = st.selectbox("Новый статус", ["🆕 Новая", "Не дозвон", "Переписка", "Отказ", "ПРОДАНО"])
        if st.button("Обновить"):
            update_status(deal_id, ns)
            st.success("Готово")
            st.rerun()


# --- 5. ЭКРАН ПРОДАЖ ---
def sales_desk():
    if 'active_deal_id' in st.session_state:
        show_deal_page(st.session_state.active_deal_id)
        return

    st.title("📞 Новая продажа")
    with st.expander("📝 ОФОРМИТЬ ЗАЯВКУ", expanded=True):
        ph = st.text_input("Телефон клиента")
        comm = st.text_area("Заметки")
        age = st.slider("Возраст клиента", 0, 25, 12)

        if 'cart' not in st.session_state: st.session_state.cart = []

        available = [s for s in SERVICES_DATA if s["age"][0] <= age <= s["age"][1]]
        cols = st.columns(3)
        for i, srv in enumerate(available):
            with cols[i % 3]:
                if st.button(f"{srv['name']}\n{srv['price']}{srv['unit']}", key=f"s_{srv['id']}"):
                    st.session_state.cart.append(srv)

        if st.session_state.cart:
            st.divider()
            sum_t = sum(x['price'] for x in st.session_state.cart if x['unit'] == '₸')
            sum_e = sum(x['price'] for x in st.session_state.cart if x['unit'] == '€')
            summary = ", ".join([x['name'] for x in st.session_state.cart])
            price_str = f"{sum_t:,} ₸" + (f" + {sum_e:,} €" if sum_e > 0 else "")

            st.write(f"**Итого:** {price_str}")
            if st.button("🚀 СОХРАНИТЬ СДЕЛКУ", type="primary"):
                if ph:
                    conn = init_db()
                    dt = datetime.now().strftime("%Y-%m-%d %H:%M")
                    hist = f"[{dt}] Создано: {st.session_state.username}"
                    conn.execute(
                        "INSERT INTO deals (manager, client_phone, services, total_price, comments, status, history, date) VALUES (?,?,?,?,?,?,?,?)",
                        (st.session_state.username, ph, summary, price_str, comm, "🆕 Новая", hist, dt))
                    conn.commit()
                    st.session_state.cart = []
                    st.success("Успех!")
                    st.rerun()

    st.divider()
    st.subheader("🗂 Последние сделки")
    conn = init_db()
    df = pd.read_sql_query(f"SELECT * FROM deals ORDER BY id DESC LIMIT 10", conn)
    for i, row in df.iterrows():
        with st.container(border=True):
            c1, c2, c3 = st.columns([3, 2, 1])
            c1.write(f"**{row['client_phone']}** | {row['manager']}")
            c2.write(f"Статус: `{row['status']}`")
            if c3.button("Открыть 🔍", key=f"op_{row['id']}"):
                st.session_state.active_deal_id = row['id']
                st.rerun()
    conn.close()


# --- 6. АДМИН-ПАНЕЛЬ ---
def admin_dashboard():
    st.title("👑 Панель управления")
    t1, t2, t3 = st.tabs(["📊 Аналитика", "👥 Команда", "📂 Все сделки"])

    conn = init_db()
    with t1:
        df = pd.read_sql_query("SELECT * FROM deals", conn)
        if not df.empty:
            st.plotly_chart(px.pie(df, names='status', title="Статистика по статусам"))
            st.metric("Всего сделок", len(df))

    with t2:
        st.subheader("Сотрудники")
        users = pd.read_sql_query("SELECT * FROM users", conn)
        st.dataframe(users, use_container_width=True)
        with st.form("new_u"):
            u = st.text_input("Логин")
            p = st.text_input("Пароль")
            n = st.text_input("Имя")
            r = st.selectbox("Роль", ["manager", "admin"])
            if st.form_submit_button("Добавить сотрудника"):
                conn.execute("INSERT INTO users VALUES (?,?,?,?)", (u, p, r, n))
                conn.commit()
                st.rerun()

    with t3:
        all_deals = pd.read_sql_query("SELECT * FROM deals ORDER BY id DESC", conn)
        st.dataframe(all_deals, use_container_width=True)
    conn.close()


# --- 7. ГЛАВНЫЙ ЦИКЛ ---
def main():
    if 'logged_in' not in st.session_state:
        st.title("Teenage CRM 🎧")
        u = st.text_input("Логин")
        p = st.text_input("Пароль", type="password")
        if st.button("Войти"):
            conn = init_db()
            user = conn.execute("SELECT * FROM users WHERE username=? AND password=?", (u, p)).fetchone()
            if user:
                st.session_state.update({"logged_in": True, "username": u, "role": user[2], "name": user[3]})
                st.rerun()
            else:
                st.error("Ошибка входа")
    else:
        st.sidebar.title(f"👾 {st.session_state.name}")
        if st.sidebar.button("Выход"):
            st.session_state.clear()
            st.rerun()

        # ВОЗВРАЩАЕМ ПЕРЕКЛЮЧАТЕЛЬ ДЛЯ АДМИНА
        if st.session_state.role == 'admin':
            page = st.sidebar.radio("Навигация", ["Админка", "Продажи"])
            if page == "Админка":
                admin_dashboard()
            else:
                sales_desk()
        else:
            sales_desk()


if __name__ == "__main__":
    init_db()
    main()
