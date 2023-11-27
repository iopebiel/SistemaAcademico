from flask import Flask, flash, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime 
import random
import smtplib
from email.mime.text import MIMEText
import re
import sqlite3


#APP FLASK

app = Flask(__name__, static_url_path='/static')

try:
    with open('https://github.com/iopebiel/SistemaAcademico/blob/meu-novo-branch/static/config/secretkey.txt', 'r') as arquivo:
        app.secret_key = arquivo.readline().strip() #Chave para sessão.
except FileNotFoundError:
    print("Arquivo não encontrado.")
except Exception as e:
    print(f"Ocorreu um erro: {e}")

email_contato = 'contato.sistemagu@gmail.com'


#-----BANCO DE DADOS-----
def criar_tabela_alunos():
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            numeroprontuario TEXT PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT,
            curso TEXT,
            semestre INTEGER,
            unidade TEXT,
            turma TEXT
        )
    ''')

    conexao.commit()
    conexao.close()

    
def criar_tabela_disciplinas():
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS disciplinas (
            sigla TEXT PRIMARY KEY,
            nome TEXT,
            professor TEXT,
            curso TEXT,
            dia TEXT,
            horario TIME,
            aulaspordia INTEGER,
            total INTEGER
        )
    ''')

    conexao.commit()
    conexao.close()

def criar_tabela_aluno_disciplina():
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS aluno_disciplina (
            aluno_id INTEGER,
            disciplina_id INTEGER,
            data_inscricao TEXT,
            nota INTEGER,
            PRIMARY KEY (aluno_id, disciplina_id),
            FOREIGN KEY (aluno_id) REFERENCES alunos (id),
            FOREIGN KEY (disciplina_id) REFERENCES disciplinas (id)
        )
    ''')

    conexao.commit()
    conexao.close()


#-----INDEX-----


@app.route('/')
def index():
    return render_template('login.html')


#-----ENVIO DE E-MAIL-----

def enviar_email(destinatario, assunto, corpo):
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = email_contato
    
    arquivoemail = 'https://github.com/iopebiel/SistemaAcademico/blob/meu-novo-branch/static/config/senha.txt'
        
    try:
        with open(arquivoemail, 'r') as arquivo:
            smtp_password = arquivo.readline().strip()
    except FileNotFoundError:
        print("Arquivo não encontrado.")
    except Exception as e:
        print(f"Ocorreu um erro: {e}")

    # Criação da mensagem de e-mail
    msg = MIMEText(corpo)
    msg['Subject'] = assunto
    msg['From'] = email_contato
    msg['To'] = destinatario

    # Conexão ao servidor SMTP e envio do e-mail
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(smtp_username, smtp_password)
    server.sendmail('...', [destinatario], msg.as_string())
    server.quit()
 
 
#-----PRIMEIRAS TELAS-----
 
@app.route('/cadastro', methods=['GET','POST'])
def cadastrar():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        nome = request.form['nome']
        curso = request.form['curso']
        
        semestre = int(request.form['semestre'])
        turma = curso + str(semestre)

        unidade = request.form['unidade']
        numeroprontuario = request.form['numeroprontuario']

        #Deve conter exatamente 7 caracteres
        if not re.match(r'^.{7}$', numeroprontuario):
            flash ("Número de prontuário inválido. Deve conter exatamente 7 caracteres.", "danger")
            
        senha_hash = generate_password_hash(senha, method='sha256')
        
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        try:
            cursor.execute('SELECT email FROM alunos WHERE email = ?', (email,))
            usuario_existente = cursor.fetchone()
            if usuario_existente:
                flash("Erro durante o cadastro: Este email já está cadastrado.", "danger")
                return render_template('cadastro.html')

            senha_hash = generate_password_hash(senha, method='sha256')
            cursor.execute('''
                        INSERT INTO alunos (nome, email, senha, curso, turma, semestre, unidade, numeroprontuario) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (nome, email, senha_hash, curso, turma, semestre, unidade, numeroprontuario))
            conexao.commit()        
            enviar_email(email, 'Cadastro realizado com sucesso!', f'''Olá {nome}!
Seu cadastro foi realizado com sucesso!
Seja bem vindo ao Sistema de Gerenciamento Universitário.
''')
    
            flash("Cadastro realizado com sucesso!", "success")
        except Exception as e:
                flash(f"Erro durante o cadastro: Número de Prontuário já existe.")
        finally:
                conexao.close()

    # Método GET
    return render_template('cadastro.html')
    


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']


        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT senha FROM alunos WHERE email = ?', (email,))
        senha_hash = cursor.fetchone()

        if senha_hash and check_password_hash(senha_hash[0], senha): #(Senha correta)
            session['usuario'] = email
            return redirect ('/inicio')
        else:
                flash("Credenciais inválidas. Tente novamente.", "danger")

    return render_template('login.html')

#-----REDEFINIR SENHA-----


@app.route('/codigoemail', methods=['POST'])
def codigo_email():    
    email = request.form.get('email')
    session['usuario'] = email
    codigo_verificacao = str(random.randint(100000, 999999))
    session['codigo'] = codigo_verificacao  
    
    enviar_email(email, 'Código de Verificação', f'''Olá!
Seu código de verificação é: {codigo_verificacao}
Acesse a página de verificação, insira seu código e redefina sua senha.
''')
    return render_template('redefinir_senha.html', codigo = codigo_verificacao, etapa='etapa2-form')

@app.route('/verificarcodigo', methods=['POST'])    
def verificarcodigo():
    codigoenviado = session.get('codigo')
    codigodigitado = request.form.get('codigo_usuario')
    if (codigoenviado == codigodigitado):
        return render_template('redefinir_senha.html', etapa='etapa3-form')    
    return render_template('redefinir_senha.html', etapa='etapa2-form')
   
@app.route('/redefinirsenha', methods=['GET','POST'])
def redefinirsenha():
    if request.method == 'POST':
        nova_senha = request.form['nova-senha']
        confirmar_senha = request.form['confirmar-senha']
        if (nova_senha ==  confirmar_senha):
            email_usuario = session.get('usuario')
            senha_hash = generate_password_hash(nova_senha, method='sha256')
            atualizar_senha_no_banco_de_dados(email_usuario, senha_hash)
            flash("Senha alterada com sucesso.", "success")
            return redirect('/login')
        flash("As senhas não coincidem", "danger")
        return render_template('redefinir_senha.html', etapa = 'etapa3-form')  
    
    return render_template('redefinir_senha.html', etapa = 'etapa1-form')  


#-----LOGADO-----

@app.route('/inicio')
def inicio():
    email = session.get('usuario')  
    if email:
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT nome, curso FROM alunos WHERE email = ?', (email,))
        usuario_info = cursor.fetchone()
        horarios = obter_disciplinas_do_banco_de_dados(email)
        conexao.close()
        nome_usuario, curso_usuario = usuario_info
        return render_template('inicio.html', nome=nome_usuario, curso=curso_usuario, email=email, horarios=horarios)
    else:
        #Usuário não logado
        return redirect('/login')


#-----PERFIL-----


@app.route('/perfil')
def perfil():
    email_usuario = session.get('usuario')  
    if email_usuario:
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT * FROM alunos WHERE email = ?', (email_usuario,))
        dados_usuario = cursor.fetchone()
        conexao.close()
        return render_template('perfil.html', usuario=dados_usuario)
    else:
        #Usuário não logado
        return redirect('/login')

@app.route('/perfil/atualizar', methods=['POST'])
def atualizar_perfil():
    email_usuario = session.get('usuario')
    if email_usuario:
        novo_nome = request.form.get('novoNome')
        novo_email = request.form.get('novoEmail')
        novo_curso = request.form.get('novoCurso')
        novo_semestre = request.form.get('novoSemestre')

        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('UPDATE alunos SET nome = ?, email = ?, curso = ?, semestre = ? WHERE email = ?',
                       (novo_nome, novo_email, novo_curso, novo_semestre, email_usuario))
        conexao.commit()
        conexao.close()

        flash('Perfil atualizado com sucesso!', 'success')
        return redirect(url_for('perfil'))
    else:
        #usuario não logado
        return redirect('/login')

@app.route('/perfil/atualizarsenha', methods=['POST'])
def alterar_senha():
    if request.method == 'POST':
        senha_atual = request.form['senha_atual']
        nova_senha = request.form['nova_senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if validar_senhas(senha_atual, nova_senha, confirmar_senha):
            email_usuario = session.get('usuario')
            if validar_senha_atual(email_usuario, senha_atual):
                nova_senha_hash = generate_password_hash(nova_senha, method='sha256')
                atualizar_senha_no_banco_de_dados(email_usuario, nova_senha_hash)
                flash("Senha alterada com sucesso.", "success")
                return redirect('/perfil')  
            else:
                flash("Senha atual incorreta. Tente novamente.", "danger")
        
        flash("As senhas não coincidem ou não atendem aos critérios.", "danger")

    return

#-----SENHAS-----

def validar_senhas(senha_atual, nova_senha, confirmar_senha):
    return senha_atual and nova_senha == confirmar_senha  

def validar_senha_atual(email, senha_atual):
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    cursor.execute('SELECT senha FROM alunos WHERE email = ?', (email,))
    senha_hash = cursor.fetchone()[0]
    conexao.close()
    
    return check_password_hash(senha_hash, senha_atual)

def atualizar_senha_no_banco_de_dados(email, nova_senha_hash):
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    cursor.execute('UPDATE alunos SET senha = ? WHERE email = ?', (nova_senha_hash, email))
    conexao.commit()
    conexao.close()


#DISCIPLINAS

def obter_disciplinas_do_banco_de_dados(email_aluno):
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT disciplina_id
        FROM aluno_disciplina
        WHERE aluno_id = ?
    """, (email_aluno,))
    disciplinas_ids = cursor.fetchall()

    # Use uma lista de compreensão para extrair os IDs das disciplinas
    disciplinas_ids = [row[0] for row in disciplinas_ids]
    
    # Consulta para obter informações sobre as disciplinas
    cursor.execute("""
        SELECT *
        FROM disciplinas
        WHERE sigla IN ({})
        ORDER BY
            CASE
                WHEN dia = 'Segunda-feira' THEN 1
                WHEN dia = 'Terça-feira' THEN 2
                WHEN dia = 'Quarta-feira' THEN 3
                WHEN dia = 'Quinta-feira' THEN 4
                WHEN dia = 'Sexta-feira' THEN 5
                WHEN dia = 'Sábado' THEN 6
                ELSE 8
            END, horario
    """.format(','.join(['?']*len(disciplinas_ids))), disciplinas_ids)

    dados_disciplinas = cursor.fetchall()

    conexao.close()

    return dados_disciplinas

@app.route('/disciplina')
def disciplina():
    email = session.get('usuario')
    if email:
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT nome, curso FROM alunos WHERE email = ?', (email,))
        usuario_info = cursor.fetchone()
        nome_usuario, curso_usuario = usuario_info
        disciplinas = obter_disciplinas_do_banco_de_dados(email)
        return render_template('disciplina.html',  nome=nome_usuario, curso=curso_usuario, email=email, disciplinas=disciplinas)
        

def verificar_registro_aluno_disciplina(email_aluno, codigo_disciplina):
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()

    cursor.execute('''
        SELECT * FROM aluno_disciplina
        WHERE aluno_id = ? AND disciplina_id = ?
    ''', (email_aluno, codigo_disciplina))
    resultado = cursor.fetchone()
    conexao.close()
        
    if resultado:
        print(f"O aluno com o email {email_aluno} já está registrado na disciplina com ID {codigo_disciplina}.")
    else:
        registrar_aluno_disciplina(email_aluno, codigo_disciplina)

def registrar_aluno_disciplina(email_aluno, codigo_disciplina):
    data_inscricao = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    cursor.execute('''
        INSERT INTO aluno_disciplina (aluno_id, disciplina_id, data_inscricao)
        VALUES (?, ?, ?)
    ''', (email_aluno, codigo_disciplina, data_inscricao))  
    conexao.commit()
    conexao.close()
    flash('Disciplina adicionada com sucesso.', 'success')
    return redirect('/disciplina')


@app.route('/disciplina/adicionar', methods=['GET', 'POST'])
def adicionar_disciplina():
    if 'usuario' not in session:
        return redirect('/login')

    if request.method == 'POST':
        nome_disciplina = request.form['nome']
        codigo_disciplina = request.form['codigo']
        professor = request.form['professor']
        dia_semana = request.form['dia']
        horario = request.form['horario']
        aulas_por_dia = int(request.form.get('opcao'))

        conexao = sqlite3.connect('usuarios.db')
        cursordisciplina = conexao.cursor()

        email_usuario = session['usuario']
        
        cursordisciplina.execute('SELECT sigla FROM disciplinas WHERE sigla = ? OR nome = ?', (codigo_disciplina, nome_disciplina))
        disciplina_existente = cursordisciplina.fetchone()
        if disciplina_existente:
            verificar_registro_aluno_disciplina(email_usuario, codigo_disciplina)
        else:
            cursor = conexao.cursor()
            cursor.execute('''
                INSERT INTO disciplinas (sigla, nome, professor, dia, horario, aulaspordia, total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (codigo_disciplina, nome_disciplina, professor, dia_semana, horario, aulas_por_dia, aulas_por_dia*19))
            conexao.commit()
            conexao.close()
            verificar_registro_aluno_disciplina(email_usuario, codigo_disciplina) 
        
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()
    email_usuario = session['usuario']
    cursor.execute('SELECT nome, curso FROM alunos WHERE email = ?', (email_usuario,))
    usuario_info = cursor.fetchone()
    nome_usuario, curso_usuario = usuario_info
    return render_template('adicionar_disciplina.html', email = email_usuario, nome = nome_usuario, curso = curso_usuario)  # Renderize a página de adição de disciplina


#-----PÁGINAS FUTURAS-----

@app.route('/relatorio')
def relatorio():
    email_usuario = session.get('usuario')  
    if email_usuario:
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT nome, curso FROM alunos WHERE email = ?', (email_usuario,))
        usuario_info = cursor.fetchone()
        nome_usuario, curso_usuario = usuario_info
        return render_template('relatorio.html', email = email_usuario, nome = nome_usuario, curso = curso_usuario)
    
    else:
        #Usuário não logado.
        return redirect('/login')

@app.route('/mensagens')
def mensagens():
    email_usuario = session.get('usuario')
    if email_usuario:
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT nome, curso FROM alunos WHERE email = ?', (email_usuario,))
        usuario_info = cursor.fetchone()
        nome_usuario, curso_usuario = usuario_info
        return render_template('mensagens.html', email = email_usuario, nome = nome_usuario, curso = curso_usuario)
    
    else:
        #Usuário não logado.
        return redirect('/login')


@app.route('/logout')
def logout():
    # Remova os dados da sessão que identificam o usuário como autenticado
    session.pop('usuario', None)
    # Crie uma resposta HTTP com cabeçalho de controle de cache
    response = make_response(redirect(url_for('login')))
    # Adicione o cabeçalho "no-store" para evitar o cache
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'  
    return response

        
        
#-----DEFAULT-----
        
if __name__ == '__main__':
    criar_tabela_alunos()
    criar_tabela_disciplinas()
    criar_tabela_aluno_disciplina()
    app.run(debug=True)