import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide")

# --- STYLE CSS (Tło, JASNY NIEBIESKI) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    html, body, [class*="st-"], h1, h2, h3, h4, h5, h6, p, label {
        color: #1E90FF !important;
        font-weight: bold;
    }
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        padding: 15px; border-radius: 10px; border: 2px solid #1E90FF;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color: #1E90FF !important; }
    .stExpander { background-color: rgba(255, 255, 255, 0.9) !important; border: 1px solid #1E90FF !important; }
    button[data-baseweb="tab"] p { color: #1E90FF !important; }
    </style>
    """, unsafe_allow_html=True)

def get_data():
    try:
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        st.error(f"Błąd połączenia: {e}")
        return [], []

prod_data, kat_data = get_data()

st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

# --- WIZUALIZACJA ---
if prod_data:
    df = pd.DataFrame(prod_data)
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    df['liczba'] = pd.to_numeric(df['liczba'], errors='coerce').fillna(0)
    df['cena'] = pd.to_numeric(df['cena'], errors='coerce').fillna(0)
    df['stan_minimalny'] = pd.to_numeric(df.get('stan_minimalny', 0), errors='coerce').fillna(0)
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    c2.metric("💰 Wartość", f"{round((df['liczba'] * df['cena']).sum(), 2)} zł")
    alerty = len(df[df['liczba'] < df['stan_minimalny']])
    c3.metric("⚠️ Alerty", f"{alerty} poz.")
    c4.metric("📂 Kategorie", len(kat_data))

    col_l, col_r = st.columns([1, 1.5])
    with col_l:
        st.plotly_chart(px.pie(df, values='liczba', names='kategoria_nazwa', hole=0.4, title="Udział kategorii"), use_container_width=True)
    with col_r:
        st.plotly_chart(px.bar(df, x='nazwa', y=['liczba', 'stan_minimalny'], barmode='group', title="Stan obecny vs Minimum"), use_container_width=True)

    st.subheader("📋 Lista Produktów")
    st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena']], use_container_width=True)
else:
    st.info("Magazyn jest obecnie pusty.")

st.divider()

# --- OPERACJE ---
t1, t2, t3 = st.tabs(["🆕 Produkty", "🚚 Dostawa", "📂 Kategorie"])

with t1:
    st.subheader("Dodaj Nowy Produkt")
    
    # PARAMETR clear_on_submit=True czyści wszystko w momencie kliknięcia przycisku
    with st.form("p_form", clear_on_submit=True):
        n = st.text_input("Nazwa produktu")
        q = st.number_input("Ilość obecna", min_value=0, step=1, value=0)
        min_q = st.number_input("Ilość minimalna (Alert)", min_value=0, step=1, value=5)
        p = st.number_input("Cena", min_value=0.0, step=0.1, value=0.0)
        
        kat_options = [k['nazwa'] for k in kat_data]
        kat_options.append("+ Dodaj nową kategorię...")
        k_sel = st.selectbox("Wybierz kategorię", options=kat_options)
        
        new_kat_input = st.text_input("Nazwa nowej kategorii (jeśli wybrano opcję powyżej)")
        
        if st.form_submit_button("Zapisz Produkt"):
            if not n:
                st.warning("Musisz podać nazwę produktu!")
            else:
                try:
                    final_kat_id = None
                    if k_sel == "+ Dodaj nową kategorię...":
                        if new_kat_input:
                            new_k_res = supabase.table("kategorie").insert({"nazwa": new_kat_input}).execute()
                            final_kat_id = new_k_res.data[0]['id']
                        else:
                            st.error("Wpisz nazwę dla nowej kategorii!")
                            st.stop()
                    else:
                        final_kat_id = next(k['id'] for k in kat_data if k['nazwa'] == k_sel)
                    
                    supabase.table("produkty").insert({
                        "nazwa": n, "liczba": q, "stan_minimalny": min_q, 
                        "cena": p, "kategoria_id": final_kat_id
                    }).execute()
                    
                    st.toast(f"Pomyślnie dodano: {n}", icon='✅')
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd bazy: {e}")

with t2:
    if prod_data:
        with st.form("delivery_form", clear_on_submit=True):
            p_name = st.selectbox("Wybierz produkt", options=[p['nazwa'] for p in prod_data])
            amount = st.number_input("Dodaj ilość", min_value=1, step=1, value=1)
            if st.form_submit_button("Aktualizuj stan"):
                row = next(item for item in prod_data if item["nazwa"] == p_name)
                supabase.table("produkty").update({"liczba": int(row['liczba']) + amount}).eq("id", row['id']).execute()
                st.toast("Stan magazynowy zaktualizowany!", icon='🚚')
                st.rerun()

with t3:
    with st.form("k_form_standalone", clear_on_submit=True):
        nk = st.text_input("Szybkie dodawanie kategorii")
        if st.form_submit_button("Dodaj"):
            if nk:
                supabase.table("kategorie").insert({"nazwa": nk}).execute()
                st.toast(f"Dodano kategorię: {nk}", icon='📂')
                st.rerun()
