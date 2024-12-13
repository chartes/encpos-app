import os

basedir = os.path.abspath(os.path.dirname(__file__))


def parse_var_env(var_name):
    v = os.environ.get(var_name)
    if v == "True":
        v = True
    elif v == "False":
        v = False
    return v


class Config(object):
    ENV = 'production'
    DEBUG = parse_var_env('DEBUG')

    ELASTICSEARCH_URL = parse_var_env('ELASTICSEARCH_URL')
    DOCUMENT_INDEX = parse_var_env('DOCUMENT_INDEX')
    COLLECTION_INDEX = parse_var_env('COLLECTION_INDEX')

    ALL_YEARS = parse_var_env('ALL_YEARS')

    DTS_URL = parse_var_env('DTS_URL')
    METADATA_FILE_URL = parse_var_env('METADATA_FILE_URL')
    METADATA_FILE_INDEXABLE_COLUMNS = parse_var_env('METADATA_FILE_INDEXABLE_COLUMNS')

    API_VERSION = parse_var_env('API_VERSION')
    API_URL_PREFIX = parse_var_env('API_URL_PREFIX')

    SEARCH_RESULT_PER_PAGE = parse_var_env('SEARCH_RESULT_PER_PAGE')

    @staticmethod
    def init_app(app):
        pass


class LocalConfig(Config):
    ENV = 'development'


class StagingConfig(Config):
    ENV = 'development'


config = {
    "local": LocalConfig,
    "staging": StagingConfig,
    "prod": Config,
}
