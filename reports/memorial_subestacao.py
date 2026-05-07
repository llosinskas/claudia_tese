from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas 
from reportlab.platypus import Paragraph, SimpleDocTemplate, PageBreak, BaseDocTemplate, Frame, PageTemplate, Image, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle 
from reportlab.lib.units import cm
from reportlab.lib.sequencer import getSequencer
import io
import matplotlib.pyplot as plt
import sympy as sp

NAME_PROJECT = "SUBESTAÇÃO 300KVA"
TITULO_MEMORIAL = "SUBESTAÇÃO 300KVA - LOCAL"
AUTOR = "Engº Lucas"

# 1) Classe personalizada para interceptar os Parágrafos e enviar pro Índice (TOC)
class MyDocTemplate(BaseDocTemplate):
    def afterFlowable(self, flowable):
        """Registra entradas no Índice."""
        if flowable.__class__.__name__ == 'Paragraph':
            text = flowable.getPlainText()
            style = flowable.style.name
            if style == 'Section':
                self.notify('TOCEntry', (0, text, self.page))
            elif style == 'SubSection':
                self.notify('TOCEntry', (1, text, self.page))

def draw_watermark(canvas, doc):
    """Desenha a marca d'água em cada página."""
    canvas.saveState()
    canvas.setFont('Helvetica-Bold', 60)
    canvas.setFillGray(0.5, 0.3)  # Cinza translúcido
    canvas.translate(A4[0]/2, A4[1]/2)
    canvas.rotate(45)
    canvas.drawCentredString(0, 0, "EMPRESA-XXX")
    canvas.restoreState()

doc = MyDocTemplate(f"{NAME_PROJECT}.pdf", pagesize=A4)
frame = Frame(2*cm, 2*cm, 17*cm, 25*cm, id='normal')
template = PageTemplate(id='template', frames=[frame], onPage=draw_watermark)
doc.addPageTemplates([template])

story = []
styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        name = 'Section', 
        fontSize = 12,   
        spaceBefore = 15,
        spaceAfter = 12, 
        outlineLevel = 0))

styles.add(
    ParagraphStyle(
        name='SubSection', 
        fontSize = 12, 
        spaceBefore = 12, 
        spaceAfter = 12, 
        outlineLevel=1))


styles.add(
    ParagraphStyle(
        name='normal', 
        fontSize = 12, 
        leading = 18,       # Espaçamento entre as linhas (1.5x)
        alignment = TA_JUSTIFY, # Texto justificado
        spaceBefore = 6, 
        spaceAfter = 12,    # Espaçamento após o parágrafo
        outlineLevel=2))
# 2) Configuração do TOC
toc = TableOfContents()
toc.levelStyles = [
    ParagraphStyle(name='TOC1', fontSize=12, leftIndent=20, firstLineIndent=-20, spaceBefore=5),
    ParagraphStyle(name='TOC2', fontSize=10, leftIndent=40, firstLineIndent=-20),
]

seq = getSequencer()

def section(title):
    sec_num = seq.next("section")
    p = Paragraph(f"{sec_num}. {title}", styles["Section"])
    story.append(p)
    return sec_num

def subsection(title):
    num_section = seq.__getitem__("section")
    sub_num = seq.next("subsection")
    p = Paragraph(f"{num_section}.{sub_num}. {title}", styles["SubSection"])
    story.append(p)
    return sub_num

def normal(text):
    p = Paragraph(text, styles["normal"])
    story.append(p)

def formula(latex_str, width_scale=1.0):
    """Renderiza uma equação LaTeX para o PDF usando matplotlib e adiciona numeração."""
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${latex_str}$", fontsize=14)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, transparent=True, bbox_inches='tight', pad_inches=0.1)
    plt.close(fig)
    buf.seek(0)
    
    img = Image(buf)
    # Converte DPI para escala do ReportLab
    img.drawWidth = (img.imageWidth * 72 / 300) * width_scale
    img.drawHeight = (img.imageHeight * 72 / 300) * width_scale
    
    # Obtém o próximo número de equação
    eq_num = seq.next("equation")
    
    # Monta uma tabela de 3 colunas: [Espaço vazio, Imagem, Número]
    # Largura total disponível = 17cm (pois A4 width = 21cm, e usamos frame 17cm width)
    # Coluna central = 13cm, laterais = 2cm cada
    data = [['', img, Paragraph(f"({eq_num})", styles["normal"])]]
    t = Table(data, colWidths=[2*cm, 13*cm, 2*cm])
    t.setStyle(TableStyle([
        ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
        ('ALIGN', (2, 0), (2, 0), 'RIGHT'),
        ('VALIGN', (2, 0), (2, 0), 'MIDDLE'),
    ]))
    
    story.append(t)


# ==== Capa e Índice ====
story.append(Paragraph(f"MEMORIAL DESCRITIVO E DE CÁLCULO DE {TITULO_MEMORIAL}", styles["h1"]))
story.append(PageBreak())

story.append(Paragraph("SUMÁRIO", styles["h2"]))
story.append(toc)
story.append(PageBreak())

# ==== Conteúdo ====
section("INTRODUÇÃO")
normal(
    "O presente memorial tem como finalidade apresentar o projeto elétrico de subestação com potência de xxx kVA abrigada."
)
normal("O refrente projeto foi desenvolvido com base na norma CNC-OMBR-MAT-20-0942-EDBR da ENEL-SP.")
normal("""Esse projeto teve por finalidade atender os requisitos estabelecidos nas normas técnicas 
da Enel – São Paulo no dimensionamento de uma 
subestação Abrigada de 300 KVA para suprir a demanda de energia elétrica do cliente xxxx-xxxx, Situado na Rua XXXX""")
normal("""O Fornecimento de energia será feito em média tensão, portanto, a medição será realizada por meio 
de um conjunto de medição polimérico """)


section("IDENTIFICAÇÃO")
normal("Dados de identificação da obra...")

section("CARACTERÍSTICAS DA SUBESTAÇÃO")
normal("A subestação possui potência de 300 kVA...")

subsection("PONTO DE ENTREGA")
normal("A subestação será abrigada, de carga instalada de 300 kVA, com medição em média tensão no padrão ENEL-SP, conforme peças gráficas anexas.")

subsection("ESTRUTURA DE MEDIÇÃO")
normal("""O conjunto de medição será implantado no limite do terreno, com a via pública, 
A estrutura de medição possui poste especificado de 300/11.""")
normal("""Da estrutura do conjunto de medição sairá rede subeterrânea até a subestação de energia elétrica de 300kVA em eletroduto PVC 
rígido 4", sendo um eletroduto para cada via de condutor elétrico em média tensão isolados. É previsto a colocação de mais um eletroduto em paralelo a ser utilizado como reserva""")
normal("""A medição da subestação será feita através de um conjunto de medição polimérico, o qual é o recomendado no item 6.8 da norma 
CNC-OMBR-MAT-20-0942-EDBR da ENEL-SP. Fornecimento de Energia Elétrica em Tensão Primária de Distribuição quando o fornecimento acontece em média tensão. 
Além disso, as operadoras de telefonia são TIM, Claro e Vivo.""")
normal("""
A medição será em média tensão, através de um conjunto de medição compacto, em material porlimérico, sendo que o medidor deverá ser instalado internamente ao conjunto de medição, juntamente 
com um módulo telemetria

""")

section("ATERRAMENTO")
normal("O sistema de aterramento foi dimensionado conforme as normas vigentes...")

section("NORMAS")
normal("As normas NBR 5410 e NBR 14039 foram adotadas...")

section("CÁLCULOS DA DEMANDA")
normal("O cálculo da demanda considerou os seguintes fatores e fórmulas fundamentais:")

# Exemplo de fórmula LaTeX complexa:
eq1 = r"D = \sum_{i=1}^{n} P_i \cdot Fd_i"
formula(eq1)

normal("E também, utilizando o SymPy, podemos gerar integrais, matrizes ou expressões complexas diretamente no PDF:")
x, y = sp.symbols('x y')
expr = sp.Integral(sp.sqrt(x**2 + y**2), x)
formula(sp.latex(expr))

formula(r"sen(x) dx")
# 3) O multiBuild é obrigatório para que o ReportLab passe pelo documento
# várias vezes até calcular todas as páginas do Índice corretamente.
section("ANEXOS")


doc.multiBuild(story)
print(f"{NAME_PROJECT}.pdf gerado com sucesso!")

