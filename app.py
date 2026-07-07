import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pw, mx_ext, my_ext, q_ult, fs, piles_df):
    piles = piles_df.to_dict('records')
    n = len(piles)
    
    if n == 0:
        return None, None

    # คำนวณ Safe Load จาก FS
    safe_load = q_ult / fs

    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']

    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    ecc_mx = pw * cg_y
    ecc_my = pw * cg_x
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x
        p['y_i'] = p['y_actual'] - cg_y
        p['x_i_sq'] = p['x_i'] ** 2
        p['y_i_sq'] = p['y_i'] ** 2
        ixx += p['y_i_sq']
        iyy += p['x_i_sq']

    overall_passed = True
    for p in piles:
        term1 = pw / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3
        
        # Safety Evaluation (ใช้ Safe Load ที่หาร FS แล้ว)
        if p['Ri'] > safe_load:
            p['Status'] = 'FAIL (Overload)'
            overall_passed = False
        else:
            p['Status'] = 'PASS'

    summary = {
        'n': n, 'cg_x': cg_x, 'cg_y': cg_y,
        'ixx': ixx, 'iyy': iyy,
        'mx_cg': mx_cg, 'my_cg': my_cg,
        'ecc_mx': ecc_mx, 'ecc_my': ecc_my,
        'pw': pw, 'mx_ext': mx_ext, 'my_ext': my_ext,
        'q_ult': q_ult, 'fs': fs, 'safe_load': safe_load,
        'overall_passed': overall_passed
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. Streamlit UI and Output Rendering
# ==========================================
st.set_page_config(page_title="Pile Deviation & Safety Analysis", layout="wide")

st.title("🏗️ Pile Deviation & Safety Analysis Report")
st.markdown("Calculate individual pile reactions with **Working Loads** and verify against safe capacity using a **Factor of Safety (FS)**.")

st.divider()

# --- Input Section ---
st.subheader("1. Design Loads (Working Stress) & Pile Capacity")
col_p, col_mx, col_my = st.columns(3)
pw_input = col_p.number_input("Total Working Axial Load (Pw) - [Tons]", value=100.0, step=10.0, help="DL + LL (Unfactored)")
mx_input = col_mx.number_input("Working Moment Mx - [Ton-m]", value=0.0, step=1.0)
my_input = col_my.number_input("Working Moment My - [Ton-m]", value=0.0, step=1.0)

col_qult, col_fs, col_safe = st.columns(3)
qult_input = col_qult.number_input("Ultimate Pile Capacity (Q_ult) - [Tons]", value=75.0, step=5.0)
fs_input = col_fs.number_input("Factor of Safety (FS)", value=2.5, step=0.1)

# แสดงค่า Safe load แบบ Real-time ให้ผู้ใช้เห็น
calculated_safe_load = qult_input / fs_input if fs_input > 0 else 0
col_safe.info(f"🛡️ **Safe Load Capacity:** {calculated_safe_load:.2f} Tons")

st.subheader("2. Pile Coordinates & Deviations")
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'dev_x': [0.05, 0.03, -0.01, 0.04],
    'dev_y': [0.08, -0.02, -0.04, 0.06]
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- Calculation & Results Section ---
if st.button("🧮 Calculate & Verify Safety Status", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pw_input, mx_input, my_input, qult_input, fs_input, edited_df)
    
    if df_res is not None:
        
        st.subheader("🛡️ Safety Verification Status")
        if summary['overall_passed']:
            st.success(f"🟢 **PASSED** - All piles are safe. Maximum pile reaction $\le$ Safe Load ({summary['safe_load']:.2f} Tons).")
        else:
            st.error(f"🔴 **FAILED (OVERLOADED)** - Critical Alert! One or more piles have exceeded the Safe Load ({summary['safe_load']:.2f} Tons).")

        st.divider()

        with st.expander("📝 View Step-by-Step Calculation Sheet", expanded=False):
            st.markdown("### Step 1: Pile Safe Capacity Calculation")
            st.markdown(rf"$$ \text{{Safe Load}} = \frac{{Q_{{ult}}}}{{FS}} = \frac{{{summary['q_ult']}}}{{{summary['fs']}}} = {summary['safe_load']:.3f} \text{{ Tons}} $$")

            st.markdown("### Step 2: New Center of Gravity (CG)")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum x_{{actual}}}}{{n}} = {summary['cg_x']:.4f} \text{{ m}}, \quad \bar{{y}} = \frac{{\sum y_{{actual}}}}{{n}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            
            st.markdown("### Step 3: Total Eccentric Moments ($M_{x,cg}, M_{y,cg}$)")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_w \cdot \bar{{y}}) = {summary['mx_ext']} + ({summary['pw']} \cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_w \cdot \bar{{x}}) = {summary['my_ext']} + ({summary['pw']} \cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("### Step 4: Group Moment of Inertia ($I_{xx}, I_{yy}$)")
            st.markdown(rf"$$ I_{{xx}} = \sum (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2, \quad I_{{yy}} = \sum (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            
            st.markdown("### Step 5: Individual Pile Reactions & Safety Check")
            st.markdown(r"$$ R_i = \frac{P_w}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} \le \text{Safe Load} $$")
            
            for idx, row in df_res.iterrows():
                check_symbol = r"\le" if row['Ri'] <= summary['safe_load'] else r"\gt"
                status_latex = r"\text{ [OK]}" if row['Ri'] <= summary['safe_load'] else r"\text{ [NG]}"
                formula = rf"$$ R_{{{row['Pile_Name']}}} = \dots = {row['Ri']:.3f} \text{{ Tons}} {check_symbol} {summary['safe_load']:.3f} \text{{ Tons}} {status_latex} $$"
                st.markdown(formula)

        st.divider()

        out_col1, out_col2 = st.columns([1, 1])
        
        with out_col1:
            st.subheader("📊 Summary of Pile Reactions ($R_i$)")
            
            def highlight_fail(row):
                return ['background-color: #ffcccc' if row['Status'] != 'PASS' else '' for _ in row]
            
            df_display = df_res[['Pile_Name', 'dev_x', 'dev_y', 'Ri', 'Status']]
            st.dataframe(
                df_display.style.apply(highlight_fail, axis=1).format({'dev_x': '{:.3f}', 'dev_y': '{:.3f}', 'Ri': '{:.3f}'}), 
                use_container_width=True
            )
            
            max_r = df_res['Ri'].max()
            max_pile = df_res.loc[df_res['Ri'].idxmax(), 'Pile_Name']
            
            if max_r > summary['safe_load']:
                st.error(f"⚠️ **Critical Overload:** Pile **{max_pile}** Max Load = **{max_r:.3f} Tons** (Safe Limit = {summary['safe_load']:.2f} Tons).")
            else:
                st.info(f"ℹ️ **Maximum Pile Load:** Pile **{max_pile}** carries **{max_r:.3f} Tons** (Within safe limits).")

        with out_col2:
            st.subheader("📐 Foundation Deviation Plan")
            
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.scatter(df_res['x_design'], df_res['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            
            colors = ['#ff4d4d' if status != 'PASS' else 'deepskyblue' for status in df_res['Status']]
            edge_colors = ['red' if status != 'PASS' else 'blue' for status in df_res['Status']]
            ax.scatter(df_res['x_actual'], df_res['y_actual'], s=450, color=colors, alpha=0.4, edgecolors=edge_colors, linewidth=1.5, label='Actual Position')
            
            for idx, row in df_res.iterrows():
                label_color = 'red' if row['Status'] != 'PASS' else 'black'
                ax.text(row['x_actual'], row['y_actual'], f"{row['Pile_Name']}\n{row['Ri']:.2f} t", ha='center', va='center', fontsize=9, color=label_color, weight='bold')
                ax.annotate('', xy=(row['x_actual'], row['y_actual']), xytext=(row['x_design'], row['y_design']), arrowprops=dict(arrowstyle="->", color='red', lw=1))

            ax.plot(0, 0, marker='+', color='black', markersize=18, markeredgewidth=2.5, label='Column Center (0,0)')
            ax.plot(summary['cg_x'], summary['cg_y'], marker='x', color='crimson', markersize=12, markeredgewidth=2.5, label='New Pile CG')
            
            ax.axhline(0, color='black', linewidth=0.6, linestyle=':')
            ax.axvline(0, color='black', linewidth=0.6, linestyle=':')
            ax.set_aspect('equal')
            
            max_val = max(df_res['x_design'].abs().max(), df_res['y_design'].abs().max()) * 1.8
            ax.set_xlim(-max_val, max_val)
            ax.set_ylim(-max_val, max_val)
            
            ax.set_xlabel("X-Axis (meters)")
            ax.set_ylabel("Y-Axis (meters)")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(loc='upper right', fontsize=8)
            
            st.pyplot(fig)
    else:
        st.warning("Please add at least one pile to the coordinate table.")
