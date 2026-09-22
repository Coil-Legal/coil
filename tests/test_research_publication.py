"""Publication coverage must survive the real transport and fallback reader paths."""
import re
from html import unescape
from urllib.parse import urlencode

from tests.test_zip_import_review import app, client
from app.blueprints import _courtlistener as cl


def test_search_includes_unpublished_on_both_pages(app, client, monkeypatch):
    cl.clear_cache()
    seen=[]
    def get(url, params=None, **kwargs):
        seen.append(dict(params))
        second='cursor' in params
        inclusive=params.get('stat_Published')=='on' and params.get('stat_Unpublished')=='on'
        class Response:
            status_code=200
            def json(self):
                rows=[] if not inclusive else [{'cluster_id':202 if second else 101,
                    'caseName':'Unpublished fixture' if second else 'Published fixture',
                    'status':'Unpublished' if second else 'Published',
                    'opinions':[{'id':202 if second else 101}]}]
                return {'count':2 if inclusive else 0, 'results':rows,
                    'next':None if second or not inclusive else cl.BASE+'/search/?'+urlencode({'cursor':'second=='})}
        return Response()
    monkeypatch.setattr(cl.requests, 'get', get)
    try:
        first=client.get('/research?q=publication-fixture&court=ca9')
        assert b'Published fixture' in first.data
        href=unescape(re.search(r'href="([^"]+)">Next page</a>', first.get_data(as_text=True)).group(1))
        second=client.get(href)
        assert b'Unpublished fixture' in second.data
        assert b'<span class="badge draft">Unpublished</span>' in second.data
        assert len(seen)==2 and all(p['court']=='ca9' for p in seen)
        assert seen[-1]['cursor']=='second=='
    finally:
        cl.clear_cache()


def test_unpublished_metadata_available_when_full_text_requires_token(app, client, monkeypatch):
    cl.clear_cache()
    def get(url, params=None, **kwargs):
        search=url.endswith('/search/')
        class Response:
            status_code=200 if search else 401
            def json(self):
                if not search:return {'detail':'Authentication required'}
                assert params['q']=='cluster_id:202'
                visible=params.get('stat_Published')=='on' and params.get('stat_Unpublished')=='on'
                return {'results':[{'cluster_id':202,'caseName':'Unpublished fallback fixture',
                    'status':'Unpublished','opinions':[{'id':202,'snippet':'Synthetic fallback excerpt'}]}] if visible else []}
        return Response()
    monkeypatch.setattr(cl.requests, 'get', get)
    try:
        response=client.get('/research/opinion/202?cluster_id=202')
        assert response.status_code==200
        assert b'Unpublished fallback fixture' in response.data
        assert b'Synthetic fallback excerpt' in response.data
        assert b'Full opinion text needs a CourtListener token' in response.data
        assert b'<dd>Unpublished</dd>' in response.data
    finally:
        cl.clear_cache()
