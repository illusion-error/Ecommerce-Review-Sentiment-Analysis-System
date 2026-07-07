FROM nginx:1.27-alpine

RUN printf '%s\n' \
    '<!doctype html>' \
    '<html lang="zh-CN">' \
    '<head>' \
    '  <meta charset="utf-8" />' \
    '  <meta name="viewport" content="width=device-width, initial-scale=1" />' \
    '  <title>E-commerce Review Sentiment Analysis</title>' \
    '  <style>body{font-family:Arial,"Microsoft YaHei",sans-serif;margin:40px;background:#f6f8fb;color:#1f2937}.box{max-width:760px;margin:auto;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:28px}code{background:#eef2ff;padding:2px 6px;border-radius:4px}</style>' \
    '</head>' \
    '<body>' \
    '  <main class="box">' \
    '    <h1>电商评论情感分析系统</h1>' \
    '    <p>第一阶段 Docker 前端占位页已启动。</p>' \
    '    <p>后端健康检查：<code>/api/health</code></p>' \
    '  </main>' \
    '</body>' \
    '</html>' \
    > /usr/share/nginx/html/index.html

EXPOSE 80
