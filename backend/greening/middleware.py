from django.db import connection


class QueryMonitor:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        for query in connection.queries:
            sql = f"\033[1;31m[TIME: {query['time']} sec]\033[0m {query['sql']}"
            print(sql, "\n")  # noqa:T201

        print(f"\033[1;32m[TOTAL QUERIES: {len(connection.queries)}]\033[0m")  # noqa:T201
        return response
