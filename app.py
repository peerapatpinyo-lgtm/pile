import streamlit as st
import pandas as pd

class PileGroupAnalysis:
    def __init__(self, pu, mx_ext=0, my_ext=0):
        self.pu = pu
        self.mx_ext = mx_ext
        self.my_ext = my_ext
        self.piles = []

    def add_pile(self, name, x_actual, y_actual):
        self.piles.append({
            'Pile': name,
            'x': x_actual,
            'y': y_actual
        })

    def calculate(self):
        n = len(self.piles)
        if n == 0:
            return None, None

        # 1. หาจุดศูนย์ถ่วง (CG)
        cg_x = sum(p['x'] for p in self.piles) / n
        cg_y = sum(p['y'] for p in self.piles) / n

        # 2. คำนวณโมเมนต์เยื้องศูนย์ (Eccentric Moments)
        ecc_mx = self.pu * cg_y
        ecc_my = self.pu * cg_x

        mx_cg = self.mx_ext + ecc_mx
        my_cg = self.my_ext + ecc_my

        # 3. หา Moment of Inertia (Ixx, Iyy)
        ixx = 0
        iyy = 0
        
        for p in self.piles:
            p['x_i'] = p['x'] - cg_x
            p['y_i'] = p['y'] - cg_y
            ixx += p['y_i'] ** 2
            iyy += p['x_i'] ** 2

        # 4. คำนวณแรงที่กระทำลงบนเสาเข็มแต่ละต้น (Ri)
        for p in self.piles:
            term1 = self.pu / n
            term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
            term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
            p['Ri'] = term1 + term2 + term3

        df_result = pd.DataFrame(self.piles)
        
        # เก็บค่า Summary ไว้แสดงผล
        summary = {
            'n': n,
            'cg_x': cg_x, 'cg_y': cg_y,
            'ixx': ixx, 'iyy': iyy,
            'mx_cg': mx_cg, 'my_cg': my_cg
        }
        
        return df_result, summary

# ==========================================
# ส่วนของการแสดงผลบน Streamlit UI
# ==========================================

st.set_page_config(page_title="Pile Deviation Calculator", layout="wide")

st.title("🏗️ โปรแกรมคำนวณ Pile Deviation (ฐานราก 4 ต้น)")
st.markdown("คำนวณการรับน้ำหนักของเสาเข็มเมื่อเกิดการเยื้องศูนย์ โดยอ้างอิงสมการ $R_i = \\frac{\\Sigma P_u}{n} + \\frac{M_{x,cg} \\cdot y_i}{I_{xx}} + \\frac{M_{y,cg} \\cdot x_i}{I_{yy}}$")

st.divider()

# --- ส่วนรับข้อมูล (Input Section) ---
st.subheader("1. กำหนดน้ำหนักบรรทุก (Load Input)")
pu_input = st.number_input("น้ำหนักในแนวดิ่งรวม (Pu) - หน่วย: ตัน", value=100.0, step=10.0)

st.subheader("2. กำหนดพิกัดเสาเข็มจริงหน้างาน (Coordinate Input)")
st.write("ระบุระยะ x, y โดยให้จุดศูนย์กลางตอม่ออยู่ที่ (0,0) หน่วยเป็นเมตร")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("**เสาเข็ม P1 (ซ้ายบน)**")
    x1 = st.number_input("X ของ P1", value=-0.40, step=0.05)
    y1 = st.number_input("Y ของ P1", value=0.55, step=0.05)

with col2:
    st.markdown("**เสาเข็ม P2 (ขวาบน)**")
    x2 = st.number_input("X ของ P2", value=0.50, step=0.05)
    y2 = st.number_input("Y ของ P2", value=0.50, step=0.05)

with col3:
    st.markdown("**เสาเข็ม P3 (ซ้ายล่าง)**")
    x3 = st.number_input("X ของ P3", value=-0.50, step=0.05)
    y3 = st.number_input("Y ของ P3", value=-0.50, step=0.05)

with col4:
    st.markdown("**เสาเข็ม P4 (ขวาล่าง)**")
    x4 = st.number_input("X ของ P4", value=0.50, step=0.05)
    y4 = st.number_input("Y ของ P4", value=-0.50, step=0.05)

# --- ส่วนคำนวณและแสดงผล (Calculation & Output Section) ---
if st.button("🧮 คำนวณ (Calculate)", type="primary"):
    
    # ดึง Class มาใช้งาน
    foundation = PileGroupAnalysis(pu=pu_input)
    foundation.add_pile("P1", x1, y1)
    foundation.add_pile("P2", x2, y2)
    foundation.add_pile("P3", x3, y3)
    foundation.add_pile("P4", x4, y4)
    
    df, summary = foundation.calculate()
    
    st.divider()
    st.subheader("📊 ผลการคำนวณ (Calculation Results)")
    
    # แสดงค่าพารามิเตอร์ต่างๆ เป็นตัวเลขสวยๆ ด้วย st.metric
    m_col1, m_col2, m_col3, m_col4 = st.columns(4)
    m_col1.metric("พิกัด CG ใหม่ (X, Y)", f"({summary['cg_x']:.3f}, {summary['cg_y']:.3f}) m")
    m_col2.metric("Mx,cg / My,cg", f"{summary['mx_cg']:.2f} / {summary['my_cg']:.2f} ton-m")
    m_col3.metric("Ixx", f"{summary['ixx']:.3f} m^2")
    m_col4.metric("Iyy", f"{summary['iyy']:.3f} m^2")
    
    st.markdown("**ตารางแสดงแรงปฏิกิริยาที่เสาเข็มแต่ละต้น (Ri)**")
    
    # จัด Format ทศนิยมให้ตารางก่อนนำไปโชว์
    df_styled = df.style.format({
        'x': '{:.3f}', 'y': '{:.3f}', 
        'x_i': '{:.3f}', 'y_i': '{:.3f}', 
        'Ri': '{:.3f}'
    })
    
    # แสดงตารางด้วย st.dataframe
    st.dataframe(df_styled, use_container_width=True)
    
    # ตรวจสอบค่า Max Load เบื้องต้น
    max_load = df['Ri'].max()
    max_pile = df.loc[df['Ri'].idxmax(), 'Pile']
    st.info(f"💡 **เสาเข็มที่รับน้ำหนักมากที่สุดคือ {max_pile}** รับน้ำหนักเท่ากับ **{max_load:.3f} ตัน** (ตรวจสอบกับ Safe Load ของเสาเข็มด้วยนะครับ)")
