import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pw, mx_ext, my_ext, q_ult, fs, piles_df):
    """
    Calculates individual pile reactions using the Rigid Pile Cap Method.
    Includes data cleaning to handle dynamic row additions safely.
    """
    # 1.1 Data Cleaning: Remove rows without a name and fill NaNs with 0.0
    piles_df = piles_df.dropna(subset=['Pile_Name'])
    if piles_df.empty:
        return None, None

    for col in ['x_design', 'y_design', 'dev_x', 'dev_y']:
        piles_df[col] = pd.to_numeric(piles_df[col]).fillna(0.0)

    piles = piles_df.to_dict('records')
    n = len(piles)
    
    # Calculate Allowable Safe Load Capacity
    safe_load = q_ult / fs

    # Pre-processing: Compute actual coordinates from design + deviation
    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']

    # Step 1: Compute New Center of Gravity (CG) of the pile group
    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    # Step 2: Compute Eccentricities & Total Eccentric Moments about the new CG
    ecc_mx = pw * cg_y
    ecc_my = pw * cg_x
    
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # Step 3: Compute Pile Coordinates relative to New CG and Group Moments of Inertia
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x
        p['y_i'] = p['y_actual'] - cg_y
        p['x_i_sq'] = p['x_i'] ** 2
        p['y_i_sq'] = p['y_i'] ** 2
        ixx += p['y_i_sq']
        iyy += p['x_i_sq']

    # Step 4: Compute Pile Reactions (Ri) & Validate Safety Status
    overall_passed = True
    for p in piles:
        term1 = pw / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3
        
        # Safety Evaluation
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
st.set_page_config(page_title="Advanced Pile Deviation Analysis", layout="wide")

st.title("🏗️ Dynamic Pile Deviation & Safety Analysis Report")
st.markdown("Calculate pile reactions with **fully dynamic pile configurations**. Add or remove piles freely using the interactive table.")

st.divider()

# --- Input Section ---
st.subheader("1. Design Parameters Input")
col_p, col_mx, col_my = st.columns(3)
pw_input = col_p.number_input("Total Working Axial Load (Pw) - [Tons]", value=100.0, step=10.0)
mx_input = col_mx.number_input("External Working Moment Mx - [Ton-m]", value=0.0, step=1.0)
my_input = col_my.number_input("External Working Moment My - [Ton-m]", value=0.0, step=1.0)

col_qult, col_fs, col_safe = st.columns(3)
qult_input = col_qult.number_input("Ultimate Pile Capacity (Q_ult) - [Tons]", value=75.0, step=5.0)
fs_input = col_fs.number_input("Factor of Safety (FS)", value=2.5, step=0.1)

calculated_safe_load = qult_input / fs_input if fs_input > 0 else 0
col_safe.info(f"🛡️ **Calculated Safe Pile Capacity:** {calculated_safe_load:.3f} Tons")

st.subheader("2. Pile Coordinates & Construction Deviations Management")
st.markdown("""
💡 **How to modify the Pile Group configuration:**
* **To Edit:** Click directly on any cell to change coordinates or names.
* **To Add a Pile:** Scroll to the bottom of the table and click the **`+ Add row`** button.
* **To Delete a Pile:** Click the blank space on the left side of the row to select it, then press **`Delete`** or **`Backspace`** on your keyboard.
""")

# Default Data (F4 Foundation Setup)
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'dev_x': [0.05, 0.03, -0.01, 0.04],
    'dev_y': [0.08, -0.02, -0.04, 0.06]
})

# เปิดใช้งาน Dynamic Table
edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- Calculation & Results Section ---
if st.button("🧮 Calculate & Generate High-Detail Report", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pw_input, mx_input, my_input, qult_input, fs_input, edited_df)
    
    if df_res is not None:
        
        # VISUAL STATUS BADGE
        st.subheader("🛡️ Safety Verification Status")
        if summary['overall_passed']:
            st.success(f"🟢 **PASSED** - Structural safety requirements met. All individual pile reactions are within the allowable safe capacity ($\le$ {summary['safe_load']:.3f} Tons).")
        else:
            st.error(f"🔴 **FAILED (OVERLOADED)** - Design criteria breached! One or more piles have exceeded the allowable safe capacity ({summary['safe_load']:.3f} Tons). Structural intervention required.")

        st.divider()

        # HIGH-DETAIL CALCULATION SHEET
        with st.expander("📝 View Comprehensive Step-by-Step Calculation Sheet", expanded=True):
            
            st.markdown("### Step 1: Geotechnical Allowable Pile Capacity ($R_{allow}$)")
            st.markdown(rf"$$ R_{{allow}} = \frac{{Q_{{ult}}}}{{FS}} = \frac{{{summary['q_ult']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_load']:.3f} \text{{ Tons}} $$")

            st.markdown("### Step 2: Pre-processing & Actual Coordinates Estimation")
            st.markdown(r"$$ x_{{actual}} = x_{{design}} + \text{{dev\_x}}, \quad y_{{actual}} = y_{{design}} + \text{{dev\_y}} $$")
            
            df_actuals = df_res[['Pile_Name', 'x_design', 'dev_x', 'x_actual', 'y_design', 'dev_y', 'y_actual']].copy()
            st.table(df_actuals.style.format({col: '{:.4f}' for col in df_actuals.columns if col != 'Pile_Name'}))

            st.markdown("### Step 3: Shifted Center of Gravity (CG) of the Group")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum x_{{actual}}}}{{n}} = \frac{{{df_res['x_actual'].sum():.4f}}}{{{summary['n']}}} = {summary['cg_x']:.4f} \text{{ m}} $$")
            st.markdown(rf"$$ \bar{{y}} = \frac{{\sum y_{{actual}}}}{{n}} = \frac{{{df_res['y_actual'].sum():.4f}}}{{{summary['n']}}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            
            st.markdown("### Step 4: Total Eccentric Moments about New Centroid ($M_{x,cg}, M_{y,cg}$)")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_w \cdot \bar{{y}}) = {summary['mx_ext']:.3f} + ({summary['pw']:.3f} \cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_w \cdot \bar{{x}}) = {summary['my_ext']:.3f} + ({summary['pw']:.3f} \cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("### Step 5: Group Properties & Individual Moments of Inertia ($I_{xx}, I_{yy}$)")
            
            df_inertia = df_res[['Pile_Name', 'x_actual', 'y_actual', 'x_i', 'y_i', 'x_i_sq', 'y_i_sq']].copy()
            df_inertia.columns = ['Pile', 'x_actual', 'y_actual', 'x_i (x - x̄)', 'y_i (y - ȳ)', 'x_i²', 'y_i²']
            st.table(df_inertia.style.format({col: '{:.4f}' for col in df_inertia.columns if col != 'Pile'}))

            st.markdown(rf"$$ I_{{xx}} = \sum (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{yy}} = \sum (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            
            st.markdown("### Step 6: Detailed Pile Reaction Substitution & Evaluation ($R_i$)")
            st.markdown(r"$$ R_i = \frac{P_w}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} \le R_{allow} $$")
            
            st.markdown("**Complete Substitution Breakdown:**")
            for idx, row in df_res.iterrows():
                check_symbol = r"\le" if row['Ri'] <= summary['safe_load'] else r"\gt"
                status_latex = r"\text{ [OK - PASSED]}" if row['Ri'] <= summary['safe_load'] else r"\text{ [NG - OVERLOADED]}"
                
                formula = (
                    rf"$$ R_{{{row['Pile_Name']}}} = \frac{{{summary['pw']:.2f}}}{{{summary['n']}}} + "
                    rf"\frac{{{summary['mx_cg']:.4f} \cdot ({row['y_i']:.4f})}}{{{summary['ixx']:.4f}}} + "
                    rf"\frac{{{summary['my_cg']:.4f} \cdot ({row['x_i']:.4f})}}{{{summary['iyy']:.4f}}} "
                    rf"= {row['Ri']:.3f} \text{{ Tons}} {check_symbol} {summary['safe_load']:.3f} \text{{ Tons}} {status_latex} $$"
                )
                st.markdown(formula)

        st.divider()

        # --- Graphical Plots & Summary Display ---
        out_col1, out_col2 = st.columns([1, 1])
        
        with out_col1:
            st.subheader("📊 Summary Table")
            
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
                st.error(f"⚠️ **Critical Alert:** Pile **{max_pile}** carries **{max_r:.3f} Tons** which overshoots the structural safety barrier of {summary['safe_load']:.2f} Tons.")
            else:
                st.info(f"ℹ️ **Design Summary:** Pile **{max_pile}** sustains the governing maximum load of **{max_r:.3f} Tons**, operating safely within limits.")

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
            
            # --- AUTO SCALING LOGIC FOR AXIS ---
            all_x = pd.concat([df_res['x_design'], df_res['x_actual']])
            all_y = pd.concat([df_res['y_design'], df_res['y_actual']])
            max_val = max(all_x.abs().max(), all_y.abs().max(), 0.5) * 1.6
            ax.set_xlim(-max_val, max_val)
            ax.set_ylim(-max_val, max_val)
            
            ax.set_xlabel("X-Axis (meters)")
            ax.set_ylabel("Y-Axis (meters)")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(loc='upper right', fontsize=8)
            
            st.pyplot(fig)
    else:
        st.warning("Please add at least one pile to the coordinate table.")
