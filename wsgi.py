from wsgiref.simple_server import make_server


def application(environ, start_response):
    produtos = [{'Nome': 'Notebook', 'Preço': 4350.99}, 
                {'Nome': 'Mouse', 'Preço': 125.99}, 
                {'Nome': 'Teclado', 'Preço': 250.99}, 
                {'Nome': 'Monitor', 'Preço': 1200.99}
    ]

    linhas_html = '' 
    for produto in produtos:
        linhas_html += f'<li>{produto['Nome']} - R$ {produto['Preço']}</li>'

    start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])
    
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    html_final = html.replace('{{PRODUTOS}}', linhas_html)
    return [html_final.encode('utf-8')]

make_server('', 5000, application).serve_forever()