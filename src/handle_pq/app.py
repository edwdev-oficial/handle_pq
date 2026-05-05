import streamlit as st
from streamlit_option_menu import option_menu

from handle_pq.pages import (
    handle_pq, test_dev, tlm
)
from handle_pq.utils import handle_json
from handle_pq.database.database import(
    get_database,
    get_gollection_tlm,
    get_collection_normal_itens
)

def app():
    st.set_page_config(
        page_title='Handle Pq',
        page_icon='⛏️',
        layout='wide',
    )

    def handle_pq_show():
        handle_pq.show()
        # if st.sidebar.button('Send Normal Itens'):
        #     col_normal_itens = get_collection_normal_itens()
        #     normal_itens = handle_json.read_json(name='normal_itens', tipo='df').to_dict(orient='records')
        #     resultado = col_normal_itens.insert_many(normal_itens)
        #     if resultado.acknowledged:
        #         st.success(f'{len(resultado.inserted_ids)} registros inseridos')
        #     else:
        #         st.error('Inserção não confirmada')        

        # if st.sidebar.button('Send TLM'):
        #     tlm_dict = handle_json.read_json(name='tlm', tipo='dict')
        #     col_tlm = get_gollection_tlm()
        #     result = col_tlm.insert_one(tlm_dict)
        #     if result.acknowledged:
        #         st.success('Documento inserido com sucesso')
        #         st.write(f'ID: {result.inserted_id}')
        #     else:
        #         st.error('Inserção não confirmada')        

    def cadastrar_show():
        tlm.show()

    def test_dev_show():
        if not st.session_state.df_pq.empty:
            test_dev.show(st.session_state.df_pq)
        else:
            handle_pq.show()
            st.warning('Carregue os arquivos de parque de máquinas baixados no HOL')

    with st.sidebar:
        selected = option_menu(
            'Páginas',
            [
                'Handle Pq',
                'Cadastrar TLM',
                # '---',
                # 'Test Dev',
            ],
            icons=[
                'tools',
                'r-circle',
                # None,
                # 'filetype-py'
            ]
        )

    root = {
        'Handle Pq': handle_pq_show,
        'Cadastrar TLM': cadastrar_show,
        'Test Dev': test_dev_show
    }        

    root[selected]()

