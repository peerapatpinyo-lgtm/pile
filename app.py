import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pw, mx_ext, my_ext, q_main, q_micro, fs, piles_df):
    
    piles_df = piles_df.dropna(subset=['Pile_Name'])
    if piles_df.empty:
        return None, None

    # แปลงค่าว่างให้เป็น 0.0 สำหรับพิกัด
    for col in ['x_design', 'y_design', 'dev_x', 'dev_y']:
        piles_df[col] = pd.to_numeric(piles_df[col]).fillna(0.0)

    piles = piles_df.to_dict('records')
    n = len(piles)
    
    safe_load_main = q_main / fs
    safe_load_micro = q_micro / fs

    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']
        # กำหนด Safe Load ประจำตัวเสาเข็ม
        p['Allowable_Load'] = safe_load_main if p['Pile_Type'] == 'Main' else safe_load_micro

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
        
        # ตรวจสอบความปลอดภัยเทียบกับ Allowable_Load ของตัวเอง
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
        'safe_main': safe_load_main, 'safe_micro': safe_load_micro,
        'overall_passed': overall_passed
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. Streamlit UI and Output Rendering
# ==========================================
st.set_page_config(page_title="Pile Deviation & Mitigation Analysis", layout="wide")

st.title("🏗️ Pile Deviation & Mitigation Analysis")
st.markdown("Calculate pile reactions and simulate **Micro-pile Mitigations** to resolve overloaded foundation issues.")

st.divider()

# --- Input Section ---
st.subheader("1. Design Loads & Capacities")
col_p, col_mx, col_my = st.columns(3)
pw_input = col_p.number_input("Total Working Axial Load (Pw) - [Tons]", value=100.0, step=10.0)
mx_input = col_mx.number_input("External Moment Mx - [Ton-m]", value=0.0, step=1.0)
my_input = col_my.number_input("External Moment My - [Ton-m]", value=0.0, step=1.0)

col_qmain, col_qmicro, col_fs = st.columns(3)
qmain_input = col_qmain.number_input("Ultimate Capacity (Main Pile) - [Tons]", value=75.0, step=5.0)
qmicro_input = col_qmicro.number_input("Ultimate Capacity (Micro-pile) - [Tons]", value=35.0, step=5.0)
fs_input = col_fs.number_input("Factor of Safety (FS)", value=2.5, step=0.1)

col_info1, col_info2 = st.columns(2)
col_info1.info(f"🛡️ **Safe Load (Main):** {qmain_input/fs_input if fs_input>0 else 0:.2f} Tons")
col_info2.info(f"🛡️ **Safe Load (Micro-pile):** {qmicro_input/fs_input if fs_input>0 else 0:.2f} Tons")

st.subheader("2. Pile Coordinates & Construction Deviations")
st.markdown("💡 **Mitigation Guide:** Click `+ Add row`, name it (e.g., MP1), set type to `Micro`, and place its coordinates to pull the CG and reduce loads on failing piles.")

# Default Data includes a Pile_Type column
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'Pile_Type': ['Main', 'Main', 'Main', 'Main'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'dev_x': [0.15, 0.03, -0.01, 0.04],  # Intentional large deviation on P1 to simulate failure
    'dev_y': [0.10, -0.02, -0.04, 0.06]
})

# ใช้ st.data_editor พร้อมกำหนดให้คอลัมน์ Pile_Type เป็น Dropdown (Categorical)
config = {
    "Pile_Type": st.column_config.SelectboxColumn(
        "Type", options=["Main", "Micro"], required=True
    )
}

edited_df = st.data_editor(default_data, column_config=config, num_rows="dynamic", use_container_width=True)

st.divider()

# --- Calculation & Results Section ---
if st.button("🧮 Calculate & Verify Design", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pw_input, mx_input, my_input, qmain_input, qmicro_input, fs_input, edited_df)
    
    if df_res is not None:
        
        st.subheader("🛡️ Safety Verification Status")
        if summary['overall_passed']:
            st.success("🟢 **PASSED** - All structural safety requirements met. All piles are within their respective allowable capacities.")
        else:
            st.error("🔴 **FAILED (OVERLOADED)** - Design criteria breached! One or more piles exceed their allowable capacity. Try adding a Micro-pile in the table above to shift the CG.")

        st.divider()

        out_col1, out_col2 = st.columns([1.2, 1])
        
        with out_col1:
            st.subheader("📊 Summary Table")
            
            def highlight_fail(row):
                return ['background-color: #ffcccc' if row['Status'] != 'PASS' else '' for _ in row]
            
            df_display = df_res[['Pile_Name', 'Pile_Type', 'x_actual', 'y_actual', 'Ri', 'Allowable_Load', 'Status']]
            st.dataframe(
                df_display.style.apply(highlight_fail, axis=1).format({
                    'x_actual': '{:.3f}', 'y_actual': '{:.3f}', 
                    'Ri': '{:.3f}', 'Allowable_Load': '{:.2f}'
                }), 
                use_container_width=True
            )
            
            # โชว์เตือนเฉพาะต้นที่พัง
            failed_piles = df_res[df_res['Status'] != 'PASS']
            for _, row in failed_piles.iterrows():
                st.error(f"⚠️ **Pile {row['Pile_Name']} ({row['Pile_Type']})** is overloaded! Load = **{row['Ri']:.3f} t** > Limit ({row['Allowable_Load']:.2f} t).")

        with out_col2:
            st.subheader("📐 Foundation Deviation & Mitigation Plan")
            
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # วาดตำแหน่ง Design (เฉพาะต้น Main)
            df_main = df_res[df_res['Pile_Type'] == 'Main']
            ax.scatter(df_main['x_design'], df_main['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            
            # ตั้งค่าสีและรูปร่างตามประเภทเสาเข็มและสถานะ
            for idx, row in df_res.iterrows():
                # สีขอบและสีพื้น
                edge_color = 'red' if row['Status'] != 'PASS' else ('blue' if row['Pile_Type'] == 'Main' else 'green')
                face_color = '#ff4d4d' if row['Status'] != 'PASS' else ('deepskyblue' if row['Pile_Type'] == 'Main' else 'lightgreen')
                marker_style = 'o' if row['Pile_Type'] == 'Main' else 's' # เข็มแซมใช้รูปสี่เหลี่ยม
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
            
            all_x = df_res['x_actual']
            all_y = df_res['y_actual']
            max_val = max(all_x.abs().max(), all_y.abs().max(), 0.5) * 1.6
            ax.set_xlim(-max_val, max_val)
            ax.set_ylim(-max_val, max_val)
            
            ax.set_xlabel("X-Axis (meters)")
            ax.set_ylabel("Y-Axis (meters)")
            ax.grid(True, linestyle='--', alpha=0.5)
            
            # สร้าง Legend หลอกเพื่อให้โชว์ประเภทครบ
            ax.scatter([], [], s=200, c='deepskyblue', edgecolors='blue', marker='o', alpha=0.4, label='Main Pile')
            ax.scatter([], [], s=200, c='lightgreen', edgecolors='green', marker='s', alpha=0.4, label='Micro-pile')
            ax.legend(loc='upper right', fontsize=8)
            
            st.pyplot(fig)
    else:
        st.warning("Please add at least one pile to the coordinate table.")
