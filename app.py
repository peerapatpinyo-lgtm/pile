import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyArrowPatch
import math

# =========================================================================
# 1. Engineering Calculation Core (Upgraded for Asymmetry & Stiffness)
# =========================================================================
def calculate_pile_deviation(pw, mx_ext, my_ext, q_main, q_micro, fs, min_spacing, piles_df):
    """
    Calculates pile reactions using Generalized Asymmetrical Bending Theory
    and accounts for Relative Stiffness differences between Main and Micro piles.
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

    # 1. Stiffness Assumption: Approximate stiffness ratio based on ultimate capacity
    k_main = 1.0
    k_micro = q_micro / q_main if q_main > 0 else 0.5 

    sum_k = 0
    for p in piles:
        p['x_actual'] = p['x_design'] + p['dev_x']
        p['y_actual'] = p['y_design'] + p['dev_y']
        p['Allowable_Load'] = safe_load_main if p['Pile_Type'] == 'Main' else safe_load_micro
        # Assign relative stiffness factor
        p['k_factor'] = k_main if p['Pile_Type'] == 'Main' else k_micro
        sum_k += p['k_factor']

    # Spacing Verification Check
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

    # 2. Stiffness-Weighted Center of Gravity (CG)
    cg_x = sum(p['k_factor'] * p['x_actual'] for p in piles) / sum_k
    cg_y = sum(p['k_factor'] * p['y_actual'] for p in piles) / sum_k

    # 3. Eccentric Moments (Column center is at 0,0 -> relative to CG is -cg_x, -cg_y)
    ecc_mx = pw * (-cg_y)
    ecc_my = pw * (-cg_x)
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # 4. Generalized Group Inertias (including asymmetric product of inertia I_xy)
    ixx = iyy = ixy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x  
        p['y_i'] = p['y_actual'] - cg_y  
        
        # Multiply by relative stiffness factor to scale structural contribution
        ixx += p['k_factor'] * (p['y_i'] ** 2)
        iyy += p['k_factor'] * (p['x_i'] ** 2)
        ixy += p['k_factor'] * (p['x_i'] * p['y_i'])

    denom = (ixx * iyy) - (ixy ** 2)

    # 5. Pile Reaction Calculation (Asymmetrical Bending Formula)
    overall_load_passed = True
    for p in piles:
        # Axial translation component
        term1 = pw / sum_k
        
        # Biaxial rotational components (coupled via cross product of inertia)
        if denom != 0:
            term2 = ((mx_cg * iyy - my_cg * ixy) / denom) * p['y_i']
            term3 = ((my_cg * ixx - mx_cg * ixy) / denom) * p['x_i']
        else:
            term2 = term3 = 0
            
        # Total force reaction = Relative Stiffness * (Combined Unit Displacement)
        p['Ri'] = p['k_factor'] * (term1 + term2 + term3)
        
        if p['Ri'] > p['Allowable_Load']:
            p['Status'] = 'FAIL (Overload)'
            overall_load_passed = False
        else:
            p['Status'] = 'PASS'

    summary = {
        'n': n, 'cg_x': cg_x, 'cg_y': cg_y, 'sum_k': sum_k,
        'ixx': ixx, 'iyy': iyy, 'ixy': ixy,
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


# =========================================================================
# 2. Proof Tab Rendering Function (Refined Scale & Full Details)
# =========================================================================
def render_proof_tab():
    st.header("📐 Rigid Pile Cap: Rigorous Vector Derivation")
    st.markdown("This section provides an advanced, step-by-step vector mechanics proof that directly links the position vector $\\vec{r}_i$ to the final Cartesian biaxial bending formula.")
    
    st.divider()

    # --- STEP 1 ---
    st.subheader("Step 1: Coordinate Setup & Eccentricity at CG")
    
    col1, col2 = st.columns([1.2, 1.0]) 
    
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
        fig1, ax1 = plt.subplots(figsize=(3.8, 3.8))

        cap = patches.Rectangle((-2.5, -2.5), 5.0, 5.0, linewidth=1.2, edgecolor='#2c3e50', facecolor='#f8f9fa', zorder=1)
        ax1.add_patch(cap)

        ax1.axhline(0, color='black', linewidth=1, zorder=2)
        ax1.axvline(0, color='black', linewidth=1, zorder=2)
        ax1.text(2.3, 0.1, 'X', fontsize=8, fontweight='bold')
        ax1.text(0.1, 2.3, 'Y', fontsize=8, fontweight='bold')

        piles_x = [1.5, -1.5, -1.5, 1.5]
        piles_y = [1.5, 1.5, -1.5, -1.5]
        cg_x, cg_y = 0, 0
        col_x, col_y = -0.8, 1.2

        for i, (px, py) in enumerate(zip(piles_x, piles_y)):
            pile = patches.Circle((px, py), 0.25, linewidth=1, edgecolor='#34495e', facecolor='#bdc3c7', zorder=3)
            ax1.add_patch(pile)
            bbox_props = dict(boxstyle="round,pad=0.1", fc="white", ec="gray", alpha=0.9)
            ax1.text(px, py - 0.35, f'Pile {i+1}\n($x_{i+1}, y_{i+1}$)', ha='center', va='top', fontsize=6, bbox=bbox_props, zorder=4)

        col = patches.Rectangle((col_x - 0.2, col_y - 0.2), 0.4, 0.4, linewidth=1, edgecolor='black', facecolor='#f1c40f', zorder=5)
        ax1.add_patch(col)
        ax1.plot(col_x, col_y, marker='x', color='black', markersize=4, markeredgewidth=1, zorder=6)
        ax1.text(col_x, col_y - 0.35, r'$P_w$', ha='center', fontsize=7, fontweight='bold', color='#d35400', zorder=6)

        mx_ext_arrow = FancyArrowPatch((col_x + 0.25, col_y + 0.15), (col_x + 0.25, col_y - 0.15), 
                                       connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=2.5,head_length=2.5", 
                                       color='#8e44ad', lw=0.8, zorder=6)
        ax1.add_patch(mx_ext_arrow)
        ax1.text(col_x + 0.35, col_y, r'$\vec{M}_{x,ext}$', color='#8e44ad', fontsize=7, fontweight='bold', va='center')

        my_ext_arrow = FancyArrowPatch((col_x - 0.15, col_y + 0.25), (col_x + 0.15, col_y + 0.25), 
                                       connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=2.5,head_length=2.5", 
                                       color='#2980b9', lw=0.8, zorder=6)
        ax1.add_patch(my_ext_arrow)
        ax1.text(col_x, col_y + 0.35, r'$\vec{M}_{y,ext}$', color='#2980b9', fontsize=7, fontweight='bold', ha='center')

        ax1.plot(cg_x, cg_y, marker='o', color='#e74c3c', markersize=5, zorder=5)
        ax1.plot(cg_x, cg_y, marker='x', color='black', markersize=3, zorder=6)
        ax1.text(0.1, -0.25, 'CG', color='#c0392b', fontsize=7, fontweight='bold', zorder=6)

        dim_bbox = dict(boxstyle="round,pad=0.1", fc="white", ec="none", alpha=0.8)
        ax1.annotate('', xy=(col_x, 0), xytext=(0, 0), arrowprops=dict(arrowstyle='<->', color='#27ae60', lw=1), zorder=6)
        ax1.text(col_x / 2, 0.1, r'$e_x$', color='#27ae60', fontsize=7, ha='center', va='bottom', fontweight='bold', bbox=dim_bbox, zorder=7)
        
        ax1.annotate('', xy=(col_x, col_y), xytext=(col_x, 0), arrowprops=dict(arrowstyle='<->', color='#e67e22', lw=1), zorder=6)
        ax1.text(col_x - 0.1, col_y / 2, r'$e_y$', color='#d35400', fontsize=7, ha='right', va='center', fontweight='bold', bbox=dim_bbox, zorder=7)
        
        ax1.plot([col_x, col_x], [0, col_y], color='gray', linestyle='--', linewidth=0.5, zorder=2)
        ax1.plot([0, col_x], [col_y, col_y], color='gray', linestyle='--', linewidth=0.5, zorder=2)

        mx_arrow = FancyArrowPatch((0.2, 0.3), (0.2, -0.3), connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=3,head_length=3", color='#e67e22', lw=1, zorder=6)
        ax1.add_patch(mx_arrow)
        ax1.text(0.4, 0, r'$\vec{M}_{x,cg}$', color='#d35400', fontsize=7, fontweight='bold', va='center')

        my_arrow = FancyArrowPatch((-0.3, 0.2), (0.3, 0.2), connectionstyle="arc3,rad=.5", arrowstyle="simple,head_width=3,head_length=3", color='#2980b9', lw=1, zorder=6)
        ax1.add_patch(my_arrow)
        ax1.text(0, 0.4, r'$\vec{M}_{y,cg}$', color='#2980b9', fontsize=7, fontweight='bold', ha='center')

        ax1.set_aspect('equal')
        ax1.set_xlim(-2.6, 2.6)
        ax1.set_ylim(-2.6, 2.6)
        ax1.set_title('1) Top View: Equivalent Actions', fontsize=8, fontweight='bold', pad=5)
        ax1.grid(True, linestyle=':', alpha=0.5)
        ax1.axis('off')

        st.pyplot(fig1, use_container_width=False)

    st.divider()

    # --- STEP 2 ---
    st.subheader("Step 2: Vector Kinematics (Rigid Cap Compatibility)")
    
    col3, col4 = st.columns([1.2, 1.0])

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
        fig2, ax2 = plt.subplots(figsize=(3.8, 3.8))

        ax2.axhline(0, color='black', linewidth=1, zorder=2)
        ax2.axvline(0, color='black', linewidth=1, zorder=2)
        ax2.text(2.4, 0.1, 'X', fontsize=8, fontweight='bold')
        ax2.text(0.1, 2.4, 'Y', fontsize=8, fontweight='bold')

        px, py = 1.8, 1.3
        pile_i = patches.Circle((px, py), 0.25, linewidth=1, edgecolor='#34495e', facecolor='#bdc3c7', zorder=3)
        ax2.add_patch(pile_i)
        ax2.text(px, py + 0.35, 'Pile $i$', ha='center', fontsize=7, fontweight='bold', bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="gray", alpha=0.9))

        ax2.annotate('', xy=(px, py), xytext=(0,0), arrowprops=dict(arrowstyle='-|>', color='#2980b9', lw=1.5, mutation_scale=10), zorder=4)
        ax2.text(px/2 - 0.2, py/2 + 0.2, r'$\vec{r}_i$', color='#2980b9', fontsize=9, fontweight='bold', bbox=dict(boxstyle="circle,pad=0.1", fc="white", ec="none", alpha=0.8))
        
        ax2.annotate('', xy=(px, 0), xytext=(0,0), arrowprops=dict(arrowstyle='->', color='#3498db', lw=1, ls='--'), zorder=3)
        ax2.annotate('', xy=(px, py), xytext=(px,0), arrowprops=dict(arrowstyle='->', color='#3498db', lw=1, ls='--'), zorder=3)
        ax2.text(px/2, -0.2, r'$x_i \hat{i}$', color='#2980b9', fontsize=7, ha='center', fontweight='bold')
        ax2.text(px + 0.15, py/2, r'$y_i \hat{j}$', color='#2980b9', fontsize=7, va='center', fontweight='bold')

        tx, ty = 0.8, 1.8
        ax2.annotate('', xy=(tx, ty), xytext=(0,0), arrowprops=dict(arrowstyle='-|>', color='#c0392b', lw=1.5, mutation_scale=10), zorder=4)
        ax2.text(tx/2 - 0.2, ty/2 + 0.1, r'$\vec{\theta}$', color='#c0392b', fontsize=9, fontweight='bold', bbox=dict(boxstyle="circle,pad=0.1", fc="white", ec="none", alpha=0.8))
        
        ax2.annotate('', xy=(tx, 0), xytext=(0,0), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1, ls='-.'), zorder=3)
        ax2.annotate('', xy=(0, ty), xytext=(0,0), arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1, ls='-.'), zorder=3)
        ax2.text(tx/2, 0.15, r'$\theta_x \hat{i}$', color='#c0392b', fontsize=7, ha='center', fontweight='bold')
        ax2.text(0.15, ty/2, r'$\theta_y \hat{j}$', color='#c0392b', fontsize=7, va='center', fontweight='bold')

        ax2.set_aspect('equal')
        ax2.set_xlim(-0.5, 2.6)
        ax2.set_ylim(-0.5, 2.6)
        ax2.set_title('2) Position & Rotation Vectors', fontsize=8, fontweight='bold', pad=5)
        ax2.grid(True, linestyle=':', alpha=0.5)
        ax2.axis('off')

        st.pyplot(fig2, use_container_width=False)

    st.divider()

    # --- STEP 3 ---
    st.subheader("Step 3: Constitutive Force-Displacement Relationship")
    st.markdown("Assuming all piles behave as identical linear elastic springs with an axial stiffness $k$, the reaction force is directly proportional to the vertical displacement (Hooke's Law):")
    st.markdown(r"$$ R_i = k \cdot w_i $$")
    st.markdown("Expressing the vertical reaction force vector $\\vec{R}_i$ at pile $i$ in vector form:")
    st.markdown(r"$$ \vec{R}_i = R_i \hat{k} = (k \cdot w_i) \hat{k} $$")
    st.markdown(r"$$ R_i = k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \quad \text{--- (Eq. 1)} $$")

    # --- STEP 4 ---
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
    st.markdown(r"Using standard unit vector cross products ($\hat{i} \times \hat{k} = -\hat{j}$ and $\hat{j} \times \hat{k} = \hat{i}$):")
    st.markdown(r"$$ M_{x,cg}\hat{i} + M_{y,cg}\hat{j} = \sum (R_i y_i)\hat{i} - \sum (R_i x_i)\hat{j} $$")
    
    st.markdown("By equating the orthogonal vector components, we obtain two scalar equations:")
    st.markdown(r"$$ M_{x,cg} = \sum (R_i y_i) \quad \text{and} \quad M_{y,cg} = -\sum (R_i x_i) $$")

    # --- STEP 5 ---
    st.subheader("Step 5: Solving for Bending Stiffness Constants")
    st.markdown("Substitute the general expression for $R_i$ (Eq. 1) into the scalar moment equations, assuming principal axes of symmetry ($\sum x_i y_i = 0$):")
    st.markdown(r"$$ M_{x,cg} = \sum \left[ k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \right] y_i = k \theta_x \sum y_i^2 $$")
    st.markdown(r"$$ M_{y,cg} = -\sum \left[ k w_0 + (k \theta_x) y_i - (k \theta_y) x_i \right] x_i = k \theta_y \sum x_i^2 $$")
    st.markdown("By defining the Pile Group Moments of Inertia as $I_{xx} = \sum y_i^2$ and $I_{yy} = \sum x_i^2$, we solve for the rotational terms:")
    st.markdown(r"$$ k \theta_x = \frac{M_{x,cg}}{I_{xx}} \quad \text{--- (Eq. 3)} $$")
    st.markdown(r"$$ k \theta_y = \frac{M_{y,cg}}{I_{yy}} \quad \text{--- (Eq. 4)} $$")

    # --- STEP 6 (Theory Only) ---
    st.subheader("Step 6: Generalized Asymmetrical Formulation")
    st.markdown("When substituting the solutions back into Eq. 1 and generalizing for asymmetrical pile groups (where $I_{xy} \neq 0$ and stiffness $k_i$ varies), we arrive at the full governing equation utilized in this software:")
    st.info(r"$$ R_i = k_i \cdot \left[ \frac{P_w}{\sum k} + \left( \frac{M_{x,cg} I_{yy} - M_{y,cg} I_{xy}}{I_{xx} I_{yy} - I_{xy}^2} \right) y_i + \left( \frac{M_{y,cg} I_{xx} - M_{x,cg} I_{xy}}{I_{xx} I_{yy} - I_{xy}^2} \right) x_i \right] $$")
    
    # --- STEP 7 ---
    st.subheader("Step 7: Analysis of As-Built Pile Deviation")
    
    st.warning("⚠️ **Limitation of the Simplified Formula**")
    st.markdown("The master equation derived in Step 6 assumes that the pile group layout is perfectly symmetrical, meaning the product of inertia is zero ($I_{xy} = \sum x_i y_i = 0$).")
    
    st.markdown("If piles deviate significantly from their intended locations during construction (**As-Built Deviation**):")
    st.markdown("- **1. Centroidal Shift:** The physical center of gravity of the group shifts. The coordinate origin must be re-established, which consequently changes the load eccentricities ($e_x, e_y$).")
    st.markdown("- **2. Asymmetrical Bending Induction:** The group structure loses its axis of symmetry ($I_{xy} \\neq 0$). The rotation parameters (Eq. 3 and Eq. 4) become strongly coupled, requiring the generalized asymmetrical bending equation.")

    st.divider()
    st.markdown("### 📌 Summary of Geometric Mapping")
    st.markdown("- The position vector **$\\vec{r}_i = x_i \hat{i} + y_i \hat{j}$** physically maps each pile's coordinates relative to the group's elastic centroid.")
    st.markdown("- The vector cross product elegantly demonstrates why $y_i$ couples with $I_{xx}$ (rotation about the X-axis) and $x_i$ couples with $I_{yy}$ (rotation about the Y-axis) without relying on arbitrary layout assumptions.")


# =========================================================================
# 3. Streamlit UI and Output Rendering
# =========================================================================
st.set_page_config(page_title="Advanced Pile Redesign System", layout="wide")

st.title("🏗️ Pile Deviation, Mitigation & Spacing Analysis Report")
st.markdown("Professional foundation redesign tool featuring dual-capacity checking, minimum spacing verification, and a **High-Detail Calculation Report**.")

tab_calc, tab_proof = st.tabs(["🧮 Calculation & Mitigation", "📐 Formula Derivation (Proof)"])

# ----------------- TAB 1: Calculation & Mitigation -----------------
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
                    st.success("🟢 **LOAD CHECK: PASSED** - All piles are operating within allowable structural capacities.")
                else:
                    st.error("🔴 **LOAD CHECK: FAILED** - One or more piles exceed safe allowable capacity limits!")
                    
            with status_col2:
                if summary['overall_spacing_passed']:
                    st.success(f"🟢 **SPACING CHECK: PASSED** - All piles meet the minimum spacing criteria ($\ge$ {summary['min_spacing']} m).")
                else:
                    st.error(f"🔴 **SPACING CHECK: FAILED** - Piles are placed too close to each other. Soil shearing risk detected!")

            st.divider()

            # ==========================================
            # 2.2 HIGH-DETAIL CALCULATION SHEET (Asymmetrical & Stiffness-Weighted)
            # ==========================================
            st.subheader("📝 Engineering Step-by-Step Calculation Sheet")
            
            st.markdown("#### Step 1: Geotechnical Allowable Pile Capacities ($R_{allow}$)")
            st.markdown("Allowable safe loads computed based on the assigned Factor of Safety (FS):")
            st.markdown(rf"$$ R_{{allow, Main}} = \frac{{Q_{{ult, Main}}}}{{FS}} = \frac{{{summary['q_main']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_main']:.3f} \text{{ Tons}} $$")
            st.markdown(rf"$$ R_{{allow, Micro}} = \frac{{Q_{{ult, Micro}}}}{{FS}} = \frac{{{summary['q_micro']:.3f}}}{{{summary['fs']:.1f}}} = {summary['safe_micro']:.3f} \text{{ Tons}} $$")

            st.markdown("#### Step 2: Construction Pre-processing & Actual Coordinates Estimation")
            st.markdown(r"$$ x_{{actual}} = x_{{design}} + \text{{dev\_x}}, \quad y_{{actual}} = y_{{design}} + \text{{dev\_y}} $$")
            df_actuals = df_res[['Pile_Name', 'Pile_Type', 'x_design', 'dev_x', 'x_actual', 'y_design', 'dev_y', 'y_actual']].copy()
            st.table(df_actuals.style.format({col: '{:.4f}' for col in df_actuals.columns if col not in ['Pile_Name', 'Pile_Type']}))

            st.markdown("#### Step 3: Stiffness-Weighted Center of Gravity (CG) of the Global Pile Group")
            st.markdown("For configurations with mixed pile types/capacities, the relative stiffness factor ($k_{factor}$) is utilized to calculate the stiffness-weighted elastic center of rotation:")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum (k_{{factor}} \cdot x_{{actual}})}}{{\sum k_{{factor}}}} = {summary['cg_x']:.4f} \text{{ m}} $$")
            st.markdown(rf"$$ \bar{{y}} = \frac{{\sum (k_{{factor}} \cdot y_{{actual}})}}{{\sum k_{{factor}}}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            st.caption(f"Note: Total Relative Stiffness ($\sum k$) = {summary['sum_k']:.4f}")
            
            st.markdown("#### Step 4: Total Eccentric Moments about New Shifted Centroid ($M_{x,cg}, M_{y,cg}$)")
            st.markdown("Since the physical column center is located at $(0,0)$, the resulting eccentricities relative to the new stiffness-weighted CG are defined as $e_x = -\bar{x}$ and $e_y = -\bar{y}$:")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_w \cdot (-\bar{{y}})) = {summary['mx_ext']:.3f} + ({summary['pw']:.3f} \cdot {-summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_w \cdot (-\bar{{x}})) = {summary['my_ext']:.3f} + ({summary['pw']:.3f} \cdot {-summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("#### Step 5: Group Geometrical Properties & Stiffness-Weighted Moments of Inertia ($I_{xx}, I_{yy}, I_{xy}$)")
            st.markdown(r"Where $x_i = x_{actual} - \bar{{x}}$ and $y_i = y_{actual} - \bar{{y}}$:")
            df_inertia = df_res[['Pile_Name', 'Pile_Type', 'k_factor', 'x_actual', 'y_actual', 'x_i', 'y_i']].copy()
            df_inertia['k_factor * x_i²'] = df_res['k_factor'] * (df_res['x_i'] ** 2)
            df_inertia['k_factor * y_i²'] = df_res['k_factor'] * (df_res['y_i'] ** 2)
            df_inertia['k_factor * x_i * y_i'] = df_res['k_factor'] * (df_res['x_i'] * df_res['y_i'])
            
            df_inertia.columns = ['Pile', 'Type', 'k_factor', 'x_act', 'y_act', 'x_i', 'y_i', 'k·x_i²', 'k·y_i²', 'k·x_i·y_i']
            st.table(df_inertia.style.format({col: '{:.4f}' for col in df_inertia.columns if col not in ['Pile', 'Type']}))

            st.markdown(rf"$$ I_{{xx}} = \sum k_{{factor}} \cdot (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{yy}} = \sum k_{{factor}} \cdot (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{xy}} = \sum k_{{factor}} \cdot (x_i \cdot y_i) = {summary['ixy']:.4f} \text{{ m}}^2 \quad \color{{red}}{{\text{{(Product of Inertia due to structural asymmetry)}}}} $$")
            
            denom_val = (summary['ixx'] * summary['iyy']) - (summary['ixy'] ** 2)
            st.markdown(rf"$$ \text{{Denominator Constraint (Deterministic Demanding)}} = I_{{xx}}I_{{yy}} - I_{{xy}}^2 = {denom_val:.6f} $$")
            
            # =================================================================
            # NEW/REWRITTEN STEP 6: HIGH-DETAIL EXPLICIT NUMERICAL SUBSTITUTION
            # =================================================================
            st.markdown("#### Step 6: Detailed Pile Reaction Substitution via Asymmetrical Bending Theory ($R_i$)")
            st.markdown("To ensure complete analytical transparency, the calculation is strictly based on the **Full Generalized Asymmetrical Bending Equation**:")
            
            st.info(r"$$ R_i = k_i \cdot \left[ \frac{P_w}{\sum k} + \left( \frac{M_{x,cg} I_{yy} - M_{y,cg} I_{xy}}{I_{xx} I_{yy} - I_{xy}^2} \right) y_i + \left( \frac{M_{y,cg} I_{xx} - M_{x,cg} I_{xy}}{I_{xx} I_{yy} - I_{xy}^2} \right) x_i \right] $$")
            
            st.markdown("To simplify the explicit substitution for each pile, the bracketed terms are first evaluated globally as fundamental coefficients ($A, B$, and $C$):")
            
            # Compute global coefficients for the entire group
            coef_axial = pw_input / summary['sum_k']
            coef_mx = (summary['mx_cg'] * summary['iyy'] - summary['my_cg'] * summary['ixy']) / denom_val if denom_val != 0 else 0
            coef_my = (summary['my_cg'] * summary['ixx'] - summary['mx_cg'] * summary['ixy']) / denom_val if denom_val != 0 else 0
            
            st.markdown("##### 🔸 Global Foundation Coefficients")
            st.markdown(rf"""
            * **Axial Translation Term ($A$):**  
              $$\frac{{P_w}}{{\sum k}} = \frac{{{pw_input:.3f}}}{{{summary['sum_k']:.4f}}} = {coef_axial:.4f}$$
            * **X-Axis Bending Gradient ($B$):**  
              $$\frac{{M_{{x,cg}} \cdot I_{{yy}} - M_{{y,cg}} \cdot I_{{xy}}}}{{I_{{xx}}I_{{yy}} - I_{{xy}}^2}} = \frac{{({summary['mx_cg']:.3f} \cdot {summary['iyy']:.4f}) - ({summary['my_cg']:.3f} \cdot {summary['ixy']:.4f})}}{{{denom_val:.6f}}} = {coef_mx:.4f}$$
            * **Y-Axis Bending Gradient ($C$):**  
              $$\frac{{M_{{y,cg}} \cdot I_{{xx}} - M_{{x,cg}} \cdot I_{{xy}}}}{{I_{{xx}}I_{{yy}} - I_{{xy}}^2}} = \frac{{({summary['my_cg']:.3f} \cdot {summary['ixx']:.4f}) - ({summary['mx_cg']:.3f} \cdot {summary['ixy']:.4f})}}{{{denom_val:.6f}}} = {coef_my:.4f}$$
            """)
            
            st.markdown("##### 🔸 Individual Pile-by-Pile Explicit Substitution")
            
            # Iterate through each pile with absolute mathematical visibility
            for idx, row in df_res.iterrows():
                ki = row['k_factor']
                xi = row['x_i']
                yi = row['y_i']
                ri = row['Ri']
                r_allow = row['Allowable_Load']
                
                term1 = coef_axial
                term2 = coef_mx * yi
                term3 = coef_my * xi
                
                check_symbol = r"\le" if ri <= r_allow else r"\gt"
                status_text = "PASS (Safe)" if ri <= r_allow else "FAIL (Overloaded)"
                
                with st.container():
                    st.markdown(f"###### 🔹 Pile ID: **{row['Pile_Name']}** ({row['Pile_Type']} Pile)")
                    
                    st.markdown(r"**A. Governing Mathematical Model:**")
                    st.markdown(r"$$ R_i = k_i \cdot \left[ A + B \cdot y_i + C \cdot x_i \right] $$")
                    
                    st.markdown(r"**B. Explicit Numerical Substitution:**")
                    st.markdown(rf"$$ R_{{{row['Pile_Name']}}} = {ki:.3f} \cdot \left[ {coef_axial:.4f} + ({coef_mx:.4f}) \cdot ({yi:.4f}) + ({coef_my:.4f}) \cdot ({xi:.4f}) \right] $$")
                    
                    st.markdown(r"**C. Evaluated Component Stresses:**")
                    st.markdown(rf"$$ R_{{{row['Pile_Name']}}} = {ki:.3f} \cdot \left[ {term1:.4f} \text{{ (Axial)}} + ({term2:.4f}) \text{{ (X-Rot)}} + ({term3:.4f}) \text{{ (Y-Rot)}} \right] $$")
                    
                    st.markdown(r"**D. Boundary Capacity Verification:**")
                    st.markdown(rf"$$ R_{{{row['Pile_Name']}}} = \mathbf{{{ri:.3f} \text{{ Tons}}}} \quad {check_symbol} \quad R_{{allow}} = {r_allow:.3f} \text{{ Tons}} $$")
                    
                    if ri <= r_allow:
                        st.success(f"✅ **{row['Pile_Name']} Verification:** Calculated Load {ri:.3f} t ≤ Allowable {r_allow:.3f} t → **{status_text}**")
                    else:
                        st.error(f"❌ **{row['Pile_Name']} Verification:** Calculated Load {ri:.3f} t > Allowable {r_allow:.3f} t → **{status_text}**")
                    
                    st.write("") # Spacer

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

# ----------------- TAB 2: Formula Derivation (Proof) -----------------
with tab_proof:
    render_proof_tab()
