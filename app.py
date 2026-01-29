"""
FastAPI приложение для просмотра и тестирования парсера УПД
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import tempfile
from pathlib import Path
import json

from upd_parser import UPDParser, parse_all_upd_files

app = FastAPI(title="УПД Parser Viewer", version="1.0")

# CORS для локального использования
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Главная страница с интерфейсом"""
    return HTML_CONTENT


@app.post("/api/parse-file")
async def parse_file(file: UploadFile = File(...)):
    """Парсит загруженный XML файл УПД"""
    try:
        # Сохранить временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        # Парсить
        parser = UPDParser(tmp_path)
        doc = parser.parse()
        
        # Очистить временный файл
        Path(tmp_path).unlink()
        
        # Вернуть результат
        return {
            "status": doc.parsing_status,
            "document_number": doc.document_number,
            "document_date": doc.document_date,
            "supplier_name": doc.supplier_name,
            "supplier_inn": doc.supplier_inn,
            "item_count": doc.item_count,
            "structure_type": doc.structure_type,
            "xml_version": doc.xml_version,
            "generator": doc.generator,
            "total_without_vat": round(doc.total_without_vat, 2),
            "total_vat": round(doc.total_vat, 2),
            "total_with_vat": round(doc.total_with_vat, 2),
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": round(item.unit_price, 2),
                    "sum_without_vat": round(item.sum_without_vat, 2),
                    "vat_rate": item.vat_rate,
                    "vat_amount": round(item.vat_amount, 2),
                }
                for item in doc.items
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/parse-directory")
async def parse_directory():
    """Парсит все XML файлы в директории приложения"""
    try:
        directory = str(Path(__file__).parent)
        results = parse_all_upd_files(directory)
        
        response_data = []
        for filename, doc in results:
            response_data.append({
                "filename": filename,
                "status": doc.parsing_status,
                "document_number": doc.document_number,
                "document_date": doc.document_date,
                "supplier_name": doc.supplier_name,
                "supplier_inn": doc.supplier_inn,
                "item_count": doc.item_count,
                "xml_version": doc.xml_version,
                "generator": doc.generator,
                "total_with_vat": round(doc.total_with_vat, 2),
                "total_vat": round(doc.total_vat, 2),
                "parsing_issues_count": len(doc.parsing_issues) if doc.parsing_issues else 0,
                "parsing_status_detailed": doc.parsing_status,
            })
        
        # Статистика
        total_files = len(response_data)
        success_count = sum(1 for r in response_data if "SUCCESS" in r["status"])
        error_count = total_files - success_count
        
        # Считаем файлы с проблемами
        files_with_issues = sum(1 for r in response_data if r["parsing_issues_count"] > 0)
        
        return {
            "total_files": total_files,
            "successful": success_count,
            "failed": error_count,
            "files_with_issues": files_with_issues,
            "documents": response_data
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{error_trace}")


@app.get("/api/document-details/{filename}")
async def get_document_details(filename: str):
    """Получить детали конкретного документа с товарами"""
    try:
        directory = str(Path(__file__).parent)
        file_path = Path(directory) / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        parser = UPDParser(str(file_path))
        doc = parser.parse()
        
        return {
            "filename": filename,
            "status": doc.parsing_status,
            "document_number": doc.document_number,
            "document_date": doc.document_date,
            "supplier_name": doc.supplier_name,
            "supplier_inn": doc.supplier_inn,
            "xml_version": doc.xml_version,
            "generator": doc.generator,
            "total_without_vat": round(doc.total_without_vat, 2),
            "total_vat": round(doc.total_vat, 2),
            "total_with_vat": round(doc.total_with_vat, 2),
            "parsing_issues": doc.parsing_issues if doc.parsing_issues else [],
            "items": [
                {
                    "product_name": item.product_name,
                    "quantity": item.quantity,
                    "unit": item.unit,
                    "unit_price": round(item.unit_price, 2),
                    "sum_without_vat": round(item.sum_without_vat, 2),
                    "vat_rate": item.vat_rate,
                    "vat_amount": round(item.vat_amount, 2),
                    "sum_with_vat": round(item.sum_without_vat + item.vat_amount, 2),
                }
                for item in doc.items
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR: {error_trace}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}\n{error_trace}")


HTML_CONTENT = r"""
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>УПД Parser - Тестер парсера</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 12px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .controls {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-top: 30px;
        }
        
        .control-block {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }
        
        .control-block h3 {
            color: #333;
            margin-bottom: 15px;
            font-size: 16px;
        }
        
        input[type="file"],
        button {
            width: 100%;
            padding: 12px 20px;
            border: none;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        input[type="file"] {
            background: white;
            border: 2px dashed #667eea;
            color: #333;
        }
        
        button {
            background: #667eea;
            color: white;
            margin-top: 10px;
        }
        
        button:hover {
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .stat-card .number {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-card .label {
            color: #666;
            font-size: 12px;
            margin-top: 5px;
            text-transform: uppercase;
        }
        
        .content {
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        
        .tabs {
            display: flex;
            border-bottom: 2px solid #e9ecef;
        }
        
        .tab-button {
            flex: 1;
            padding: 15px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        
        .tab-button.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-button:hover {
            background: #f8f9fa;
        }
        
        .tab-content {
            display: none;
            padding: 20px;
        }
        
        .tab-content.active {
            display: block;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
        }
        
        th {
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e9ecef;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            color: #555;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .status-success {
            color: #22c55e;
            font-weight: 600;
        }
        
        .status-warning {
            color: #f59e0b;
            font-weight: 600;
        }
        
        .status-error {
            color: #ef4444;
            font-weight: 600;
        }
        
        .detail-table {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
        }
        
        .detail-table h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .detail-table table {
            width: 100%;
            background: white;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 600;
            background: #f0f0f0;
            color: #333;
        }
        
        .badge.type1 {
            background: #e3f2fd;
            color: #1976d2;
        }
        
        .badge.type23 {
            background: #f3e5f5;
            color: #7b1fa2;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #666;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
        }
        
        .success-message {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 6px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🧪 УПД Parser - Тестер</h1>
            <p class="subtitle">Проверка работоспособности парсера на реальных файлах</p>
            
            <div class="controls">
                <div class="control-block">
                    <h3>📁 Загрузить файл</h3>
                    <input type="file" id="fileInput" accept=".xml" />
                    <button onclick="parseFile()">Парсить файл</button>
                </div>
                
                <div class="control-block">
                    <h3>📂 Парсить всю директорию</h3>
                    <button onclick="parseDirectory()" style="margin-top: 0;">Загрузить все файлы</button>
                    <p style="font-size: 12px; color: #666; margin-top: 10px;">
                        Парсит все .xml файлы из c:\Users\milena\Desktop\new 2
                    </p>
                </div>
            </div>
        </header>
        
        <div class="content">
            <div class="tabs">
                <button class="tab-button active" onclick="switchTab('directory')">📊 Все файлы (15)</button>
                <button class="tab-button" onclick="switchTab('file')">🔍 Один файл</button>
            </div>
            
            <div id="directory" class="tab-content active">
                <div id="directoryResults"></div>
            </div>
            
            <div id="file" class="tab-content">
                <div id="fileResults"></div>
            </div>
        </div>
    </div>
    
    <script>
        function switchTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-button').forEach(btn => {
                btn.classList.remove('active');
            });
            
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        async function parseFile() {
            const fileInput = document.getElementById('fileInput');
            if (!fileInput.files.length) {
                alert('Выберите файл');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', fileInput.files[0]);
            
            const resultsDiv = document.getElementById('fileResults');
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Парсинг файла...</div>';
            
            try {
                const response = await fetch('/api/parse-file', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) throw new Error('Ошибка парсинга');
                
                const data = await response.json();
                displayFileResults(data);
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error-message">❌ Ошибка: ${error.message}</div>`;
            }
        }
        
        async function parseDirectory() {
            const resultsDiv = document.getElementById('directoryResults');
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Парсинг всех файлов в директории...</div>';
            
            try {
                const response = await fetch('/api/parse-directory');
                if (!response.ok) throw new Error('Ошибка парсинга');
                
                const data = await response.json();
                displayDirectoryResults(data);
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error-message">❌ Ошибка: ${error.message}</div>`;
            }
        }
        
        function displayDirectoryResults(data) {
            const resultsDiv = document.getElementById('directoryResults');
            
            let html = `
                <div class="results">
                    <div class="stat-card">
                        <div class="number">${data.total_files}</div>
                        <div class="label">Всего файлов</div>
                    </div>
                    <div class="stat-card">
                        <div class="number" style="color: #22c55e;">${data.successful}</div>
                        <div class="label">Успешно</div>
                    </div>
                    <div class="stat-card">
                        <div class="number" style="color: #ef4444;">${data.failed}</div>
                        <div class="label">Ошибок</div>
                    </div>
                    <div class="stat-card">
                        <div class="number" style="color: #f59e0b;">${data.files_with_issues || 0}</div>
                        <div class="label">С проблемами</div>
                    </div>
                </div>
                
                <div class="detail-table">
                    <h3>📋 Результаты парсинга</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Файл</th>
                                <th>Статус</th>
                                <th>Номер УПД</th>
                                <th>Дата</th>
                                <th>Поставщик</th>
                                <th>Товаров</th>
                                <th>Тип</th>
                                <th>Версия</th>
                                <th>Генератор</th>
                                <th>Проблемы</th>
                                <th>Итого</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            data.documents.forEach(doc => {
                const statusClass = doc.status.includes('SUCCESS') ? 'status-success' : 'status-error';
                const issuesCount = doc.parsing_issues_count || 0;
                const issuesClass = issuesCount === 0 ? 'status-success' : 'status-warning';
                const issuesText = issuesCount === 0 ? '✓' : `⚠️ ${issuesCount}`;
                
                html += `
                    <tr onclick="showDocumentDetails('${doc.filename}')" style="cursor: pointer; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#f0f0f0'" onmouseout="this.style.backgroundColor=''">
                        <td><strong>${doc.filename.substring(0, 50)}</strong></td>
                        <td><span class="${statusClass}">${doc.status}</span></td>
                        <td>${doc.document_number}</td>
                        <td>${doc.document_date}</td>
                        <td>${doc.supplier_name.substring(0, 30)}</td>
                        <td><strong>${doc.item_count}</strong></td>
                        <td>${doc.xml_version}</td>
                        <td>${doc.generator}</td>
                        <td><span class="${issuesClass}" style="padding: 4px 8px; border-radius: 4px; font-weight: bold;">${issuesText}</span></td>
                        <td><strong>${doc.total_with_vat.toLocaleString('ru-RU')} ₽</strong></td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
            
            resultsDiv.innerHTML = html;
        }
        
        function displayFileResults(data) {
            const resultsDiv = document.getElementById('fileResults');
            
            if (data.status !== 'SUCCESS') {
                resultsDiv.innerHTML = `<div class="error-message">❌ ${data.status}</div>`;
                return;
            }
            
            let html = `
                <div class="detail-table">
                    <h3>📄 Информация о документе</h3>
                    <table>
                        <tr><td><strong>Номер УПД</strong></td><td>${data.document_number}</td></tr>
                        <tr><td><strong>Дата</strong></td><td>${data.document_date}</td></tr>
                        <tr><td><strong>Поставщик</strong></td><td>${data.supplier_name}</td></tr>
                        <tr><td><strong>ИНН</strong></td><td>${data.supplier_inn}</td></tr>
                        <tr><td><strong>Версия XML</strong></td><td>${data.xml_version}</td></tr>
                        <tr><td><strong>Генератор</strong></td><td>${data.generator}</td></tr>
                    </table>
                </div>
                
                <div class="detail-table">
                    <h3>💰 Финансовые данные</h3>
                    <table>
                        <tr><td><strong>Товаров в документе</strong></td><td>${data.item_count}</td></tr>
                        <tr><td><strong>Сумма без НДС</strong></td><td>${data.total_without_vat.toLocaleString('ru-RU')} ₽</td></tr>
                        <tr><td><strong>Сумма НДС</strong></td><td>${data.total_vat.toLocaleString('ru-RU')} ₽</td></tr>
                        <tr><td><strong>ИТОГО</strong></td><td><strong style="color: #667eea; font-size: 16px;">${data.total_with_vat.toLocaleString('ru-RU')} ₽</strong></td></tr>
                    </table>
                </div>
                
                <div class="detail-table">
                    <h3>📦 Товарные позиции (${data.items.length})</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Название товара</th>
                                <th>Кол-во</th>
                                <th>Ед.</th>
                                <th>Цена</th>
                                <th>Сумма</th>
                                <th>НДС %</th>
                                <th>НДС сумма</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            data.items.forEach(item => {
                html += `
                    <tr>
                        <td>${item.product_name}</td>
                        <td>${item.quantity.toLocaleString('ru-RU')}</td>
                        <td>${item.unit}</td>
                        <td>${item.unit_price.toLocaleString('ru-RU')} ₽</td>
                        <td><strong>${item.sum_without_vat.toLocaleString('ru-RU')} ₽</strong></td>
                        <td>${item.vat_rate}%</td>
                        <td>${item.vat_amount.toLocaleString('ru-RU')} ₽</td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
            
            resultsDiv.innerHTML = html;
        }
        
        async function showDocumentDetails(filename) {
            const resultsDiv = document.getElementById('directoryResults');
            resultsDiv.innerHTML = '<div class="loading"><div class="spinner"></div>Загрузка деталей документа...</div>';
            
            try {
                const response = await fetch(`/api/document-details/${filename}`);
                if (!response.ok) throw new Error('Ошибка загрузки');
                
                const data = await response.json();
                displayDocumentDetails(data);
            } catch (error) {
                resultsDiv.innerHTML = `<div class="error-message">❌ Ошибка: ${error.message}</div>`;
            }
        }
        
        function displayDocumentDetails(data) {
            const resultsDiv = document.getElementById('directoryResults');
            
            let html = `
                <div class="detail-table">
                    <h3>📄 Информация о документе</h3>
                    <table>
                        <tr><td><strong>Файл</strong></td><td>${data.filename}</td></tr>
                        <tr><td><strong>Номер УПД</strong></td><td>${data.document_number}</td></tr>
                        <tr><td><strong>Дата</strong></td><td>${data.document_date}</td></tr>
                        <tr><td><strong>Поставщик</strong></td><td>${data.supplier_name}</td></tr>
                        <tr><td><strong>ИНН</strong></td><td>${data.supplier_inn}</td></tr>
                        <tr><td><strong>Версия XML</strong></td><td>${data.xml_version}</td></tr>
                        <tr><td><strong>Генератор</strong></td><td>${data.generator}</td></tr>
                    </table>
                </div>
                
                <div class="detail-table">
                    <h3>💰 Финансовые итоги</h3>
                    <table>
                        <tr><td><strong>Сумма без НДС</strong></td><td><strong>${data.total_without_vat.toLocaleString('ru-RU')} ₽</strong></td></tr>
                        <tr><td><strong>НДС</strong></td><td><strong>${data.total_vat.toLocaleString('ru-RU')} ₽</strong></td></tr>
                        <tr><td><strong>Итого с НДС</strong></td><td><strong style="color: #2563eb; font-size: 1.1em;">${data.total_with_vat.toLocaleString('ru-RU')} ₽</strong></td></tr>
                    </table>
                </div>
            `;
            
            // Показываем parsing_issues если они есть
            if (data.parsing_issues && data.parsing_issues.length > 0) {
                html += `
                    <div class="detail-table" style="border-left: 4px solid #f59e0b;">
                        <h3>⚠️ Проблемы при парсинге (${data.parsing_issues.length})</h3>
                        <table>
                            <thead>
                                <tr>
                                    <th>Уровень</th>
                                    <th>Элемент</th>
                                    <th>Описание проблемы</th>
                                    <th>Генератор</th>
                                </tr>
                            </thead>
                            <tbody>
                `;
                
                data.parsing_issues.forEach(issue => {
                    let severityColor = '#10b981';  // green for info
                    if (issue.severity === 'warning') severityColor = '#f59e0b';  // orange
                    if (issue.severity === 'error') severityColor = '#ef4444';    // red
                    
                    html += `
                        <tr>
                            <td><span style="background-color: ${severityColor}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em;">${issue.severity.toUpperCase()}</span></td>
                            <td><code>${issue.element}</code></td>
                            <td>${issue.message}</td>
                            <td>${issue.generator || '-'}</td>
                        </tr>
                    `;
                });
                
                html += `
                            </tbody>
                        </table>
                    </div>
                `;
            }
            
            html += `
                <div class="detail-table">
                    <h3>📦 Товарные позиции (${data.items.length})</h3>
                    <table>
                        <thead>
                            <tr>
                                <th>Товар</th>
                                <th>Кол-во</th>
                                <th>Ед.</th>
                                <th>Цена</th>
                                <th>Сумма</th>
                                <th>НДС %</th>
                                <th>Сумма НДС</th>
                                <th>Итого</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            data.items.forEach((item, idx) => {
                html += `
                    <tr>
                        <td><strong>${item.product_name}</strong></td>
                        <td style="text-align: center;">${item.quantity}</td>
                        <td>${item.unit}</td>
                        <td>${item.unit_price.toLocaleString('ru-RU')} ₽</td>
                        <td>${item.sum_without_vat.toLocaleString('ru-RU')} ₽</td>
                        <td style="text-align: center;">${item.vat_rate}%</td>
                        <td>${item.vat_amount.toLocaleString('ru-RU')} ₽</td>
                        <td><strong>${item.sum_with_vat.toLocaleString('ru-RU')} ₽</strong></td>
                    </tr>
                `;
            });
            
            html += `
                        </tbody>
                    </table>
                </div>
                
                <button onclick="parseDirectory()" style="margin-top: 20px; padding: 10px 20px; background-color: #2563eb; color: white; border: none; border-radius: 5px; cursor: pointer; font-size: 1em;">← Вернуться к списку</button>
            `;
            
            resultsDiv.innerHTML = html;
        }
        
        // Автоматически загрузить данные при загрузке страницы
        window.addEventListener('load', () => {
            parseDirectory();
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='127.0.0.1', port=8000)
