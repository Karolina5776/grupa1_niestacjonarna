import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS: TŁO, CZERWONY TYTUŁ, CZARNE KPI ---
st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.82), rgba(255, 255, 255, 0.82)), 
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

st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

if prod_data:
    df = pd.DataFrame(prod_data)
    
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    if 'stan_minimalny' not in df.columns: 
        df['stan_minimalny'] = 5
    df['wartosc_magazynu'] = df['liczba'] * df['cena']
    
    # --- SEKCJA 1: STATYSTYKI (KPI) ---
    m1, m2, m3, m4 = st.columns(4)
    with m1: 
        st.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    with m2: 
        st.metric("💰 Wartość Całkowita", f"{df['wartosc_magazynu'].sum():,.2f} zł")
    with m3: 
        # POPRAWIONA LINIA (uważaj na klamry i f-stringi):
        niskie = len(df[df['liczba'] < df['stan_minimalny']])
        st.metric("⚠️ Niskie Stany", f"{niskie} poz.")
    with m4: 
        st.metric("📂 Kategorie", len(kat_data))

    # --- SEKCJA 2: WYKRESY ---
    col_chart1, col_chart2 = st.columns([1, 1.5])
    with col_chart1:
        st.subheader("Udział kategorii (%)")
        fig_pie = px.pie(df, values='liczba', names='kategoria_nazwa', hole=0.5)
        st.plotly_chart(fig_pie, use_container_width=True)
    with col_chart2:
        st.subheader("Stan obecny vs Minimalny")
        fig_bar = px.bar(df, x='nazwa', y=['liczba', 'stan_minimalny'], barmode='group')
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- SEKCJA 3: TABELA ---
    st.subheader("📋 Zestawienie Produktów")
    display_df = df[['nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena']].copy()
    display_df.columns = ['Produkt', 'Kategoria', 'Stan', 'Min', 'Cena (zł)']
    st.dataframe(display_df.style.background_gradient(subset=['Stan'], cmap='YlGn'), use_container_width=True)

st.markdown("---")

# --- SEKCJA 4: OPERACJE ---
t1, t2, t3 = st.tabs(["🆕 Zarządzanie", "📦 Szybka Dostawa", "📂 Kategorie"])

with t1:
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("➕ Dodaj Produkt"):
            with st.form("new_p"):
                name = st.text_input("Nazwa")
                qty = st.number_input("Ilość", min_value=0)
                min_s = st.number_input("Stan min.", value=5)
                p_s = st.number_input("Cena sprzedaży", 0.0)
                k_dict = {k['nazwa']: k['id'] for k in kat_data}
                k_sel = st.selectbox("Wybierz kategorię", options=list(k_dict.keys()))
                if st.form_submit_button("Zapisz"):
                    supabase.table("produkty").insert({
                        "nazwa": name, "liczba": qty, "stan_minimalny": min_s,
                        "cena": p_s, "kategoria_id": k_dict[k_sel]
                    }).execute()
                    st.rerun()
    with c2:
        with st.expander("🗑️ Usuń Produkt"):
            if not df.empty:
                to_del = st.selectbox("Wybierz do usunięcia", df['nazwa'].tolist())
                if st.button("Potwierdź usunięcie"):
                    supabase.table("produkty").delete().eq("nazwa", to_del).execute()
                    st.rerun()

with t2:
    if not df.empty:
        st.write("Dostawa towaru:")
        p_name = st.selectbox("Wybierz produkt", options=df['nazwa'].tolist(), key="delivery_key")
        amount = st.number_input("Ilość nowej dostawy", min_value=1)
        if st.button("Dodaj do stanu"):
            row = df[df['nazwa'] == p_name].iloc[0]
            new_qty = int(row['liczba']) + amount
            supabase.table("produkty").update({"liczba": new_qty}).eq("id", row['id']).execute()
            st.rerun()

with t3:
    col_k1, col_k2 = st.columns(2)
    with col_k1:
        st.subheader("Aktualne Kategorie")
        for k in kat_data: st.write(f"• {k['nazwa']}")
    with col_k2:
        with st.form("new_kat"):
            new_k = st.text_input("Nazwa nowej kategorii")
            if st.form_submit_button("Dodaj kategorię"):
                if new_k:
                    supabase.table("kategorie").insert({"nazwa": new_k}).execute()
                    st.rerun()
