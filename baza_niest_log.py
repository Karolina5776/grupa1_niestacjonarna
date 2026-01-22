import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS dla lepszego wyglądu
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
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

# --- HEADER ---
st.title("📊 Panel Analityczny Magazynu")
st.markdown("---")

if prod_data:
    df = pd.DataFrame(prod_data)
    # Przygotowanie danych
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    df['wartosc_magazynu'] = df['liczba'] * df['cena']
    
    # --- SEKCJA 1: KPI ---
    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("📦 Suma Produktów", f"{int(df['liczba'].sum())} szt.")
    with m2: st.metric("💰 Wartość Całkowita", f"{df['wartosc_magazynu'].sum():,.2f} zł")
    with m3: 
        niskie_stany = len(df[df['liczba'] < df.get('stan_minimalny', 5)])
        st.metric("⚠️ Alerty", f"{niskie_stany} poz.", delta_color="inverse")
    with m4: st.metric("📂 Kategorie", len(kat_data))

    # --- SEKCJA 2: WYKRESY ---
    col_chart1, col_chart2 = st.columns([1, 1.5])

    with col_chart1:
        st.subheader("Udział procentowy kategorii")
        # Wykres Donut dla procentów
        fig_pie = px.pie(df, values='liczba', names='kategoria_nazwa', 
                         hole=0.5, 
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_chart2:
        st.subheader("Stany vs Cele Minimalne")
        fig_bar = px.bar(df, x='nazwa', y=['liczba', 'stan_minimalny'], 
                         barmode='group',
                         title="Ilość obecna a wymagane minimum",
                         color_discrete_map={'liczba': '#00CC96', 'stan_minimalny': '#EF553B'})
        st.plotly_chart(fig_bar, use_container_width=True)

    # --- SEKCJA 3: ATRAKCYJNA TABELA ---
    st.subheader("📋 Pełne Zestawienie Produktów")
    
    # Tworzymy ładniejszy widok tabeli
    display_df = df[['nazwa', 'kategoria_nazwa', 'liczba', 'stan_minimalny', 'cena']].copy()
    display_df.columns = ['Produkt', 'Kategoria', 'Stan', 'Min. Stan', 'Cena (zł)']
    
    # Dodajemy wizualny pasek postępu (stan / 100 jako przykład)
    st.dataframe(
        display_df.style.background_gradient(subset=['Stan'], cmap='YlGn')
        .format({'Cena (zł)': '{:.2f}'}),
        use_container_width=True,
        height=400
    )

st.markdown("---")

# --- SEKCJA 4: OPERACJE ---
t1, t2 = st.tabs(["🆕 Zarządzanie Bzą", "📦 Szybka Dostawa"])

with t1:
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("➕ Dodaj Nowy Produkt"):
            with st.form("new_p"):
                name = st.text_input("Nazwa")
                col_sub1, col_sub2 = st.columns(2)
                with col_sub1:
                    qty = st.number_input("Ilość", min_value=0)
                    min_s = st.number_input("Stan min.", value=5)
                with col_sub2:
                    price_z = st.number_input("Cena zakupu", 0.0)
                    price_s = st.number_input("Cena sprzedaży", 0.0)
                
                k_dict = {k['nazwa']: k['id'] for k in kat_data}
                k_sel = st.selectbox("Wybierz kategorię", options=list(k_dict.keys()))
                
                if st.form_submit_button("Zapisz w magazynie"):
                    supabase.table("produkty").insert({
                        "nazwa": name, "liczba": qty, "stan_minimalny": min_s,
                        "cena_zakupu": price_z, "cena": price_s, "kategoria_id": k_dict[k_sel]
                    }).execute()
                    st.rerun()
    with c2:
        with st.expander("📂 Dodaj Nową Kategorię"):
            with st.form("new_k"):
                nk = st.text_input("Nazwa kategorii")
                if st.form_submit_button("Stwórz kategorię"):
                    supabase.table("kategorie").insert({"nazwa": nk}).execute()
                    st.rerun()

with t2:
    if prod_data:
        st.write("Wyszukaj i uzupełnij towar:")
        p_name = st.selectbox("Produkt", options=df['nazwa'].tolist())
        amount = st.number_input("Ile sztuk dojechało?", min_value=1)
        if st.button("Zatwierdź dostawę"):
            current_q = df[df['nazwa
