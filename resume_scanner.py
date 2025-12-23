from flask import Flask, request, render_template_string
from markupsafe import Markup
import pdfplumber
import re

app = Flask(__name__)

JOB_KEYWORDS = {
    'python': 15, 'flask': 12, 'matlab': 12, 'api': 10,
    'pandas': 8, 'sql': 8, 'git': 7, 'docker': 6,
    'c': 10, 'data': 8, 'web': 8, 'javascript': 6
}

HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>🤖 AI Resume Scanner by S. Gomathi Durga</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        *{margin:0;padding:0;box-sizing:border-box;font-family:'Segoe UI',system-ui,-apple-system,BlinkMacSystemFont,sans-serif}
        body{
            min-height:100vh;
            padding:24px 10px;
            background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);
            color:#1f2933;
        }
        .container{
            max-width:820px;
            margin:0 auto;
            background:rgba(255,255,255,0.96);
            border-radius:22px;
            padding:26px 18px 26px;
            box-shadow:0 24px 60px rgba(15,23,42,0.45);
            border:1px solid rgba(226,232,240,0.95);
        }
        h1{
            text-align:center;
            color:#4a5568;
            margin-bottom:6px;
            font-size:2rem;
        }
        .subtitle{
            text-align:center;
            color:#718096;
            margin-bottom:18px;
            font-size:0.9rem;
        }
        form{margin-bottom:12px}
        input[type="file"],
        textarea,
        button{
            width:100%;
            padding:12px;
            margin:8px 0;
            border:2px solid #e2e8f0;
            border-radius:12px;
            font-size:0.95rem;
            transition:all .25s;
        }
        textarea{
            min-height:80px;
            resize:vertical;
        }
        input[type="file"]{
            padding:10px;
            background:#f7fafc;
        }
        input:focus,textarea:focus{
            outline:none;
            border-color:#667eea;
            box-shadow:0 0 0 3px rgba(102,126,234,0.14);
        }
        button{
            background:linear-gradient(135deg,#667eea,#764ba2);
            color:#f9fafb;
            font-weight:600;
            border:none;
            cursor:pointer;
            font-size:1rem;
            margin-top:6px;
            box-shadow:0 14px 30px rgba(102,126,234,0.35);
        }
        button:hover{
            transform:translateY(-1px);
            filter:brightness(1.03);
        }

        .result{
            background:#f7fafc;
            border-radius:14px;
            padding:18px 14px 14px;
            margin:18px 0 4px;
            border-left:5px solid #667eea;
            font-size:0.9rem;
        }
        .score{
            font-size:3rem;
            font-weight:800;
            background:linear-gradient(135deg,#48bb78,#38a169);
            -webkit-background-clip:text;
            -webkit-text-fill-color:transparent;
            display:block;
            text-align:center;
            margin:14px 0;
        }
        .skills-grid{
            display:grid;
            grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
            gap:10px;
            margin:10px 0 6px;
        }
        .skill-card{
            background:#ffffff;
            border-radius:10px;
            padding:10px 11px 9px;
            box-shadow:0 6px 16px rgba(148,163,184,0.35);
            text-align:center;
            font-size:0.85rem;
        }
        .skill-score{
            font-size:1.3rem;
            font-weight:600;
            color:#667eea;
        }
        .progress-bar{
            height:7px;
            background:#e2e8f0;
            border-radius:4px;
            overflow:hidden;
            margin-top:6px;
        }
        .progress-fill{
            height:100%;
            background:linear-gradient(90deg,#667eea,#764ba2);
            transition:width .5s;
        }
        .tips{
            margin-top:8px;
            color:#4a5568;
        }
        .tips strong{color:#2d3748}

        /* Mobile tweaks */
        @media(max-width:640px){
            body{padding:18px 8px;}
            .container{padding:20px 14px 22px;border-radius:18px;}
            h1{font-size:1.65rem;}
            .score{font-size:2.4rem;}
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
Python, Flask/Django, REST APIs, Git, SQL, pandas, machine learning, Docker, MATLAB, C
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
            return render_template_string(HTML, result="❌ No PDF uploaded", plot="")

        file = request.files['resume']

        try:
            # Extract text from PDF
            with pdfplumber.open(file) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() or ""

            if not text.strip():
                return render_template_string(HTML, result="❌ No text found in PDF", plot="")

            # Keyword analysis (simple weighted keyword count as used in many resume tools). [web:107][web:109]
            text_lower = text.lower()
            skills_found = {}

            for keyword, weight in JOB_KEYWORDS.items():
                count = len(re.findall(re.escape(keyword.lower()), text_lower))
                if count > 0:
                    skills_found[keyword] = min(100, count * weight)

            total_score = sum(skills_found.values())
            max_score = sum(JOB_KEYWORDS.values())
            percentage = min(100, (total_score / max_score) * 100) if max_score else 0

            skills_html = ""
            for skill, score in sorted(
                skills_found.items(), key=lambda x: x[1], reverse=True
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
                result_html += "<p class='tips'><strong>🚀 Quick Wins:</strong> " + ", ".join(suggestions) + "</p>"
            else:
                result_html += "<p class='tips'><strong>✅ Ready for Python internships!</strong></p>"

            return render_template_string(HTML, result=Markup(result_html), plot="")

        except Exception as e:
            return render_template_string(HTML, result=f"❌ Error: {str(e)}", plot="")

    return render_template_string(HTML, result="", plot="")

if __name__ == '__main__':
    print("🚀 AI Resume Scanner LIVE at http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
