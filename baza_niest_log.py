import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide")

# --- STYLE CSS (Tło, Niebieskie Czcionki) ---
st.markdown("""
    <style>
    /* Główne tło */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    
    /* WSZYSTKIE CZCIONKI NA NIEBIESKO */
    html, body, [class*="st-"] {
        color: #0000FF !important;
    }
    
    h1, h2, h3, h4, h5, h6, p, label {
        color: #0000FF !important;
        font-weight: bold;
    }

    /* Karty KPI - ramka i tekst niebieski */
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        padding: 15px; border-radius: 10px; border: 2px solid #0000FF;
    }
    
    /* Wartości i etykiety w KPI */
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { 
        color: #0000FF !important; 
    }

    /* Napisy w zakładkach (Tabs) */
    button[data-baseweb="tab"] p {
        color: #0000FF !important;
    }
    
    /* Pasek boczny i expandery */
    .stExpander { 
        background-color: rgba(255, 255, 255, 0.9) !important; 
        border: 1px solid #0000FF !important; 
    }
    </style>
    """, unsafe_allow_html=True)

def get_data():
    try:
        p_res = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        k_res = supabase.table("kategorie").select("*").execute()
        return p_res.data, k_res.data
    except Exception as e:
        st.error(f"Problem z połączeniem: {e}")
        return [], []

prod_data, kat_data = get_data()

st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

# --- SEKCJA WIZUALIZACJI ---
if prod_data:
    df = pd.DataFrame(prod_data)
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    df['liczba'] = pd.to_numeric(df['liczba'], errors='coerce').fillna(0)
    df['cena'] = pd.to_numeric(df['cena'], errors='coerce').fillna(0)
    df['stan_minimalny'] = pd.to_numeric(df.get('stan_minimalny', 5), errors='coerce').fillna(5)
    
    # KPI - Teraz będą niebieskie dzięki CSS
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    c2.metric("💰 Wartość", f"{round((df['liczba'] * df['cena']).sum(), 2)} zł")
    c3.metric("⚠️ Alerty", len(df[df['liczba'] < df['stan_minimalny']]))
    c4.metric("📂 Kategorie", len(kat_data))

    # WYKRESY
    col_l, col_r = st.columns([1, 1.5])
    with col_l:
        fig_pie = px.pie(df, values='liczba', names='kategoria_nazwa', hole=0.4, title="Udział kategorii (%)")
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_r:
        fig_bar = px.bar(df, x='nazwa', y='liczba', color='kategoria_nazwa', title="Stan na magazynie")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📋 Lista Produktów")
    st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena']], use_container_width=True)
else:
    st.info("Magazyn jest pusty. Dodaj dane poniżej.")

st.divider()

# --- SEKCJA OPERACJI ---
t1, t2, t3 = st.tabs(["🆕 Produkty", "🚚 Dostawa", "📂 Kategorie"])

with t3:
    st.subheader("Dodaj Kategorię")
    with st.form("k_form"):
        new_k = st.text_input("Nazwa nowej kategorii")
        if st.form_submit_button("Dodaj Kategorię"):
            if new_k:
                supabase.table("kategorie").insert({"nazwa": new_k}).execute()
                st.success(f"Dodano: {new_k}")
                st.rerun()

with t1:
    st.subheader("Dodaj Produkt")
    if not kat_data:
        st.warning("Najpierw dodaj kategorię!")
    else:
        with st.form("p_form"):
            n = st.text_input("Nazwa produktu")
            q = st.number_input("Ilość", min_value=0, value=0)
            ms = st.number_input("Stan min.", min_value=0, value=5)
            p = st.number_input("Cena", min_value=0.0, value=0.0)
            k_map = {k['nazwa']: k['id'] for k in kat_data}
            k_sel = st.selectbox("Kategoria", options=list(k_map.keys()))
            if st.form_submit_button("Zapisz Produkt"):
                supabase.table("produkty").insert({
                    "nazwa": n, "liczba": q, "stan_minimalny": ms, 
                    "cena": p, "kategoria_id": k_map[k_sel]
                }).execute()
                st.rerun()

with t2:
    st.subheader("Szybka Dostawa")
    if prod_data:
        p_list = [p['nazwa'] for p in prod_data]
        p_name = st.selectbox("Wybierz produkt", options=p_list)
        amount = st.number_input("Dodaj sztuk", min_value=1)
        if st.button("Aktualizuj stan"):
            row = next(item for item in prod_data if item["nazwa"] == p_name)
            new_q = int(row['liczba']) + amount
            supabase.table("produkty").update({"liczba": new_q}).eq("id", row['id']).execute()
            st.rerun()
