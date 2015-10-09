from bs4 import BeautifulSoup
import markdown
import inlinestyler.utils as inline_styler
import mandrill
import asyncio

email_css = """
<style type="text/css">
    table.diff {font-family:Courier; border:medium;}
    .diff_header {background-color:#e0e0e0}
    td.diff_header {text-align:right;}
    .diff tr {border: 1px solid black;}
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa}
    .diff_chg {background-color:#ffff77}
    .diff_sub {background-color:#ffaaaa}
    table {width:100%;}
    .info_text {margin-bottom: 15px;}
</style>
"""

email_error = """
<div class="info-text">
    <h3>KeepSafe's validation tool has found some problems with the translation</h3>
    <p>
        The elements on the left show the reference text, the elements on the right the translation.<br />
        The elements that are missing are highlighted in green, the ones which are unnecessary are highlighted in red. <br />
        The tool is not always 100% accurate, sometimes it might show things that are correct as errors if there are other errors in the text. <br />
        Please correct the errors you can find first. If you think the text is correct and the tool is still showing errors please contact KeepSafe's employee.
    </p>
</div>

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
    <tr><td width="50%"><p id="left_diff"></p></td><td width="50%"><p id="right_diff"></p></td></tr>
    </tbody>
</table>

<div id="error_messages">

</div>

<a id="section_link" href="" target="_blank">Go to section</a>
"""


def _append_content(soup, tag_id, content):
    tags = soup.select('#{}'.format(tag_id))
    if tags and content:
        tags[0].append(content)
    return soup


def _fill_error(diff):
    base_html = markdown.markdown(diff.diff.base.parsed)
    other_html = markdown.markdown(diff.diff.other.parsed)
    error_msgs = '</br>'.join(diff.diff.error_msgs)
    email_soup = BeautifulSoup(email_error)
    email_soup = _append_content(email_soup, 'left_path', diff.file_path)
    email_soup = _append_content(email_soup, 'left_path', diff.base_path)
    email_soup = _append_content(email_soup, 'right_path', diff.other_path)
    email_soup = _append_content(email_soup, 'left_html', BeautifulSoup(base_html).body)
    email_soup = _append_content(email_soup, 'right_html', BeautifulSoup(other_html).body)
    email_soup = _append_content(email_soup, 'left_diff', BeautifulSoup(diff.diff.base.diff).body)
    email_soup = _append_content(email_soup, 'right_diff', BeautifulSoup(diff.diff.other.diff).body)
    # email_soup = _append_content(email_soup, 'error_messages', error_msgs)

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
        'from_email': 'no-reply@getkeepsafe.com',
        'from_name': 'KeepSafe Translation Verifier',
        'subject': topic or 'Translations not passing the validation test',
        'html': email_body,
        'to': [
            {'email': user_email, 'type': 'to'},
            {'email': 'philipp+content-validator@getkeepsafe.com', 'type': 'cc'}
        ],
    }
    return mandrill_client.messages.send(message=message, async=True, ip_pool='Main Pool')
