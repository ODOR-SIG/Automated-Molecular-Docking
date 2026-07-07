import streamlit as st

st.set_page_config(page_title="Help & Support", page_icon="❓", layout="centered")

st.title("Help & Support")

st.markdown("This guide will walk you through how to use the Molecular Docking UI and explain key terminologies and result interpretation strategies.")

# How to Use
with st.expander("📘 How to Use"):
    st.markdown("""
1. **Enter your desired receptor name** correctly (e.g., `OR1A1`,`OR6F1`)
2. **Enter one or more ligand names** (comma-separated), e.g., `Citral, 4-decenal`
3. **Ensure spelling is correct** for both receptor and ligands.
4. Click the **“Submit and Validate”** button.
5. Wait a few minutes — the model will download receptor and ligand(s).
6. Once validation results appear, Click **“Proceed to docking”**
7. Adjust the **docking configuration**
8. Click **“Start Docking”**
9. Review the docking results.
10. To save the results, click **“Download CSV”**
""")

# Terminologies
with st.expander("📚 Terminologies"):

    st.subheader("Molecular Docking")
    st.write("""
Molecular docking is like trying to fit a key (called a ligand) into a lock (called a receptor or protein).
""")

    st.subheader("Binding Affinity")
    st.write("""
Binding affinity tells us how strongly a ligand sticks to a receptor (target).""")

    st.subheader("Docking Configuration")
    st.markdown("""
- **Exhaustiveness**:  
  Controls how much effort the software puts into finding the best fit between the receptor and ligand.

- **Number of Poses (`num_modes`)**:  
  Specifies how many ligand poses are saved. Helps explore alternate binding geometries.

- **Energy Range**:  
  Determines how many poses are kept based on their score relative to the best one.

- **Random Seed**:  
  Initializes the random search process. Setting this ensures reproducibility of results.

- **User Input Seed**:  
  Manually entered seed value to control reproducibility, especially useful in benchmarking or scientific reporting.
""")

# Result Interpretation
with st.expander("📊 Result Interpretation"):

    st.subheader("Bond Strength")
    st.markdown("""
Binding energy indicates ligand-receptor strength.  
Lower (more negative) values = stronger binding.

Typical threshold:
`≤ -7.0 kcal/mol` → **strong, promising binding**

**Colour coding based on binding energy:**

| Binding Energy Range | Bond Strength            | Color |
|----------------------|--------------------------|-------|
| ≤ -7.0                | Strong Binding Affinity  | 🟦 Blue |
| -7.0 to -5.0          | Moderate Binding Affinity| 🟧 Amber |
| > -5.0                | Weak Binding Affinity    | 🟧 Orange |
""")

    st.subheader("Bond Consistency")
    st.markdown("""
For each receptor-ligand pair, docking runs 3 times.  
The tool calculates best, average binding energy and **standard deviation (SD)** for consistency.

**Colour coding based on SD:**

| Std. Deviation Range | Bond Consistency     | Color |
|----------------------|----------------------|-------|
| 0.0 to 0.2           | Consistent Binding   | 🟩 Green |
| 0.2 to 0.5           | Medium Consistency   | 🟧 Orange |
| > 0.5                | Inconsistent Binding | 🟥 Red |
""")
    
st.markdown("---")
st.markdown("""
<div style="text-align: center; font-size: 13px; color: #6c757d; font-family: 'Segoe UI', sans-serif;">
    © 2025 · Molecular Docking Interface<br>
</div>
""", unsafe_allow_html=True)
