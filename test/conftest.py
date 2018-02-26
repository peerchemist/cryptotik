
def pytest_addoption(parser):
    parser.addoption("--apikey", action="store",
                     help="API key.")
    parser.addoption("--secret", action="store",
                     help="API secret.")
    parser.addoption("--id", action="store",
                     help="API user id.")
    parser.addoption("--exchange", action="store",
                     help="Class name for exchange module")


def pytest_generate_tests(metafunc):

    if 'apikey' in metafunc.fixturenames:
        metafunc.parametrize('apikey', [metafunc.config.option.apikey])

    if 'secret' in metafunc.fixturenames:
        metafunc.parametrize('secret', [metafunc.config.option.secret])

    if 'id' in metafunc.fixturenames:
            metafunc.parametrize('id', [metafunc.config.option.secret])