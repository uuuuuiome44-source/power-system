import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Power System Analysis", layout="wide")
st.title("⚡ Power System Project - ABCD Parameters Model")

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.header("🎛️ مدخلات النظام")
vr_kv = st.sidebar.number_input("جهد الاستقبال (Vr) kV", value=220.0)
pr_mw = st.sidebar.slider("القدرة المطلوبة (Pr) MW", 10, 500, 150)
pf_type = st.sidebar.selectbox("نوع معامل القدرة للحمل", ["Lagging", "Unity", "Leading"])
pf_val = 1.0 if pf_type == "Unity" else st.sidebar.slider("قيمة معامل القدرة", 0.5, 0.99, 0.85)

st.sidebar.subheader("ثوابت الخط (Line Constants)")
R = st.sidebar.number_input("المقاومة R (Ω)", value=10.0)
XL = st.sidebar.number_input("المفاعلة الحثية XL (Ω)", value=50.0)
XC = st.sidebar.number_input("المفاعلة السعوية XC (Ω)", value=1000.0)

# --- الحسابات الهندسية (Nominal Pi Model) ---
Vr_ph = (vr_kv * 1000) / np.sqrt(3)
phi_r = 0 if pf_type == "Unity" else np.arccos(pf_val)
if pf_type == "Leading": phi_r = -phi_r

# تيار الحمل كمتجه
Ir_mag = (pr_mw * 1e6 / 3) / (Vr_ph * pf_val)
Ir_vec = Ir_mag * (np.cos(phi_r) - 1j * np.sin(phi_r))

# حساب ثوابت ABCD
Z = complex(R, XL)
Y = 1j / XC
A = 1 + (Y * Z / 2)
B = Z
C_param = Y * (1 + Y * Z / 4)
D = A

# حساب مركبات الجهد (Vs = A*Vr + B*Ir)
Term1 = A * Vr_ph  
Term2 = B * Ir_vec 
Vs_vec = Term1 + Term2
vs_kv_calc = (abs(Vs_vec) * np.sqrt(3)) / 1000

# حساب القدرة
Sr_vec = 3 * Vr_ph * np.conj(Ir_vec)
Is_vec = C_param * Vr_ph + D * Ir_vec
Ss_vec = 3 * Vs_vec * np.conj(Is_vec)
pr_calc, qr_calc = Sr_vec.real/1e6, Sr_vec.imag/1e6
ps_calc, qs_calc = Ss_vec.real/1e6, Ss_vec.imag/1e6

# --- رسم الـ 6 رسومات ---
col1, col2, col3 = st.columns(3)

# 1. رسمة جهد الاستقبال (كمثلث مرجعي)
with col1:
    st.subheader("1. Receiving Voltage")
    fig1, ax1 = plt.subplots()
    ax1.quiver(0, 0, Vr_ph, 0, angles='xy', scale_units='xy', scale=1, color='g', label='Vr (Ref)')
    ax1.set_xlim(-Vr_ph*0.1, Vr_ph*1.2); ax1.set_ylim(-Vr_ph*0.5, Vr_ph*0.5)
    ax1.grid(True); ax1.legend(); st.pyplot(fig1)

# 2. رسمة جهد الإرسال (المثلث الكامل Vs = A*Vr + B*Ir)
with col2:
    st.subheader("2. Sending Voltage Triangle")
    fig2, ax2 = plt.subplots()
    # رسم A*Vr
    ax2.quiver(0, 0, Term1.real, Term1.imag, angles='xy', scale_units='xy', scale=1, color='orange', label='A*Vr')
    # رسم B*Ir يبدأ من نهاية A*Vr
    ax2.quiver(Term1.real, Term1.imag, Term2.real, Term2.imag, angles='xy', scale_units='xy', scale=1, color='red', label='B*Ir (Drop)')
    # المحصلة Vs
    ax2.quiver(0, 0, Vs_vec.real, Vs_vec.imag, angles='xy', scale_units='xy', scale=1, color='b', label='Vs (Total)')
    ax2.set_title(f"Vs = {vs_kv_calc:.1f} kV")
    lim_v = max(abs(Vs_vec), Vr_ph) * 1.2
    ax2.set_xlim(-lim_v*0.1, lim_v); ax2.set_ylim(-lim_v*0.5, lim_v*0.5)
    ax2.grid(True); ax2.legend(); st.pyplot(fig2)

# 3. مثلث قدرة الاستقبال
with col3:
    st.subheader("3. Receiving Power Triangle")
    fig3, ax3 = plt.subplots()
    ax3.plot([0, pr_calc], [0, 0], 'g-', lw=3, label='Pr (MW)')
    ax3.plot([pr_calc, pr_calc], [0, qr_calc], 'lime', lw=3, label='Qr (MVAr)')
    ax3.plot([0, pr_calc], [0, qr_calc], 'k--') # الوتر Sr
    ax3.grid(True); ax3.legend(); st.pyplot(fig3)

col4, col5, col6 = st.columns(3)

# 4. مثلث قدرة الإرسال
with col4:
    st.subheader("4. Sending Power Triangle")
    fig4, ax4 = plt.subplots()
    ax4.plot([0, ps_calc], [0, 0], 'b-', lw=3, label='Ps (MW)')
    ax4.plot([ps_calc, ps_calc], [0, qs_calc], 'skyblue', lw=3, label='Qs (MVAr)')
    ax4.plot([0, ps_calc], [0, qs_calc], 'k--') # الوتر Ss
    ax4.grid(True); ax4.legend(); st.pyplot(fig4)

# 5. دائرة القدرة (Power Circle)
with col5:
    st.subheader("5. Power Circle Diagram")
    fig5, ax5 = plt.subplots()
    t = np.linspace(0, 2*np.pi, 100)
    r_circle = abs(Sr_vec/1e6)
    ax5.plot(r_circle*np.cos(t), r_circle*np.sin(t), 'r--', alpha=0.6, label='Pr-Qr Circle')
    ax5.scatter([pr_calc], [qr_calc], color='black', s=100, label='Operating Pt')
    ax5.axhline(0, color='black', lw=1); ax5.axvline(0, color='black', lw=1)
    ax5.grid(True); ax5.legend(); st.pyplot(fig5)

# 6. المخطط التجميعي (Vs vs Vr)
with col6:
    st.subheader("6. Combined Voltage Phasors")
    fig6, ax6 = plt.subplots()
    ax6.quiver(0, 0, Vr_ph, 0, angles='xy', scale_units='xy', scale=1, color='g', label='Vr')
    ax6.quiver(0, 0, Vs_vec.real, Vs_vec.imag, angles='xy', scale_units='xy', scale=1, color='b', label='Vs')
    ax6.set_title(f"Delta Angle = {np.angle(Vs_vec, deg=True):.2f}°")
    ax6.grid(True); ax6.legend(); st.pyplot(fig6)

# --- الجدول والنتائج ---
st.divider()
st.subheader("📊 Analytical Results")
st.table({
    "البيان (Parameter)": ["جهد الإرسال (Vs)", "جهد الاستقبال (Vr)", "كفاءة النظام (Efficiency)", "تنظيم الجهد (Regulation)"],
    "القيمة (Value)": [f"{vs_kv_calc:.2f} kV", f"{vr_kv} kV", f"{(pr_calc/ps_calc)*100:.2f} %", f"{((vs_kv_calc-vr_kv)/vr_kv)*100:.2f} %"]
})
