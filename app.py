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

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch

# ==========================================
# 2. Proof Tab Rendering Function (Ultra-Compact & Refined Vectors)
# ==========================================
def render_proof_tab():
    st.header("📐 Rigid Pile Cap: Rigorous Vector Derivation")
    st.markdown("This section provides an advanced, step-by-step vector mechanics proof that directly links the position vector $\\vec{r}_i$ to the final Cartesian biaxial bending formula.")
    
    st.divider()

    # --- STEP 1 ---
    st.subheader("Step 1: Coordinate Setup & Eccentricity at CG")
    
    col1, col2 = st.columns([1.1, 1.2]) 
    
    with col1:
        st.markdown("Let the origin $(0,0)$ be located at the **Center of Gravity (CG)** of the pile group, meaning $\\sum x_i = 0$ and $\\sum y_i = 0$.")
        st.markdown("Any external load acting on the column is transferred to this CG, establishing eccentricities ($e_x, e_y$) as shown on the diagram:")
        st.markdown(r"$$ e_x = CG_x - Col_x $$")
        st.markdown(r"$$ e_y = CG_y - Col_y $$")
        st.markdown("The net force and moment vectors acting on the pile cap at the CG are defined as:")
        st.markdown(r"$$ \vec{F}_{ext} = P_w \hat{k} $$")
        st.markdown(r"$$ \vec{M}_{cg} = M_{x,cg}\hat{i} + M_{y,cg}\hat{j} $$")
        
        st.info(r"""
        **Moment Transfer Equation:**
        $$ M_{x,cg} = M_{x,ext} + (P_w \cdot e_y) $$
        $$ M_{y,cg} = M_{y,ext} + (P_w \cdot e_x) $$
        """)

    with col2:
        # --- Figure 1: Geometric Mapping & Equivalent Forces ---
        # ปรับขนาดรูปให้เล็กสุดๆ
        fig1, ax1 = plt.subplots(figsize=(4.2, 4.2))

        # 1. วาดฐานราก (Pile Cap)
        cap = patches.Rectangle((-2.5, -2.5), 5.0, 5.0, linewidth=1.5, edgecolor='#2c3e50', facecolor='#f8f9fa', zorder=1)
        ax1.add_patch(cap)

        # 2. แกนหลัก (Axes)
        ax1.axhline(0, color='black', linewidth=1.2, zorder=2)
        ax1.axvline(0, color='black', linewidth=1.2, zorder=2)
        ax1.text(2.3, 0.1, 'X', fontsize=9, fontweight='bold')
        ax1.text(0.1, 2.3, 'Y', fontsize=9, fontweight='bold')

        # พิกัด
        piles_x = [1.5, -1.5, -1.5, 1.5]
        piles_y = [1.5, 1.5, -1.5, -1.5]
        cg_x, cg_y = 0, 0
        col_x, col_y = -0.8, 1.2

        # 3. วาดเสาเข็ม
        for i, (px, py) in enumerate(zip(piles_x, piles_y)):
            pile = patches.Circle((px, py), 0.25, linewidth=1.2, edgecolor='#34495e', facecolor='#bdc3c7', zorder=3)
            ax1.add_patch(pile)
            bbox_props = dict(boxstyle="round,pad=0.1", fc="white", ec="gray", alpha=0.9)
            ax1.text(px, py - 0.45, f'Pile {i+1}\n($x_{i+1}, y_{i+1}$)', ha='center', va='top', fontsize=7, bbox=bbox_props, zorder=4)

        # 4. วาดจุดเสาและแรง (Column Load Pw)
        col = patches.Rectangle((col_x - 0.2, col_y - 0.2), 0.4, 0.4, linewidth=1.5, edgecolor='black', facecolor='#f1c40f', zorder=5)
        ax1.add_patch(col)
        ax1.plot(col_x, col_y, marker='x', color='black', markersize=6, markeredgewidth=1.5, zorder=6)
        ax1.text(col_x, col_y - 0.35, r'$P_w$', ha='center', fontsize=9, fontweight='bold', color='#d35400', zorder=6)

        # *** วาด M_x,ext และ M_y,ext ***
        mx_ext_arrow = FancyArrowPatch((col_x + 0.25, col_y + 0.15), (col_x + 0.25, col_y - 0.15), 
                                       connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=3,head_length=3", 
                                       color='#8e44ad', lw=1, zorder=6)
        ax1.add_patch(mx_ext_arrow)
        ax1.text(col_x + 0.35, col_y, r'$\vec{M}_{x,ext}$', color='#8e44ad', fontsize=8, fontweight='bold', va='center')

        my_ext_arrow = FancyArrowPatch((col_x - 0.15, col_y + 0.25), (col_x + 0.15, col_y + 0.25), 
                                       connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=3,head_length=3", 
                                       color='#2980b9', lw=1, zorder=6)
        ax1.add_patch(my_ext_arrow)
        ax1.text(col_x, col_y + 0.35, r'$\vec{M}_{y,ext}$', color='#2980b9', fontsize=8, fontweight='bold', ha='center')

        # 5. จุดศูนย์ถ่วง (CG)
        ax1.plot(cg_x, cg_y, marker='o', color='#e74c3c', markersize=7, zorder=5)
        ax1.plot(cg_x, cg_y, marker='x', color='black', markersize=4, zorder=6)
        ax1.text(0.1, -0.25, r'CG', color='#c0392b', fontsize=8, fontweight='bold', zorder=6)

        # 6. เส้นบอกระยะเยื้องศูนย์ (Eccentricity + Colx/Coly)
        dim_bbox = dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8)
        ax1.annotate('', xy=(col_x, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<->', color='#27ae60', lw=1.2), zorder=6)
        ax1.text(col_x / 2, 0.1, r'$Col_x\ (e_x)$', color='#27ae60', fontsize=8, ha='center', va='bottom', fontweight='bold', bbox=dim_bbox, zorder=7)
        
        ax1.annotate('', xy=(col_x, col_y), xytext=(col_x, 0), arrowprops=dict(arrowstyle='<->', color='#e67e22', lw=1.2), zorder=6)
        ax1.text(col_x - 0.1, col_y / 2, r'$Col_y\ (e_y)$', color='#d35400', fontsize=8, ha='right', va='center', fontweight='bold', bbox=dim_bbox, zorder=7)
        
        ax1.plot([col_x, col_x], [0, col_y], color='gray', linestyle='--', linewidth=0.8, zorder=2)
        ax1.plot([0, col_x], [col_y, col_y], color='gray', linestyle='--', linewidth=0.8, zorder=2)

        # 7. โมเมนต์รอบแกน X และ Y ที่ CG
        mx_arrow = FancyArrowPatch((0.2, 0.3), (0.2, -0.3), connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=4,head_length=4", color='#e67e22', lw=1.2, zorder=6)
        ax1.add_patch(mx_arrow)
        ax1.text(0.4, 0, r'$\vec{M}_{x,cg}$', color='#d35400', fontsize=9, fontweight='bold', va='center')

        my_arrow = FancyArrowPatch((-0.3, 0.2), (0.3, 0.2), connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=4,head_length=4", color='#2980b9', lw=1.2, zorder=6)
        ax1.add_patch(my_arrow)
        ax1.text(0, 0.4, r'$\vec{M}_{y,cg}$', color='#2980b9', fontsize=9, fontweight='bold', ha='center')

        # สมการสรุปในรูป (กัน ValueError)
        ax1.text(-2.4, -2.4, r'$M_{x,cg} = M_{x,ext} + (P_w \cdot e_y)$', fontsize=8, color='#c0392b', fontweight='bold', bbox=dict(facecolor='white', alpha=0.9, edgecolor='#e74c3c'), zorder=8)

        ax1.set_aspect('equal')
        ax1.set_xlim(-2.6, 2.6)
        ax1.set_ylim(-2.6, 2.6)
        ax1.set_title('1) Top View: Equivalent Force & Moments', fontsize=10, fontweight='bold', pad=8)
        ax1.grid(True, linestyle=':', alpha=0.5)
        ax1.axis('off')

        # บังคับไม่ให้ Streamlit ขยายภาพเต็มความกว้าง
        st.pyplot(fig1, use_container_width=False)

    st.divider()

    # --- STEP 2 ---
    st.subheader("Step 2: Vector Kinematics (Rigid Cap Compatibility)")
    
    col3, col4 = st.columns([1.1, 1.2])

    with col3:
        st.markdown("According to the rigid pile cap assumption, the cap does not deform internally; it only translates vertically by $w_0$ and rotates as a rigid plane. We define the rotation vector $\\vec{\\theta}$ about the CG as:")
        st.markdown(r"$$ \vec{\theta} = \theta_x \hat{i} + \theta_y \hat{j} $$")
        st.markdown("The position vector $\\vec{r}_i$ pointing from the CG to any specific pile $i$ is defined as:")
        st.markdown(r"$$ \vec{r}_i = x_i \hat{i} + y_i \hat{j} $$")
        st.markdown("The total vertical displacement ($w_i$) of pile $i$ is the sum of uniform translation and the vertical component resulting from the rotation vector cross product ($\\vec{\\theta} \times \\vec{r}_i$):")
        st.markdown(r"$$ w_i = w_0 + (\vec{\theta} \times \vec{r}_i) \cdot \hat{k} $$")
        st.markdown("Evaluating the cross product explicitly:")
        st.markdown(r"$$ \vec{\theta} \times \vec{r}_i = (\theta_x \hat{i} + \theta_y \hat{j}) \times (x_i \hat{i} + y_i \hat{j}) = (\theta_x y_i - \theta_y x_i)\hat{k} $$")
        st.markdown("Taking the dot product with $\\hat{k}$ yields the linear kinematic displacement equation:")
        st.markdown(r"$$ w_i = w_0 + \theta_x y_i - \theta_y x_i $$")

    with col4:
        # --- Figure 2: Vector Components ---
        fig2, ax2 = plt.subplots(figsize=(4.2, 4.2))

        ax2.axhline(0, color='black', linewidth=1.2, zorder=2)
        ax2.axvline(0, color='black', linewidth=1.2, zorder=2)
        ax2.text(2.4, 0.1, 'X', fontsize=9, fontweight='bold')
        ax2.text(0.1, 2.4, 'Y', fontsize=9, fontweight='bold')

        px, py = 1.8, 1.3
        pile_i = patches.Circle((px, py), 0.25, linewidth=1.2, edgecolor='#34495e', facecolor='#bdc3c7', zorder=3)
        ax2.add_patch(pile_i)
        ax2.text(px, py + 0.35, 'Pile $i$', ha='center', fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="gray", alpha=0.9))

        ax2.annotate('', xy=(px, py), xytext=(0,0), arrowprops=dict(arrowstyle='-|>', color='#2980b9', lw=2, mutation_scale=15), zorder=4)
        ax2.text(px/2 - 0.2, py/2 + 0.2, r'$\vec{r}_i$', color='#2980b9', fontsize=11, fontweight='bold', bbox=dict(boxstyle="circle,pad=0.1", fc="white", ec="none", alpha=0.8))
        
        ax2.annotate('', xy=(px, 0), xytext=(0,0), arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5, ls='--'), zorder=3)
        ax2.annotate('', xy=(px, py), xytext=(px,0), arrowprops=dict(arrowstyle='->', color='#3498db', lw=1.5, ls='--'), zorder=3)
        ax2.text(px/2, -0.2, r'$x_i \hat{i}$', color='#2980b9', fontsize=9, ha='center', fontweight='bold')
        ax2.text(px + 0.15, py/2, r'$y_i \hat{j}$', color='#2980b9', fontsize=9, va='center', fontweight='bold')

        tx, ty = 0.8, 1.8
        ax2.annotate('', xy=(tx, ty), xytext=(0,0), arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=2, mutation_scale=15), zorder=4)
        ax2.text(tx/2 - 0.3, ty/2 + 0.1, r'$\vec{\theta}$', color='#c0392b', fontsize=11, fontweight='bold', bbox=dict(boxstyle="circle,pad=0.1", fc="white", ec="none", alpha=0.8))
        
        ax2.annotate('', xy=(tx, 0), xytext=(0,0), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5, ls='-.'), zorder=3)
        ax2.annotate('', xy=(0, ty), xytext=(0,0), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.5, ls='-.'), zorder=3)
        ax2.text(tx/2, 0.15, r'$\theta_x \hat{i}$', color='#c0392b', fontsize=9, ha='center', fontweight='bold')
        ax2.text(0.15, ty/2, r'$\theta_y \hat{j}$', color='#c0392b', fontsize=9, va='center', fontweight='bold')

        ax2.set_aspect('equal')
        ax2.set_xlim(-0.5, 2.6)
        ax2.set_ylim(-0.5, 2.6)
        ax2.set_title('2) Position & Rotation Vectors', fontsize=10, fontweight='bold', pad=8)
        ax2.grid(True, linestyle=':', alpha=0.5)
        ax2.axis('off')

        st.pyplot(fig2, use_container_width=False)

    st.divider()

    # --- STEP 3 ถึง STEP 6 ---
    st.subheader("Step 3: Constitutive Force-Displacement Relationship")
    st.markdown("Assuming all piles behave as identical linear elastic springs with an axial stiffness $k$, the vertical reaction force vector $\\vec{R}_i$ at pile $i$ is:")
    st.markdown(r"$$ \vec{R}_i = R_i \hat{k} = (k \cdot w_i) \hat{k} $$")
    st.markdown(r"$$ R_i = k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \quad \text{--- (Eq. 1)} $$")

    st.subheader("Step 4: Vector Static Equilibrium")
    st.markdown("The summation of all internal pile reactions must satisfy both force and moment equilibrium against external actions.")
    
    st.markdown("#### A. Vertical Force Equilibrium")
    st.markdown(r"$$ \sum \vec{R}_i = \vec{F}_{ext} \implies \sum R_i = P_w $$")
    st.markdown(r"$$ \sum \left[ k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \right] = P_w $$")
    st.markdown("Since the origin is at the CG, $\\sum x_i = 0$ and $\\sum y_i = 0$. The equation simplifies to:")
    st.markdown(r"$$ n \cdot (k w_0) = P_w \implies k w_0 = \frac{P_w}{n} \quad \text{--- (Eq. 2)} $$")

    st.markdown("#### B. Moment Equilibrium via Cross Product")
    st.markdown("The external net moment vector at the CG must equal the sum of moments generated by the pile reactions:")
    st.markdown(r"$$ \vec{M}_{cg} = \sum (\vec{r}_i \times \vec{R}_i) $$")
    st.markdown(r"$$ M_{x,cg}\hat{i} + M_{y,cg}\hat{j} = \sum \left[ (x_i \hat{i} + y_i \hat{j}) \times (R_i \hat{k}) \right] $$")
    st.markdown("Using standard unit vector cross products ($\\hat{i} \times \hat{k} = -\hat{j}$ and $\\hat{j} \times \hat{k} = \hat{i}$):")
    st.markdown(r"$$ M_{x,cg}\hat{i} + M_{y,cg}\hat{j} = \sum (R_i y_i)\hat{i} - \sum (R_i x_i)\hat{j} $$")
    
    st.markdown("By equating the orthogonal vector components, we obtain two scalar equations:")
    st.markdown(r"$$ M_{x,cg} = \sum R_i y_i \quad \text{and} \quad M_{y,cg} = -\sum R_i x_i $$")

    st.subheader("Step 5: Solving for Bending Stiffness Constants")
    st.markdown("Substitute the general expression for $R_i$ (Eq. 1) into the scalar moment equations, assuming principal axes of symmetry ($\sum x_i y_i = 0$):")
    st.markdown(r"$$ M_{x,cg} = \sum \left[ k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \right] y_i = k \theta_x \sum y_i^2 $$")
    st.markdown(r"$$ M_{y,cg} = -\sum \left[ k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \right] x_i = k \theta_y \sum x_i^2 $$")
    st.markdown("By defining the Pile Group Moments of Inertia as $I_{xx} = \sum y_i^2$ and $I_{yy} = \sum x_i^2$, we solve for the rotational terms:")
    st.markdown(r"$$ k \theta_x = \frac{M_{x,cg}}{I_{xx}} \quad \text{--- (Eq. 3)} $$")
    st.markdown(r"$$ k \theta_y = \frac{M_{y,cg}}{I_{yy}} \quad \text{--- (Eq. 4)} $$")

    st.subheader("Step 6: Final Linear Superposition")
    st.markdown("Substituting the solved equilibrium constants (Eq. 2, Eq. 3, and Eq. 4) back into the pile reaction equation (Eq. 1) yields the final master formula:")
    
    st.success("🎯 **Final Master Equation:**")
    st.markdown(r"$$ R_i = \frac{P_w}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} $$")
    
    st.divider()
    st.markdown("### 📌 Summary of Geometric Mapping")
    st.markdown("- The position vector **$\\vec{r}_i = x_i \hat{i} + y_i \hat{j}$** physically maps each pile's coordinates relative to the CG.")
    st.markdown("- The vector cross product elegantly demonstrates why $y_i$ couples with $I_{xx}$ (rotation about the X-axis) and $x_i$ couples with $I_{yy}$ (rotation about the Y-axis) without relying on arbitrary assumptions.")

    
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
