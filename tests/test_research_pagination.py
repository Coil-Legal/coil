"""Exercise a provider cursor through HTML, Flask and back to the HTTP client."""
import re
from html import unescape
from urllib.parse import parse_qs, urlencode, urlsplit
import pytest
from tests.test_zip_import_review import app, client
from app.blueprints import _courtlistener as cl


@pytest.mark.parametrize('cursor',['position==','offset+/with space%2F'])
def test_encoded_cursor_round_trip_preserves_filters(app,client,monkeypatch,cursor):
    cl.clear_cache()
    filters={'q':'Miranda','court':'ca9','filed_after':'2024-01-01','filed_before':'2024-12-31','order_by':'dateFiled desc'}
    requests=[]
    def get(url,params=None,**kwargs):
        requests.append(dict(params))
        page2='cursor' in params
        if page2:assert params['cursor']==cursor
        for key,value in filters.items():assert params[key]==value
        class Response:
            status_code=200
            def json(self):
                return {'count':2,'next':None if page2 else cl.BASE+'/search/?'+urlencode({'q':'Miranda','cursor':cursor}),
                        'results':[{'cluster_id':202 if page2 else 101,'caseName':'Second page example' if page2 else 'First page example',
                                    'dateFiled':'2024-05-01' if page2 else '2024-06-01','court_id':'ca9',
                                    'opinions':[{'id':202 if page2 else 101}]}]}
        return Response()
    monkeypatch.setattr(cl.requests,'get',get)
    try:
        first=client.get('/research?'+urlencode(filters))
        assert first.status_code==200 and b'First page example' in first.data
        href=unescape(re.search(r'href="([^"]+)">Next page</a>',first.get_data(as_text=True)).group(1))
        query=parse_qs(urlsplit(href).query)
        assert query['cursor']==[cursor]
        second=client.get(href)
        assert second.status_code==200 and b'Second page example' in second.data
        assert b'First page example' not in second.data and b'Next page</a>' not in second.data
        assert len(requests)==2 and requests[-1]['cursor']==cursor
    finally:cl.clear_cache()


@pytest.mark.parametrize('url',['',None,'http://[invalid','https://www.courtlistener.com/api/rest/v4/search/?q=Miranda'])
def test_absent_cursor_means_no_next_page(url):
    assert cl._cursor_from(url)==''


def test_decodes_only_query_cursor_once():
    assert cl._cursor_from('https://www.courtlistener.com/?q=x%2By&cursor=abc%252F%2B%3D#cursor=wrong')=='abc%2F+='
