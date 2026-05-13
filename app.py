import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Power System Engineering Tool", layout="wide")

# --- 1. الربط التبادلي بين الثوابت (Sidebar) ---
with st.sidebar:
    st.header("📋 معطيات الخط (Line Constants)")
    mode = st.radio("إدخال البيانات عن طريق:", ["ABCD Constants", "Z & Y Magnitudes"])
    
    if mode == "ABCD Constants":
        a_m = st.number_input("A Magnitude:", value=0.9704, format="%.4f")
        alpha = st.number_input("Alpha (deg):", value=1.118)
        b_m = st.number_input("B Magnitude:", value=36.7569, format="%.4f")
        beta = st.number_input("Beta (deg):", value=80.0)
        
        # حساب Z و Y استنتاجياً
        z_mag_calc, z_ang_calc = b_m, beta
        A_comp = complex(a_m * np.cos(np.radians(alpha)), a_m * np.sin(np.radians(alpha)))
        B_comp = complex(b_m * np.cos(np.radians(beta)), b_m * np.sin(np.radians(beta)))
        y_comp = (2 * (A_comp - 1)) / B_comp
        y_mag_calc, y_ang_calc = np.abs(y_comp), np.degrees(np.angle(y_comp))
    else:
        z_mag = st.number_input("Z Magnitude (Ohm):", value=38.1)
        z_ang = st.number_input("Z Angle (deg):", value=74.0)
        y_mag = st.number_input("Y Magnitude (S):", value=0.001, format="%.6f")
        y_ang = st.number_input("Y Angle (deg):", value=90.0)
        
        # حساب ABCD
        Z = z_mag * np.exp(1j * np.radians(z_ang))
        Y = y_mag * np.exp(1j * np.radians(y_ang))
        A_comp = 1 + (Z * Y) / 2
        a_m, alpha = np.abs(A_comp), np.degrees(np.angle(A_comp))
        b_m, beta = z_mag, z_ang
        z_mag_calc, z_ang_calc, y_mag_calc, y_ang_calc = z_mag, z_ang, y_mag, y_ang

    st.divider()
    st.header("🔌 بيانات الحمل (Load)")
    vr_kv = st.number_input("Vr (kV):", value=132.0)
    pr_mw = st.number_input("Pr (MW):", value=100.0)
    pf_type = st.selectbox("نوع PF:", ["Lagging", "Leading", "Unity"])
    pf_val = st.slider("قيمة PF:", 0.1, 1.0, 0.85)

# --- 2. الحسابات الهندسية والأداء ---
alpha_rad, beta_rad = np.radians(alpha), np.radians(beta)
gamma_rad = beta_rad - alpha_rad
phi_r = -np.arccos(pf_val) if pf_type == "Lagging" else (np.arccos(pf_val) if pf_type == "Leading" else 0.0)
qr_mvar = pr_mw * np.tan(phi_r)

# حسابات الاستقبال
r_n = (a_m * vr_kv**2) / b_m
nx, ny = -r_n * np.cos(gamma_rad), r_n * np.sin(gamma_rad)
chord_len = np.sqrt((pr_mw - nx)**2 + (qr_mvar - ny)**2)
vs_calc = (chord_len * b_m) / vr_kv
theta_rad = np.arctan2(qr_mvar - ny, pr_mw - nx) - (np.pi - gamma_rad)

# حسابات الإرسال (تثبيت النقطة يمين)
r_m = (a_m * vs_calc**2) / b_m
mx, my = r_m * np.cos(gamma_rad), -r_m * np.sin(gamma_rad)
total_angle_s = -gamma_rad + abs(theta_rad + alpha_rad)
ps_mw = mx + chord_len * np.cos(total_angle_s)
qs_mvar = my + chord_len * np.sin(total_angle_s)

# حسابات إضافية للجدول
pfs = ps_mw / np.sqrt(ps_mw**2 + qs_mvar**2)
eff = (pr_mw / ps_mw) * 100
v_reg = (((vs_calc/a_m) - vr_kv) / vr_kv) * 100
p_opt = (vr_kv**2) / z_mag_calc # Optimal Power (SIL)

# --- 3. عرض الجدول والبيانات المستنتجة ---
st.header("📊 Power System Projrct")
col_table, col_const = st.columns([2, 1])

with col_table:
    st.subheader("جدول الأداء (Performance Table)")
    performance_df = pd.DataFrame({
        "المتغير (Parameter)": ["Vs (Sending Voltage)", "Ps (Sending Power)", "PFs (Sending Power Factor)", "Efficiency (%)", "Voltage Regulation (%)"],
        "القيمة (Value)": [f"{vs_calc:.2f} kV", f"{ps_mw:.2f} MW", f"{pfs:.3f}", f"{eff:.2f} %", f"{v_reg:.2f} %"]
    })
    st.table(performance_df)

with col_const:
    st.subheader("الثوابت المستنتجة")
    st.info(f"**Z:** {z_mag_calc:.2f} ∠ {z_ang_calc:.2f}° Ω")
    st.info(f"**Y:** {y_mag_calc:.6f} ∠ {y_ang_calc:.2f}° S")

# --- 4. الرسومات الثلاثة ---
def plot_circle_system(fig, cx, cy, radius, px, py, name, color):
    # الدائرة
    angles = np.linspace(0, 2*np.pi, 200)
    fig.add_trace(go.Scatter(x=cx + radius*np.cos(angles), y=cy + radius*np.sin(angles), 
                             mode='lines', line=dict(dash='dot', color='rgba(150,150,150,0.5)'), name=f"{name} Circle"))
    # المثلث
    fig.add_trace(go.Scatter(x=[0, cx, px, 0], y=[0, cy, py, 0], fill='toself', 
                             fillcolor=f'rgba({color}, 0.2)', line=dict(color=f'rgb({color})', width=2), name=f"{name} Triangle"))
    # نقطة التشغيل الحالية
    fig.add_trace(go.Scatter(x=[px], y=[py], mode='markers', marker=dict(size=10, color='black'), name="Operating Point"))
    # نقطة أحسن باور (Optimal)
    fig.add_trace(go.Scatter(x=[p_opt], y=[0], mode='markers+text', text=["Best Power (SIL)"], 
                             textposition="bottom center", marker=dict(size=12, symbol='star', color='gold'), name="Optimal Pt"))

st.header("📉 المخططات الهندسية (Power Circle Diagrams)")
t1, t2, t3 = st.tabs(["1. Receiving End", "2. Sending End", "3. Comparison (Combined)"])

with t1:
    f1 = go.Figure(); f1.add_hline(0); f1.add_vline(0)
    plot_circle_system(f1, nx, ny, chord_len, pr_mw, qr_mvar, "Receiving", "255, 0, 0")
    f1.update_layout(xaxis_title="Pr (MW)", yaxis_title="Qr (MVAR)", height=600)
    st.plotly_chart(f1, use_container_width=True)

with t2:
    f2 = go.Figure(); f2.add_hline(0); f2.add_vline(0)
    plot_circle_system(f2, mx, my, chord_len, ps_mw, qs_mvar, "Sending", "0, 128, 0")
    f2.update_layout(xaxis_title="Ps (MW)", yaxis_title="Qs (MVAR)", height=600)
    st.plotly_chart(f2, use_container_width=True)

with t3:
    f3 = go.Figure(); f3.add_hline(0); f3.add_vline(0)
    # رسم الاستقبال
    f3.add_trace(go.Scatter(x=[0, nx, pr_mw, 0], y=[0, ny, qr_mvar, 0], fill='toself', name='Receiving', line=dict(color='red', width=1)))
    # رسم الإرسال
    f3.add_trace(go.Scatter(x=[0, mx, ps_mw, 0], y=[0, my, qs_mvar, 0], fill='toself', name='Sending', line=dict(color='green', width=1)))
    f3.update_layout(title="Comparison View", xaxis_title="Power (MW)", yaxis_title="Reactive (MVAR)", height=600)
    st.plotly_chart(f3, use_container_width=True)
