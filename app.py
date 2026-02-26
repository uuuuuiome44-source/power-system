import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# إعداد الصفحة
st.set_page_config(page_title="Power System Project", layout="wide")
st.title("⚡ Power System Project: Transmission Line Analysis")

# --- القائمة الجانبية (Sidebar) ---
st.sidebar.header("🎛️ مدخلات النظام (Input Parameters)")
vr_kv = st.sidebar.number_input("Receiving Voltage (Vr) kV", value=220.0)
pr_mw = st.sidebar.slider("Active Power (Pr) MW", 10, 500, 150)

# اختيار النوع أولاً ثم القيمة
pf_type = st.sidebar.selectbox("Load PF Type", ["Lagging", "Unity", "Leading"])
if pf_type == "Unity":
    qr_mvar = 0.0
else:
    qr_mvar = st.sidebar.slider("Reactive Power (Qr) MVAr", 1, 300, 100)
    if pf_type == "Leading": qr_mvar = -qr_mvar

st.sidebar.subheader("Line Constants (Z & Y)")
R = st.sidebar.number_input("Resistance R (Ω)", value=10.0)
XL = st.sidebar.number_input("Inductive XL (Ω)", value=50.0)
XC = st.sidebar.number_input("Capacitive XC (Ω)", value=1000.0)

# --- الحسابات الهندسية (Nominal Pi Model) ---
Vr_ph = (vr_kv * 1000) / np.sqrt(3) # جهد الوجه (Reference)
Sr_vec = 3 * (pr_mw + 1j * qr_mvar) * 1e6 / 3 # قدرة الوجه الواحد
Ir_vec = np.conj(Sr_vec / Vr_ph) # تيار الحمل (Vector)

# ثوابت ABCD
Z = complex(R, XL)
Y = 1j / XC
A = 1 + (Y * Z / 2)
B = Z
C_param = Y * (1 + Y * Z / 4)
D = A

# حساب جهد الإرسال (Vs = A*Vr + B*Ir)
Term1 = A * Vr_ph # مركبة الـ No Load
Term2 = B * Ir_vec # مركبة الـ Load Drop
Vs_vec = Term1 + Term2
vs_kv_calc = (abs(Vs_vec) * np.sqrt(3)) / 1000

# حساب تيار وقدرة الإرسال
Is_vec = C_param * Vr_ph + D * Ir_vec
Ss_vec = 3 * Vs_vec * np.conj(Is_vec)
ps_mw, qs_mvar = Ss_vec.real/1e6, Ss_vec.imag/1e6
eff = (pr_mw / ps_mw * 100) if ps_mw > 0 else 0
pf_calc = pr_mw / (np.sqrt(pr_mw**2 + qr_mvar**2))

# --- الرسم البياني (6 رسومات) ---
c1, c2, c3 = st.columns(3)

with c1:
    st.subheader("1. Receiving End Voltage")
    fig1, ax1 = plt.subplots()
    ax1.quiver(0, 0, Vr_ph/1000, 0, angles='xy', scale_units='xy', scale=1, color='g', label='Vr')
    ax1.set_xlim(-20, (Vr_ph/1000)*1.5); ax1.set_ylim(-50, 50)
    ax1.set_xlabel("kV"); ax1.grid(True); st.pyplot(fig1)

with c2:
    st.subheader("2. Vs Phasor Triangle")
    fig2, ax2 = plt.subplots()
    # رسم A*Vr
    ax2.quiver(0, 0, Term1.real/1000, Term1.imag/1000, angles='xy', scale_units='xy', scale=1, color='orange', label='A*Vr')
    # رسم B*Ir يبدأ من نهاية A*Vr
    ax2.quiver(Term1.real/1000, Term1.imag/1000, Term2.real/1000, Term2.imag/1000, angles='xy', scale_units='xy', scale=1, color='r', label='B*Ir')
    # المحصلة Vs
    ax2.quiver(0, 0, Vs_vec.real/1000, Vs_vec.imag/1000, angles='xy', scale_units='xy', scale=1, color='b', label='Vs')
    v_max = max(abs(Vs_vec)/1000, Vr_ph/1000) * 1.2
    ax2.set_xlim(-10, v_max); ax2.set_ylim(-v_max/2, v_max/2)
    ax2.legend(); ax2.grid(True); st.pyplot(fig2)

with c3:
    st.subheader("3. Receiving Power Triangle")
    fig3, ax3 = plt.subplots()
    ax3.plot([0, pr_mw], [0, 0], 'b-', lw=4, label='Pr')
    ax3.plot([pr_mw, pr_mw], [0, qr_mvar], 'r-', lw=4, label='Qr')
    ax3.plot([0, pr_mw], [0, qr_mvar], 'k--')
    ax3.set_title(f"PF = {pf_calc:.3f}"); ax3.legend(); ax3.grid(True); st.pyplot(fig3)

c4, c5, c6 = st.columns(3)

with c4:
    st.subheader("4. Sending Power Triangle")
    fig4, ax4 = plt.subplots()
    ax4.plot([0, ps_mw], [0, 0], 'darkblue', lw=3, label='Ps')
    ax4.plot([ps_mw, ps_mw], [0, qs_mvar], 'darkred', lw=3, label='Qs')
    ax4.legend(); ax4.grid(True); st.pyplot(fig4)

with c5:
    st.subheader("5. Power Circle")
    fig5, ax5 = plt.subplots()
    t = np.linspace(0, 2*np.pi, 100)
    rad = np.sqrt(pr_mw**2 + qr_mvar**2)
    ax5.plot(rad*np.cos(t), rad*np.sin(t), 'r--', alpha=0.5)
    ax5.scatter([pr_mw], [qr_mvar], color='k')
    ax5.axhline(0, color='k', lw=1); ax5.axvline(0, color='k', lw=1)
    ax5.grid(True); st.pyplot(fig5)

with c6:
    st.subheader("6. Combined Voltages")
    fig6, ax6 = plt.subplots()
    ax6.quiver(0, 0, Vr_ph/1000, 0, angles='xy', scale_units='xy', scale=1, color='g', label='Vr')
    ax6.quiver(0, 0, Vs_vec.real/1000, Vs_vec.imag/1000, angles='xy', scale_units='xy', scale=1, color='b', label='Vs')
    ax6.legend(); ax6.grid(True); st.pyplot(fig6)

# --- الجدول ---
st.divider()
st.table({
    "Parameter": ["Vs (kV)", "Vr (kV)", "Efficiency (%)", "Voltage Reg (%)", "Power Angle (δ)"],
    "Result": [f"{vs_kv_calc:.2f}", f"{vr_kv}", f"{eff:.2f}%", f"{((vs_kv_calc-vr_kv)/vr_kv)*100:.2f}%", f"{np.angle(Vs_vec, deg=True):.2f}°"]
})
