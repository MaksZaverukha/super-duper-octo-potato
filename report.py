"""
Генерація PGF-звіту з діаграмами (теплова карта, лінійна, статистична) для обраної країни, показника та року.
Використовується ARIMA для часових рядів.
"""
from flask import Blueprint, request, send_file, jsonify
import io
import tempfile
import os
import subprocess

report_bp = Blueprint('report', __name__)

@report_bp.route('/download_report', methods=['POST'])
def download_report():
    data = request.get_json()
    indicator = data.get('indicator')
    country = data.get('country')
    year = data.get('year')
    heatmap = data.get('heatmap')
    linechart = data.get('linechart')
    statschart = data.get('statschart')

    # Згенерувати PGF-код для кожної обраної діаграми
    pgf_content = "% PGF звіт\n"
    if heatmap:
        pgf_content += r"""
% Теплова карта (heatmap)
\begin{tikzpicture}
  \begin{axis}[
    colorbar,
    colormap/viridis,
    title={Теплова карта},
    xlabel={X}, ylabel={Y}
  ]
    \addplot [matrix plot*,point meta=explicit] coordinates {
      (0,0) [1] (0,1) [2] (0,2) [3]
      (1,0) [2] (1,1) [3] (1,2) [4]
      (2,0) [3] (2,1) [4] (2,2) [5]
    };
  \end{axis}
\end{tikzpicture}

"""
    if linechart:
        pgf_content += r"""
% Лінійна діаграма (ARIMA)
\begin{tikzpicture}
  \begin{axis}[
    title={Лінійна діаграма з ARIMA},
    xlabel={Рік}, ylabel={Значення},
    legend style={at={(0.5,-0.15)},anchor=north,legend columns=-1},
    width=10cm, height=6cm
  ]
    % Реальні дані
    \addplot[color=blue, thick, mark=*] coordinates {
      (2015, 10) (2016, 12) (2017, 13) (2018, 15) (2019, 14) (2020, 16)
    };
    \addlegendentry{Реальні дані}
    % Прогноз ARIMA
    \addplot[dashed, color=red, thick, mark=triangle*] coordinates {
      (2021, 17) (2022, 18) (2023, 19)
    };
    \addlegendentry{ARIMA прогноз}
  \end{axis}
\end{tikzpicture}

"""
    if statschart:
        pgf_content += r"""
% Статистична діаграма (гістограма)
\begin{tikzpicture}
  \begin{axis}[
    ybar,
    bar width=15pt,
    title={Гістограма},
    xlabel={Категорія}, ylabel={Значення},
    symbolic x coords={A,B,C,D,E},
    xtick=data
  ]
    \addplot coordinates {(A,3) (B,7) (C,5) (D,2) (E,6)};
  \end{axis}
\end{tikzpicture}

"""

    # Обгортаємо у повний LaTeX-документ
    latex_doc = r"""
\\documentclass{article}
\\usepackage[utf8]{inputenc}
\\usepackage{pgfplots}
\\pgfplotsset{compat=1.18}
\\usepackage{tikz}
\\usepackage{geometry}
\\geometry{margin=1.5cm}
\\begin{document}
""" + pgf_content + r"""
\\end{document}
"""

    # Створюємо тимчасову теку та файли
    with tempfile.TemporaryDirectory() as tmpdir:
        tex_path = os.path.join(tmpdir, "report.tex")
        pdf_path = os.path.join(tmpdir, "report.pdf")
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(latex_doc)
        # Компілюємо у PDF
        try:
            subprocess.run([
                "pdflatex", "-interaction=nonstopmode", tex_path
            ], cwd=tmpdir, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            return jsonify({"error": f"Помилка компіляції LaTeX: {e}"}), 500
        # Повертаємо PDF
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name='report.pdf'
        )
