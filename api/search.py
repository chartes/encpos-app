import json
import pprint
import time
from typing import Callable
from flask import Response, request, current_app


def parse_range_parameter():
    _range = None
    _parsed_ranges = []
    for f in request.args.keys():
        if f.startswith('range[') and f.endswith(']'):
            key, ops = (f[len('range['):-1], [op.split(':') for op in request.args[f].split(",")])
            print(key, ops)
            _range = {key: {}}
            for op, value in ops:
                _range[key][op] = value
            _parsed_ranges.append(_range)
    return _parsed_ranges


def register_search_endpoint(bp, api_version="1.0", compose_result_func: Callable[[str], list] = lambda s: []):
    def api_search_endpoint():
        start_time: float = time.time()
        # PARAMETERS
        index: str = request.args.get("index", None)
        query: str = request.args.get("query", None)

        # eg. range[year]=gte:1871,lte:1899
        ranges: list[dict] = parse_range_parameter()

        groupby_field: str = request.args.get("groupby[field]", None)
        groupby_after: str = request.args.get("groupby[after-page]", None)
        groupby_with_ids: int = request.args.get("groupby[with-ids]", 10000) or 10000

        if query is None:
            return Response(status=400)

        # if request has pagination parameters
        # add links to the top-level object
        if 'page[number]' in request.args or 'page[size]' in request.args:
            num_page = int(request.args.get('page[number]', 1))
            page_size = min(
                int(current_app.config["SEARCH_RESULT_PER_PAGE"]) + num_page,
                int(request.args.get('page[size]'))
            )
        else:
            num_page = 1
            page_size = int(current_app.config["SEARCH_RESULT_PER_PAGE"])

        # Search, retrieve, filter, sort and paginate objs
        # eg. &sort=-year
        sort_criteriae: list[dict] = []
        if "sort" in request.args:
            sort_criteriae = []
            for criteria in request.args["sort"].split(','):
                if criteria.startswith('-'):
                    sort_order = "desc"
                    criteria = criteria[1:]
                else:
                    sort_order = "asc"
                # criteria = criteria.replace("-", "_")
                sort_criteriae.append({criteria: {"order": sort_order}})

        r = {}
        if hasattr(current_app, 'elasticsearch'):
            body = {
                "query": {
                    "bool": {
                        "must": [
                            {
                                "query_string": {
                                    "query": query,
                                    "default_operator": "AND"
                                }
                            }
                        ],
                        "should": [
                            {
                            "bool": {
                                "must_not": [
                                        {
                                            "exists": {
                                                "field": "metadata.topic_notBefore",
                                            }
                                        },
                                        {
                                            "exists": {
                                                "field": "metadata.topic_notAfter"
                                            }
                                        }
                                    ]
                                }
                            }
                        ],
                    },
                },
                "highlight": {
                    "type": "fvh",
                    "fields": {
                        "content": {}
                    },
                    "number_of_fragments": 100,
                    "options": {"return_offsets": True}
                },
                "aggregations": {

                },
                "sort": [
                    #  {"creation": {"order": "desc"}}
                    *sort_criteriae
                ]
            }

            if ranges:
                for r in ranges:
                    key = [k for k in r.keys()][0]
                    if key.startswith("metadata.topic_"):
                        body["query"]["bool"]["should"].append({"range": r})
                    else:
                        body["query"]["bool"]["must"].append({"range": r})

            if groupby_field is not None:
                body["aggregations"] = {
                    "items": {
                        "composite": {
                            "sources": [
                                {
                                    groupby_field: {
                                        "terms": {
                                            "field": groupby_field,
                                        },
                                    }
                                }
                            ],
                            "size": page_size,
                        }
                    },
                    "total_count": {
                        "cardinality": {
                            "field": "_id"
                        }
                    },
                    "bucket_count": {
                        "cardinality": {
                            "field": groupby_field
                        },
                    },
                }
                body["size"] = 0

                sort_criteriae.reverse()
                #for crit in sort_criteriae:
                #    for crit_name, crit_order in crit.items():
                #        source = {
                #            crit_name: {
                #                "terms": {
                #                    "field": crit_name,
                #                    **crit_order},
                #            }
                #        }
                #        body["aggregations"]["items"]["composite"]["sources"].insert(0, source)

                if groupby_after is not None:
                    sources_keys = [list(s.keys())[0] for s in body["aggregations"]["items"]["composite"]["sources"]]
                    body["aggregations"]["items"]["composite"]["after"] = {key: value for key, value in
                                                                           zip(sources_keys, groupby_after.split(','))}
                    print(sources_keys, groupby_after,
                          {key: value for key, value in zip(sources_keys, groupby_after.split(','))})

            # if page_size is not None:
            # if groupby_field is not None:
            page: int = 0 if groupby_field is not None else num_page - 1

            body["from"]: int = page * page_size
            body["size"]: int = page_size
            # else:
            #    body["from"] = 0 * page_size
            #    body["size"] = page_size
            # print("WARNING: /!\ for debug purposes the query size is limited to", body["size"])
            try:
                if index is None or len(index) == 0:
                    index = current_app.config["DOCUMENT_INDEX"]

                pprint.pprint(body)
                # perform the search
                search_result = current_app.elasticsearch.search(index=index, doc_type="_doc", body=body)
                #pprint.pprint(search_result['aggregations'])
                results: list = compose_result_func(search_result)
                count: int = search_result['hits']['total']

                # print(body, len(results), search['hits']['total'], index)
                # pprint.pprint(search)
                if 'aggregations' in search_result:
                    after_key = None
                    buckets = search_result["aggregations"]["items"]["buckets"]

                    # grab the after_key returned by ES for future queries
                    if "after_key" in search_result["aggregations"]["items"]:
                        after_key = search_result["aggregations"]["items"]["after_key"]
                    print("aggregations: {0} buckets; after_key: {1}".format(len(buckets), after_key))
                    # pprint.pprint(buckets)
                    total_count = search_result["aggregations"]["total_count"]["value"]
                    bucket_count = search_result["aggregations"]["bucket_count"]["value"]

                    if groupby_with_ids is not False and len(buckets) > 0:
                        try:
                            size_limit = int(groupby_with_ids)
                        except Exception as e:
                            print(str(e))
                            print("Size limit reached in aggregation ids fetch:", groupby_with_ids)
                            size_limit = 10000

                        for bucket in buckets:
                            ids_query = {
                                "query": {
                                    "query_string": {
                                        "query": f"({query}) AND {groupby_field}:{bucket['key'][groupby_field]}"
                                    }
                                },
                                "size": size_limit
                            }
                            ids_result = current_app.elasticsearch.search(index=index, doc_type="_doc", body=ids_query)
                            bucket['_ids'] = sorted([h["_id"] for h in ids_result['hits']["hits"]])

                    r = {
                        #"data": results,
                        "buckets": buckets,
                        "after_key": after_key,
                        "total-count": total_count,
                        "bucket-count": bucket_count
                    }
                else:
                    r = {
                        "data": results,
                        "total-count": count
                    }

                r["duration"] = float('%.4f' % (time.time() - start_time))

            except Exception as e:
                return Response(str(e), status=400)

        return Response(
            json.dumps(r, indent=2, ensure_ascii=False),
            status=200,
            content_type="application/json; charset=utf-8",
            headers={
                "Access-Control-Allow-Origin": "*",
                # "Access-Control-Allow-Credentials": "true"
            }
        )

    # register the endpoint route
    bp.add_url_rule(f"/api/{api_version}/search", endpoint=api_search_endpoint.__name__, view_func=api_search_endpoint)
