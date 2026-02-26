import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# إعداد الصفحة
st.set_page_config(page_title="Power Performance Analysis", layout="wide")
st.title("⚡ Power Flow Analysis & Performance Tool")

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.header("🎛️ مدخلات النظام")

# 1. الجهود
vs_kv = st.sidebar.number_input("جهد الإرسال (Vs) kV", value=230, step=5)
vr_kv = st.sidebar.number_input("جهد الاستقبال (Vr) kV", value=220, step=5)

# 2. نوع ومعامل القدرة للحمل فقط
st.sidebar.subheader("Load Power Factor (Receiving)")
pf_type = st.sidebar.selectbox("نوع PF للحمل", ["Lagging", "Unity", "Leading"])
if pf_type == "Unity":
    pf_val = 1.0
else:
    pf_val = st.sidebar.slider("قيمة PF للحمل", 0.5, 0.99, 0.85)

# 3. القدرة المستلمة
pr_mw = st.sidebar.slider("القدرة المطلوبة (Pr) MW", 10, 500, 150)

# --- الحسابات الكهربائية ---
phi_r = 0 if pf_type == "Unity" else np.arccos(pf_val)
if pf_type == "Leading": phi_r = -phi_r

qr_mvar = pr_mw * np.tan(phi_r)
sr_mva = np.sqrt(pr_mw**2 + qr_mvar**2)

# حساب المفاقيد (Line Losses)
vr_ph = (vr_kv * 1000) / np.sqrt(3)
ir_mag = (pr_mw * 1e6 / 3) / (vr_ph * pf_val) if pr_mw > 0 else 0

R_line, X_line = 10, 50 # ثوابت الخط
p_loss = (3 * (ir_mag**2) * R_line) / 1e6
q_loss = (3 * (ir_mag**2) * X_line) / 1e6

ps_mw = pr_mw + p_loss
qs_mvar = qr_mvar + q_loss
ss_mva = np.sqrt(ps_mw**2 + qs_mvar**2)
eff = (pr_mw / ps_mw * 100) if ps_mw > 0 else 0
pf_s = ps_mw / ss_mva if ss_mva > 0 else 1

# --- دالة رسم المثلثات بألوان وكتابة بيانات ---
def plot_detailed_triangle(ax, p, q, s, title):
    # رسم ضلع P (أفقي) - أزرق
    ax.plot([0, p], [0, 0], color='blue', linewidth=4, label=f'P = {p:.1f} MW')
    ax.text(p/2, -max(abs(q), 10)*0.1, f'P={p:.1f}', color='blue', fontweight='bold', ha='center')
    
    # رسم ضلع Q (رأسي) - أحمر
    ax.plot([p, p], [0, q], color='red', linewidth=4, label=f'Q = {q:.1f} MVAr')
    ax.text(p + max(p,10)*0.02, q/2, f'Q={q:.1f}', color='red', fontweight='bold', va='center')
    
    # رسم وتر S (مائل) - أخضر
    ax.plot([0, p], [0, q], color='green', linestyle='-', linewidth=3, label=f'S = {s:.1f} MVA')
    ax.text(p/2, q/2 + (max(abs(q),10)*0.1 if q>0 else -max(abs(q),10)*0.1), f'S={s:.1f}', color='green', fontweight='bold', ha='center')
    
    ax.set_title(title, fontsize=14, fontweight='bold')
    lim = max(abs(p), abs(q), 20) * 1.3
    ax.set_xlim(-lim/10, lim)
    ax.set_ylim(min(0, q)-lim/4, max(0, q)+lim/4)
    ax.axhline(0, color='black', lw=1)
    ax.axvline(0, color='black', lw=1)
    ax.grid(True, linestyle=':', alpha=0.6)

# --- عرض الرسومات ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📍 Receiving End (Load) Triangle")
    fig1, ax1 = plt.subplots()
    plot_detailed_triangle(ax1, pr_mw, qr_mvar, sr_mva, "Load Side Triangle")
    st.pyplot(fig1)

with col2:
    st.subheader("📍 Sending End (Generator) Triangle")
    fig2, ax2 = plt.subplots()
    plot_detailed_triangle(ax2, ps_mw, qs_mvar, ss_mva, "Source Side Triangle")
    st.pyplot(fig2)

# رسم دائرة القدرة مدمجة
st.subheader("🎯 Combined Power Circle Visualization")
fig3, ax3 = plt.subplots(figsize=(8, 4))
theta = np.linspace(0, 2*np.pi, 100)
ax3.plot(sr_mva*np.cos(theta), sr_mva*np.sin(theta), 'g--', alpha=0.3, label='Receiving Limit')
ax3.plot(ss_mva*np.cos(theta), ss_mva*np.sin(theta), 'b--', alpha=0.3, label='Sending Limit')
ax3.scatter([pr_mw], [qr_mvar], color='green', s=100, label='Rec. Point')
ax3.scatter([ps_mw], [qs_mvar], color='blue', s=100, label='Send. Point')
ax3.legend()
ax3.grid(True)
st.pyplot(fig3)

# --- الجدول التحليلي الشامل ---
st.divider()
st.subheader("📊 الجدول التحليلي النهائي (Analytical Results)")

results_data = {
    "البيان (Parameter)": ["Active Power (P)", "Reactive Power (Q)", "Apparent Power (S)", "Voltage (Line)", "Power Factor"],
    "الاستقبال (Receiving)": [f"{pr_mw} MW", f"{qr_mvar:.2f} MVAr", f"{sr_mva:.2f} MVA", f"{vr_kv} kV", f"{pf_val} ({pf_type})"],
    "الإرسال (Sending)": [f"{ps_mw:.2f} MW", f"{qs_mvar:.2f} MVAr", f"{ss_mva:.2f} MVA", f"{vs_kv} kV", f"{pf_s:.2f}"],
    "النتائج (Performance)": [f"P-Loss: {p_loss:.2f} MW", f"Q-Loss: {q_loss:.2f} MVAr", "-", "-", f"Efficiency: {eff:.2f}%"]
}

st.table(results_data)
