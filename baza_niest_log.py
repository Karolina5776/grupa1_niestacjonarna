# Zmień ten fragment w swoim kodzie:
import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA (Dane z Twoich Secrets TOML)
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

# Ustawienia strony
st.set_page_config(page_title="Magazyn Finanse Pro", layout="wide")

# Funkcja pobierania danych
def get_data():
    try:
        prod = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        kat = supabase.table("kategorie").select("*").execute()
        return prod.data, kat.data
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

prod_data, kat_data = get_data()

st.title("💰 Inteligentny Magazyn z Analizą Zysków")

# --- SEKCJA 1: ALERTY I ZAMÓWIENIA ---
if prod_data:
    df = pd.DataFrame(prod_data)
    
    # Zabezpieczenie przed brakiem nowych kolumn w bazie
    if 'stan_minimalny' not in df.columns: df['stan_minimalny'] = 5
    if 'cena_zakupu' not in df.columns: df['cena_zakupu'] = 0.0
    
    # Naprawa brakujących danych (NaN -> 0)
    df['cena_zakupu'] = pd.to_numeric(df['cena_zakupu']).fillna(0)
    df['cena'] = pd.to_numeric(df['cena']).fillna(0)
    df['liczba'] = pd.to_numeric(df['liczba']).fillna(0)
    
    # Produkty poniżej stanu minimalnego
    df_low = df[df['liczba'] < df['stan_minimalny']].copy()
    
    if not df_low.empty:
        st.warning(f"🚨 Masz {len(df_low)} produkty wymagające uzupełnienia!")
        exp = st.expander("Kliknij, aby rozwinąć listę zamówień")
        with exp:
            cols = st.columns(3)
            for idx, row in df_low.reset_index().iterrows():
                with cols[idx % 3]:
                    st.write(f"**{row['nazwa']}** (Obecnie: {int(row['liczba'])})")
                    add_qty = st.number_input(f"Dostawa dla {row
