"""PG tournaments Jan-Jul 2027, one Schedule filter submission per (month, state) so each result fits on one grid page.
Each request is the page's own form post (change dropdowns, click Filter). -> pg_groups_all.json, pg_overflow.json"""
import html, json, re, time, urllib.parse
from pg_sched import curl, state, P, CS, MONTHS, JAR
from pg_all import parse
STATES = ('AK AL AR AZ CA CO CT DE FL GA HI IA IL IN KS KY LA MA MD ME MI MN MO MS NC ND NE NH NJ NM NV NY OH OK OR PA '
          'RI SC SD TN TX UT VA VT WA WI WV').split()
ITEMS = [None, 'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', 'IA', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD',
         'ME', 'MI', 'MN', 'MO', 'MS', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'PR', 'RI', 'SC',
         'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV']


def fields(h):
    f = {}
    for tag in re.findall(r'<input[^>]*>', h):
        n = re.search(r'name="([^"]+)"', tag); v = re.search(r'value="([^"]*)"', tag); ty = re.search(r'type="([^"]+)"', tag)
        if n and (not ty or ty[1] in ('hidden', 'text')):
            f[html.unescape(n[1])] = html.unescape(v[1]) if v else ''
    return f


if __name__ == '__main__':
    open(JAR, 'w').close()
    h = curl()
    groups, overflow, n = {}, [], 0
    for mi in range(1, 8):
        for st in STATES:
            f = fields(h)
            f = {k: v for k, v in f.items() if '$rgSchedule$' not in k}     # drop previous result rows
            f.update({'__EVENTTARGET': P + 'lbFilter', '__EVENTARGUMENT': '',
                      CS + 'ddlYear_ClientState': state('2027', '2027', 2),
                      CS + 'ddlMonth_ClientState': state(MONTHS[mi], str(mi), mi),
                      CS + 'ddlState_ClientState': state(st, f'{st}-1', ITEMS.index(st)),
                      CS + 'rddEventTypes_ClientState': state('Baseball Tournament', '3,6,7,12,13,14', 1)})
            h2 = curl(urllib.parse.urlencode(f))
            n += 1
            if 'rgSchedule' not in h2 or '__VIEWSTATE' not in h2:
                print('bad response', mi, st, len(h2)); time.sleep(10); continue
            h = h2
            rows, _, total = parse(h)
            for r in rows:
                r['state_q'] = st
                groups[r['gid']] = r
            if total and int(total[2]) > 1:
                overflow.append((mi, st, total[0]))
            time.sleep(1.2)
        print(MONTHS[mi], 'requests', n, 'groups', len(groups), 'overflow', overflow, flush=True)
        json.dump(list(groups.values()), open('pg_groups_all.json', 'w'))
    json.dump(overflow, open('pg_overflow.json', 'w'))
    print('done', len(groups))
