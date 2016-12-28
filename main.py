import requests
from getpass import getpass
from bs4 import BeautifulSoup


urls = {
        'main': 'https://beta.hobi.com/wms/',
        'login': 'https://beta.hobi.com/tools/login.php',
        'info': 'https://beta.hobi.com/wms/process.php?'
                'action=view&what=barcode&barcode=',
        'move': 'https://beta.hobi.com/wms/process.php',
        'locate': 'https://beta.hobi.com/wms/process.php?'
                  'action=locate&what=skid&skid=',
        'logout': 'https://beta.hobi.com/tools/logout.php?ref=wms'
        }


class Item(object):

    def __init__(self, s, item, skid):
        self.s = s
        self.item = item.upper()
        self.pre_skid = find_str('Skid:', self.info_html)[0].split()[2]
        self.post_skid = skid.upper()
        self.is_moved = False
        self.info_html = self.s.get(urls['info']+self.item).text.split('<br>')
        self.is_tbr = self._is_tbr()
        self._get_info()

    def __len__(self):
        return int(find_str('rcvd:', self.info_html)[0].split()[1].strip(','))

    def _is_tbr(self):
        try:
            if find_str('TBR:', self.info_html)[0] and \
                    find_str('HSCR', self.info_html)[0]:
                return True
        except IndexError:
            return False

    def _is_moved(self):
        try:
            if find_str(self.post_skid, self.info_html)[0]:
                return True
        except IndexError:
            return False

    def move(self):
        data = {
            'action': 'move',
            'what': 'item',
            'barcode': self.item,
            'skid': self.post_skid
        }

        self.s.post(urls['move'], data)
        self.is_moved = self._is_moved()


def find_str(is_str, html):
    s_list = [string for string in html if is_str in string]
    return BeautifulSoup(s_list[0], 'html.parser').text


def is_skid_loc(s, skid):
    data = {'action': 'view', 'what': 'skid', 'skid': skid}
    pg_html = s.post(urls['locate']+skid, data).content
    html_str = find_html_str(pg_html, 1, 'br')
   
    return ('The skid {} is at'.format(skid.upper())) in html_str


def login_user(s):
    user_name = str(input('Login: '))
    password = str(getpass('Password: '))
    data = {
        'loginid': user_name,
        'pword': password,
        'ref': 'wms',
        'status': 'do'
    }

    s.post(urls['login'], data)


def is_login(s):
    html_str = find_html_str(s.get(urls['main']).text, 0, 'span', 'font-size:10px;')
    if 'Currently logged in' in html_str:
        return html_str
    else:
        return False


def find_html_str(html, index, html_tag, attrib=''):
    html_str_list = BeautifulSoup(
                   html, 'html.parser'
                   ).find_all(html_tag, style=attrib)
    try:
        return html_str_list[index].text
    except IndexError:
        return 'None'
      

def move_item_loop(s, skid):
    item_dict = {}
    while True:
        if not is_login(s):
            print('You are no longer logged in.')
            break
        else:
            item = str(input('Item > '))

            if 'back' in item:
                break
            elif item not in item_dict.keys():
                item_dict[item] = Item(s, item, skid)
                v = item_dict[item]
                v.move()
                print('Item: ' + v.item)
                print('TBR: {}'.format(v.is_tbr))
                print('Old Skid: ' + v.pre_skid)
                print('New Skid: ' + v.post_skid)
                print('Moved: {}'.format(v.is_moved))
                print('Count: {}'.format(len(v)))
            elif item in item_dict.keys():
                print(v.item + ' already on ' + v.pre_skid)


def main_loop():
    skid = ''
   
    with requests.Session() as s:
        while True:
            is_user_logged = is_login(s)
         
            if is_user_logged:
                print(is_user_logged[:-24])
            else:
                print('Not logged in.')
         
            user_input = str(input('> ')).split(' ')
         
            valid_commands = ['login', 'logout', 'skid', 'move', 'exit']

            if is_user_logged and user_input[0] == valid_commands[0]:
                user_name = is_user_logged[23:-24]
                print(user_name + ' - logged in.')
            elif not is_user_logged and user_input[0] == valid_commands[0]:
                login_user(s)

            elif is_user_logged and user_input[0] == valid_commands[1]:
                s.get(urls['logout'])
                skid = ''

            elif is_user_logged and user_input[0] == valid_commands[2]:
                try:
                    skid = user_input[1]
                    if not is_skid_loc(s, skid) and skid:
                        print("Invalid Skid Location: Skid doesn't have a location")
                        skid = ''
                    else:
                        print('Active Skid: {}'.format(skid))
                except IndexError:
                    if skid:
                        print('Active Skid: {}'.format(skid))
                    else:
                        print('No Active Skid:' +
                              "Please enter one by issuing command: skid 'skid id' ")

            elif is_user_logged and user_input[0] == valid_commands[3]:
                if not skid:
                    print('Invalid Option: No skid entered.')
                else:
                    move_item_loop(s, skid)

            elif not is_user_logged and user_input[0] in valid_commands[1:3]:
                print('Invalid Option: Not logged in.')

            elif user_input[0] == valid_commands[4]:
                print('Closing application.')
                s.close()
                break
         
            else:
                print('Invalid Command: Command not recognized.\n' +
                      'Please refer to help, by typing command: help')


main_loop()
