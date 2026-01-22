import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Finanse Pro", layout="wide")

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
    
    # Zabezpieczenia kolumn
    if 'stan_minimalny' not in df.columns: df['stan_minimalny'] = 5
    if 'cena_zakupu' not in df.columns: df['cena_zakupu'] = 0.0
    
    df['cena_zakupu'] = pd.to_numeric(df['cena_zakupu']).fillna(0)
    df['cena'] = pd.to_numeric(df['cena']).fillna(0)
    df['liczba'] = pd.to_numeric(df['liczba']).fillna(0)
    
    df_low = df[df['liczba'] < df['stan_minimalny']].copy()
    
    if not df_low.empty:
        st.warning(f"🚨 Produkty wymagające uzupełnienia: {len(df_low)}")
        with st.expander("Otwórz panel szybkich dostaw"):
            cols = st.columns(3)
            for idx, row in df_low.reset_index().iterrows():
                with cols[idx % 3]:
                    st.write(f"**{row['nazwa']}**")
                    st.caption(f"Stan: {int(row['liczba'])} / Min: {int(row['stan_minimalny'])}")
                    # POPRAWIONA LINIA:
                    add_qty = st.number_input("Ilość dostawy", min_value=1, value=10, key=f"input_{row['id']}")
                    if st.button("Zatwierdź", key=f"btn_order_{row['id']}"):
                        new_total = row['liczba'] + add_qty
                        supabase.table("produkty").update({"liczba": new_total}).eq("id", row['id']).execute()
                        st.success(f"Dodano {add_qty} sztuk!")
                        st.rerun()

st.divider()

# --- SEKCJA 2: ANALITYKA FINANSOWA ---
if prod_data:
    df['kategoria_nazwa'] = df['kategorie'].apply(lambda x: x['nazwa'] if x else 'Brak')
    df['marza_jednostkowa'] = df['cena'] - df['cena_zakupu']
    df['marza_procentowa'] = df.apply(lambda x: (x['marza_jednostkowa'] / x['cena'] * 100) if x['cena'] > 0 else 0, axis=1)
    df['wartosc_magazynu'] = df['liczba'] * df['cena']
    df['potencjalny_zysk'] = df['liczba'] * df['marza_jednostkowa']

    st.subheader("📊 Wyniki Finansowe")
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Wartość (Sprzedaż)", f"{df['wartosc_magazynu'].sum():,.2f} zł")
    kpi2.metric("Potencjalny zysk", f"{df['potencjalny_zysk'].sum():,.2f} zł")
    kpi3.metric("Średnia marża", f"{df['marza_procentowa'].mean():.1f}%")

    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.plotly_chart(px.pie(df, values='wartosc_magazynu', names='kategoria_nazwa', title="Wartość wg kategorii"), use_container_width=True)
    with c_chart2:
        st.plotly_chart(px.bar(df, x='nazwa', y='marza_procentowa', color='marza_procentowa', title="Rentowność (%)", color_continuous_scale="RdYlGn"), use_container_width=True)

st.divider()

# --- SEKCJA 3: ZARZĄDZANIE ---
tab_p, tab_k = st.tabs(["🛒 Produkty", "📂 Kategorie"])

with tab_p:
    st.dataframe(df[['id', 'nazwa', 'liczba', 'stan_minimalny', 'cena_zakupu', 'cena', 'marza_procentowa']], use_container_width=True)
    
    c_add, c_del = st.columns(2)
    with c_add:
        with st.expander("➕ Dodaj nowy produkt"):
            with st.form("new_prod"):
                n = st.text_input("Nazwa")
                l = st.number_input("Ilość", min_value=0)
                sm = st.number_input("Stan minimalny", min_value=0, value=5)
                cz = st.number_input("Cena zakupu", min_value=0.0)
                cs = st.number_input("Cena sprzedaży", min_value=0.0)
                k_opt = {k['nazwa']: k['id'] for k in kat_data}
                k_sel = st.selectbox("Kategoria", options=list(k_opt.keys()))
                if st.form_submit_button("Zapisz"):
                    supabase.table("produkty").insert({"nazwa": n, "liczba": l, "stan_minimalny": sm, "cena_zakupu": cz, "cena": cs, "kategoria_id": k_opt[k_sel]}).execute()
                    st.rerun()
    with c_del:
        with st.expander("🗑️ Usuń produkt"):
            p_list = df['nazwa'].tolist() if not df.empty else []
            p_to_del = st.selectbox("Wybierz do usunięcia", options=p_list)
            if st.button("Usuń produkt"):
                supabase.table("produkty").delete().eq("nazwa", p_to_del).execute()
                st.rerun()

with tab_k:
    ck1, ck2 = st.columns(2)
    with ck1:
        st.write("### Kategorie")
        for k in kat_data: st.write(f"- {k['nazwa']}")
    with ck2:
        with st.form("new_kat"):
            nk = st.text_input("Nazwa kategorii")
            if st.form_submit_button("Dodaj"):
                supabase.table("kategorie").insert({"nazwa": nk}).execute()
                st.rerun()
