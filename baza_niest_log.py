import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS: TŁO, KOLORY CZCIONEK I STYLIZACJA ---
st.markdown("""
    <style>
    /* Tło magazynu */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.82)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    
    /* GŁÓWNY TYTUŁ NA CZERWONO */
    h1 {
        color: #ff0000 !important;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
        font-weight: bold;
    }

    /* Karty KPI - Czarna czcionka */
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border: 1px solid #cccccc;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { 
        color: #000000 !important; 
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

# Nagłówek (teraz będzie czerwony dzięki CSS powyżej)
st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

if prod_data:
    df = pd.DataFrame(prod_data)
    
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    if 'stan_minimalny' not in df.columns: df['stan_minimalny'] = 5
    df['wartosc_magazynu'] = df['liczba'] * df['cena']
    
    # --- SEKCJA 1: STATYSTYKI ---
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    with m2: st.metric("💰 Wartość Całkowita", f"{df['wartosc_magazynu'].sum():,.2f} zł")
    with m3: 
        niskie = len(df[df['liczba'] < df['stan_minimalny']])
        st.metric("⚠️ Niskie Stany", f
