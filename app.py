import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# ฟังก์ชันคำนวณ Pile Deviation
# ==========================================
def calculate_pile_deviation(pu, mx_ext, my_ext, piles):
    n = len(piles)
    
    # 1. หาพิกัด CG ใหม่ของกลุ่มเสาเข็ม (x_bar, y_bar)
    cg_x = sum(p['x'] for p in piles) / n
    cg_y = sum(p['y'] for p in piles) / n

    # 2. คำนวณโมเมนต์ที่เกิดจากการเยื้องศูนย์ของกลุ่มเสาเข็ม
    ecc_mx = pu * cg_y
    ecc_my = pu * cg_x

    # โมเมนต์รวมรอบจุด CG ใหม่
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # 3. คำนวณ Moment of Inertia (Ixx, Iyy) เทียบกับ CG ใหม่
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x'] - cg_x  # ระยะแกน X เทียบกับ CG
        p['y_i'] = p['y'] - cg_y  # ระยะแกน Y เทียบกับ CG
        ixx += p['y_i'] ** 2
        iyy += p['x_i'] ** 2

    # 4. คำนวณแรงที่กระทำลงบนเสาเข็มแต่ละต้น (Ri)
    for p in piles:
        term1 = pu / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3

    summary = {
        'n': n, 'cg_x': cg_x, 'cg_y': cg_y,
        'ixx': ixx, 'iyy': iyy,
        'mx_cg': mx_cg, 'my_cg': my_cg
    }
    return piles, summary

# ==========================================
# ส่วนของการแสดงผลบน Streamlit UI
# ==========================================
st.set_page_config(page_title="Pile Deviation Report", layout="wide")

st.title("🏗️ โปรแกรมคำนวณและวาดรูป Pile Deviation (F4)")
st.markdown("รองรับการคำนวณเสาเข็มเยื้องศูนย์ พร้อมวาดรูปแปลนแสดงจุด CG ใหม่")

st.divider()

# --- 1. รับค่า Input ---
st.subheader("1. กำหนดน้ำหนักบรรทุก (Load Input)")
col_p, col_mx, col_my = st.columns(3)
pu_input = col_p.number_input("น้ำหนักในแนวดิ่งรวม Pu (ตัน)", value=100.0, step=10.0)
mx_input = col_mx.number_input("โมเมนต์ภายนอก Mx (ตัน-เมตร)", value=0.0, step=1.0)
my_input = col_my.number_input("โมเมนต์ภายนอก My (ตัน-เมตร)", value=0.0, step=1.0)

st.subheader("2. กำหนดพิกัดเสาเข็มจริงหน้างาน (Actual Coordinates)")
st.caption("กำหนดจุดศูนย์กลางตอม่อ (Column Center) อยู่ที่พิกัด (0,0) หน่วยเป็นเมตร")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**P1 (ซ้ายบน)**")
    x1 = st.number_input("X ของ P1", value=-0.50, step=0.01)
    y1 = st.number_input("Y ของ P1", value=0.55, step=0.01) # สมมติเยื้องขึ้น 5 cm

with col2:
    st.markdown("**P2 (ขวาบน)**")
    x2 = st.number_input("X ของ P2", value=0.53, step=0.01) # สมมติเยื้องขวา 3 cm
    y2 = st.number_input("Y ของ P2", value=0.50, step=0.01)

with col3:
    st.markdown("**P3 (ซ้ายล่าง)**")
    x3 = st.number_input("X ของ P3", value=-0.50, step=0.01)
    y3 = st.number_input("Y ของ P3", value=-0.50, step=0.01)

with col4:
    st.markdown("**P4 (ขวาล่าง)**")
    x4 = st.number_input("X ของ P4", value=0.50, step=0.01)
    y4 = st.number_input("Y ของ P4", value=-0.45, step=0.01) # สมมติเยื้องขึ้น 5 cm

# --- 2. คำนวณและแสดงผล ---
if st.button("🧮 คำนวณและสร้างรายงาน", type="primary"):
    
    # สร้าง List เก็บข้อมูลเสาเข็ม
    piles_data = [
        {'Pile': 'P1', 'x': x1, 'y': y1, 'x_ideal': -0.5, 'y_ideal': 0.5},
        {'Pile': 'P2', 'x': x2, 'y': y2, 'x_ideal': 0.5, 'y_ideal': 0.5},
        {'Pile': 'P3', 'x': x3, 'y': y3, 'x_ideal': -0.5, 'y_ideal': -0.5},
        {'Pile': 'P4', 'x': x4, 'y': y4, 'x_ideal': 0.5, 'y_ideal': -0.5}
    ]
    
    # เรียกใช้ฟังก์ชันคำนวณ
    results, summary = calculate_pile_deviation(pu_input, mx_input, my_input, piles_data)
    df_results = pd.DataFrame(results)
    
    st.divider()
    
    # --- แบ่งหน้าจอเป็น 2 ฝั่ง (รายการคำนวณ กับ รูปวาด) ---
    res_col1, res_col2 = st.columns([1, 1.2])
    
    with res_col1:
        st.subheader("📋 รายการคำนวณ (Calculation Sheet)")
        
        st.markdown("**1. พิกัดศูนย์ถ่วงใหม่ (New CG)**")
        st.write(f"- x̄ = {summary['cg_x']:.4f} m")
        st.write(f"- ȳ = {summary['cg_y']:.4f} m")
        
        st.markdown("**2. โมเมนต์และ Inerta รอบจุด CG**")
        st.write(f"- Mx,cg = {summary['mx_cg']:.3f} ton-m")
        st.write(f"- My,cg = {summary['my_cg']:.3f} ton-m")
        st.write(f"- Ixx = {summary['ixx']:.4f} m²")
        st.write(f"- Iyy = {summary['iyy']:.4f} m²")
        
        st.markdown("**3. ตารางสรุปน้ำหนักลงเสาเข็ม (Ri)**")
        df_display = df_results[['Pile', 'x', 'y', 'x_i', 'y_i', 'Ri']].copy()
        
        # ตกแต่งตาราง
        st.dataframe(df_display.style.format({
            'x': '{:.3f}', 'y': '{:.3f}', 
            'x_i': '{:.3f}', 'y_i': '{:.3f}', 
            'Ri': '{:.3f}'
        }), use_container_width=True)
        
        max_load = df_display['Ri'].max()
        max_pile = df_display.loc[df_display['Ri'].idxmax(), 'Pile']
        st.success(f"🔥 **Max Load:** เสาเข็ม {max_pile} รับน้ำหนักสูงสุดที่ **{max_load:.3f} ตัน**")

    with res_col2:
        st.subheader("📐 รูปประกอบ (Foundation Plan)")
        
        # --- ใช้ Matplotlib วาดรูป ---
        fig, ax = plt.subplots(figsize=(6, 6))
        
        # วาดเสาเข็มตำแหน่ง Design (วงกลมเส้นประ)
        for p in piles_data:
            ax.add_patch(plt.Circle((p['x_ideal'], p['y_ideal']), 0.15, color='gray', fill=False, linestyle='--', label='Design Pile' if p['Pile']=='P1' else ""))
            
        # วาดเสาเข็มตำแหน่ง Actual (วงกลมทึบ)
        for p in piles_data:
            ax.add_patch(plt.Circle((p['x'], p['y']), 0.15, color='blue', alpha=0.3, label='Actual Pile' if p['Pile']=='P1' else ""))
            ax.text(p['x'], p['y'], f"{p['Pile']}\n({p['Ri']:.1f}t)", ha='center', va='center', fontsize=9, color='black', weight='bold')

        # วาดจุดกึ่งกลางตอม่อ (0,0)
        ax.plot(0, 0, marker='+', color='black', markersize=15, markeredgewidth=2, label='Column Center (0,0)')
        
        # วาดจุด CG ใหม่ของกลุ่มเสาเข็ม
        ax.plot(summary['cg_x'], summary['cg_y'], marker='x', color='red', markersize=10, markeredgewidth=2, label='New Pile CG')
        
        # ตั้งค่ากราฟ
        ax.axhline(0, color='black', linewidth=0.5, linestyle='--')
        ax.axvline(0, color='black', linewidth=0.5, linestyle='--')
        ax.set_aspect('equal')
        ax.set_xlim(-1.2, 1.2)
        ax.set_ylim(-1.2, 1.2)
        ax.set_xlabel("X Axis (m)")
        ax.set_ylabel("Y Axis (m)")
        ax.set_title("Pile Layout & Deviation Map")
        
        # จัดการ Legend ไม่ให้ซ้ำกัน
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys(), loc='upper right', fontsize=8)
        
        # โชว์กราฟบน Streamlit
        st.pyplot(fig)
