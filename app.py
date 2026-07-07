import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pw, mx_ext, my_ext, q_main, q_micro, fs, piles_df):
    """
    Calculates individual pile reactions using the Rigid Pile Cap Method.
    Supports dual capacity system (Main & Micro-piles) and full structural verification.
    """
    piles_df = piles_df.dropna(subset=['Pile_Name'])
    if piles_df.empty:
        return None, None

    # แปลงค่าว่างหรือค่า Text ให้เป็น Float เพื่อป้องกันคณิตศาสตร์พัง
    for col in ['x_design', 'y_design', 'dev_x', 'dev_y']:
        piles_df[col] = pd.to_numeric(piles_df[col]).fillna(0.0)

    piles = piles_df.to_dict('records')
    n = len(piles)
    
    # คำนวณน้ำหนักปลอดภัยแยกตามประเภทเข็ม
    safe_load_main = q_main / fs if fs > 0 else 0
    safe_load_micro = q_micro / fs if fs > 0 else 0

    # คำนวณพิกัดหน้างานจริง และกำหนดขีดจำกัดแรงปฏิกิริยาประจำต้น
    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']
        p['Allowable_Load'] = safe_load_main if p['Pile_Type'] == 'Main' else safe_load_micro

    # Step 1: คำนวณจุดศูนย์ถ่วงใหม่ (New CG) ของกลุ่มเสาเข็มทั้งหมด
    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    # Step 2: คำนวณโมเมนต์สุทธิรวมเยื้องศูนย์รอบจุด CG ใหม่
    ecc_mx = pw * cg_y
    ecc_my = pw * cg_x
    
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # Step 3: คำนวณพิกัดสัมพัทธ์และค่า Moment of Inertia (Ixx, Iyy) ของกลุ่มเข็ม
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x  # ระยะตั้งฉากถึงแกน Y-CG
        p['y_i'] = p['y_actual'] - cg_y  # ระยะตั้งฉากถึงแกน X-CG
        p['x_i_sq'] = p['x_i'] ** 2
        p['y_i_sq'] = p['y_i'] ** 2
        ixx += p['y_i_sq']  # Ixx เกิดจากผลรวมระยะ y^2
        iyy += p['x_i_sq']  # Iyy เกิดจากผลรวมระยะ x^2

    # Step 4: คำนวณแรงปฏิกิริยารายต้น (Ri) และประเมินสถานะความปลอดภัย
    overall_passed = True
    for p in piles:
        term1 = pw / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3
        
        # เปรียบเทียบกับน้ำหนักบรรทุกที่ยอมให้ตามเงื่อนไขประเภทของตัวเอง
        if p['Ri'] > p['Allowable_Load']:
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
        'q_main': q_main, 'q_micro': q_micro, 'fs': fs,
        'safe_main': safe_load_main, 'safe_micro': safe_load_micro,
        'overall_passed': overall_passed
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. Streamlit UI and Output Rendering
# ==========================================
st.set_page_config(page_title="Advanced Pile Mitigation & Report", layout="wide")

st.title("🏗️ Pile Deviation & Mitigation Analysis (With Detailed Calculation Report)")
st.markdown("Professional-grade foundation redesign tool featuring dual-capacity checking and an **High-Precision Calculation Sheet**.")

st.divider()

# --- Input Section ---
st.subheader("1. Design Parameters Input")
col_p, col_mx, col_my = st.columns(3)
pw_input = col_p.number_input("Total Working Axial Load (Pw) - [Tons]", value=100.0, step=10.0, help="Unfactored Load (DL + LL)")
mx_input = col_mx.number_input("External Working Moment Mx - [Ton-m]", value=0.0, step=1.0)
my_input = col_my.number_input("External Working Moment My - [Ton-m]", value=0.0, step=1.0)

col_qmain, col_qmicro, col_fs = st.columns(3)
qmain_input = col_qmain.number_input("Ultimate Capacity (Main Pile) - [Tons]", value=75.0, step=5.0)
qmicro_input = col_qmicro.number_input("Ultimate Capacity (Micro-pile) - [Tons]", value=35.0, step=5.0)
fs_input = col_fs.number_input("Factor of Safety (FS)", value=2.5, step=0.1)

col_info1, col_info2 = st.columns(2)
col_info1.info(f"🛡️ **Safe Capacity (Main Pile):** {qmain_input/fs_input if fs_input>0 else 0:.3f} Tons")
col_info2.info(f"🛡️ **Safe Capacity (Micro-pile):** {qmicro_input/fs_input if fs_input>0 else 0:.3f} Tons")

st.subheader("2. Pile Coordinates & Construction Deviations Management")
st.markdown("""
💡 **Mitigation & Redesign Guide:**
* **To Simulate Remedial Pile:** Click **`+ Add row`** at the bottom, select Type as **`Micro`**, and input the installation coordinates to re-balance the center of gravity.
* **To Delete:** Highlight the row by clicking the left-most empty cell and hit **`Delete`** or **`Backspace`**.
""")

# Default Data (F4 Base Configuration)
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'Pile_Type': ['Main', 'Main', 'Main', 'Main'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'dev_x': [0.15, 0.03, -0.01, 0.04],  # ใส่ค่าเยื้องศูนย์ขนาดใหญ่ที่ P1 เพื่อจำลองการวิบัติ
    'dev_y': [0.10, -0.02, -0.04, 0.06]
})

config = {
    "Pile_Type": st.column_config.SelectboxColumn(
        "Type", options=["Main", "Micro"], required=True
    )
}
edited_df = st.data_editor(default_data, column_config=config, num_rows="dynamic", use_container_width=True)

st.divider()

# --- Calculation & Results Section ---
if st.button("🧮 Calculate & Generate High-Detail Report", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pw_input, mx_input, my_input, qmain_input, qmicro_input, fs_input, edited_df)
    
    if df_res is not None:
        
        # VISUAL STATUS BADGE
        st.subheader("🛡️ Safety Verification Status")
        if summary['overall_passed']:
            st.success("🟢 **PASSED** - Structural safety requirements met. All individual pile reactions are within their respective allowable capacities.")
        else:
            st.error("🔴 **FAILED (OVERLOADED)** - Critical design criteria breached! One or more piles exceed their allowable capacity. Try adjusting or adding a Micro-pile to fix the CG.")

        st.divider()

        # HIGH-DETAIL CALCULATION SHEET (รายการคำนวณที่สมบูรณ์)
        with st.expander("📝 View Comprehensive Step-by-Step Calculation Sheet", expanded=True):
            
            st.markdown("### Step 1: Geotechnical Allowable Capacities ($R_{allow}$)")
            st.markdown("Allowable load capacity derived from Factor of Safety (FS):")
            st.markdown(rf"$$ R_{{allow, Main}} = \frac{{Q_{{ult, Main}}}}{{FS}} = \frac{{{summary['q_main']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_main']:.3f} \text{{ Tons}} $$")
            st.markdown(rf"$$ R_{{allow, Micro}} = \frac{{Q_{{ult, Micro}}}}{{FS}} = \frac{{{summary['q_micro']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_micro']:.3f} \text{{ Tons}} $$")

            st.markdown("### Step 2: Pre-processing & Actual Coordinates Estimation")
            st.markdown(r"$$ x_{{actual}} = x_{{design}} + \text{{dev\_x}}, \quad y_{{actual}} = y_{{design}} + \text{{dev\_y}} $$")
            
            df_actuals = df_res[['Pile_Name', 'Pile_Type', 'x_design', 'dev_x', 'x_actual', 'y_design', 'dev_y', 'y_actual']].copy()
            st.table(df_actuals.style.format({col: '{:.4f}' for col in df_actuals.columns if col not in ['Pile_Name', 'Pile_Type']}))

            st.markdown("### Step 3: Shifted Center of Gravity (CG) of the Group")
            st.markdown("Centroid shift calculation including newly introduced micro-piles:")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum x_{{actual}}}}{{n}} = \frac{{{df_res['x_actual'].sum():.4f}}}{{{summary['n']}}} = {summary['cg_x']:.4f} \text{{ m}} $$")
            st.markdown(rf"$$ \bar{{y}} = \frac{{\sum y_{{actual}}}}{{n}} = \frac{{{df_res['y_actual'].sum():.4f}}}{{{summary['n']}}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            
            st.markdown("### Step 4: Total Eccentric Moments about New Centroid ($M_{x,cg}, M_{y,cg}$)")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_w \cdot \bar{{y}}) = {summary['mx_ext']:.3f} + ({summary['pw']:.3f} \cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_w \cdot \bar{{x}}) = {summary['my_ext']:.3f} + ({summary['pw']:.3f} \cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("### Step 5: Group Properties & Individual Moments of Inertia ($I_{xx}, I_{yy}$)")
            st.markdown(r"Where $x_i = x_{actual} - \bar{{x}}$ and $y_i = y_{actual} - \bar{{y}}$:")
            
            df_inertia = df_res[['Pile_Name', 'Pile_Type', 'x_actual', 'y_actual', 'x_i', 'y_i', 'x_i_sq', 'y_i_sq']].copy()
            df_inertia.columns = ['Pile', 'Type', 'x_actual', 'y_actual', 'x_i (x - x̄)', 'y_i (y - ȳ)', 'x_i²', 'y_i²']
            st.table(df_inertia.style.format({col: '{:.4f}' for col in df_inertia.columns if col not in ['Pile', 'Type']}))

            st.markdown(rf"$$ I_{{xx}} = \sum (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{yy}} = \sum (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            
            st.markdown("### Step 6: Detailed Pile Reaction Substitution & Individual Safety Check ($R_i$)")
            st.markdown(r"$$ R_i = \frac{P_w}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} \le R_{allow} $$")
            
            st.markdown("**Complete Numerical Substitution:**")
            for idx, row in df_res.iterrows():
                check_symbol = r"\le" if row['Ri'] <= row['Allowable_Load'] else r"\gt"
                status_latex = r"\text{ [OK]}" if row['Ri'] <= row['Allowable_Load'] else r"\text{ [NG - OVERLOADED]}"
                
                formula = (
                    rf"$$ R_{{{row['Pile_Name']}}} = \frac{{{summary['pw']:.2f}}}{{{summary['n']}}} + "
                    rf"\frac{{{summary['mx_cg']:.4f} \cdot ({row['y_i']:.4f})}}{{{summary['ixx']:.4f}}} + "
                    rf"\frac{{{summary['my_cg']:.4f} \cdot ({row['x_i']:.4f})}}{{{summary['iyy']:.4f}}} "
                    rf"= {row['Ri']:.3f} \text{{ Tons}} {check_symbol} {row['Allowable_Load']:.3f} \text{{ Tons (Type: {row['Pile_Type']})}} {status_latex} $$"
                )
                st.markdown(formula)

        st.divider()

        # --- Graphical Plots & Summary Display ---
        out_col1, out_col2 = st.columns([1.2, 1])
        
        with out_col1:
            st.subheader("📊 Summary Data Table")
            
            def highlight_fail(row):
                return ['background-color: #ffcccc' if row['Status'] != 'PASS' else '' for _ in row]
            
            df_display = df_res[['Pile_Name', 'Pile_Type', 'x_actual', 'y_actual', 'Ri', 'Allowable_Load', 'Status']]
            st.dataframe(
                df_display.style.apply(highlight_fail, axis=1).format({
                    'x_actual': '{:.3f}', 'y_actual': '{:.3f}', 
                    'Ri': '{:.3f}', 'Allowable_Load': '{:.3f}'
                }), 
                use_container_width=True
            )
            
            # แจ้งเตือนเฉพาะต้นที่รับโหลดไม่ไหวแบบเจาะจง
            failed_piles = df_res[df_res['Status'] != 'PASS']
            for _, row in failed_piles.iterrows():
                st.error(f"⚠️ **Pile {row['Pile_Name']} ({row['Pile_Type']})** exceeds capacity: Load = **{row['Ri']:.3f} t** > Limit ({row['Allowable_Load']:.3f} t).")

        with out_col2:
            st.subheader("📐 Foundation Deviation & Mitigation Plan")
            
            fig, ax = plt.subplots(figsize=(6, 6))
            
            df_main = df_res[df_res['Pile_Type'] == 'Main']
            ax.scatter(df_main['x_design'], df_main['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            
            for idx, row in df_res.iterrows():
                edge_color = 'red' if row['Status'] != 'PASS' else ('blue' if row['Pile_Type'] == 'Main' else 'green')
                face_color = '#ff4d4d' if row['Status'] != 'PASS' else ('deepskyblue' if row['Pile_Type'] == 'Main' else 'lightgreen')
                marker_style = 'o' if row['Pile_Type'] == 'Main' else 's'
                size = 450 if row['Pile_Type'] == 'Main' else 250
                
                ax.scatter(row['x_actual'], row['y_actual'], s=size, color=face_color, alpha=0.4, edgecolors=edge_color, linewidth=1.5, marker=marker_style)
                
                label_color = 'red' if row['Status'] != 'PASS' else 'black'
                ax.text(row['x_actual'], row['y_actual'], f"{row['Pile_Name']}\n{row['Ri']:.1f}t", ha='center', va='center', fontsize=8, color=label_color, weight='bold')
                
                if row['Pile_Type'] == 'Main':
                    ax.annotate('', xy=(row['x_actual'], row['y_actual']), xytext=(row['x_design'], row['y_design']), arrowprops=dict(arrowstyle="->", color='red', lw=1))

            ax.plot(0, 0, marker='+', color='black', markersize=18, markeredgewidth=2.5, label='Column Center (0,0)')
            ax.plot(summary['cg_x'], summary['cg_y'], marker='x', color='crimson', markersize=12, markeredgewidth=2.5, label='New Pile CG')
            
            ax.axhline(0, color='black', linewidth=0.6, linestyle=':')
            ax.axvline(0, color='black', linewidth=0.6, linestyle=':')
            ax.set_aspect('equal')
            
            # Auto-scale เผื่อระยะกราฟตามขนาดพิกัดเข็มแซม
            all_x = df_res['x_actual']
            all_y = df_res['y_actual']
            max_val = max(all_x.abs().max(), all_y.abs().max(), 0.5) * 1.6
            ax.set_xlim(-max_val, max_val)
            ax.set_ylim(-max_val, max_val)
            
            ax.set_xlabel("X-Axis (meters)")
            ax.set_ylabel("Y-Axis (meters)")
            ax.grid(True, linestyle='--', alpha=0.5)
            
            ax.scatter([], [], s=200, c='deepskyblue', edgecolors='blue', marker='o', alpha=0.4, label='Main Pile')
            ax.scatter([], [], s=200, c='lightgreen', edgecolors='green', marker='s', alpha=0.4, label='Micro-pile')
            ax.legend(loc='upper right', fontsize=8)
            
            st.pyplot(fig)
    else:
        st.warning("Please add at least one pile to the coordinate table.")
