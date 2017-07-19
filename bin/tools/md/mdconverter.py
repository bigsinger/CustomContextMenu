# coding: utf-8

import os
import sys
import codecs
import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import html
from weasyprint import HTML

# 使用此脚本需要安装mistune
# pip install mistune


# 返回当前脚本的全路径，末尾不带\
def getthispath():
    path = sys.path[0]
    #判断为脚本文件还是py2exe编译后的文件，如果是脚本文件，则返回的是脚本的目录，如果是py2exe编译后的文件，则返回的是编译后的文件路径
    if os.path.isdir(path):
        return path
    elif os.path.isfile(path):
        return os.path.split(path)[0]


global CODE_LANG

# 代码见：https://pypi.python.org/pypi/mistune
# 由于不怎么指定源码语言，这里设置了一个全局变量来控制
class HighlightRenderer(mistune.Renderer):
    def block_code(self, code, lang):
        lang = CODE_LANG
        if not lang:
            return '\n<pre><code>%s</code></pre>\n' % \
                mistune.escape(code)
        lexer = get_lexer_by_name(lang, stripall=True)
        formatter = html.HtmlFormatter()
        return highlight(code, lexer, formatter)

# renderer = HighlightRenderer()
# markdown = mistune.Markdown(renderer=renderer)
# print(markdown('```python\nassert 1 == 1\n```'))


def md2html_by_markdown2(md_text):
    import markdown2
    extras = ['code-friendly', 'fenced-code-blocks', 'footnotes']
    html_text = markdown2.markdown(md_text, extras=extras)
    return html_text


def convert_md_file(argv):
    is_convert_html = True
    if len(sys.argv) >= 3:
        is_convert_html = False

    md_filename = argv[0]
    css_filename = os.path.join(getthispath(), 'default.css')   # 更多CSS样式见：http://richleland.github.io/pygments-css/
    html_filename = '%s.html' % (md_filename[:-3])
    pdf_filename = '.'.join([md_filename.rsplit('.')[0], 'pdf'])
    css_text = None
    md_text = None

    with codecs.open(css_filename, mode='r', encoding='utf-8') as f:
        css_text = '<style type = "text/css">\n' + f.read() + "\n</style>\n"

    with codecs.open(md_filename, mode='r', encoding='utf-8') as f:
        md_text = f.read()

    # 两种方法转换，推荐mistune
    if False:
        html_text = md2html_by_markdown2(md_text)
    else:
        global CODE_LANG
        CODE_LANG = 'java'
        markdown = mistune.Markdown(renderer=HighlightRenderer())
        html_text = markdown(md_text)

    if is_convert_html:
        # save to html file
        with codecs.open(html_filename, 'w', encoding='utf-8', errors='xmlcharrefreplace') as f:
            f.write(css_text + html_text)
        if os.path.exists(html_filename):
            os.popen(html_filename)
    else:
        # save to pdf file
        HTML(string=html_text).write_pdf(pdf_filename, stylesheets=[css_filename])
        if os.path.exists(pdf_filename):
            os.popen(pdf_filename)


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        convert_md_file(sys.argv[1:])
    else:
        print("Error:please specify markdown file path")