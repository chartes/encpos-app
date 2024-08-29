from csv import DictReader
import io
import json
import pprint
import re

import click
import requests

from api import create_app

clean_tags = re.compile('<.*?>')
body_tag = re.compile('<body(?:(?:.|\n)*?)>((?:.|\n)*?)</body>')

app = None


def remove_html_tags(text):
    return re.sub(clean_tags, ' ', text)


def extract_body(text):
    match = re.search(body_tag, text)
    if match:
        return match.group(1)
    return text


def load_elastic_conf(index_name, rebuild=False):
    url = '/'.join([app.config['ELASTICSEARCH_URL'], index_name])
    res = None
    try:
        if rebuild:
            res = requests.delete(url)
        with open(f'{app.config["ELASTICSEARCH_CONFIG_DIR"]}/_global.conf.json', 'r') as _global:
            global_settings = json.load(_global)

            with open(f'{app.config["ELASTICSEARCH_CONFIG_DIR"]}/{index_name}.conf.json', 'r') as f:
                payload = json.load(f)
                payload["settings"] = global_settings
                print("UPDATE INDEX CONFIGURATION:", url)
                res = requests.put(url, json=payload)
                assert str(res.status_code).startswith("20")

    except FileNotFoundError as e:
        print(str(e))
        print("conf not found", flush=True, end=" ")
    except Exception as e:
        print(res.text, str(e), flush=True, end=" ")
        raise e


def make_cli(env='dev'):
    """ Creates a Command Line Interface for everydays tasks

    :return: Click groum
    """

    @click.group()
    def cli():
        global app
        app = create_app(env)
        app.all_indexes = f"{app.config['DOCUMENT_INDEX']},{app.config['COLLECTION_INDEX']}"

    @click.command("search")
    @click.argument('query')
    @click.option('--indexes', required=False, default=None, help="index names separated by a comma")
    @click.option('-t', '--term', is_flag=True, help="use a term instead of a whole query")
    def search(query, indexes, term):
        """
        Perform a search using the provided query. Use --term or -t to simply search a term.
        """
        if term:
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "query_string": {
                                    "query": query,
                                }
                            }
                        ]
                    },
                }
            }
        else:
            body = query

        config = {"index": indexes if indexes else app.all_indexes, "body": body}

        result = app.elasticsearch.search(**config)
        print("\n", "=" * 12, " RESULT ", "=" * 12)
        pprint.pprint(result)

    @click.command("update-conf")
    @click.option('--indexes', default=None, help="index names separated by a comma")
    @click.option('--rebuild', is_flag=True, help="truncate the index before updating its configuration")
    def update_conf(indexes, rebuild):
        """
        Update the index configuration and mappings
        """
        indexes = indexes if indexes else app.all_indexes
        for name in indexes.split(','):
            load_elastic_conf(name, rebuild=rebuild)

    @click.command("delete")
    @click.option('--indexes', required=True, help="index names separated by a comma")
    def delete_indexes(indexes):
        """
        Delete the indexes
        """
        indexes = indexes if indexes else app.all_indexes
        for name in indexes.split(','):
            url = '/'.join([app.config['ELASTICSEARCH_URL'], name])
            res = None
            try:
                res = requests.delete(url)
            except Exception as e:
                print(res.text, str(e), flush=True, end=" ")
                raise e

    @click.command("index")
    @click.option('--years', required=True, default="all", help="1987-1999")
    def index(years):
        """
        Rebuild the elasticsearch indexes
        """

        # BUILD THE METADATA DICT FROM THE GITHUB TSV FILE
        response = requests.get(app.config["METADATA_FILE_URL"])
        metadata = {}
        reader = DictReader(io.StringIO(response.text), delimiter="\t")
        for row in reader:
            try:
                metadata[row["id"]] = {
                    "author_name": row["author_name"],
                    "author_firstname": row["author_firstname"],
                    "title_rich": row["title_rich"],
                    "promotion_year": int(row["promotion_year"]) if row["promotion_year"] else None,
                    "topic_notBefore": int(row["topic_notBefore"]) if row["topic_notBefore"] else None,
                    "topic_notAfter": int(row["topic_notAfter"]) if row["topic_notAfter"] else None,
                    "author_gender": int(row["author_gender"]) if row["author_gender"] else None,
                        # 1/2, verify that there is no other value
                    "author_is_enc_teacher": 1 if row["author_is_enc_teacher"]=="1" else None, 
                }
            except Exception as exc:
                print(f"ERROR while indexing {row['id']}, {exc}")

        _DTS_URL = app.config["DTS_URL"]

        # INDEXATION DES DOCUMENTS
        all_docs = []
        try:
            _index_name = app.config["DOCUMENT_INDEX"]
            if years == "all":
                years = app.config["ALL_YEARS"]
            start_year, end_year = (int(y) for y in years.split("-"))
            for year in range(start_year, end_year + 1):

                _ids = [
                    d
                    for d in metadata.keys()
                    if str(year) in d and "_PREV" not in d and "_NEXT" not in d
                ]

                for encpos_id in _ids:
                    response = requests.get(f"{_DTS_URL}/document?id={encpos_id}")
                    print(encpos_id, response.status_code)

                    content = extract_body(response.text)
                    content = remove_html_tags(content)
                    all_docs.append("\n".join([
                        json.dumps(
                            {"index": {"_index": _index_name, "_id": encpos_id}}
                        ),
                        json.dumps(
                            {"content": content, "metadata": metadata[encpos_id]}
                        )
                    ]))

            app.elasticsearch.bulk(body=all_docs, request_timeout=60*10)

        except Exception as e:
            print('Indexation error: ', str(e))

        # INDEXATION DES COLLECTIONS
        try:
            _index_name = app.config['COLLECTION_INDEX']
            # app.elasticsearch.index(index=_index_name, id=encpos_id,  body={})
        except Exception as e:
            print('Indexation error: ', str(e))

    cli.add_command(delete_indexes)
    cli.add_command(update_conf)
    cli.add_command(index)
    cli.add_command(search)
    return cli
