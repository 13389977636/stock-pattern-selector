#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的文件上传服务器 - 用于接收用户图片
运行后提供Web界面上传图片到指定目录
"""

import os
import sys
import json
import base64
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import cgi

class UploadHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """提供简单的上传页面"""
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html_content = '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>选股系统 - 图片上传</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                    h1 { color: #333; text-align: center; margin-bottom: 30px; }
                    .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; border-radius: 8px; }
                    .upload-area:hover { border-color: #007bff; }
                    input[type="file"] { display: none; }
                    .upload-btn { background: #007bff; color: white; padding: 12px 24px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; }
                    .upload-btn:hover { background: #0056b3; }
                    .status { margin-top: 20px; padding: 10px; border-radius: 5px; }
                    .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                    .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📈 选股系统 - 模板图片上传</h1>
                    <div class="upload-area" id="dropArea">
                        <p>📁 选择模板股票日线图进行上传</p>
                        <input type="file" id="fileInput" accept="image/*" multiple>
                        <button class="upload-btn" onclick="document.getElementById('fileInput').click()">
                            📤 选择图片文件
                        </button>
                    </div>
                    <div id="status"></div>
                    
                    <script>
                    document.getElementById('fileInput').addEventListener('change', function(e) {
                        const files = e.target.files;
                        if (files.length === 0) return;
                        
                        const formData = new FormData();
                        for (let i = 0; i < files.length; i++) {
                            formData.append('files', files[i]);
                        }
                        
                        const statusDiv = document.getElementById('status');
                        statusDiv.innerHTML = '<div class="status">📤 正在上传...</div>';
                        
                        fetch('/upload', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                statusDiv.innerHTML = '<div class="status success">✅ 上传成功！' + data.message + '</div>';
                            } else {
                                statusDiv.innerHTML = '<div class="status error">❌ 上传失败：' + data.message + '</div>';
                            }
                        })
                        .catch(error => {
                            statusDiv.innerHTML = '<div class="status error">❌ 上传错误：' + error.message + '</div>';
                        });
                    });
                    
                    // 拖拽上传支持
                    const dropArea = document.getElementById('dropArea');
                    dropArea.addEventListener('dragover', (e) => {
                        e.preventDefault();
                        dropArea.style.borderColor = '#007bff';
                    });
                    
                    dropArea.addEventListener('dragleave', () => {
                        dropArea.style.borderColor = '#ccc';
                    });
                    
                    dropArea.addEventListener('drop', (e) => {
                        e.preventDefault();
                        dropArea.style.borderColor = '#ccc';
                        const files = e.dataTransfer.files;
                        if (files.length > 0) {
                            document.getElementById('fileInput').files = files;
                            // 触发上传
                            const event = new Event('change');
                            document.getElementById('fileInput').dispatchEvent(event);
                        }
                    });
                    </script>
                </div>
            </body>
            </html>
            '''
            self.wfile.write(html_content.encode('utf-8'))
        else:
            self.send_error(404)

    def do_POST(self):
        """处理文件上传"""
        if self.path == '/upload':
            try:
                # 解析multipart/form-data
                content_type = self.headers.get('content-type')
                if not content_type or not content_type.startswith('multipart/form-data'):
                    self.send_error(400, "Invalid content type")
                    return
                
                # 获取boundary
                boundary = content_type.split("boundary=")[1]
                boundary = boundary.encode()
                
                # 读取整个请求体
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                
                # 保存上传的文件
                upload_dir = "/root/.copaw/stock_pattern_selector/uploads"
                os.makedirs(upload_dir, exist_ok=True)
                
                # 简单解析（实际生产环境应该用更好的库）
                parts = post_data.split(boundary)
                saved_files = []
                
                for part in parts:
                    if b'filename="' in part:
                        # 提取文件名
                        filename_start = part.find(b'filename="') + len(b'filename="')
                        filename_end = part.find(b'"', filename_start)
                        if filename_start > len(b'filename="') and filename_end > filename_start:
                            filename = part[filename_start:filename_end].decode('utf-8')
                            # 提取文件内容
                            file_start = part.find(b'\r\n\r\n') + 4
                            file_end = part.rfind(b'\r\n--')
                            if file_end == -1:
                                file_end = len(part)
                            file_content = part[file_start:file_end]
                            
                            # 保存文件
                            safe_filename = os.path.basename(filename)
                            file_path = os.path.join(upload_dir, safe_filename)
                            with open(file_path, 'wb') as f:
                                f.write(file_content)
                            saved_files.append(safe_filename)
                
                if saved_files:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {
                        'success': True,
                        'message': f'成功上传 {len(saved_files)} 个文件: {", ".join(saved_files)}'
                    }
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                else:
                    self.send_error(400, "No files uploaded")
                    
            except Exception as e:
                self.send_error(500, f"Upload failed: {str(e)}")
        else:
            self.send_error(404)

def start_upload_server(port=8081):
    """启动上传服务器"""
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, UploadHandler)
    print(f"🚀 文件上传服务器启动成功！")
    print(f"🌐 访问地址: http://你的服务器IP:{port}")
    print(f"📁 上传目录: /root/.copaw/stock_pattern_selector/uploads/")
    print(f"💡 请通过浏览器访问上述地址上传图片")
    httpd.serve_forever()

if __name__ == "__main__":
    start_upload_server()