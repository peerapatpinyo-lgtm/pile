import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pu, mx_ext, my_ext, safe_load, piles_df):
    """
    Calculates the individual pile reactions and performs a safety check 
    against the allowable safe load capacity.
    """
    piles = piles_df.to_dict('records')
    n = len(piles)
    
    if n == 0:
        return None, None

    # Pre-processing: Calculate Actual Coordinates from Design + Deviation
    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']

    # Step 1: Calculate New Center of Gravity (CG)
    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    # Step 2: Calculate Eccentric Moments
    ecc_mx = pu * cg_y
    ecc_my = pu * cg_x
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # Step 3: Calculate Pile Distances from New CG and Group Moment of Inertia
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x
        p['y_i'] = p['y_actual'] - cg_y
        p['x_i_sq'] = p['x_i'] ** 2
        p['y_i_sq'] = p['y_i'] ** 2
        ixx += p['y_i_sq']
        iyy += p['x_i_sq']

    # Step 4: Calculate Individual Pile Reactions (Ri) & Safety Status
    overall_passed = True
    for p in piles:
        term1 = pu / n
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
        'pu': pu, 'mx_ext': mx_ext, 'my_ext': my_ext,
        'safe_load': safe_load,
        'overall_passed': overall_passed
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. Streamlit UI and Output Rendering
# ==========================================
st.set_page_config(page_title="Pile Deviation & Safety Analysis", layout="wide")

st.title("🏗️ Pile Deviation & Safety Analysis Report")
st.markdown("Calculate individual pile reactions with an **Automatic Safety (Pass/Fail) Verification System** based on structural design criteria.")

st.divider()

# --- Input Section ---
st.subheader("1. Design Parameters Input")
col_p, col_mx, col_my, col_safe = st.columns(4)
pu_input = col_p.number_input("Total Ultimate Axial Load (Pu) - [Tons]", value=100.0, step=10.0)
mx_input = col_mx.number_input("External Moment Mx - [Ton-m]", value=0.0, step=1.0)
my_input = col_my.number_input("External Moment My - [Ton-m]", value=0.0, step=1.0)
# ช่องกรอกข้อมูล Safe Load สำหรับตรวจสอบความปลอดภัย
safe_load_input = col_safe.number_input("Safe Pile Capacity (Allowable) - [Tons]", value=30.0, step=5.0)

st.subheader("2. Pile Coordinates & Deviations")
st.caption("💡 Input the Design Coordinates and the Deviation (offset) for each pile. The system will compute the actual position and status automatically. All units are in **Meters (m)**.")

# Default Data (F4 Foundation Setup)
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'dev_x': [0.05, 0.03, -0.01, 0.04],  # Adjusted to trigger realistic load changes
    'dev_y': [0.08, -0.02, -0.04, 0.06]
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- Calculation & Results Section ---
if st.button("🧮 Calculate & Verify Safety Status", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pu_input, mx_input, my_input, safe_load_input, edited_df)
    
    if df_res is not None:
        
        # ==========================================
        # VISUAL STATUS BADGE (แสดงผลทันทีหลังกดคำนวณ)
        # ==========================================
        st.subheader("🛡️ Safety Verification Status")
        if summary['overall_passed']:
            st.success("🟢 **PASSED** - All piles are safe. Maximum pile reaction does not exceed the structural safe load capacity.")
        else:
            st.error("🔴 **FAILED (OVERLOADED)** - Critical Alert! One or more piles have exceeded the allowable safe load capacity. Structural mitigation or additional piles required.")

        st.divider()

        # ==========================================
        # Dynamic Calculation Sheet (Expander)
        # ==========================================
        with st.expander("📝 View Step-by-Step Calculation Sheet", expanded=False):
            st.markdown("### Pre-processing: Actual Coordinates")
            st.markdown("Actual coordinates are calculated by adding the deviations to the design coordinates: $x_{actual} = x_{design} + dev_x$")
            
            df_actuals = df_res[['Pile_Name', 'x_design', 'dev_x', 'x_actual', 'y_design', 'dev_y', 'y_actual']].copy()
            st.dataframe(df_actuals.style.format({col: '{:.3f}' for col in df_actuals.columns if col != 'Pile_Name'}))

            st.markdown("### Step 1: New Center of Gravity (CG) of the Pile Group")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum x_{{actual}}}}{{n}} = {summary['cg_x']:.4f} \text{{ m}} $$")
            st.markdown(rf"$$ \bar{{y}} = \frac{{\sum y_{{actual}}}}{{n}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            
            st.markdown("### Step 2: Total Eccentric Moments ($M_{x,cg}, M_{y,cg}$)")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_u \cdot \bar{{y}}) = {summary['mx_ext']} + ({summary['pu']} \cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_u \cdot \bar{{x}}) = {summary['my_ext']} + ({summary['pu']} \cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("### Step 3: Group Moment of Inertia ($I_{xx}, I_{yy}$)")
            df_inertia = df_res[['Pile_Name', 'x_actual', 'y_actual', 'x_i', 'y_i', 'x_i_sq', 'y_i_sq']].copy()
            df_inertia.columns = ['Pile', 'x_actual', 'y_actual', 'x_i (x - x̄)', 'y_i (y - ȳ)', 'x_i²', 'y_i²']
            st.table(df_inertia.style.format({col: '{:.4f}' for col in df_inertia.columns if col != 'Pile'}))

            st.markdown(rf"$$ I_{{xx}} = \sum (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{yy}} = \sum (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            
            st.markdown("### Step 4: Individual Pile Reactions & Safety Check")
            st.markdown(r"$$ R_i = \frac{P_u}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} \le \text{Safe Load} $$")
            
            for idx, row in df_res.iterrows():
                check_symbol = r"\le" if row['Ri'] <= summary['safe_load'] else r"\gt"
                status_latex = r"\text{ [OK]}" if row['Ri'] <= summary['safe_load'] else r"\text{ [NG - OVERLOAD]}"
                
                formula = rf"$$ R_{{{row['Pile_Name']}}} = \frac{{{summary['pu']}}}{{{summary['n']}}} + \frac{{{summary['mx_cg']:.4f} \cdot ({row['y_i']:.4f})}}{{{summary['ixx']:.4f}}} + \frac{{{summary['my_cg']:.4f} \cdot ({row['x_i']:.4f})}}{{{summary['iyy']:.4f}}} = {row['Ri']:.3f} \text{{ Tons}} {check_symbol} {summary['safe_load']} \text{{ Tons}} {status_latex} $$"
                st.markdown(formula)

        st.divider()

        # ==========================================
        # Summary and Plotting Section
        # ==========================================
        out_col1, out_col2 = st.columns([1, 1])
        
        with out_col1:
            st.subheader("📊 Summary of Pile Reactions ($R_i$)")
            
            # ฟังก์ชันช่วยตบแต่งไฮไลต์สีแดงเฉพาะแถวที่สถานะเป็น FAIL
            def highlight_fail(row):
                return ['background-color: #ffcccc' if row['Status'] != 'PASS' else '' for _ in row]
            
            df_display = df_res[['Pile_Name', 'dev_x', 'dev_y', 'x_actual', 'y_actual', 'Ri', 'Status']]
            
            # แสดงตารางพร้อมทศนิยมและไฮไลต์สีแดง
            st.dataframe(
                df_display.style.apply(highlight_fail, axis=1).format({
                    'dev_x': '{:.3f}', 'dev_y': '{:.3f}',
                    'x_actual': '{:.3f}', 'y_actual': '{:.3f}', 'Ri': '{:.3f}'
                }), 
                use_container_width=True
            )
            
            max_r = df_res['Ri'].max()
            max_pile = df_res.loc[df_res['Ri'].idxmax(), 'Pile_Name']
            
            if max_r > summary['safe_load']:
                st.error(f"⚠️ **Critical Overload:** Pile **{max_pile}** exceeds safe capacity! Max Load = **{max_r:.3f} Tons** (Safe Limit = {summary['safe_load']} Tons).")
            else:
                st.info(f"ℹ️ **Maximum Pile Load:** Pile **{max_pile}** carries the highest load of **{max_r:.3f} Tons**, which is within safe limits.")

        with out_col2:
            st.subheader("📐 Foundation Deviation Plan")
            
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # วาดตำแหน่งดีไซน์ (เส้นประสีเทา)
            ax.scatter(df_res['x_design'], df_res['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            
            # แยกสีเสาเข็มในรูปภาพ: ถ้าต้นไหน Fail ให้เป็นสีแดงใส ถ้า Pass ให้เป็นสีฟ้าใส
            colors = ['#ff4d4d' if status != 'PASS' else 'deepskyblue' for status in df_res['Status']]
            edge_colors = ['red' if status != 'PASS' else 'blue' for status in df_res['Status']]
            
            ax.scatter(df_res['x_actual'], df_res['y_actual'], s=450, color=colors, alpha=0.4, edgecolors=edge_colors, linewidth=1.5, label='Actual Position')
            
            for idx, row in df_res.iterrows():
                label_color = 'red' if row['Status'] != 'PASS' else 'black'
                ax.text(row['x_actual'], row['y_actual'], f"{row['Pile_Name']}\n{row['Ri']:.2f} t", ha='center', va='center', fontsize=9, color=label_color, weight='bold')
                ax.annotate('', xy=(row['x_actual'], row['y_actual']), xytext=(row['x_design'], row['y_design']),
                            arrowprops=dict(arrowstyle="->", color='red', lw=1))

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
