from flask import Flask, request, render_template_string
from markupsafe import Markup
import pdfplumber
import re

app = Flask(__name__)

JOB_KEYWORDS = {
    'python': 15, 'flask': 12, 'MATLAB': 12, 'api': 10,
    'pandas': 8, 'sql': 8, 'git': 7, 'docker': 6,
    'C': 10, 'data': 8, 'web': 8, 'javascript': 6
}

HTML = '''
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AI Resume Scanner by S. Gomathi Durga</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * {margin:0;padding:0;box-sizing:border-box}
        body {
            font-family:'Segoe UI',sans-serif;
            background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
            min-height:100vh;
            padding:20px;
            color:#333;
        }
        .container {
            max-width:800px;
            margin:0 auto;
            background:rgba(255,255,255,0.95);
            border-radius:20px;
            padding:40px;
            box-shadow:0 20px 40px rgba(0,0,0,0.1);
        }
        h1 {
            text-align:center;
            color:#4a5568;
            margin-bottom:10px;
            font-size:2.5em;
        }
        .subtitle {
            text-align:center;
            color:#718096;
            margin-bottom:30px;
            font-size:1.1em;
        }
        input,textarea,button {
            width:100%;
            padding:15px;
            margin:10px 0;
            border:2px solid #e2e8f0;
            border-radius:12px;
            font-size:16px;
            transition:all 0.3s;
        }
        input:focus,textarea:focus {
            outline:none;
            border-color:#667eea;
            box-shadow:0 0 0 3px rgba(102,126,234,0.1);
        }
        button {
            background:linear-gradient(135deg,#667eea,#764ba2);
            color:white;
            font-weight:600;
            border:none;
            cursor:pointer;
            font-size:18px;
        }
        button:hover {
            transform:translateY(-2px);
            box-shadow:0 10px 20px rgba(102,126,234,0.3);
        }
        .result {
            background:#f7fafc;
            border-radius:12px;
            padding:25px;
            margin:25px 0;
            border-left:5px solid #667eea;
        }
        .score {
            font-size:4em;
            font-weight:800;
            background:linear-gradient(135deg,#48bb78,#38a169);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            display:block;
            text-align:center;
            margin:20px 0;
        }
        .skills-grid {
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
            gap:15px;
            margin:20px 0;
        }
        .skill-card {
            background:white;
            border-radius:10px;
            padding:15px;
            box-shadow:0 4px 12px rgba(0,0,0,0.1);
            text-align:center;
        }
        .skill-score {
            font-size:1.5em;
            font-weight:bold;
            color:#667eea;
        }
        .progress-bar {
            height:8px;
            background:#e2e8f0;
            border-radius:4px;
            overflow:hidden;
            margin-top:8px;
        }
        .progress-fill {
            height:100%;
            background:linear-gradient(90deg,#667eea,#764ba2);
            transition:width 0.5s;
        }
    </style>
</head>
<body>
<div class="container">
    <h1>🤖 AI Resume Scanner</h1>
    <p class="subtitle">Upload PDF → Instant Python Internship Score + Skills Analysis</p>
    <form method="POST" enctype="multipart/form-data">
        <input type="file" name="resume" accept=".pdf" required>
        <textarea name="job_desc" placeholder="Paste job description (or leave blank)">
Python, Flask/Django, REST APIs, Git, SQL, pandas, machine learning, Docker, Matlab 
        </textarea>
        <button type="submit">🔍 SCAN MY RESUME</button>
    </form>
    {{ plot|safe }}
    <div class="result">{{ result|safe }}</div>
</div>
</body>
</html>
'''

@app.route('/', methods=['GET', 'POST'])
def scan_resume():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return render_template_string(HTML,
                                          result="❌ No PDF uploaded",
                                          plot="")

        file = request.files['resume']

        try:
            # Extract text from PDF
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""

            if not text.strip():
                return render_template_string(
                    HTML,
                    result="❌ No text found in PDF",
                    plot=""
                )

            # Keyword analysis
            text_lower = text.lower()
            skills_found = {}

            for keyword, weight in JOB_KEYWORDS.items():
                count = len(re.findall(re.escape(keyword), text_lower))
                if count > 0:
                    skills_found[keyword] = min(100, count * weight)

            # Score
            total_score = sum(skills_found.values())
            max_score = sum(JOB_KEYWORDS.values())
            percentage = min(100, (total_score / max_score) * 100) if max_score else 0

            # Skills cards with progress bars
            skills_html = ""
            for skill, score in sorted(
                skills_found.items(),
                key=lambda x: x[1],
                reverse=True
            )[:6]:
                progress = min(100, score)
                skills_html += f"""
                <div class="skill-card">
                    <strong>{skill.title()}</strong>
                    <div class="skill-score">{score:.0f}</div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress}%"></div>
                    </div>
                </div>
                """

            suggestions = []
            if percentage < 70:
                suggestions = [
                    "⭐ Add Python/Flask projects to GitHub",
                    "⭐ Mention API/database experience",
                    "⭐ Include ML/data science projects"
                ]

            result_html = f"""
            <h2>🎯 Your Score: <span class="score">{percentage:.0f}%</span></h2>
            <p><strong>📈 Skills Found:</strong> {len(skills_found)}/{len(JOB_KEYWORDS)} matches</p>
            <div class="skills-grid">{skills_html}</div>
            """
            if suggestions:
                result_html += (
                    "<p><strong>🚀 Quick Wins:</strong> "
                    + ", ".join(suggestions)
                    + "</p>"
                )
            else:
                result_html += "<p><strong>✅ Ready for Python internships!</strong></p>"

            return render_template_string(
                HTML,
                result=Markup(result_html),
                plot=""
            )

        except Exception as e:
            return render_template_string(
                HTML,
                result=f"❌ Error: {str(e)}",
                plot=""
            )

    # GET request
    return render_template_string(HTML, result="", plot="")

if __name__ == '__main__':
    print("🚀 AI Resume Scanner LIVE at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
