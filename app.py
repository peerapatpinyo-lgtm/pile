import pandas as pd

class PileGroupAnalysis:
    def __init__(self, pu, mx_ext=0, my_ext=0):
        """
        กำหนดค่าเริ่มต้นให้กับฐานราก
        pu: น้ำหนักตามแนวแกนที่กระทำกับฐานราก (Total Vertical Load)
        mx_ext: โมเมนต์ดัดภายนอกรอบแกน X (External Moment about X)
        my_ext: โมเมนต์ดัดภายนอกรอบแกน Y (External Moment about Y)
        """
        self.pu = pu
        self.mx_ext = mx_ext
        self.my_ext = my_ext
        self.piles = []

    def add_pile(self, name, x_actual, y_actual):
        """
        เพิ่มข้อมูลพิกัดเสาเข็มแต่ละต้น (พิกัดจริงหน้างานที่มีการ Deviation)
        โดยให้ศูนย์กลางเสา (Column Center) อยู่ที่พิกัด (0,0)
        """
        self.piles.append({
            'Pile': name,
            'x': x_actual,
            'y': y_actual
        })

    def calculate(self):
        n = len(self.piles)
        if n == 0:
            raise ValueError("ยังไม่ได้เพิ่มข้อมูลเสาเข็ม")

        # 1. หาจุดศูนย์ถ่วง (CG) ใหม่ของกลุ่มเสาเข็มที่เยื้องศูนย์
        cg_x = sum(p['x'] for p in self.piles) / n
        cg_y = sum(p['y'] for p in self.piles) / n

        # 2. คำนวณโมเมนต์เยื้องศูนย์ (Eccentric Moments) 
        # เกิดจากน้ำหนักเสา Pu กระทำที่ (0,0) แต่จุดศูนย์ถ่วงเข็มเปลี่ยนไป
        ecc_mx = self.pu * cg_y
        ecc_my = self.pu * cg_x

        # โมเมนต์รวมที่กระทำรอบจุด CG ของกลุ่มเสาเข็ม
        mx_cg = self.mx_ext + ecc_mx
        my_cg = self.my_ext + ecc_my

        # 3. คำนวณระยะพิกัดเทียบกับจุด CG ใหม่ และหา Moment of Inertia (Ixx, Iyy)
        # หมายเหตุ: สำหรับเสาเข็มขนาดเท่ากัน Ixx = Sum(y^2), Iyy = Sum(x^2)
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

        # สรุปผลลัพธ์เป็นตาราง
        df_result = pd.DataFrame(self.piles)
        
        print("=== รายงานการคำนวณ Pile Deviation ===")
        print(f"จำนวนเสาเข็ม (n): {n} ต้น")
        print(f"Total Load (Pu): {self.pu} ton")
        print(f"พิกัด CG ใหม่ (x, y): ({cg_x:.3f}, {cg_y:.3f}) m")
        print(f"Ixx: {ixx:.3f} m^2, Iyy: {iyy:.3f} m^2")
        print(f"Mx,cg: {mx_cg:.3f} ton-m, My,cg: {my_cg:.3f} ton-m\n")
        print("แรงปฏิกิริยาที่เสาเข็มแต่ละต้น (Ri):")
        print(df_result[['Pile', 'x', 'y', 'x_i', 'y_i', 'Ri']].round(3))
        
        return df_result


# ==========================================
# วิธีใช้งาน (Example Usage)
# ==========================================
if __name__ == "__main__":
    # กำหนดน้ำหนักบรรทุก (สมมติ Pu = 100 ตัน, ไม่มีโมเมนต์ภายนอก)
    pu_load = 100.0 
    
    # สร้าง Object สำหรับคำนวณ
    foundation = PileGroupAnalysis(pu=pu_load, mx_ext=0, my_ext=0)
    
    # ใส่พิกัดเสาเข็มหน้างานจริง (หน่วย: เมตร) โดยให้ศูนย์กลางเสา (0,0)
    # ตัวอย่าง: ฐานราก F4 ขนาด 1.5 x 1.5 ม. ระยะห่างเสาเข็ม 1.0 ม. (แบบยังไม่ Deviation)
    # สมมติว่าต้นที่ 1 (P1) ตอกเยื้องไปทางขวา 0.1 ม. และขึ้นบน 0.05 ม.
    foundation.add_pile("P1", x_actual=-0.40, y_actual= 0.55) 
    foundation.add_pile("P2", x_actual= 0.50, y_actual= 0.50)
    foundation.add_pile("P3", x_actual=-0.50, y_actual=-0.50)
    foundation.add_pile("P4", x_actual= 0.50, y_actual=-0.50)
    
    # รันการคำนวณ
    results = foundation.calculate()
