"""Radius backend URL config."""
from django.conf.urls.defaults import url, patterns
from nav.web.radius.views import index, log_search, account_charts, account_search, log_detail, account_detail

urlpatterns = patterns('nav.web.radius.views',
    url(r'^$', index, name='radius-index'),
    url(r'^logsearch$', log_search, name='radius-log_search'),
    url(r'^logdetail$', log_detail, name='radius-log_detail'),
    url(r'^acctdetail$', account_detail, name='radius-account_detail'),
    url(r'^acctcharts$', account_charts, name='radius-account_charts'),
    url(r'^acctsearch$', account_search, name='radius-account_search')
)
