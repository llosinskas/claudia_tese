import streamlit as st
from models.Microrrede import listar_microrredes, listar_fontes_microrrede

def listar_fontes_interface():
    st.title("Listar Fontes da Microrrede")

    microrredes = listar_microrredes()
    if not microrredes:
        st.warning("Nenhuma microrrede encontrada.")
        return

    microrrede_selecionada = st.selectbox("Selecione uma Microrrede", microrredes, format_func=lambda x: x.nome)

    if microrrede_selecionada:
        fontes = listar_fontes_microrrede(microrrede_selecionada.id)
        if fontes:
            st.subheader(f"Fontes da Microrrede '{microrrede_selecionada.nome}'")
            for tipo, fonte in fontes.items():
                if fonte:
                    st.write(f"{tipo}: {fonte}")
                else:
                    st.write(f"{tipo}: Não configurado")

if __name__ == "__main__":
    listar_fontes_interface()