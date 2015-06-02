from bs4 import BeautifulSoup
import inlinestyler.utils as inline_styler
import mandrill
import asyncio

email_css = """
<style type="text/css">
    table.diff {font-family:Courier; border:medium;}
    .diff_header {background-color:#e0e0e0}
    td.diff_header {text-align:right}
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa}
    .diff_chg {background-color:#ffff77}
    .diff_sub {background-color:#ffaaaa}
    table {width:100%;}
</style>
"""

email_error = """
<table class="diff" id="difflib_chg_to4__top"
       cellspacing="0" cellpadding="0" rules="groups" width="600">
    <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
    <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>

    <thead>
    <tr><td width="100%" id="file_path" colspan="2"></td></tr>
    <tr><td width="50%" id="left_path"></td><td width="50%" id="right_path"></td></tr>
    </thead>

    <tbody>
    <tr><td width="50%"><p id="left_html"></p></td><td width="50%"><p id="right_html"></p></td></tr>
    </tbody>
</table>

<div id="md_diff"></div>

<a id="section_link" href="" target="_blank">Go to section</a>
"""


def _append_content(soup, tag_id, content):
    tags = soup.select('#{}'.format(tag_id))
    if tags and content:
        tags[0].append(content)
    return soup


def _fill_error(diff):
    email_soup = BeautifulSoup(email_error)
    email_soup = _append_content(email_soup, 'file_path', diff.file_path)
    email_soup = _append_content(email_soup, 'left_path', diff.base_path)
    email_soup = _append_content(email_soup, 'right_path', diff.other_path)
    email_soup = _append_content(email_soup, 'left_html', BeautifulSoup(diff.base).body)
    email_soup = _append_content(email_soup, 'right_html', BeautifulSoup(diff.other).body)
    email_soup = _append_content(email_soup, 'md_diff', BeautifulSoup(diff.diff).body)

    tag = email_soup.select('#section_link')
    if tag:
        tag[0]['href'] = diff.section_link

    return email_soup.prettify()

@asyncio.coroutine
def send(mandrill_key, user_email, diffs, topic=None):
    mandrill_client = mandrill.Mandrill(mandrill_key)
    template = '\n<hr>\n'.join(_fill_error(diff) for diff in diffs)
    email_body = inline_styler.inline_css(email_css + template)
    message = {
        'from_email': 'message.from_email@example.com',
        'from_name': 'KeepSafe Translation Verifier',
        'subject': topic or 'Translations not passing the validation test',
        'html': email_body,
        'to': [{'email': user_email,'type': 'to'}],
    }
    return mandrill_client.messages.send(message=message, async=True, ip_pool='Main Pool')
