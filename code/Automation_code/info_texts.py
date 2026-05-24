import streamlit as st

def show_binding_energy_info():
    st.markdown("""
        <div style="background-color:#1E3A5F;margin:10px 0; padding:20px 20px 20px 45px; border-radius:8px; color:white;">
            <h3>Understanding Binding Energy</h3>
            <ul>
                <li><b>Binding energy</b> reflects how strongly the ligand binds to the receptor.</li>
                <li><b>Lower (more negative) values</b> indicate <b>stronger binding</b> and more stable complexes.</li>
                <li>Typically, a value <b>&lt; -6.0 kcal/mol</b> is considered promising in virtual screening.</li>
                <li>Results can vary depending on <b>seed</b>, <b>exhaustiveness</b>, and <b>docking strategy</b>.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
