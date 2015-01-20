from bs4 import BeautifulSoup
import mandrill

email_template = """
<style type="text/css">
    table.diff {font-family:Courier; border:medium;}
    .diff_header {background-color:#e0e0e0}
    td.diff_header {text-align:right}
    .diff_next {background-color:#c0c0c0}
    .diff_add {background-color:#aaffaa}
    .diff_chg {background-color:#ffff77}
    .diff_sub {background-color:#ffaaaa}
</style>
<table class="diff" id="difflib_chg_to4__top"
       cellspacing="0" cellpadding="0" rules="groups" >
    <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>
    <colgroup></colgroup> <colgroup></colgroup> <colgroup></colgroup>

    <thead>
    <tr><td width="50%" id="left_path"></td><td width="50%" id="right_path"></td></tr>
    </thead>

    <tbody>
    <tr><td width="50%"><p id="left_html"></p></td><td width="50%"><p id="right_html"></p></td></tr>
    </tbody>
</table>

<div id="md_diff"></div>
"""


def _append_content(soup, tag_id, content):
    tags = soup.select('#{}'.format(tag_id))
    if tags and content:
        tags[0].append(content)
    return soup


def _fill_template(diff):
    email_soup = BeautifulSoup(email_template)
    email_soup = _append_content(email_soup, 'left_path', diff.base_path)
    email_soup = _append_content(email_soup, 'right_path', diff.other_path)
    email_soup = _append_content(email_soup, 'left_html', BeautifulSoup(diff.base).body)
    email_soup = _append_content(email_soup, 'right_html', BeautifulSoup(diff.other).body)
    email_soup = _append_content(email_soup, 'md_diff', BeautifulSoup(diff.diff).body)
    return email_soup.prettify()


def send(mandrill_key, user, diff):
    mandrill_client = mandrill.Mandrill(mandrill_key)
    email = _fill_template(diff)
    address = user['email']
    message = {
        'from_email': 'message.from_email@example.com',
        'from_name': 'Example Name',
        'headers': {'Reply-To': 'message.reply@example.com'},
        'subject': 'example subject',
        'html': email,
        'to': [{'email': 'tomek.kwiecien@gmail.com',
             'name': 'Recipient Name',
             'type': 'to'}],
    }
    
    mandrill_client.messages.send(message=message, async=True, ip_pool='Main Pool')
