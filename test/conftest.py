
def pytest_addoption(parser):
    parser.addoption("--apikey", action="store",
                     help="Bittrex API key.")
    parser.addoption("--secret", action="store",
                     help="Bittrex API secret.")

def pytest_generate_tests(metafunc):

    if 'apikey' in metafunc.fixturenames:
        metafunc.parametrize('apikey', [metafunc.config.option.apikey])

    if 'secret' in metafunc.fixturenames:
        metafunc.parametrize('secret', [metafunc.config.option.secret])
