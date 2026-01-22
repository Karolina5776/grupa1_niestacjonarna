import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide", initial_sidebar_state="collapsed")

# --- STYLE CSS (Tło, Czerwony Tytuł, Panele) ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    h1 {
        color: #ff0000 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        font-weight: bold;
    }
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        padding: 15px; border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); border: 1px solid #cccccc;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { 
        color: #000000 !important; 
    }
    .stExpander {
        background-color: rgba(255, 255, 255, 0.9) !important;
        border-radius: 10px !important; border: 1px solid #ddd !important;
    }
    </style>
    """, unsafe_allow_html=True)

def get_data():
    try:
        prod = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        kat = supabase.table("kategorie").select("*").execute()
        return prod.data, kat.data
    except Exception as e:
        st.error(f"Błąd bazy: {e}")
        return [], []

prod_data, kat_data = get_data()

st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

if prod_data:
    df = pd.DataFrame(prod_data)
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    if 'stan_minimalny' not in df.columns: 
        df['stan_minimalny'] = 5
    df['wartosc_magazynu'] = df['liczba'] * df['cena']
    
    # SEKCJA 1: KPI (Poprawione formatowanie, aby uniknąć błędów)
    m1, m2, m3, m4 = st.columns(4)
    with m1: 
        total_qty = int(df['liczba'].sum())
        st.metric("📦 Suma Produktów", f"{total_qty} szt.")
    with m2: 
        total_val = round(df['wartosc_magazynu'].sum(), 2)
        st.metric("💰 Wartość", f"{total_val} zł")
    with m3: 
        niskie = len(df[df['liczba'] < df['stan_minimalny']])
        st.metric("⚠️ Niskie Stany", f"{niskie} poz.")
    with m4: 
        st.metric("📂 Kategorie", len(kat_data))

    # SEKCJA 2: WYKRESY
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.subheader("Udział kategorii (%)")
        st.plotly_chart(px.pie(df, values='liczba', names='kategoria_nazwa', hole=0.5), use_container_width=True)
    with c2:
        st.subheader("Stan obecny vs Minimalny")
        st.plotly_chart(px.bar(df, x='nazwa', y=['liczba', 'stan_minimalny'], barmode='group'), use_container_width=True)

    # SEKCJA 3: TABELA
    st.subheader("📋 Zestawienie Produktów")
    display_df = df
