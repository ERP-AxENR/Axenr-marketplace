"""Example scenario for mock_api.py: a paged list of users and the creation of a project.

Copy it next to the connector, replace routes and data with what the third-party doc shows, and keep
the doc URL on each route. `paginate` is injected by mock_api.py.
"""

# Data sets, switched with POST /__admin/scenario {"name": "edge"}.
SCENARIOS = {
    "base": {"users": [{"id": 1, "firstName": "Ana", "lastName": "Test", "establishmentId": 10},
                       {"id": 2, "firstName": "Ben", "lastName": "Test", "establishmentId": 11}]},
    # edge cases the connector must survive: missing field, unknown establishment
    "edge": {"users": [{"id": 3, "firstName": "Cy", "lastName": None, "establishmentId": 99}]},
}
PROJECTS = {}


def data(req):
    return SCENARIOS[req.scenario]


# doc: https://example.invalid/docs/users#list  (envelope {"data": {"items": [...]}}, paging offset/limit)
def list_users(req):
    return 200, {"data": {"items": paginate(data(req)["users"], req)}}


# doc: https://example.invalid/docs/projects#create  (409 when the code already exists)
def create_project(req):
    code = (req.json or {}).get("code")
    if not code:
        return 400, {"detail": "code is required"}
    if code in PROJECTS:
        return 409, {"detail": f"project {code} already exists", "id": PROJECTS[code]}
    PROJECTS[code] = 1000 + len(PROJECTS)
    return 201, {"data": {"id": PROJECTS[code]}}


ROUTES = [
    ("GET", r"/api/v1/users", list_users),
    ("POST", r"/api/v1/projects", create_project),
]
