import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. ฟังก์ชันคำนวณทางวิศวกรรม
# ==========================================
def calculate_pile_deviation(pu, mx_ext, my_ext, piles_df):
    piles = piles_df.to_dict('records')
    n = len(piles)
    
    if n == 0:
        return None, None

    # ขั้นตอนที่ 1: หาจุดศูนย์ถ่วง (CG) ใหม่
    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    # ขั้นตอนที่ 4: คำนวณโมเมนต์รวม
    ecc_mx = pu * cg_y
    ecc_my = pu * cg_x
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # ขั้นตอนที่ 2 & 3: หาค่า Ixx, Iyy
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x
        p['y_i'] = p['y_actual'] - cg_y
        ixx += p['y_i'] ** 2
        iyy += p['x_i'] ** 2

    # ขั้นตอนที่ 5: คำนวณแรงปฏิกิริยา (Ri)
    for p in piles:
        term1 = pu / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3

    summary = {
        'n': n, 'cg_x': cg_x, 'cg_y': cg_y,
        'ixx': ixx, 'iyy': iyy,
        'mx_cg': mx_cg, 'my_cg': my_cg,
        'pu': pu, 'mx_ext': mx_ext, 'my_ext': my_ext
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. ส่วนการจัดหน้าจอและแสดงผล UI (Streamlit)
# ==========================================
st.set_page_config(page_title="Pile Deviation Analysis", layout="wide")

st.title("🏗️ โปรแกรมคำนวณและออกรายงาน Pile Deviation")
st.markdown("ระบบคำนวณแรงปฏิกิริยาในเสาเข็ม พร้อม **สร้างรายการคำนวณแสดงวิธีทำ (Step-by-Step)** อัตโนมัติ")

st.divider()

# --- ส่วนรับข้อมูล (Input) ---
st.subheader("1. ป้อนข้อมูลน้ำหนักและโมเมนต์ออกแบบ (Design Loads)")
col_p, col_mx, col_my = st.columns(3)
pu_input = col_p.number_input("น้ำหนักแนวแกนรวม (Pu) - [ตัน]", value=100.0, step=10.0)
mx_input = col_mx.number_input("โมเมนต์ภายนอกดัดรอบแกน X (Mx) - [ตัน-เมตร]", value=0.0, step=1.0)
my_input = col_my.number_input("โมเมนต์ภายนอกดัดรอบแกน Y (My) - [ตัน-เมตร]", value=0.0, step=1.0)

st.subheader("2. จัดการพิกัดเสาเข็มหน้างานจริง (Actual Coordinates)")
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'x_actual': [-0.48, 0.53, -0.50, 0.51],
    'y_actual': [0.55, 0.48, -0.52, -0.45]
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- ส่วนคำนวณและแสดงผลลัพธ์ ---
if st.button("🧮 เริ่มการคำนวณและสร้างรายงาน", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pu_input, mx_input, my_input, edited_df)
    
    if df_res is not None:
        
        # ==========================================
        # ส่วนแสดงรายการคำนวณ (Dynamic Calculation Sheet)
        # ==========================================
        with st.expander("📝 ดูรายการคำนวณแสดงวิธีทำ (Step-by-Step Calculation)", expanded=True):
            st.markdown("รายการคำนวณนี้ถูกสร้างขึ้นแบบอัตโนมัติตามตัวเลขที่คุณกรอก เพื่อให้ง่ายต่อการตรวจสอบ (Cross-check)")
            
            st.markdown("### ขั้นตอนที่ 1: หาจุดศูนย์ถ่วงใหม่ของกลุ่มเสาเข็ม (New CG)")
            st.markdown(f"$$ \\bar{{x}} = \\frac{{\\sum x_{{actual}}}}{{n}} = {summary['cg_x']:.4f} \\text{{ m}} $$")
            st.markdown(f"$$ \\bar{{y}} = \\frac{{\\sum y_{{actual}}}}{{n}} = {summary['cg_y']:.4f} \\text{{ m}} $$")
            
            st.markdown("### ขั้นตอนที่ 2: คำนวณโมเมนต์ดัดรอบจุด CG ใหม่ (Eccentric Moments)")
            st.markdown(f"$$ M_{{x,cg}} = M_{{x,ext}} + (\\Sigma P_u \\cdot \\bar{{y}}) = {summary['mx_ext']} + ({summary['pu']} \\cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \\text{{ ton-m}} $$")
            st.markdown(f"$$ M_{{y,cg}} = M_{{y,ext}} + (\\Sigma P_u \\cdot \\bar{{x}}) = {summary['my_ext']} + ({summary['pu']} \\cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \\text{{ ton-m}} $$")

            st.markdown("### ขั้นตอนที่ 3: คำนวณโมเมนต์ความเฉื่อยของกลุ่มเสาเข็ม (Moment of Inertia)")
            st.markdown(f"$$ I_{{xx}} = \\sum (y_i)^2 = {summary['ixx']:.4f} \\text{{ m}}^2 $$")
            st.markdown(f"$$ I_{{yy}} = \\sum (x_i)^2 = {summary['iyy']:.4f} \\text{{ m}}^2 $$")
            
            st.markdown("### ขั้นตอนที่ 4: คำนวณแรงปฏิกิริยาเสาเข็มแต่ละต้น ($R_i$)")
            st.markdown(r"$$ R_i = \frac{\Sigma P_u}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} $$")
            
            st.markdown("**แทนค่าในสมการสำหรับเสาเข็มแต่ละต้น:**")
            for idx, row in df_res.iterrows():
                # จัดสมการ LaTeX ทีละต้น โดยดึงค่าจาก DataFrame มาแสดง
                formula = f"$$ R_{{{row['Pile_Name']}}} = \\frac{{{summary['pu']}}}{{{summary['n']}}} + \\frac{{{summary['mx_cg']:.4f} \\cdot ({row['y_i']:.4f})}}{{{summary['ixx']:.4f}}} + \\frac{{{summary['my_cg']:.4f} \\cdot ({row['x_i']:.4f})}}{{{summary['iyy']:.4f}}} = {row['Ri']:.3f} \\text{{ tons}} $$"
                st.markdown(formula)

        st.divider()

        # ==========================================
        # ส่วนแสดงผลสรุปและรูปภาพ
        # ==========================================
        out_col1, out_col2 = st.columns([1, 1])
        
        with out_col1:
            st.subheader("📊 ตารางสรุปน้ำหนักลงเสาเข็ม ($R_i$)")
            st.dataframe(df_res.style.format({
                'x_design': '{:.3f}', 'y_design': '{:.3f}',
                'x_actual': '{:.3f}', 'y_actual': '{:.3f}',
                'x_i': '{:.3f}', 'y_i': '{:.3f}', 'Ri': '{:.3f}'
            }), use_container_width=True)
            
            max_r = df_res['Ri'].max()
            max_pile = df_res.loc[df_res['Ri'].idxmax(), 'Pile_Name']
            st.error(f"⚠️ **เสาเข็มที่รับน้ำหนักสูงสุด:** {max_pile} รับแรงทั้งหมด = **{max_r:.3f} ตัน**")

        with out_col2:
            st.subheader("📐 แผนผังแสดงการเยื้องศูนย์ (Foundation Plan)")
            
            fig, ax = plt.subplots(figsize=(6, 6))
            ax.scatter(df_res['x_design'], df_res['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            ax.scatter(df_res['x_actual'], df_res['y_actual'], s=450, color='deepskyblue', alpha=0.4, edgecolors='blue', linewidth=1.5, label='Actual Position')
            
            for idx, row in df_res.iterrows():
                ax.text(row['x_actual'], row['y_actual'], f"{row['Pile_Name']}\n{row['Ri']:.2f} t", ha='center', va='center', fontsize=9, color='black', weight='bold')
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
        st.warning("กรุณาเพิ่มข้อมูลเสาเข็มในตารางอย่างน้อย 1 ต้น")
