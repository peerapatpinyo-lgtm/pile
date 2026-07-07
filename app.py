import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# 1. Engineering Calculation Core
# ==========================================
def calculate_pile_deviation(pu, mx_ext, my_ext, piles_df):
    """
    Calculates the individual pile reactions for an eccentrically loaded pile group
    assuming a rigid pile cap.
    """
    piles = piles_df.to_dict('records')
    n = len(piles)
    
    if n == 0:
        return None, None

    # Step 1: Calculate New Center of Gravity (CG)
    cg_x = sum(p['x_actual'] for p in piles) / n
    cg_y = sum(p['y_actual'] for p in piles) / n

    # Step 2: Calculate Eccentric Moments
    # Moment = Force x Perpendicular Distance to the new CG
    ecc_mx = pu * cg_y
    ecc_my = pu * cg_x
    
    # Total Moments about the new CG
    mx_cg = mx_ext + ecc_mx
    my_cg = my_ext + ecc_my

    # Step 3: Calculate Pile Distances from New CG and Group Moment of Inertia
    ixx = 0
    iyy = 0
    for p in piles:
        p['x_i'] = p['x_actual'] - cg_x  # Distance from CG along X-axis
        p['y_i'] = p['y_actual'] - cg_y  # Distance from CG along Y-axis
        p['x_i_sq'] = p['x_i'] ** 2
        p['y_i_sq'] = p['y_i'] ** 2
        ixx += p['y_i_sq']
        iyy += p['x_i_sq']

    # Step 4: Calculate Individual Pile Reactions (Ri)
    for p in piles:
        term1 = pu / n
        term2 = (mx_cg * p['y_i']) / ixx if ixx != 0 else 0
        term3 = (my_cg * p['x_i']) / iyy if iyy != 0 else 0
        p['Ri'] = term1 + term2 + term3

    summary = {
        'n': n, 'cg_x': cg_x, 'cg_y': cg_y,
        'ixx': ixx, 'iyy': iyy,
        'mx_cg': mx_cg, 'my_cg': my_cg,
        'ecc_mx': ecc_mx, 'ecc_my': ecc_my,
        'pu': pu, 'mx_ext': mx_ext, 'my_ext': my_ext
    }
    
    return pd.DataFrame(piles), summary

# ==========================================
# 2. Streamlit UI and Output Rendering
# ==========================================
st.set_page_config(page_title="Pile Deviation Analysis", layout="wide")

st.title("🏗️ Pile Deviation Analysis & Calculation Report")
st.markdown("Calculate individual pile reactions due to construction deviations. The system generates a **Step-by-Step Calculation Sheet** and a **Foundation Plan** automatically.")

st.divider()

# --- Input Section ---
st.subheader("1. Design Loads Input")
col_p, col_mx, col_my = st.columns(3)
pu_input = col_p.number_input("Total Ultimate Axial Load (Pu) - [Tons]", value=100.0, step=10.0)
mx_input = col_mx.number_input("External Moment about X-axis (Mx) - [Ton-m]", value=0.0, step=1.0)
my_input = col_my.number_input("External Moment about Y-axis (My) - [Ton-m]", value=0.0, step=1.0)

st.subheader("2. Pile Coordinates Management")
st.caption("💡 Edit the table directly to modify coordinates. You can add or delete rows to analyze different pile configurations (e.g., F2, F3, F-Mat). Column Center is at (0,0).")

# Default Data (F4 Foundation)
default_data = pd.DataFrame({
    'Pile_Name': ['P1', 'P2', 'P3', 'P4'],
    'x_design': [-0.50, 0.50, -0.50, 0.50],
    'y_design': [0.50, 0.50, -0.50, -0.50],
    'x_actual': [-0.48, 0.53, -0.50, 0.51],
    'y_actual': [0.55, 0.48, -0.52, -0.45]
})

edited_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

st.divider()

# --- Calculation & Results Section ---
if st.button("🧮 Calculate & Generate Report", type="primary"):
    
    df_res, summary = calculate_pile_deviation(pu_input, mx_input, my_input, edited_df)
    
    if df_res is not None:
        
        # ==========================================
        # Dynamic Calculation Sheet (Expander)
        # ==========================================
        with st.expander("📝 View Step-by-Step Calculation Sheet", expanded=True):
            st.markdown("This calculation sheet is generated dynamically based on your inputs for structural cross-checking purposes.")
            
            st.markdown("### Step 1: New Center of Gravity (CG) of the Pile Group")
            st.markdown("The new CG is the average of the actual pile coordinates.")
            st.markdown(rf"$$ \bar{{x}} = \frac{{\sum x_{{actual}}}}{{n}} = {summary['cg_x']:.4f} \text{{ m}} $$")
            st.markdown(rf"$$ \bar{{y}} = \frac{{\sum y_{{actual}}}}{{n}} = {summary['cg_y']:.4f} \text{{ m}} $$")
            
            st.markdown("### Step 2: Total Eccentric Moments ($M_{x,cg}, M_{y,cg}$)")
            st.markdown("Moments generated about the new CG due to load eccentricity and external moments.")
            st.markdown(rf"$$ M_{{x,cg}} = M_{{x,ext}} + (P_u \cdot \bar{{y}}) = {summary['mx_ext']} + ({summary['pu']} \cdot {summary['cg_y']:.4f}) = {summary['mx_cg']:.4f} \text{{ Ton-m}} $$")
            st.markdown(rf"$$ M_{{y,cg}} = M_{{y,ext}} + (P_u \cdot \bar{{x}}) = {summary['my_ext']} + ({summary['pu']} \cdot {summary['cg_x']:.4f}) = {summary['my_cg']:.4f} \text{{ Ton-m}} $$")

            st.markdown("### Step 3: Group Moment of Inertia ($I_{xx}, I_{yy}$)")
            st.markdown("Calculate the distances from the new CG ($x_i, y_i$) and the resulting Moment of Inertia for the pile group.")
            
            # Show intermediate table for Inertia calculation
            df_inertia = df_res[['Pile_Name', 'x_actual', 'y_actual', 'x_i', 'y_i', 'x_i_sq', 'y_i_sq']].copy()
            df_inertia.columns = ['Pile', 'x_actual', 'y_actual', 'x_i (x - x̄)', 'y_i (y - ȳ)', 'x_i²', 'y_i²']
            st.table(df_inertia.style.format({col: '{:.4f}' for col in df_inertia.columns if col != 'Pile'}))

            st.markdown(rf"$$ I_{{xx}} = \sum (y_i)^2 = {summary['ixx']:.4f} \text{{ m}}^2 $$")
            st.markdown(rf"$$ I_{{yy}} = \sum (x_i)^2 = {summary['iyy']:.4f} \text{{ m}}^2 $$")
            
            st.markdown("### Step 4: Individual Pile Reactions ($R_i$)")
            st.markdown("Determine the load distributed to each pile using the rigid pile cap equation:")
            st.markdown(r"$$ R_i = \frac{P_u}{n} + \frac{M_{x,cg} \cdot y_i}{I_{xx}} + \frac{M_{y,cg} \cdot x_i}{I_{yy}} $$")
            
            st.markdown("**Substituting values for each pile:**")
            for idx, row in df_res.iterrows():
                formula = rf"$$ R_{{{row['Pile_Name']}}} = \frac{{{summary['pu']}}}{{{summary['n']}}} + \frac{{{summary['mx_cg']:.4f} \cdot ({row['y_i']:.4f})}}{{{summary['ixx']:.4f}}} + \frac{{{summary['my_cg']:.4f} \cdot ({row['x_i']:.4f})}}{{{summary['iyy']:.4f}}} = {row['Ri']:.3f} \text{{ Tons}} $$"
                st.markdown(formula)

        st.divider()

        # ==========================================
        # Summary and Plotting Section
        # ==========================================
        out_col1, out_col2 = st.columns([1, 1])
        
        with out_col1:
            st.subheader("📊 Summary of Pile Reactions ($R_i$)")
            
            df_display = df_res[['Pile_Name', 'x_design', 'y_design', 'x_actual', 'y_actual', 'x_i', 'y_i', 'Ri']]
            st.dataframe(df_display.style.format({
                'x_design': '{:.3f}', 'y_design': '{:.3f}',
                'x_actual': '{:.3f}', 'y_actual': '{:.3f}',
                'x_i': '{:.3f}', 'y_i': '{:.3f}', 'Ri': '{:.3f}'
            }), use_container_width=True)
            
            max_r = df_res['Ri'].max()
            max_pile = df_res.loc[df_res['Ri'].idxmax(), 'Pile_Name']
            st.error(f"⚠️ **Maximum Pile Load:** Pile **{max_pile}** governs the design with a load of **{max_r:.3f} Tons**.")

        with out_col2:
            st.subheader("📐 Foundation Deviation Plan")
            
            # --- Matplotlib Plotting ---
            fig, ax = plt.subplots(figsize=(6, 6))
            
            # Plot Design Positions
            ax.scatter(df_res['x_design'], df_res['y_design'], s=400, facecolors='none', edgecolors='gray', linestyle='--', linewidth=1.5, label='Design Position')
            
            # Plot Actual Positions
            ax.scatter(df_res['x_actual'], df_res['y_actual'], s=450, color='deepskyblue', alpha=0.4, edgecolors='blue', linewidth=1.5, label='Actual Position')
            
            # Annotate Piles and Arrows
            for idx, row in df_res.iterrows():
                ax.text(row['x_actual'], row['y_actual'], f"{row['Pile_Name']}\n{row['Ri']:.2f} t", ha='center', va='center', fontsize=9, color='black', weight='bold')
                ax.annotate('', xy=(row['x_actual'], row['y_actual']), xytext=(row['x_design'], row['y_design']),
                            arrowprops=dict(arrowstyle="->", color='red', lw=1))

            # Plot Origin and New CG
            ax.plot(0, 0, marker='+', color='black', markersize=18, markeredgewidth=2.5, label='Column Center (0,0)')
            ax.plot(summary['cg_x'], summary['cg_y'], marker='x', color='crimson', markersize=12, markeredgewidth=2.5, label='New Pile CG')
            
            # Graph Formatting
            ax.axhline(0, color='black', linewidth=0.6, linestyle=':')
            ax.axvline(0, color='black', linewidth=0.6, linestyle=':')
            ax.set_aspect('equal')
            
            # Dynamic Axis Scaling
            max_val = max(df_res['x_design'].abs().max(), df_res['y_design'].abs().max()) * 1.8
            ax.set_xlim(-max_val, max_val)
            ax.set_ylim(-max_val, max_val)
            
            ax.set_xlabel("X-Axis (meters)")
            ax.set_ylabel("Y-Axis (meters)")
            ax.grid(True, linestyle='--', alpha=0.5)
            ax.legend(loc='upper right', fontsize=8)
            
            st.pyplot(fig)
    else:
        st.warning("Please add at least one pile to the coordinate table.")
