import re
import sqlite3

from flask import Flask, render_template, request, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "chave_secreta"

def criar_tabela_alunos():
    conexao = sqlite3.connect('usuarios.db')
    cursor = conexao.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alunos (
            turma TEXT PRIMARY KEY,
            nome TEXT,
            email TEXT,
            senha TEXT,
            curso TEXT,
            semestre INTEGER,
            unidade TEXT,
            numeroprontuario TEXT
        )
    ''')

    conexao.commit()
    conexao.close()


@app.route('/')
def index():
    return render_template('cadastro.html')


@app.route('/cadastro', methods=['GET','POST'])
def cadastrar():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        nome = request.form['nome']
        curso = request.form['curso']
        
        # Converta o valor do semestre para um número inteiro
        semestre = int(request.form['semestre'])
        
        # Calcule a turma como a junção de curso e semestre
        turma = curso + str(semestre)

        unidade = request.form['unidade']
         # Obtenha o número de prontuário do formulário
        numeroprontuario = request.form['numeroprontuario']

        # Valide o número de prontuário (deve conter exatamente 7 dígitos)
        if not re.match(r'^\d{7}$', numeroprontuario):
            return "Número de prontuário inválido. Deve conter exatamente 7 dígitos."

        senha_hash = generate_password_hash(senha, method='sha256')

        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        
        try:
            # Verifique se o email já existe no banco de dados
            cursor.execute('SELECT email FROM alunos WHERE email = ?', (email,))
            usuario_existente = cursor.fetchone()

            if usuario_existente:
                return "Este email já está cadastrado. Por favor, use outro email."

            senha_hash = generate_password_hash(senha, method='sha256')

            cursor.execute('''
                        INSERT INTO alunos (nome, email, senha, curso, turma, semestre, unidade, numeroprontuario) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (nome, email, senha_hash, curso, turma, semestre, unidade, numeroprontuario))

            conexao.commit()
            return "Cadastro realizado com sucesso!"
        
        except Exception as e:
                return f"Erro durante o cadastro: {str(e)}"
        finally:
                conexao.close()

    # Se o método for GET, apenas renderize a página de cadastro
    return render_template('cadastro.html')
    


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']

        # Consultar o banco de dados para obter o hash da senha
        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()
        cursor.execute('SELECT senha FROM alunos WHERE email = ?', (email,))
        senha_hash = cursor.fetchone()

        if senha_hash and check_password_hash(senha_hash[0], senha):
            # Senha correta, autenticar o usuário
            session['usuario'] = email
            return render_template('opcoes.html')
        else:
            # Credenciais inválidas, mostrar mensagem de erro
            return "Credenciais inválidas. Tente novamente."

        # Outras rotas e configurações do aplicativo
        # Processar o formulário de login
        email = request.form['email']
        senha = request.form['senha']

        conexao = sqlite3.connect('usuarios.db')
        cursor = conexao.cursor()

        cursor.execute('SELECT senha FROM alunos WHERE email = ?', (email,))
        senha_hash = cursor.fetchone()

        conexao.close()

 
        if usuario and check_password_hash(usuario[2], senha):
        # Credenciais válidas
            session['usuario'] = senha_hash[1]
            return render_template('opcoes.html')
        else:
        # Credenciais inválidas
            return "Credenciais inválidas"

    # Se o método for GET, apenas renderize a página de login
    return render_template('login.html')
   

if __name__ == '__main__':
    criar_tabela_alunos()
    app.run(debug=True)