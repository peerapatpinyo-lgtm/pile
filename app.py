import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pw, mx_ext, my_ext, q_main, q_micro, fs, min_spacing, piles_df):
    """
    Calculates pile reactions, checks pairwise pile spacing limits, 
    and prepares comprehensive engineering calculation data.
    """
    piles_df = piles_df.dropna(subset=['Pile_Name'])
    if piles_df.empty:
        return None, None

    for col in ['x_design', 'y_design', 'dev_x', 'dev_y']:
        piles_df[col] = pd.to_numeric(piles_df[col]).fillna(0.0)

    piles = piles_df.to_dict('records')
    n = len(piles)
    
    safe_load_main = q_main / fs if fs > 0 else 0
    safe_load_micro = q_micro / fs if fs > 0 else 0

    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']
        p['Allowable_Load'] = safe_load_main if p['Pile_Type'] == 'Main' else safe_load_micro

    spacing_issues = []
    for i in range(n):
        for j in range(i + 1, n):
            dx = piles[i]['x_actual'] - piles[j]['x_actual']
            dy = piles[i]['y_actual'] - piles[j]['y_actual']
            dist = math.hypot(dx, dy)
            if dist < min_spacing:
                spacing_issues.append({
                    'p1': piles[i]['Pile_Name'],
                    'p2': piles[j]['Pile_Name'],
                    'dist': dist
                })

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

    overall_load_passed = True
    for p in piles:
        term1 = pw / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3
        
        if p['Ri'] > p['Allowable_Load']:
            p['Status'] = 'FAIL (Overload)'
            overall_load_passed = False
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
        'min_spacing': min_spacing, 'spacing_issues': spacing_issues,
        'overall_load_passed': overall_load_passed,
        'overall_spacing_passed': len(spacing_issues) == 0
    }
    
    return pd.DataFrame(piles), summary


# ==========================================
# 2. Proof Tab Rendering Function (With Integrated Diagram & Glossary)
# ==========================================
def render_proof_tab():
    st.header("📐 Rigid Pile Cap: Rigorous Vector Derivation")
    st.markdown("This section provides an advanced, step-by-step vector mechanics proof that directly links the physical column coordinates to the final Cartesian biaxial bending formula.")
    
    st.divider()

    # --- SECTION: VISUAL DIAGRAM ---
    st.subheader("📊 Coordinate Layout & Eccentricity Visualized")
    st.markdown(r"""
    This diagram illustrates how the position of the column center $(Col_x, Col_y)$ relative to the Pile Group Center of Gravity $(CG_x, CG_y)$ creates the eccentricities ($e_x, e_y$) that induce bending moments.
    """)
    
    # Render an elegant ASCII diagram inside a code block for clear visual tracking
    st.markdown(r"""
```text
 Y-Axis (Global System)
   ^
   |       +-----------------------------------------+
   |       |               Pile Cap Boundary         |
   |       |                                         |
   |       |    Column Center (Col_x, Col_y)         |
   |       |          [  Column (เสา)  ]             |
   |       |                 |                       |
   |       |                 |<------- e_x ------->| |
   |       |                 |                     | |
   +-------|-----------------|-------------------(CG)----> X-Axis (Global System)
   |       |                 |                  (0,0)  
   |       |                                       |   
   |       |                                       |   
   |       |                                      e_y  
   |       |                                       v   
   |       +-----------------------------------------+
   |
 (0,0) Global Origin
    
# ==========================================
# 3. Streamlit UI and Output Rendering
# ==========================================
st.set_page_config(page_title="Advanced Pile Redesign System", layout="wide")

st.title("🏗️ Pile Deviation, Mitigation & Spacing Analysis Report")
st.markdown("Professional foundation redesign tool featuring dual-capacity checking, minimum spacing verification, and a **High-Detail Calculation Report**.")

# 🌟 สร้างระบบ Tabs แบ่งหน้า
tab_calc, tab_proof = st.tabs(["🧮 Calculation & Mitigation", "📐 Formula Derivation (Proof)"])

# ----------------- TAB 1: หน้าคำนวณ (ถูกเว้นวรรคให้อยู่ในบล็อก Tab นี้) -----------------
with tab_calc:
    st.subheader("1. Design Parameters Input")
    col_p, col_mx, col_my = st.columns(3)
    pw_input = col_p.number_input("Total Working Axial Load (Pw) - [Tons]", value=100.0, step=10.0, help="Unfactored Dead Load + Live Load")
    mx_input = col_mx.number_input("External Working Moment Mx - [Ton-m]", value=0.0, step=1.0)
    my_input = col_my.number_input("External Working Moment My - [Ton-m]", value=0.0, step=1.0)

    col_qmain, col_qmicro, col_fs, col_space = st.columns(4)
    qmain_input = col_qmain.number_input("Ultimate Capacity (Main Pile) - [Tons]", value=75.0, step=5.0)
    qmicro_input = col_qmicro.number_input("Ultimate Capacity (Micro-pile) - [Tons]", value=35.0, step=5.0)
    fs_input = col_fs.number_input("Factor of Safety (FS)", value=2.5, step=0.1)
    min_space_input = col_space.number_input("Min. Spacing Limit (m)", value=0.90, step=0.10, help="Minimum allowable distance between any two piles (e.g., 3D or 2.5D)")

    col_info1, col_info2 = st.columns(2)
    col_info1.info(f"🛡️ **Safe Capacity (Main Pile):** {qmain_input/fs_input if fs_input>0 else 0:.3f} Tons")
    col_info2.info(f"🛡️ **Safe Capacity (Micro-pile):** {qmicro_input/fs_input if fs_input>0 else 0:.3f} Tons")

    st.subheader("2. Pile Coordinates & Construction Deviations Management")
    st.markdown("""
    💡 **Mitigation & Dynamic Row Management Guide:**
    * **To Simulate Remedial Pile:** Click **`+ Add row`** at the bottom, select Type as **`Micro`**, and input the coordinates to re-balance the center of gravity.
    * **To Delete Piles:** Highlight the row by clicking the left-most empty cell and press **`Delete`** or **`Backspace`** on your keyboard.
    """)

    default_data = pd.DataFrame({
        'Pile_Name': ['P1', 'P2', 'P3', 'P4', 'MP1'],
        'Pile_Type': ['Main', 'Main', 'Main', 'Main', 'Micro'],
        'x_design': [-0.50, 0.50, -0.50, 0.50, 0.00],
        'y_design': [0.50, 0.50, -0.50, -0.50, 0.00],
        'dev_x': [0.15, 0.03, -0.01, 0.04, -0.40],
        'dev_y': [0.10, -0.02, -0.04, 0.06, -0.30]
    })

    config = {
        "Pile_Type": st.column_config.SelectboxColumn("Type", options=["Main", "Micro"], required=True)
    }
    edited_df = st.data_editor(default_data, column_config=config, num_rows="dynamic", use_container_width=True)

    st.divider()

    # --- Calculation & Results Section ---
    if st.button("🧮 Calculate & Generate High-Detail Report", type="primary"):
        
        df_res, summary = calculate_pile_deviation(pw_input, mx_input, my_input, qmain_input, qmicro_input, fs_input, min_space_input, edited_df)
        
        if df_res is not None:
            # ==========================================
            # 2.1 VISUAL STATUS BADGE
            # ==========================================
            st.subheader("🛡️ Safety Verification Status")
            status_col1, status_col2 = st.columns(2)
            
            with status_col1:
                if summary['overall_load_passed']:
                    st.success("🟢 **LOAD CHECK: PASSED** - All piles are operating within allowable capacities.")
                else:
                    st.error("🔴 **LOAD CHECK: FAILED** - One or more piles exceed safe capacity limits!")
                    
            with status_col2:
                if summary['overall_spacing_passed']:
                    st.success(f"🟢 **SPACING CHECK: PASSED** - All piles meet the minimum spacing criteria ($\ge$ {summary['min_spacing']} m).")
                else:
                    st.error(f"🔴 **SPACING CHECK: FAILED** - Piles are placed too close to each other. Soil shearing risk detected!")

            st.divider()

            # ==========================================
            # 2.2 HIGH-DETAIL CALCULATION SHEET 
            # ==========================================
            st.subheader("📝 Engineering Step-by-Step Calculation Sheet")
            
            st.markdown("#### Step 1: Geotechnical Allowable Pile Capacities ($R_{allow}$)")
            st.markdown("Allowable safe loads computed based on Factor of Safety (FS):")
            st.markdown(rf"$$ R_{{allow, Main}} = \frac{{Q_{{ult, Main}}}}{{FS}} = \frac{{{summary['q_main']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_main']:.3f} \text{{ Tons}} $$")
            st.markdown(rf"$$ R_{{allow, Micro}} = \frac{{Q_{{ult, Micro}}}}{{FS}} = \frac{{{summary['q_micro']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_micro']:.3f} \text{{ Tons}} $$")

            st.markdown("#### Step 2: Construction Pre-processing & Actual Coordinates Estimation")
            st.markdown(r"$$ x_{{actual}} = x_{{design}} + \text{{dev\_x}}, \quad y_{{actual}} = y_{{design}} + \text{{dev\_y}} $$")
            df_actuals = df_res[['Pile_Name', 'Pile_Type', 'x_design', 'dev_x', 'x_actual', 'y_design', 'dev_y', 'y_actual']].copy()
            st.table(df_actuals.style.format({col: '{:.4f}' for col in df_actuals.columns if col not in ['Pile_Name', 'Pile_Type']}))

            st.markdown("#### Step 3: Shifted Center of Gravity (CG) of the Global Pile Group")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum x_{{actual}}}}{{n}} = \frac{{{df_res['x_actual'].sum():.4f}}}{{{summary['n']}}} = {summary['cg_x']:.4f} \text{{ m}} $$")
            st.markdown(rf"$$ \bar{{y}} = \frac{{\sum y_{{actual}}}}{{n}} = \frac{{{df_res['y_actual'].sum():.4f}}}{{{summary['n']}}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            
            st.markdown("#### Step 4: Total Eccentric Moments about New Shifted Centroid ($M_{x,cg}, M_{y,cg}$)")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_w \cdot \bar{{y}}) = {summary['mx_ext']:.3f} + ({summary['pw']:.3f} \cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_w \cdot \bar{{x}}) = {summary['my_ext']:.3f} + ({summary['pw']:.3f} \cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("#### Step 5: Group Geometrical Properties & Individual Moments of Inertia ($I_{xx}, I_{yy}$)")
            st.markdown(r"Where $x_i = x_{actual} - \bar{{x}}$ and $y_i = y_{actual} - \bar{{y}}$:")
            df_inertia = df_res[['Pile_Name', 'Pile_Type', 'x_actual', 'y_actual', 'x_i', 'y_i', 'x_i_sq', 'y_i_sq']].copy()
            df_inertia.columns = ['Pile', 'Type', 'x_actual', 'y_actual', 'x_i (x - x̄)', 'y_i (y - ȳ)', 'x_i²', 'y_i²']
            st.table(df_inertia.style.format({col: '{:.4f}' for col in df_inertia.columns if col not in ['Pile', 'Type']}))

            st.markdown(rf"$$ I_{{xx}} = \sum (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{yy}} = \sum (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            
            st.markdown("#### Step 6: Detailed Pile Reaction Substitution & Individual Safety Check ($R_i$)")
            st.markdown(r"$$ R_i = \frac{P_w}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} \le R_{allow} $$")
            
            st.markdown("**Complete Numerical Substitution:**")
            for idx, row in df_res.iterrows():
                check_symbol = r"\le" if row['Ri'] <= row['Allowable_Load'] else r"\gt"
                status_latex = r"\text{ [OK - PASSED]}" if row['Ri'] <= row['Allowable_Load'] else r"\text{ [NG - OVERLOADED]}"
                
                formula = (
                    rf"$$ R_{{{row['Pile_Name']}}} = \frac{{{summary['pw']:.2f}}}{{{summary['n']}}} + "
                    rf"\frac{{{summary['mx_cg']:.4f} \cdot ({row['y_i']:.4f})}}{{{summary['ixx']:.4f}}} + "
                    rf"\frac{{{summary['my_cg']:.4f} \cdot ({row['x_i']:.4f})}}{{{summary['iyy']:.4f}}} "
                    rf"= {row['Ri']:.3f} \text{{ Tons}} {check_symbol} {row['Allowable_Load']:.3f} \text{{ Tons (Type: {row['Pile_Type']})}} {status_latex} $$"
                )
                st.markdown(formula)

            st.divider()

            # ==========================================
            # 2.3 GRAPHICAL PLOTS & SUMMARY DISPLAY
            # ==========================================
            out_col1, out_col2 = st.columns([1.2, 1])
            
            with out_col1:
                st.subheader("📊 Load Distribution Summary Table")
                
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
                
                failed_piles = df_res[df_res['Status'] != 'PASS']
                for _, row in failed_piles.iterrows():
                    st.error(f"⚠️ **Overload Alert:** Pile **{row['Pile_Name']} ({row['Pile_Type']})** Load = **{row['Ri']:.3f} t** > Limit ({row['Allowable_Load']:.3f} t).")

                st.subheader("📏 Pile Spacing Verification")
                if summary['spacing_issues']:
                    for issue in summary['spacing_issues']:
                        st.warning(f"⚠️ **Spacing Violation:** **{issue['p1']}** and **{issue['p2']}** are only **{issue['dist']:.3f} m** apart (Minimum Allowable: {summary['min_spacing']} m).")
                else:
                    st.success(f"✅ All piles meet the minimum spacing requirement of {summary['min_spacing']} m.")

            with out_col2:
                st.subheader("📐 Foundation Mitigation & Redesign Plan")
                
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

                for issue in summary['spacing_issues']:
                    p1_data = df_res[df_res['Pile_Name'] == issue['p1']].iloc[0]
                    p2_data = df_res[df_res['Pile_Name'] == issue['p2']].iloc[0]
                    ax.plot([p1_data['x_actual'], p2_data['x_actual']], [p1_data['y_actual'], p2_data['y_actual']], color='darkorange', linestyle=':', linewidth=2)

                ax.plot(0, 0, marker='+', color='black', markersize=18, markeredgewidth=2.5, label='Column Center (0,0)')
                ax.plot(summary['cg_x'], summary['cg_y'], marker='x', color='crimson', markersize=12, markeredgewidth=2.5, label='New Pile CG')
                
                ax.axhline(0, color='black', linewidth=0.6, linestyle=':')
                ax.axvline(0, color='black', linewidth=0.6, linestyle=':')
                ax.set_aspect('equal')
                
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
                if summary['spacing_issues']:
                    ax.plot([], [], color='darkorange', linestyle=':', linewidth=2, label='Spacing Violation')
                
                ax.legend(loc='upper right', fontsize=8)
                st.pyplot(fig)
                
        else:
            st.warning("Please add at least one pile to the coordinate table.")

# ----------------- TAB 2: หน้าพิสูจน์สูตร (แสดงผลใน Tab ถัดไป) -----------------
with tab_proof:
    render_proof_tab()
