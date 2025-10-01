import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from datetime import datetime
import uuid
import time
import os
import json

# Conexão com Google Sheets - Versão segura para produção
scope = ["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"]

# Tenta carregar as credenciais das variáveis de ambiente (produção)
creds_json = os.environ.get('GOOGLE_CREDENTIALS')
if creds_json:
    try:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        st.sidebar.success("✅ Conectado ao Google Sheets (Produção)")
    except Exception as e:
        st.error(f"Erro nas credenciais: {e}")
        st.stop()
else:
    # Fallback para desenvolvimento local
    try:
        creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
        st.sidebar.info("🔧 Modo desenvolvimento local")
    except:
        st.error("❌ Credenciais não encontradas")
        st.stop()

client = gspread.authorize(creds)

# Abrir planilha usando ID fornecido
spreadsheet_id = "1rRYEj-Kvtyqqu8YQSiw-v2dgMf5a_kGYV7aQa1ue1JI"
sheet = client.open_by_key(spreadsheet_id).worksheet("Pedidos")

def get_pedidos():
    data = sheet.get_all_records()
    return pd.DataFrame(data)

def adicionar_pedido(solicitante, peca, tecnico, observacoes):
    linhas = sheet.get_all_values()
    ids_existentes = [linha[0] for linha in linhas]
    
    while True:
        novo_id = str(uuid.uuid4())[:8]
        if novo_id not in ids_existentes:
            break
    
    data = datetime.now().strftime("%d/%m/%Y")
    status = "Pendente"
    sheet.append_row([novo_id, data, solicitante, peca, tecnico, status, observacoes])
    st.success(f"Pedido {novo_id} adicionado!")

def atualizar_status(pedido_id, novo_status):
    pedidos = sheet.get_all_values()
    for i, linha in enumerate(pedidos):
        if linha[0] == str(pedido_id):
            sheet.update_cell(i+1, 6, novo_status)
            st.success(f"Status do pedido {pedido_id} atualizado para {novo_status}")
            return
    st.error("Pedido não encontrado.")

# ══════════════════════════════════════════════════════════════════════════════
# ⚠️ ALTERE A SENHA ABAIXO - TROQUE "admin123" PELA SUA SENHA DESEJADA ⚠️
SENHA_AUTORIZACAO = "admin123"  # ⬅️ MUDE ESTA SENHA!
# ══════════════════════════════════════════════════════════════════════════════

# Tempo para mensagem sumir (em segundos)
TEMPO_MENSAGEM = 5

# Inicializar session_state
if 'autorizado' not in st.session_state:
    st.session_state.autorizado = False
if 'mostrar_mensagem' not in st.session_state:
    st.session_state.mostrar_mensagem = False
if 'tempo_mensagem' not in st.session_state:
    st.session_state.tempo_mensagem = 0

st.title("Controle de Pedidos de Peças Usadas")

menu = st.sidebar.selectbox("Menu", ["Adicionar Pedido", "Visualizar Pedidos", "Atualizar Status"])

if menu == "Adicionar Pedido":
    st.header("Adicionar Pedido")
    solicitante = st.text_input("Solicitante")
    peca = st.text_input("Peça")
    tecnico = st.text_input("Técnico Responsável")
    observacoes = st.text_area("Observações")
    if st.button("Adicionar"):
        adicionar_pedido(solicitante, peca, tecnico, observacoes)

elif menu == "Visualizar Pedidos":
    st.header("Lista de Pedidos")
    df = get_pedidos()
    st.dataframe(df)

elif menu == "Atualizar Status":
    st.header("Atualizar Status do Pedido")
    
    # Se não está autorizado, pede a senha
    if not st.session_state.autorizado:
        senha = st.text_input("Digite a senha de autorização", type="password")
        
        if st.button("Validar Senha"):
            if senha == SENHA_AUTORIZACAO:
                st.session_state.autorizado = True
                st.session_state.mostrar_mensagem = True
                st.session_state.tempo_mensagem = time.time()
                st.rerun()
            else:
                st.error("❌ Senha incorreta. Tente novamente.")
    
    # Se está autorizado, mostra os campos de atualização
    else:
        # Cria um placeholder para a mensagem
        mensagem_placeholder = st.empty()
        
        # Mostra e controla a mensagem
        if st.session_state.mostrar_mensagem:
            tempo_atual = time.time()
            tempo_decorrido = tempo_atual - st.session_state.tempo_mensagem
            tempo_restante = max(0, TEMPO_MENSAGEM - tempo_decorrido)
            
            if tempo_restante > 0:
                # Mostra a mensagem com contador
                mensagem_placeholder.success(
                    f"✅ Acesso autorizado!"
                )
            else:
                # Esconde a mensagem quando o tempo acaba
                mensagem_placeholder.empty()
                st.session_state.mostrar_mensagem = False
        
        # Botão para sair (opcional)
        if st.button("🚪 Sair"):
            st.session_state.autorizado = False
            st.session_state.mostrar_mensagem = False
            st.rerun()
        
        pedido_id = st.text_input("ID do Pedido")
        novo_status = st.selectbox("Novo Status", ["Pendente", "Solicitado", "Entregue"])
        
        if st.button("Atualizar Status"):
            if pedido_id:
                atualizar_status(pedido_id, novo_status)
            else:
                st.warning("Por favor, informe o ID do pedido")