from aiohttp import web
from proxy import ProxyManager


with open('proxy_list.txt') as f:
    s = f.read()
    proxy_list = s.split()

proxy_managers = {
    'avito.ru': ProxyManager(list(proxy_list), 'avito.ru'),
    'auto.ru': ProxyManager(list(proxy_list), 'auto.ru'),
    'drom.ru': ProxyManager(list(proxy_list), 'drom.ru'),
    'youla.ru': ProxyManager(list(proxy_list), 'youla.ru'),
    None: ProxyManager(list(proxy_list), 'default')
}

routes = web.RouteTableDef()


@routes.get('/')
async def index(request):
    source = request.query.get('source')
    if source and source in proxy_managers:
        proxies_stat = proxy_managers[source].statistics()
    else:
        source = None
        proxies_stat = proxy_managers[None].statistics()
    stat_list = [f'source {source}', 'address\t\tbad_count']
    for addr, bad_req_n in proxies_stat.items():
        stat_list.append(f'{addr}\t\t{bad_req_n}')
    return web.Response(text='\n'.join(stat_list))


@routes.get('/bad_proxy')
async def bad_proxy(request):
    addr = request.query.get('proxy')
    source = request.query.get('source')
    status = 'FAIL'
    if addr:
        proxy_managers[source].cold_proxy(addr)
        status = 'OK'
    return web.json_response({'status': status})


@routes.get('/get_proxy')
async def get_proxy(request):
    args = request.query
    response_data = {'status': 'FAIL'}
    proxy = proxy_managers[args.get('source')].get_proxy()
    if proxy:
        response_data['address'] = str(proxy)
        response_data['type'] = proxy.proxy_type
        response_data['status'] = 'OK'
        response_data['bad_request'] = proxy.bad_request

    return web.json_response(response_data)


@routes.post('/upload_proxy')
async def upload_proxy(request):
    resp_data = {'status': 'FAIL'}
    data = await request.json()
    if data.get('proxies'):
        proxy_managers[data.get('source')].add_proxies(data['proxies'])
        resp_data['status'] = 'OK'
    return web.json_response(resp_data)


@routes.post('/action/{action}')
async def action(request):
    actions = {
            'clear': clear,
            'load': lambda req: [pm.load() for pm in proxy_managers.values()],
            'save': lambda req: [pm.save() for pm in proxy_managers.values()]
        }
    resp_data = {'status': 'FAIL'}
    act = request.match_info['action']
    if act in actions:
        actions[act](request)
        resp_data['status'] = 'OK'
    return web.json_response(resp_data)


async def clear(request):
    data = await request.json()
    proxies = data.get('proxies')
    source = data.get('source')

    if source.lower() == 'all':
        sources = proxy_managers.keys()
    else:
        sources = [source]

    for source in sources:
        proxy_managers[source].clear(proxies)
        proxy_managers[source].save()


if __name__ == '__main__':
    app = web.Application()
    app.add_routes(routes)
    web.run_app(app, host='0.0.0.0', port=4000)
