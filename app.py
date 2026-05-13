import streamlit as st
import numpy as np
import plotly.graph_objects as go
import pandas as pd

st.set_page_config(page_title="Power System Project - Phase #1", layout="wide")

# --- 1. Line Parameters & Constants ---
with st.sidebar:
    st.header("Line Constants")
    mode = st.radio("Input Mode:", ["ABCD Constants", "Z & Y Magnitudes"])
    if mode == "ABCD Constants":
        a_m = st.number_input("A Mag:", value=0.9704, format="%.4f")
        alpha = st.number_input("Alpha (deg):", value=1.118)
        b_m = st.number_input("B Mag:", value=36.7569, format="%.4f")
        beta = st.number_input("Beta (deg):", value=80.0)
        z_mag_calc = b_m
    else:
        z_mag = st.number_input("Z Mag:", value=38.1)
        z_ang = st.number_input("Z Ang:", value=74.0)
        y_mag = st.number_input("Y Mag:", value=0.001, format="%.6f")
        y_ang = st.number_input("Y Ang:", value=90.0)
        Z = z_mag * np.exp(1j * np.radians(z_ang))
        Y = y_mag * np.exp(1j * np.radians(y_ang))
        A_comp = 1 + (Z * Y) / 2
        a_m, alpha, b_m, beta = np.abs(A_comp), np.degrees(np.angle(A_comp)), z_mag, z_ang
        z_mag_calc = z_mag

    st.divider()
    st.header("Interactive Control")
    vr_kv = st.number_input("Vr (kV) [Global]:", value=132.0)
    p_int = st.number_input("Interactive Pr (MW):", value=100.0)
    pf_int_type = st.selectbox("Interactive PF Type:", ["Lagging", "Leading", "Unity"])
    pf_int_val = st.slider("Interactive PF Value:", 0.1, 1.0, 0.85)

# --- 2. Calculation Engine ---
def get_analysis(pr, vr, pf, pf_type):
    alpha_r, beta_r = np.radians(alpha), np.radians(beta)
    gamma_r = beta_r - alpha_r
    phi_deg = np.degrees(np.arccos(pf))
    phi_r = -np.radians(phi_deg) if pf_type == "Lagging" else (np.radians(phi_deg) if pf_type == "Leading" else 0.0)
    
    qr = pr * np.tan(phi_r)
    sr = np.sqrt(pr**2 + qr**2)
    r_n = (a_m * vr**2) / b_m
    nx, ny = -r_n * np.cos(gamma_r), r_n * np.sin(gamma_r)
    chord = np.sqrt((pr - nx)**2 + (qr - ny)**2)
    vs = (chord * b_m) / vr
    
    # Sending Calculations
    r_m = (a_m * vs**2) / b_m
    mx, my = r_m * np.cos(gamma_r), -r_m * np.sin(gamma_r)
    theta = np.arctan2(qr - ny, pr - nx) - (np.pi - gamma_r)
    angle_s = -gamma_r + abs(theta + alpha_r)
    ps = mx + chord * np.cos(angle_s)
    qs = my + chord * np.sin(angle_s)
    ss = np.sqrt(ps**2 + qs**2)
    pfs_val = ps / ss
    
    # Sending PF Angle and Type
    phi_s_deg = np.degrees(np.arccos(pfs_val))
    # If Qs is positive -> Leading, if Negative -> Lagging (Generator convention in Power Circles)
    pfs_type = "Leading" if qs > 0 else ("Lagging" if qs < 0 else "Unity")
    
    # Efficiency & Regulation
    eff = (pr / ps) * 100 if ps > 0 else 0
    v_reg = ((vs/a_m - vr) / vr) * 100
    
    return {
        "Type": pf_type, "P": pr, "Q": qr, "S": sr, "PF": pf, "Phi": phi_deg,
        "Vs": vs, "Ps": ps, "Qs": qs, "Ss": ss, "PFs": pfs_val, "Phi_s": phi_s_deg, "PFs_Type": pfs_type,
        "Eff": eff, "Vreg": v_reg,
        "nx": nx, "ny": ny, "mx": mx, "my": my, "chord": chord
    }

# --- 3. Plotting Helper ---
def draw_case_plots(case_data, case_id):
    col1, col2, col3 = st.columns(3)
    angles = np.linspace(0, 2*np.pi, 200)
    p_sil = (vr_kv**2) / z_mag_calc

    with col1:
        f1 = go.Figure(); f1.add_hline(0); f1.add_vline(0)
        f1.add_trace(go.Scatter(x=case_data['nx']+case_data['chord']*np.cos(angles), y=case_data['ny']+case_data['chord']*np.sin(angles), mode='lines', line=dict(dash='dot', color='gray'), showlegend=False))
        f1.add_trace(go.Scatter(x=[0, case_data['nx'], case_data['P'], 0], y=[0, case_data['ny'], case_data['Q'], 0], fill='toself', fillcolor='rgba(255,0,0,0.2)', name="Receiving"))
        f1.add_trace(go.Scatter(x=[p_sil], y=[0], mode='markers', marker=dict(size=10, symbol='star', color='gold'), name="SIL"))
        f1.update_layout(title="Receiving End", height=300)
        st.plotly_chart(f1, use_container_width=True, key=f"rec_{case_id}")

    with col2:
        f2 = go.Figure(); f2.add_hline(0); f2.add_vline(0)
        f2.add_trace(go.Scatter(x=case_data['mx']+case_data['chord']*np.cos(angles), y=case_data['my']+case_data['chord']*np.sin(angles), mode='lines', line=dict(dash='dot', color='gray'), showlegend=False))
        f2.add_trace(go.Scatter(x=[0, case_data['mx'], case_data['Ps'], 0], y=[0, case_data['my'], case_data['Qs'], 0], fill='toself', fillcolor='rgba(0,255,0,0.2)', name="Sending"))
        f2.update_layout(title="Sending End", height=300)
        st.plotly_chart(f2, use_container_width=True, key=f"send_{case_id}")

    with col3:
        f3 = go.Figure(); f3.add_hline(0); f3.add_vline(0)
        f3.add_trace(go.Scatter(x=[0, case_data['nx'], case_data['P'], 0], y=[0, case_data['ny'], case_data['Q'], 0], fill='toself', name="Rec", line=dict(color='red')))
        f3.add_trace(go.Scatter(x=[0, case_data['mx'], case_data['Ps'], 0], y=[0, case_data['my'], case_data['Qs'], 0], fill='toself', name="Send", line=dict(color='green')))
        f3.update_layout(title="Comparison", height=300)
        st.plotly_chart(f3, use_container_width=True, key=f"comb_{case_id}")

# --- 4. Main Interface ---
st.title("Power System Analysis - Phase #1")

# Section 1: Interactive Analysis
st.header("1. Interactive Case Analysis")
res_int = get_analysis(p_int, vr_kv, pf_int_val, pf_int_type)
draw_case_plots(res_int, "interactive")

st.subheader("Results Summary")
col_a, col_b = st.columns(2)
with col_a:
    st.write("**Sending End Parameters:**")
    st.write(f"- Voltage ($V_s$): `{res_int['Vs']:.2f} kV`")
    st.write(f"- Active Power ($P_s$): `{res_int['Ps']:.2f} MW`")
    st.write(f"- Reactive Power ($Q_s$): `{res_int['Qs']:.2f} MVAR`")
    st.write(f"- Power Factor ($PF_s$): `{res_int['PFs']:.3f} ({res_int['PFs_Type']})`")
    st.write(f"- PF Angle ($\phi_s$): `{res_int['Phi_s']:.2f}°`")

with col_b:
    st.write("**Performance & Receiving:**")
    st.write(f"- Receiver $Q_r$: `{res_int['Q']:.2f} MVAR`")
    st.write(f"- Efficiency ($\eta$): `{res_int['Eff']:.2f} %`")
    st.write(f"- Voltage Regulation: `{res_int['Vreg']:.2f} %`")

st.divider()

# Section 2: Comparative Study
st.header("2. Comparative Study (Fixed Cases)")
fixed_params = [
    {"p": 100.0, "pf": 0.85, "type": "Lagging"},
    {"p": 120.0, "pf": 1.0, "type": "Unity"},
    {"p": 80.0, "pf": 0.9, "type": "Leading"}
]

fixed_results = []
for i, param in enumerate(fixed_params):
    with st.expander(f"Condition {i+1}: {param['type']} PF", expanded=True):
        res = get_analysis(param['p'], vr_kv, param['pf'], param['type'])
        fixed_results.append(res)
        draw_case_plots(res, i)

st.header("3. Numerical Summary Table")
df_final = pd.DataFrame(fixed_results)
st.table(df_final[["Type", "P", "Q", "Ps", "Qs", "PFs", "PFs_Type", "Vs", "Eff", "Vreg"]].rename(columns={
    "PFs_Type": "S. End Type", "Eff": "Eff %", "Vreg": "Reg %"
}).style.format(subset=["P", "Q", "Ps", "Qs", "Vs", "Eff %", "Reg %"], precision=2))
