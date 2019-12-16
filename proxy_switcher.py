from flask import Flask
from flask import request

from proxy import ProxyManager

app = Flask(__name__)

with open('proxy_list.txt') as f:
    s = f.read()
    proxy_list = s.split()

proxy_managers = {
    'avito.ru': ProxyManager(list(proxy_list), 'avito.ru'),
    'auto.ru': ProxyManager(list(proxy_list), 'auto.ru'),
    'youla.ru': ProxyManager(list(proxy_list), 'youla.ru'),
    None: ProxyManager(list(proxy_list), 'default')
}


@app.route('/bad_proxy')
def bad_proxy():
    proxy = request.args.get('proxy')
    source = request.args.get('source')
    if proxy:
        proxy_managers[source].cold_proxy(proxy)
        return 'OK'
    return 'FAIL'


@app.route('/get_proxy')
def get_proxy():
    args = request.args
    proxy = proxy_managers[args.get('source')].get_proxy()
    if proxy:
        return str(proxy)
    return 'FAIL'


@app.route('/config', methods=['GET', 'POST'])
def config():
    if request.method == 'POST':
        data = request.json
        if data.get('source'):
            print('config', data)
            return 'OK'
    return 'FAIL'


@app.route('/upload_proxy')
def upload_proxy():
    if request.method == 'POST':
        data = request.json
        if data.get('proxies'):
            proxy_managers[data.get('source')].add_proxies(data['proxies'])


@app.route('/action/<string:act>')
def action(act):
    actions = {
        'clear': clear,
        'load': lambda: [pm.load() for pm in proxy_managers.values()],
        'save': lambda: [pm.save() for pm in proxy_managers.values()]
    }
    if act in actions:
        actions[act]()
        return 'OK'
    return 'FAIL ACTION'


def clear():
    if request.method == 'POST':
        data = request.json
        proxies = data.get('proxies')
        source = data.get('source')

    else:
        source = request.args.get('source')
        proxies = request.args.get('proxies')

    if source.lower() == 'all':
        sources = proxy_managers.keys()
    else:
        sources = [source]

    for source in sources:
        proxy_managers[source].clear(proxies)
        proxy_managers[source].save()


if __name__ == '__main__':
    # app.debug = True
    app.run(host="0.0.0.0", port=4000)
