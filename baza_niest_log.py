import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. POŁĄCZENIE
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Finanse", layout="wide")

def get_data():
    prod = supabase.table("produkty").select("*, kategorie(nazwa)").execute()
    kat = supabase.table("kategorie").select("*").execute()
    return prod.data, kat.data

prod_data, kat_data = get_data()

st.title("💰 Magazyn z Analizą Marży")

if prod_data:
    df = pd.DataFrame(prod_data)
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    
    # OBLICZENIA FINANSOWE
    # Zakładamy nazwy kolumn: cena (sprzedaży) i cena_zakupu
    df['marza_jednostkowa'] = df['cena'] - df['cena_zakupu']
    df['marza_procentowa'] = (df['marza_jednostkowa'] / df['cena']) * 100
    df['wartosc_magazynu_zakup'] = df['liczba'] * df['cena_zakupu']
    df['wartosc_magazynu_sprzedaz'] = df['liczba'] * df['cena']
    df['potencjalny_zysk'] = df['wartosc_magazynu_sprzedaz'] - df['wartosc_magazynu_zakup']

    # --- SEKCJA 1: KPI FINANSOWE ---
    st.subheader("📈 Podsumowanie Finansowe")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Wartość w zakupie", f"{df['wartosc_magazynu_zakup'].sum():,.2f} zł")
    m2.metric("Wartość w sprzedaży", f"{df['wartosc_magazynu_sprzedaz'].sum():,.2f} zł")
    m3.metric("Potencjalny zysk", f"{df['potencjalny_zysk'].sum():,.2f} zł", delta=f"{df['potencjalny_zysk'].sum() / df['wartosc_magazynu_zakup'].sum() * 100:.1f}% marży śr.")
    m4.metric("Liczba indeksów", len(df))

    st.divider()

    # --- SEKCJA 2: WYKRESY RENTOWNOŚCI ---
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Rentowność produktów (%)")
        fig_marza = px.bar(df, x='nazwa', y='marza_procentowa', color='marza_procentowa',
                          title="Marża % na poszczególnych produktach",
                          color_continuous_scale="Viridis")
        st.plotly_chart(fig_marza, use_container_width=True)
    
    with c2:
        st.write("### Udział kategorii w zysku")
        fig_zysk = px.pie(df, values='potencjalny_zysk', names='kategoria_nazwa', 
                         title="Skąd pochodzi Twój przyszły zysk?")
        st.plotly_chart(fig_zysk, use_container_width=True)

    st.divider()

# --- SEKCJA 3: ZARZĄDZANIE ---
# (Uproszczony widok tabeli z finansami)
st.header("🛒 Szczegóły Produktów")
st.dataframe(df[['nazwa', 'liczba', 'cena_zakupu', 'cena', 'marza_procentowa', 'potencjalny_zysk']].style.format({
    'cena_zakupu': '{:.2f} zł',
    'cena': '{:.2f} zł',
    'marza_procentowa': '{:.1f}%',
    'potencjalny_zysk': '{:.2f} zł'
}), use_container_width=True)

with st.expander("➕ Dodaj nowy produkt z ceną zakupu"):
    with st.form("add_p_finance"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            n = st.text_input("Nazwa produktu")
            l = st.number_input("Ilość", min_value=0)
        with col_f2:
            cz = st.number_input("Cena zakupu (netto/brutto)", min_value=0.0)
            cs = st.number_input("Cena sprzedaży", min_value=0.0)
        
        kat_opt = {k['nazwa']: k['id'] for k in kat_data}
        k_name = st.selectbox("Kategoria", options=list(kat_opt.keys()))
        
        if st.form_submit_button("Zapisz produkt"):
            supabase.table("produkty").insert({
                "nazwa": n, 
                "liczba": l, 
                "cena_zakupu": cz, 
                "cena": cs, 
                "kategoria_id": kat_opt[k_name]
            }).execute()
            st.rerun()
