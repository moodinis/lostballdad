"""Submit perfectgame.org/Schedule's own filter form (year, month, event type) like a browser -> HTML result pages."""
import html, json, re, subprocess, sys, urllib.parse
U = 'https://www.perfectgame.org/Schedule/Default.aspx'
JAR = 'pg.jar'
P = 'ctl00$ctl00$ContentTopLevel$ContentPlaceHolder1$'
CS = 'ctl00_ctl00_ContentTopLevel_ContentPlaceHolder1_'
MONTHS = ['Next 3 Months', 'January', 'February', 'March', 'April', 'May', 'June', 'July']


def curl(data=None):
    cmd = ['curl', '-s', '-L', '--max-time', '60', '-b', JAR, '-c', JAR, U]
    if data:
        cmd += ['--data-binary', '@-']
    return subprocess.run(cmd, input=data, capture_output=True, text=True).stdout


def hidden(h):
    return {html.unescape(n): html.unescape(v) for n, v in
            re.findall(r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', h)}


def state(text, value, idx):
    return json.dumps({'enabled': True, 'logEntries': [], 'selectedValue': value, 'selectedText': text, 'selectedIndex': idx})


def search(month_idx, year='2027', etype=('Baseball Tournament', '3,6,7,12,13,14', 1)):
    open(JAR, 'w').close()
    h = curl()
    f = hidden(h)
    f.update({'__EVENTTARGET': P + 'lbFilter', '__EVENTARGUMENT': '',
              CS + 'ddlYear_ClientState': state(year, year, 2),
              CS + 'ddlMonth_ClientState': state(MONTHS[month_idx], str(month_idx), month_idx),
              CS + 'ddlState_ClientState': state('All States', '0', 0),
              CS + 'rddEventTypes_ClientState': state(*etype)})
    return curl(urllib.parse.urlencode(f))


if __name__ == '__main__':
    h = search(int(sys.argv[1]))
    open(f'm{sys.argv[1]}.html', 'w').write(h)
    print(len(h), len(set(re.findall(r'event=(\d+)', h))), 'event ids')
