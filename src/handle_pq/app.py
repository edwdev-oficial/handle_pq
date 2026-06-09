# import streamlit as st
# from streamlit_option_menu import option_menu

# from handle_pq.pages import (
#     handle_pq, tlm, analisar_pq, renovacoes, test_dev
# )
# from handle_pq.utils import handle_json
# from handle_pq.database.database import(
#     get_database,
#     get_gollection_tlm,
#     get_collection_normal_itens
# )
# from handle_pq.utils import loaders

# def app():
#     st.set_page_config(
#         page_title='Handle Pq',
#         page_icon='⛏️',
#         layout='wide',
#     )

#     if 'page_subtitle' not in st.session_state:
#         st.session_state.page_subtitle = ''

#     def handle_pq_show():
#         st.session_state.page_subtitle = 'Carregar dados'
#         handle_pq.show()
#         st.rerun()
       

#     def cadastrar_show():
#         tlm.show()

#     def analisar_show():
#         st.session_state.page_subtitle = 'Visão consolidada do parque, composição por grupo, idade, reparações e custos.'
#         analisar_pq.show()
#         st.rerun()

#     def renovacoes_show():
#         st.session_state.page_subtitle = 'Renovações Gestão de Frotas'
#         renovacoes.show()
#         st.rerun()

#     def test_dev_show():
#         test_dev.show()

#     with st.sidebar:
#         selected = option_menu(
#             'Páginas',
#             [
#                 'Carregar dados',
#                 'Analisar Pq',
#                 'Renovações',
#                 'Cadastrar TLM',
#                 # '---',
#                 # 'Test Dev',
#             ],
#             icons=[
#                 'box-arrow-in-down',
#                 'search',
#                 'r-square',
#                 'book',
#                 # None,
#                 # 'filetype-py'
#             ]
#         )

#     # ==========================================
#     # region Header
#     # ==========================================
#     logo_base64 = loaders.logo_hilti_base64()   
#     st.markdown(
#         f"""
#         <div class="header-container">
#             <img src="data:image/png;base64,{logo_base64}">
#             <div class="header-title">
#                 Análise do Parque de Máquinas
#                 <p>{st.session_state.page_subtitle}<p>
#             </div>
#         </div>
#         """,
#         unsafe_allow_html=True
#     )
#     # ==========================================
#     # endregion    

#     root = {
#         'Carregar dados': handle_pq_show,
#         'Analisar Pq': analisar_show,
#         'Renovações': renovacoes_show,
#         'Cadastrar TLM': cadastrar_show,
#         'Test Dev': test_dev_show
#     }        

#     root[selected]()



# # ========================================================
# # region PARTE QUE ESTAVA DENTRO DA FUNÇÃO handle_pq_show()
# # ========================================================
#         # if st.sidebar.button('Send Normal Itens'):
#         #     col_normal_itens = get_collection_normal_itens()
#         #     normal_itens = handle_json.read_json(name='normal_itens', tipo='df').to_dict(orient='records')
#         #     resultado = col_normal_itens.insert_many(normal_itens)
#         #     if resultado.acknowledged:
#         #         st.success(f'{len(resultado.inserted_ids)} registros inseridos')
#         #     else:
#         #         st.error('Inserção não confirmada')        

#         # if st.sidebar.button('Send TLM'):
#         #     tlm_dict = handle_json.read_json(name='tlm', tipo='dict')
#         #     col_tlm = get_gollection_tlm()
#         #     result = col_tlm.insert_one(tlm_dict)
#         #     if result.acknowledged:
#         #         st.success('Documento inserido com sucesso')
#         #         st.write(f'ID: {result.inserted_id}')
#         #     else:
#         #         st.error('Inserção não confirmada')
# # endregion
# # ========================================================    

import streamlit as st
from streamlit_option_menu import option_menu

from handle_pq.pages import (
    handle_pq, tlm, analisar_pq, renovacoes
)

from handle_pq.utils import loaders


def render_header(subtitle: str):
    logo_base64 = loaders.logo_hilti_base64()

    st.markdown(
        f"""
        <div class="header-container">
            <img src="data:image/png;base64,{logo_base64}">
            <div class="header-title">
                Análise do Parque de Máquinas
                <p>{subtitle}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def app():
    st.set_page_config(
        page_title='Handle Pq',
        page_icon='⛏️',
        layout='wide',
    )

    st.set_option("client.toolbarMode", "minimal")

    pages = {
        'Carregar dados': {
            'icon': 'box-arrow-in-down',
            'subtitle': 'Carregar dados',
            'show': handle_pq.show
        },
        'Analisar Pq': {
            'icon': 'search',
            'subtitle': 'Visão consolidada do parque, composição por grupo, idade, reparações e custos.',
            'show': analisar_pq.show
        },
        'Renovações': {
            'icon': 'r-square',
            'subtitle': 'Renovações Gestão de Frotas',
            'show': renovacoes.show
        },
        'Cadastrar TLM': {
            'icon': 'book',
            'subtitle': 'Cadastro de tipos, linhas e modelos',
            'show': tlm.show
        },
    }

    with st.sidebar:
        selected = option_menu(
            'Páginas',
            list(pages.keys()),
            icons=[page['icon'] for page in pages.values()]
        )

    current_page = pages[selected]

    render_header(current_page['subtitle'])

    current_page['show']()