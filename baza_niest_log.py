import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide", initial_sidebar_state="collapsed")

# --- STYLE CSS ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.8), rgba(255, 255, 255, 0.8)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }
    h1 { color: #ff0000 !important; font-weight: bold; }
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.95) !important; 
        padding: 15px; border-radius: 10px; border: 1px solid #cccccc;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { color: #000000 !important; }
    .stExpander { background-color: rgba(255, 255, 255, 0.9) !important; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

def get_data():
    try:
        prod = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
        kat = supabase.table("kategorie").select("*").execute()
        return prod.data, kat.data
    except Exception as e:
        st.error(f"Błąd pobierania danych: {e}")
        return [], []

prod_data, kat_data = get_data()

st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

if prod_data:
    df = pd.DataFrame(prod_data)
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    if 'stan_minimalny' not in df.columns: df['stan_minimalny'] = 5
    # Przeliczanie wartości z zabezpieczeniem przed None
    df['cena'] = pd.to_numeric(df['cena']).fillna(0)
    df['liczba'] = pd.to_numeric(df['liczba']).fillna(0)
    df['wartosc_magazynu'] = df['liczba'] * df['cena']
    
    # KPI
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    with m2: st.metric("💰 Wartość", f"{round(df['wartosc_magazynu'].sum(), 2)} zł")
    with m3: 
        niskie = len(df[df['liczba'] < df['stan_minimalny']])
        st.metric("⚠️ Niskie Stany", f"{niskie} poz.")
    with m4: st.metric("📂 Kategorie", len(kat_data))

    # TABELA
    st.subheader("📋 Zestawienie Produktów")
    st.dataframe(df[['nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena']], use_container_width=True)

st.divider()

# OPERACJE
t1, t2, t3 = st.tabs(["🆕 Produkty", "📦 Dostawa", "📂 Kategorie"])

with t1:
    with st.expander("➕ Dodaj Nowy Produkt"):
        with st.form("form_p"):
            n = st.text_input("Nazwa produktu")
            q = st.number_input("Ilość początkowa", min_value=0, value=0)
            ms = st.number_input("Stan minimalny", min_value=0, value=5)
            p = st.number_input("Cena sprzedaży", min_value=0.0, value=0.0)
            
            k_dict = {k['nazwa']: k['id'] for k in kat_data}
            k_sel = st.selectbox("Wybierz kategorię", options=list(k_dict.keys()))
            
            if st.form_submit_button("Zatwierdź i Dodaj"):
                try:
                    # UWAGA: Upewnij się, że nazwy kolumn poniżej są identyczne jak w Supabase!
                    response = supabase.table("produkty").insert({
                        "nazwa": n, 
                        "liczba": q, 
                        "stan_minimalny": ms, 
                        "cena": p, 
                        "kategoria_id": k_dict[k_sel]
                    }).execute()
                    st.success(f"Dodano produkt: {n}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd bazy danych: {e}")

with t2:
    if not df.empty:
        p_name = st.selectbox("Wybierz produkt", options=df['nazwa'].tolist())
        amount = st.number_input("Dodaj sztuk", min_value=1, value=1)
        if st.button("Zaktualizuj stan"):
            row = df[df['nazwa'] == p_name].iloc[0]
            new_qty = int(row['liczba']) + amount
            supabase.table("produkty").update({"liczba": new_qty}).eq("id", row['id']).execute()
            st.success("Zaktualizowano stan!")
            st.rerun()

with t3:
    with st.form("form_k"):
        nk = st.text_input("Nowa kategoria")
        if st.form_submit_button("Dodaj kategorię"):
            if nk:
                try:
                    supabase.table("kategorie").insert({"nazwa": nk}).execute()
                    st.success(f"Dodano kategorię: {nk}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Błąd: {e}")
