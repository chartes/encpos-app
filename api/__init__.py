from elasticsearch import Elasticsearch
from flask import Flask, Blueprint
from dotenv import load_dotenv

api_bp = Blueprint('api_bp', __name__)


def create_app(config_name: str):
    """ Create the application """
    app = Flask(__name__)
    if not isinstance(config_name, str):
        from config import config
        app.config.from_object(config)
    else:
        print("Load environment variables for config '%s'" % config_name)
        # It is important to load the .env file before parsing the config file
        import os
        dir_path = os.path.dirname(os.path.realpath(__file__))
        env_filename = os.path.join(dir_path, '..', '%s.env' % config_name)
        load_dotenv(env_filename, verbose=True)
        from config import config
        app.config.from_object(config[config_name])

    app.elasticsearch = Elasticsearch([app.config['ELASTICSEARCH_URL']]) if app.config['ELASTICSEARCH_URL'] else None

    with app.app_context():
        from api.search import register_search_endpoint

        def compose_result(search_result):
            results = []
            for h in search_result['hits']['hits']:
                fields = h.get('_source')
                fields.pop("content")
                fields['dts_url'] = f"{app.config['DTS_URL']}/document?id={h['_id']}"
                results.append({
                    "id": h['_id'],
                    "score": h['_score'],
                    "fields": fields,
                    "highlight": h.get('highlight')
                })
            return results

        register_search_endpoint(api_bp, "1.0", compose_result)

        app.register_blueprint(api_bp)

    config[config_name].init_app(app)

    return app
