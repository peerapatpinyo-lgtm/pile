import streamlit as st

def render_proof_tab():
    st.header("📐 Rigid Pile Cap: Formula Derivation (Proof)")
    st.markdown("การพิสูจน์สมการการกระจายแรงลงเสาเข็มภายใต้สมมติฐาน **Rigid Pile Cap (ฐานรากแข็งเกร็ง)** อ้างอิงจากรูปบนกระดาน")
    
    st.divider()

    st.subheader("1. กำหนดตัวแปรและเวกเตอร์ (Vectors & Setup)")
    st.markdown(r"$$ \vec{r}_1 = x_1\hat{i} + y_1\hat{j} $$")
    st.markdown(r"$$ \vec{r}_2 = x_2\hat{i} + y_2\hat{j} $$")
    st.markdown(r"$$ \vec{M}_R = M_x\hat{i} + M_y\hat{j} $$")
    
    st.subheader("2. สมดุลของโมเมนต์ (Moment Equilibrium)")
    st.markdown("ผลรวมของโมเมนต์ที่เกิดจากแรงต้านของเสาเข็มแต่ละต้น ($P_i$) คูณด้วยระยะห่าง ($R_i$) จะต้องเท่ากับโมเมนต์ลัพธ์ภายนอก ($M_R$)")
    st.markdown(r"$$ \sum P_i \cdot R_i = M_R $$")
    st.markdown(r"$$ P_1 \cdot R_1 + P_2 \cdot R_2 + \dots + P_n \cdot R_n = M_R $$")
    
    st.subheader("3. สมมติฐานฐานรากแข็งเกร็ง (Compatibility Condition)")
    st.markdown("เมื่อฐานรากแข็งเกร็ง แรงที่ตกกระทำบนเสาเข็มจะแปรผันตรงกับระยะห่างจากจุดศูนย์ถ่วง (CG)")
    st.markdown(r"$$ \frac{P_1}{R_1} = \frac{P_2}{R_2} = \dots = \frac{P_n}{R_n} $$")
    st.markdown("จัดรูปสมการเพื่อหาแรงของเสาเข็มต้นอื่นๆ ในรูปของ $P_1$:")
    st.markdown(r"$$ P_2 = \frac{R_2}{R_1} \cdot P_1 $$")
    st.markdown(r"$$ P_3 = \frac{R_3}{R_1} \cdot P_1 $$")
    
    st.subheader("4. แทนค่ากลับลงในสมการสมดุลโมเมนต์")
    st.markdown(r"$$ P_1 \frac{R_1^2}{R_1} + P_1 \frac{R_2^2}{R_1} + P_1 \frac{R_3^2}{R_1} + \dots + P_1 \frac{R_n^2}{R_1} = M_R $$")
    st.markdown(r"ดึงตัวร่วม $\frac{P_1}{R_1}$ ออกมา:")
    st.markdown(r"$$ \frac{P_1}{R_1} \sum R_i^2 = M_R $$")
    
    st.subheader("5. สมการขั้นสุดท้าย (Final Equation)")
    st.markdown("ย้ายข้างเพื่อหาแรงปฏิกิริยาของเสาเข็มต้นที่ 1 ($P_1$) จะได้ว่า:")
    st.markdown(r"$$ P_1 = \frac{M_R \cdot R_1}{\sum R_i^2} $$")
    
    st.divider()
    
    st.info(r"💡 **Note (จากกระดานฝั่งขวา):** การหาโมเมนต์ที่เกิดจากแรงเยื้องศูนย์ (Eccentricity) คำนวณจาก $M_x = P_u \cdot \bar{y}$ และ $M_y = P_u \cdot \bar{x}$")
