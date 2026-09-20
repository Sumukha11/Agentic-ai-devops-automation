from flask import Flask

app = Flask(__name__)

@app.route('/')
def index():
    return """
    <!doctype html>
    <html>
      <head>
        <title>Agentic DevOps Demo</title>
        <style>
          body { font-family: Arial, sans-serif; background: #0b1020; color: #eef2ff; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
          .card { background: #111827; border: 1px solid #334155; border-radius: 16px; padding: 40px 60px; box-shadow: 0 12px 30px rgba(0,0,0,0.3); }
          h1 { margin-top: 0; color: #7dd3fc; }
          .badge { display: inline-block; background: #22c55e; color: #062b14; padding: 6px 12px; border-radius: 999px; font-weight: bold; margin-bottom: 12px; }
        </style>
      </head>
      <body>
        <div class='card'>
          <div class='badge'>LIVE</div>
          <h1>Agentic DevOps Demo</h1>
          <p>This container is running a real web app deployed by Terraform.</p>
          <p>Jenkins, FastAPI, Streamlit, and Ollama are also part of this local stack.</p>
        </div>
      </body>
    </html>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
