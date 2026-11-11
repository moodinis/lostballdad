"""PG tournaments Jan-Jul 2027 via perfectgame.org/Schedule's filter form + grid pager (browser-equivalent postbacks).
Parses the per-tournament group headers -> pg_groups.json"""
import html, json, re, time, urllib.parse
from pg_sched import curl, hidden, search, state, P, CS, MONTHS
t = lambda s: re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def parse(h):
    g = h[h.find('rgSchedule'):]
    out = []
    for x in re.findall(r'<tr class="rgGroupHeader"[^>]*>(.*?)</tr>\s*(?=<tr)', g, re.S):
        m = re.search(r"GroupedEvents\.aspx\?gid=(\d+)'[^>]*><span[^>]*>(.*?)</span>", x, re.S)
        if not m:
            continue
        dates = re.search(r"width:75px' class='d-none d-sm-table-cell'>(.*?)</td>", x)
        ages = re.search(r"<div class='col-md-2 col-xs-4'><span[^>]*>(.*?)</span>", x)
        loc = re.search(r"<div class='col-md-2'><div class='clearfix'></div><span style='display:inline-block'>(.*?)</span>", x)
        typ = re.search(r"<span style='display:inline-block'>&nbsp;(.*?)</span>", x)
        out.append(dict(gid=m[1], name=t(m[2]), dates=t(dates[1]) if dates else '', ages=t(ages[1]) if ages else '',
                        loc=t(loc[1]) if loc else '', type=t(typ[1]) if typ else ''))
    pages = re.findall(r"href=\"javascript:__doPostBack\(&#39;(%srgSchedule\$ctl00\$ctl03\$ctl01\$ctl\d+)&#39;,&#39;&#39;\)\"[^>]*><span>(\d+)</span>" % re.escape(P), h)
    total = re.search(r'(\d+)</strong> items in <strong>(\d+)</strong> pages', h) or re.search(r'(\d+) items in (\d+) pages', t(h[h.find('rgPager'):h.find('rgPager') + 3000]))
    return out, dict((int(n), tgt) for tgt, n in pages), total


if __name__ == '__main__':
  groups = {}
  for mi in range(1, 8):
      h = search(mi)
      rows, pages, total = parse(h)
      npages = int(total[2]) if total else 1
      for r in rows: groups[r['gid']] = r
      for p in range(2, npages + 1):
          f = hidden(h)
          f.update({'__EVENTTARGET': P + 'rgSchedule$ctl00$ctl03$ctl01$ctl12', '__EVENTARGUMENT': '',   # "Next Page"
                    CS + 'ddlYear_ClientState': state('2027', '2027', 2),
                    CS + 'ddlMonth_ClientState': state(MONTHS[mi], str(mi), mi),
                    CS + 'ddlState_ClientState': state('All States', '0', 0),
                    CS + 'rddEventTypes_ClientState': state('Baseball Tournament', '3,6,7,12,13,14', 1)})
          time.sleep(1.5)
          h = curl(urllib.parse.urlencode(f))
          rows, _, _ = parse(h)
          cur = re.search(r'class="rgCurrentPage"[^>]*>(\d+)<', h)
          print('  page', cur[1] if cur else '?', len(rows), 'groups')
          for r in rows: groups[r['gid']] = r
      print(MONTHS[mi], 'pages', npages, 'total groups so far', len(groups))
      time.sleep(2)
  json.dump(list(groups.values()), open('pg_groups.json', 'w'), indent=0)
