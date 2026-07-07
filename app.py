import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 1. ฟังก์ชันคำนวณทางวิศวกรรม
# ==========================================
def calculate_pile_deviation(pu, mx_ext, my_ext, piles_df):
    """
    ฟังก์ชันสำหรับคำนวณแรงลงเสาเข็มแต่ละต้นเมื่อเกิดการเยื้องศูนย์
    """
    # แปลง DataFrame เป็น list ของ dict เพื่อความสะดวกในการคำนวณ
    piles = piles_df.to_dict('records')
    n = len(piles)
    
    if n == 0:
        return None, None

    # ขั้นตอนที่ 1: หาจุดศูนย์ถ่วง (CG) ใหม่ของกลุ่มเสาเข็ม
    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    # ขั้นตอนที่ 4: คำนวณโมเมนต์รวมรอบจุด CG ใหม่ (รวมผลจาก Eccentricity)
    ecc_mx = pu * cg_y
    ecc_my = pu * cg_x
    
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # ขั้นตอนที่ 2 & 3: คำนวณระยะ xi, yi และหาค่า Ixx, Iyy
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x  # ระยะแกน X เทียบกับ CG ใหม่
        p['y_i'] = p['y_actual'] - cg_y  # ระยะแกน Y เทียบกับ CG ใหม่
        ixx += p['y_i'] ** 2
        iyy += p['x_i'] ** 2

    # ขั้นตอนที่ 5: คำนวณแรงปฏิกิริยาลงเสาเข็มแต่ละต้น (Ri)
    for p in piles:
        term1 = pu / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3

    summary = {
        'n': n,
        'cg_x': cg_x, 'cg_y': cg_y,
        'ixx': ixx, 'iyy': iyy,
        'mx_cg': mx_cg, 'my_cg': my_cg
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. ส่วนการจัดหน้าจอและแสดงผล UI (Streamlit)
# ==========================================
st.set_page_config(page_title="Pile Deviation Analysis", layout="wide")

st.title("🏗️ โปรแกรมคำนวณและออกรายงาน Pile Deviation")
st.markdown("ระบบคำนวณแรงปฏิกิริยาในเสาเข็มแบบ **Dynamic** รองรับการเพิ่ม/ลดจำนวนเสาเข็ม และวาดรูปแปลนฐานราก")

st.divider()

# --- ส่วนรับข้อมูล (Input) ---
st.subheader("1. ป้อนข้อมูลน้ำหนักและโมเมนต์ออกแบบ (Design Loads)")
col_p, col_mx, col_my = st.columns(3)
pu_input = col_p.number_input("น้ำหนักแนวแกนรวม ปลัย (Pu) - [ตัน]", value=100.0, step=10.0)
mx_input = col_mx.number_input("โมเมนต์ภายนอกดัดรอบแกน X (Mx) - [ตัน-เมตร]", value=0.0, step=1.0)
my_input = col_my.number_input("โมเมนต์ภายนอกดัดรอบแกน Y (My) - [ตัน-เมตร]", value=0.0, step=1.0)

st.subheader("2. จัดการพิกัดเสาเข็มหน้างานจริง (Actual Pile Coordinates)")
st.caption("💡 สามารถแก้ไขตัวเลข เพิ่มแถว (Add row) หรือลบแถว เพื่อเปลี่ยนรูปแบบฐานรากได้ตามต้องการ (ศูนย์กลางตอม่ออยู่ที่พิกัด 0,0)")

# กำหนดข้อมูลเริ่มต้น (Default เป็นฐานราก 4 ต้น ระยะห่าง 1.0 ม.)
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'x_actual': [-0.48, 0.53, -0.50, 0.51],  # สมมติตัวเลขเยื้องศูนย์หน้างานจริง
    'y_actual': [0.55, 0.48, -0.52, -0.45]   # สมมติตัวเลขเยื้องศูนย์หน้างานจริง
})

# เปิดตารางให้ผู้ใช้แก้ไขได้แบบ Dynamic
edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- ส่วนคำนวณและแสดงผลลัพธ์ ---
if st.button("🧮 เริ่มการคำนวณและสร้างรายงาน", type="primary"):
    
    # คำนวณผลลัพธ์
    df_res, summary = calculate_pile_deviation(pu_input, mx_input, my_input, edited_df)
    
    if df_res is not None:
        # แบ่งหน้าจอแสดงผลเป็น 2 ฝั่ง (ซ้าย: ตัวเลขคำนวณ, ขวา: รูปภาพประกอบ)
        out_col1, out_col2 = st.columns([1, 1])
        
        with out_col1:
            st.subheader("📋 สรุปผลรายการคำนวณ (Calculation Summary)")
            
            # แสดงพารามิเตอร์สำคัญ
            st.markdown(f"**จำนวนเสาเข็มทั้งหมด ($n$):** {summary['n']} ต้น")
            st.markdown(f"**จุดศูนย์ถ่วงใหม่ของกลุ่มเข็ม ($\\bar{{x}}, \\bar{{y}}$):** ({summary['cg_x']:.4f}, {summary['cg_y']:.4f}) เมตร")
            st.markdown(f"**โมเมนต์รวมรอบจุด CG ใหม่ ($M_{{x,cg}} / M_{{y,cg}}$):** {summary['mx_cg']:.3f} / {summary['my_cg']:.3f} ตัน-เมตร")
            st.markdown(f"**ผลรวม Inertia ($I_{{xx}} / I_{{yy}}$):** {summary['ixx']:.4f} / {summary['iyy']:.4f} ม.²")
            
            st.markdown("**📊 ตารางแสดงแรงที่เกิดขึ้นจริงในเสาเข็มแต่ละต้น ($R_i$)**")
            # จัดรูปแบบการแสดงผลทศนิยม 3 ตำแหน่ง
            st.dataframe(df_res.style.format({
                'x_design': '{:.3f}', 'y_design': '{:.3f}',
                'x_actual': '{:.3f}', 'y_actual': '{:.3f}',
                'x_i': '{:.3f}', 'y_i': '{:.3f}', 'Ri': '{:.3f}'
            }), use_container_width=True)
            
            # ไฮไลต์ต้นที่รับแรงมากที่สุด
            max_r = df_res['Ri'].max()
            max_pile = df_res.loc[df_res['Ri'].idxmax(), 'Pile_Name']
            st.error(f"⚠️ **เสาเข็มที่รับน้ำหนักสูงสุด:** {max_pile} รับแรงทั้งหมด = **{max_r:.3f} ตัน**")

        with out_col2:
            st.subheader("📐 แผนผังแสดงการเยื้องศูนย์ (Foundation Plan)")
            
            # --- วาดรูปแปลนด้วย Matplotlib ---
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # วาดตำแหน่งเสาเข็มที่ออกแบบ (เส้นประสีเทา)
            ax.scatter(df_res['x_design'], df_res['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            
            # วาดตำแหน่งเสาเข็มจริงหน้างาน (วงกลมสีฟ้าใส)
            ax.scatter(df_res['x_actual'], df_res['y_actual'], s=450, color='deepskyblue', alpha=0.4, edgecolors='blue', linewidth=1.5, label='Actual Position')
            
            # ใส่ชื่อเสาเข็มและค่าแรง Ri กำกับในรูป
            for idx, row in df_res.iterrows():
                ax.text(row['x_actual'], row['y_actual'], f"{row['Pile_Name']}\n{row['Ri']:.2f} t", ha='center', va='center', fontsize=9, color='black', weight='bold')
                # วาดเส้นลูกศรแสดงทิศทางการเยื้องจากจุดดีไซน์ไปจุดจริง
                ax.annotate('', xy=(row['x_actual'], row['y_actual']), xytext=(row['x_design'], row['y_design']),
                            arrowprops=dict(arrowstyle="->", color='red', lw=1))

            # วาดจุดศูนย์กลางตอม่อเดิม (0,0)
            ax.plot(0, 0, marker='+', color='black', markersize=18, markeredgewidth=2.5, label='Column Center (0,0)')
            
            # วาดจุดศูนย์ถ่วง (CG) ใหม่ของกลุ่มเสาเข็ม
            ax.plot(summary['cg_x'], summary['cg_y'], marker='x', color='crimson', markersize=12, markeredgewidth=2.5, label='New Pile CG')
            
            # ปรับแต่งสเกลและเส้นกริดของกราฟ
            ax.axhline(0, color='black', linewidth=0.6, linestyle=':')
            ax.axvline(0, color='black', linewidth=0.6, linestyle=':')
            ax.set_aspect('equal')
            
            # คำนวณหาระยะขอบกราฟให้เหมาะสมอัตโนมัติ
            max_val = max(df_res['x_design'].abs().max(), df_res['y_design'].abs().max()) * 1.8
            ax.set_xlim(-max_val, max_val)
            ax.set_ylim(-max_val, max_val)
            
            ax.set_xlabel("X-Axis (meters)")
            ax.set_ylabel("Y-Axis (meters)")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(loc='upper right', fontsize=8)
            
            # นำรูปภาพไปแสดงบนเว็บบราวเซอร์ Streamlit
            st.pyplot(fig)
    else:
        st.warning("กรุณาเพิ่มข้อมูลเสาเข็มในตารางอย่างน้อย 1 ต้น")
