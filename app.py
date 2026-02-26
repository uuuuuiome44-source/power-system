import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Power Analysis Pro", layout="wide")
st.title("⚡ Power System Project: Circle, Triangle & Angles")

# --- القائمة الجانبية ---
st.sidebar.header("Configuration")
pf_type = st.sidebar.selectbox("Power Factor Type:", ["Lagging", "Unity", "Leading"])
if pf_type == "Unity":
    pf_val = 1.0
    st.sidebar.text("PF is fixed at 1.0")
else:
    pf_val = st.sidebar.slider("PF Value (cos φ)", 0.5, 0.99, 0.85)

P_mw = st.sidebar.slider("Active Power (P) MW", 50, 400, 150)
Vs_kv = st.sidebar.number_input("Vs (kV)", value=230.0)
Vr_kv = st.sidebar.number_input("Vr (kV)", value=220.0)
R, X = 10.0, 50.0 # قيم الخط الثابتة

# --- الحسابات ---
Z = complex(R, X)
beta_rad = np.angle(Z)
Vr_ph = (Vr_kv * 1000) / np.sqrt(3)
Vs_ph = (Vs_kv * 1000) / np.sqrt(3)

# زاوية Phi
if pf_type == "Lagging": phi_rad = np.arccos(pf_val)
elif pf_type == "Leading": phi_rad = -np.arccos(pf_val)
else: phi_rad = 0.0

Q_mvar = P_mw * np.tan(phi_rad)
S_mva = P_mw / pf_val

# حساب زاوية الحمل Delta
term1 = (P_mw * 1e6 / 3) + (abs(Vr_ph)**2 / abs(Z)) * np.cos(beta_rad)
cos_bd = np.clip((term1 * abs(Z)) / (abs(Vs_ph) * abs(Vr_ph)), -1, 1)
delta_rad = beta_rad - np.arccos(cos_bd)

# --- الرسم البياني ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📐 Power Triangle & φ Angle")
    fig_tri, ax_tri = plt.subplots(figsize=(7, 7))
    # رسم الأضلاع
    ax_tri.quiver(0, 0, P_mw, 0, angles='xy', scale_units='xy', scale=1, color='g', label='P (MW)')
    ax_tri.quiver(P_mw, 0, 0, Q_mvar, angles='xy', scale_units='xy', scale=1, color='orange', label='Q (MVAr)')
    ax_tri.quiver(0, 0, P_mw, Q_mvar, angles='xy', scale_units='xy', scale=1, color='purple', label='S (MVA)')
    
    # رسم زاوية Phi
    if pf_type != "Unity":
        arc_r = P_mw * 0.2
        t = np.linspace(0, phi_rad, 30)
        ax_tri.plot(arc_r*np.cos(t), arc_r*np.sin(t), 'r', lw=2)
        ax_tri.text(arc_r*1.2*np.cos(phi_rad/2), arc_r*1.2*np.sin(phi_rad/2), f'φ={np.degrees(phi_rad):.1f}°', color='red', fontweight='bold')

    ax_tri.set_xlim(-20, P_mw + 50); ax_tri.set_ylim(min(Q_mvar, 0)-50, max(Q_mvar, 0)+50)
    ax_tri.axhline(0, color='black', lw=1); ax_tri.grid(True); ax_tri.legend()
    st.pyplot(fig_tri)

with col2:
    st.subheader("🔵 Power Circle & δ Angle")
    fig_cir, ax_cir = plt.subplots(figsize=(7, 7))
    scaling = 3 * 1e-6
    Cx, Cy = -(abs(Vr_ph)**2 / abs(Z)) * np.cos(beta_rad) * scaling, -(abs(Vr_ph)**2 / abs(Z)) * np.sin(beta_rad) * scaling
    rad = (abs(Vs_ph) * abs(Vr_ph) / abs(Z)) * scaling
    
    # رسم الدائرة ونقطة التشغيل
    circle = plt.Circle((Cx, Cy), rad, color='b', fill=False, ls='--')
    ax_cir.add_artist(circle)
    ax_cir.scatter([P_mw], [-Q_mvar], color='red', zorder=5)
    
    # رسم خط يوضح زاوية Delta (الزاوية من مركز الدائرة للنقطة)
    ax_cir.plot([Cx, P_mw], [Cy, -Q_mvar], 'k:', alpha=0.6)
    ax_cir.text(P_mw, -Q_mvar+10, f'δ = {np.degrees(delta_rad):.2f}°', color='blue', fontweight='bold')
    
    ax_cir.set_xlim(Cx-20, P_mw+100); ax_cir.set_ylim(Cy-20, 200)
    ax_cir.axhline(0, color='black', lw=1); ax_cir.axvline(0, color='black', lw=1); ax_cir.grid(True)
    st.pyplot(fig_cir)

# --- الجدول التحليلي ---
st.subheader("📊 Analysis Table")
df = pd.DataFrame({
    "Parameter": ["Active Power (P)", "Reactive Power (Q)", "Apparent Power (S)", "Load Angle (δ)", "PF Angle (φ)"],
    "Value": [f"{P_mw} MW", f"{Q_mvar:.2f} MVAr", f"{S_mva:.2f} MVA", f"{np.degrees(delta_rad):.2f}°", f"{np.degrees(phi_rad):.1f}°"]
})
st.table(df)