from flask import Flask, render_template_string, request, redirect, session, send_from_directory, abort
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_very_secret_key_here'
app.config['UPLOAD_FOLDER'] = 'archive'
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

VIEWABLE_TYPES = {
    'text': ['txt', 'log', 'csv', 'json', 'xml', 'html', 'htm', 'js', 'css', 'md'],
    'image': ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'],
    'pdf': ['pdf'],
    'audio': ['mp3', 'wav', 'ogg'],
    'video': ['mp4', 'webm', 'mov'],
    'code': ['py', 'java', 'cpp', 'c', 'h', 'php', 'sh']
}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Тайный Архив</title>
    <style>
        :root {
            --blood-red: #8b0000;
            --dark-red: #400000;
            --black: #0a0a0a;
            --gray: #1a1a1a;
        }
        body {
            background-color: var(--black);
            color: var(--blood-red);
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 0;
            background-image: 
                radial-gradient(circle at 25% 25%, #300000 0%, transparent 40%),
                radial-gradient(circle at 75% 75%, #300000 0%, transparent 40%),
                url('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><path d="M30,10 L70,10 L90,30 L90,70 L70,90 L30,90 L10,70 L10,30 Z" fill="none" stroke="%238b0000" stroke-width="0.5"/></svg>');
            background-size: cover, cover, 100px 100px;
            min-height: 100vh;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            background-color: rgba(10, 10, 10, 0.9);
            border: 1px solid var(--blood-red);
            box-shadow: 0 0 30px rgba(139, 0, 0, 0.5);
            position: relative;
            overflow: hidden;
        }
        .container::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--blood-red), transparent);
            animation: scanline 8s linear infinite;
        }
        @keyframes scanline {
            0% { top: 0; }
            100% { top: 100%; }
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 2rem;
        }
        h1 {
            text-align: left;
            font-size: 2.5rem;
            text-shadow: 0 0 10px var(--blood-red);
            letter-spacing: 3px;
            position: relative;
            margin: 0;
        }
        h1::after {
            content: "";
            display: block;
            width: 100%;
            height: 2px;
            background: var(--blood-red);
            margin: 0.5rem 0;
            box-shadow: 0 0 10px var(--blood-red);
        }
        .logout-btn {
            background: transparent;
            border: 1px solid var(--blood-red);
            color: var(--blood-red);
            padding: 0.5rem 1rem;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Courier New', monospace;
            font-size: 1rem;
            text-transform: uppercase;
        }
        .logout-btn:hover {
            background: var(--dark-red);
            color: white;
            box-shadow: 0 0 10px var(--blood-red);
        }
        .login-form, .archive-container {
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            animation: fadeIn 1s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        input, button, select {
            padding: 0.8rem;
            font-size: 1rem;
            background-color: var(--gray);
            color: var(--blood-red);
            border: 1px solid var(--blood-red);
            border-radius: 0;
            transition: all 0.3s;
        }
        input:focus, button:hover, select:focus {
            outline: none;
            box-shadow: 0 0 10px var(--blood-red);
            background-color: var(--dark-red);
            color: white;
        }
        button {
            cursor: pointer;
            position: relative;
            overflow: hidden;
        }
        button::after {
            content: "";
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(
                to bottom right,
                transparent 45%,
                rgba(139, 0, 0, 0.3) 50%,
                transparent 55%
            );
            transform: rotate(30deg);
            animation: shine 3s infinite;
        }
        @keyframes shine {
            0% { transform: translateX(-100%) rotate(30deg); }
            100% { transform: translateX(100%) rotate(30deg); }
        }
        .file-list {
            list-style-type: none;
            padding: 0;
            border: 1px solid var(--blood-red);
        }
        .file-item {
            padding: 1rem;
            border-bottom: 1px solid var(--dark-red);
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.3s;
        }
        .file-item:hover {
            background-color: rgba(139, 0, 0, 0.1);
        }
        .file-item:last-child {
            border-bottom: none;
        }
        .file-preview {
            margin-top: 2rem;
            padding: 1.5rem;
            background-color: var(--gray);
            border: 1px solid var(--blood-red);
            min-height: 400px;
            position: relative;
        }
        .file-preview-content {
            max-width: 100%;
            max-height: 500px;
            margin: 0 auto;
            display: block;
        }
        .text-preview {
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            overflow-x: auto;
        }
        .error {
            color: #ff3333;
            text-align: center;
            text-shadow: 0 0 5px #ff0000;
            padding: 1rem;
            border: 1px solid #ff0000;
            background-color: rgba(255, 0, 0, 0.1);
        }
        .status {
            color: #00aa00;
            text-align: center;
            padding: 1rem;
        }
        .delete-btn {
            color: #ff3333;
            cursor: pointer;
            font-weight: bold;
            padding: 0.3rem 0.6rem;
        }
        .delete-btn:hover {
            text-shadow: 0 0 5px #ff0000;
        }
        .viewer-controls {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }
        .glitch {
            animation: glitch 1s linear infinite;
        }
        @keyframes glitch {
            0% { text-shadow: 2px 0 red, -2px 0 blue; }
            25% { text-shadow: -2px 0 red, 2px 0 blue; }
            50% { text-shadow: 2px 0 red, -2px 0 blue; }
            75% { text-shadow: -2px 0 red, 2px 0 blue; }
            100% { text-shadow: 2px 0 red, -2px 0 blue; }
        }
        .viewer-container {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: rgba(0, 0, 0, 0.95);
            z-index: 1000;
            display: flex;
            flex-direction: column;
        }
        .viewer-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            background-color: var(--black);
            border-bottom: 1px solid var(--blood-red);
        }
        .viewer-content {
            flex-grow: 1;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            overflow: auto;
        }
        .viewer-actions {
            display: flex;
            gap: 10px;
            padding: 15px;
            background-color: var(--black);
            border-top: 1px solid var(--blood-red);
            justify-content: center;
        }
        .viewer-btn {
            padding: 10px 20px;
            background-color: var(--dark-red);
            color: white;
            border: none;
            cursor: pointer;
            font-family: 'Courier New', monospace;
            font-size: 1rem;
            transition: all 0.3s;
        }
        .viewer-btn:hover {
            background-color: var(--blood-red);
            box-shadow: 0 0 10px var(--blood-red);
        }
        .text-viewer {
            width: 90%;
            height: 80vh;
            background-color: var(--gray);
            color: #e0e0e0;
            padding: 20px;
            font-family: 'Courier New', monospace;
            white-space: pre-wrap;
            overflow: auto;
            border: 1px solid var(--blood-red);
        }
        .media-viewer {
            max-width: 90%;
            max-height: 80vh;
            box-shadow: 0 0 20px rgba(139, 0, 0, 0.5);
        }
        .pdf-viewer {
            width: 100%;
            height: 100%;
            border: none;
        }
        .file-icon {
            margin-right: 10px;
            width: 24px;
            text-align: center;
        }
        .unsupported-view {
            color: var(--blood-red);
            font-size: 1.2rem;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1>Т<span class="glitch">А</span>ЙНЫЙ АРХИВ</h1>
            </div>
            {% if session.logged_in %}
            <button class="logout-btn" onclick="window.location.href='/logout'">ВЫЙТИ</button>
            {% endif %}
        </div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        {% if status %}
        <div class="status">{{ status }}</div>
        {% endif %}

        {% if not session.logged_in %}
        <form class="login-form" method="POST" action="/login">
            <input type="text" name="username" placeholder="Имя хранителя" required>
            <input type="password" name="password" placeholder="Печать доступа" required>
            <button type="submit">ВОЙТИ В АРХИВ</button>
        </form>
        {% else %}
        <div class="archive-container">
            <div>
                <form method="POST" action="/upload" enctype="multipart/form-data">
                    <div style="display: flex; gap: 1rem;">
                        <input type="file" name="file" required style="flex-grow: 1;">
                        <button type="submit">ЗАГРУЗИТЬ</button>
                    </div>
                </form>
            </div>
            
            <ul class="file-list">
                {% for file in files %}
                <li class="file-item">
                    <span onclick="openViewer('{{ file }}')" style="cursor: pointer; flex-grow: 1;">
                        <span class="file-icon">{{ get_file_icon(file) }}</span>
                        {{ file }}
                    </span>
                    <span class="delete-btn" onclick="if(confirm('Уничтожить {{ file }}?')) window.location.href='/delete/{{ file }}'">
                        УНИЧТОЖИТЬ
                    </span>
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>

    <div id="viewerModal" class="viewer-container" style="display: none;">
        <div class="viewer-header">
            <h2 id="viewer-filename" style="margin: 0; color: var(--blood-red);"></h2>
            <button onclick="closeViewer()" class="viewer-btn">ЗАКРЫТЬ (ESC)</button>
        </div>
        <div class="viewer-content" id="viewer-content">
            <div style="color: var(--blood-red);">Загрузка...</div>
        </div>
        <div class="viewer-actions">
            <button onclick="downloadCurrentFile()" class="viewer-btn">СОХРАНИТЬ НА ДИСК</button>
            <button onclick="closeViewer()" class="viewer-btn">ЗАКРЫТЬ (ESC)</button>
        </div>
    </div>

    <script>
        let currentFile = null;
        
        function get_file_icon(filename) {
            const ext = filename.split('.').pop().toLowerCase();
            if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'].includes(ext)) return '🖼️';
            if (['pdf'].includes(ext)) return '📄';
            if (['mp3', 'wav', 'ogg'].includes(ext)) return '🎵';
            if (['mp4', 'webm', 'mov'].includes(ext)) return '🎬';
            if (['txt', 'log', 'csv', 'json', 'xml'].includes(ext)) return '📝';
            if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) return '🗄️';
            return '📁';
        }
        
        function openViewer(filename) {
            currentFile = filename;
            document.getElementById('viewer-filename').textContent = filename;
            document.getElementById('viewerModal').style.display = 'flex';
            
            const ext = filename.split('.').pop().toLowerCase();
            const viewerContent = document.getElementById('viewer-content');
            viewerContent.innerHTML = '<div style="color: var(--blood-red);">Загрузка...</div>';
            
            if (['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'].includes(ext)) {
                viewerContent.innerHTML = `<img src="/file/${filename}" class="media-viewer" onerror="showUnsupported()">`;
            } 
            else if (['mp3', 'wav', 'ogg'].includes(ext)) {
                viewerContent.innerHTML = `
                    <audio controls autoplay class="media-viewer">
                        <source src="/file/${filename}" type="audio/${ext === 'mp3' ? 'mpeg' : ext}">
                    </audio>
                `;
            }
            else if (['mp4', 'webm', 'mov'].includes(ext)) {
                viewerContent.innerHTML = `
                    <video controls autoplay class="media-viewer">
                        <source src="/file/${filename}" type="video/${ext}">
                    </video>
                `;
            }
            else if (ext === 'pdf') {
                viewerContent.innerHTML = `
                    <object data="/file/${filename}" 
                            type="application/pdf" 
                            class="pdf-viewer">
                        <p>Ваш браузер не поддерживает просмотр PDF. 
                           <a href="/file/${filename}">Скачайте файл</a>.</p>
                    </object>
                `;
            }
            else if (['txt', 'log', 'csv', 'json', 'xml', 'html', 'htm', 'js', 'css', 'md', 'py', 'java', 'cpp', 'c', 'h', 'php', 'sh'].includes(ext)) {
                fetch(`/file/${filename}?preview=true`)
                    .then(response => {
                        if (!response.ok) throw new Error('Ошибка загрузки');
                        return response.text();
                    })
                    .then(text => {
                        viewerContent.innerHTML = `<div class="text-viewer">${escapeHtml(text)}</div>`;
                    })
                    .catch(error => {
                        viewerContent.innerHTML = `
                            <div class="unsupported-view">
                                Не удалось загрузить файл для просмотра<br><br>
                                <button onclick="downloadCurrentFile()" class="viewer-btn">СОХРАНИТЬ ФАЙЛ</button>
                            </div>
                        `;
                    });
            }
            else {
                viewerContent.innerHTML = `
                    <div class="unsupported-view">
                        Просмотр этого типа файла не поддерживается<br><br>
                        <button onclick="downloadCurrentFile()" class="viewer-btn">СОХРАНИТЬ ФАЙЛ</button>
                    </div>
                `;
            }
            
            document.addEventListener('keydown', handleKeyPress);
        }
        
        function closeViewer() {
            document.getElementById('viewerModal').style.display = 'none';
            document.removeEventListener('keydown', handleKeyPress);
            
            const mediaElements = document.querySelectorAll('video, audio');
            mediaElements.forEach(el => {
                el.pause();
                el.currentTime = 0;
            });
        }
        
        function downloadCurrentFile() {
            if (currentFile) {
                window.open(`/download/${currentFile}`, '_blank');
            }
        }
        
        function handleKeyPress(e) {
            if (e.key === 'Escape') {
                closeViewer();
            }
        }
        
        function showUnsupported() {
            const viewerContent = document.getElementById('viewer-content');
            viewerContent.innerHTML = `
                <div class="unsupported-view">
                    Не удалось загрузить изображение<br><br>
                    <button onclick="downloadCurrentFile()" class="viewer-btn">СОХРАНИТЬ ФАЙЛ</button>
                </div>
            `;
        }
        
        function escapeHtml(unsafe) {
            return unsafe
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }
    </script>
</body>
</html>
"""

def get_file_icon(filename):
    ext = filename.split('.')[-1].lower()
    if ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg']: return '🖼️'
    if ext == 'pdf': return '📄'
    if ext in ['mp3', 'wav', 'ogg']: return '🎵'
    if ext in ['mp4', 'webm', 'mov']: return '🎬'
    if ext in ['txt', 'log', 'csv', 'json', 'xml']: return '📝'
    if ext in ['zip', 'rar', '7z', 'tar', 'gz']: return '🗄️'
    return '📁'

@app.route('/')
def index():
    if not session.get('logged_in'):
        return render_template_string(HTML_TEMPLATE, 
                                  files=[],
                                  error=request.args.get('error'),
                                  get_file_icon=get_file_icon)
    
    try:
        files = sorted(os.listdir(app.config['UPLOAD_FOLDER']))
    except:
        files = []
    
    return render_template_string(HTML_TEMPLATE,
                               files=files,
                               status=request.args.get('status'),
                               error=request.args.get('error'),
                               get_file_icon=get_file_icon)

@app.route('/login', methods=['POST'])
def login():
    if request.form['username'] == 'admin' and request.form['password'] == '123':
        session['logged_in'] = True
        return redirect('/')
    return redirect('/?error=Неверные+учетные+данные')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload():
    if not session.get('logged_in'):
        return redirect('/')
    
    if 'file' not in request.files:
        return redirect('/?error=Файл+не+выбран')
    
    file = request.files['file']
    if file.filename == '':
        return redirect('/?error=Файл+не+выбран')
    
    try:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return redirect('/?status=Файл+успешно+загружен')
    except Exception as e:
        return redirect(f'/?error=Ошибка+загрузки: {str(e)}')

@app.route('/file/<filename>')
def serve_file(filename):
    if not session.get('logged_in'):
        abort(403)
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.isfile(filepath):
        abort(404)

    # Для PDF файлов
    if filename.lower().endswith('.pdf'):
        response = send_from_directory(app.config['UPLOAD_FOLDER'], filename)
        # Устанавливаем правильные заголовки
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'inline; filename=' + filename
        return response
    
    # Для текстовых файлов
    if request.args.get('preview'):
        ext = filename.split('.')[-1].lower()
        if ext in VIEWABLE_TYPES['text'] + VIEWABLE_TYPES['code']:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(500000)
                return content
            except:
                return "Не удалось прочитать файл"
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/download/<filename>')
def download(filename):
    if not session.get('logged_in'):
        abort(403)
    
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/delete/<filename>')
def delete(filename):
    if not session.get('logged_in'):
        return redirect('/')
    
    try:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.isfile(filepath):
            os.remove(filepath)
            return redirect('/?status=Файл+уничтожен')
        return redirect('/?error=Файл+не+найден')
    except Exception as e:
        return redirect(f'/?error=Ошибка+удаления: {str(e)}')

if __name__ == '__main__':
    app.run(debug=True)
