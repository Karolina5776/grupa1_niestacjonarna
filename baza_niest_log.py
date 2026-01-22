import streamlit as st
from supabase import create_client, Client
import pandas as pd
import plotly.express as px

# 1. KONFIGURACJA POŁĄCZENIA
url = st.secrets["supabase_url"]
key = st.secrets["supabase_key"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="Magazyn Dashboard Pro", layout="wide", initial_sidebar_state="collapsed")

# --- CUSTOM CSS: TŁO I STYLIZACJA ---
st.markdown("""
    <style>
    /* Tło całej aplikacji */
    .stApp {
        background: linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), 
                    url('https://images.unsplash.com/photo-1586528116311-ad8dd3c8310d?q=80&w=2070&auto=format&fit=crop');
        background-size: cover;
        background-attachment: fixed;
    }

    /* Stylizacja kart KPI - Czarna czcionka */
    .stMetric { 
        background-color: rgba(255, 255, 255, 0.9) !important; 
        padding: 15px; 
        border-radius: 10px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
        border: 1px solid #dddddd;
    }
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] { 
        color: #000000 !important; 
    }

    /* Półprzezroczyste kontenery dla wykresów i tabel */
    .stTabs, .stTable, .stDataFrame {
        background-color: rgba(255, 255, 255, 0.9);
        padding: 10px;
        border-radius: 10px;
    }
    
    h1, h2, h3 {
        color: #1a1a1a !important;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
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

# --- NAGŁÓWEK ---
st.title("🏭 System Zarządzania Magazynem")
st.markdown("---")

if prod_data:
    df = pd.DataFrame(prod_data
