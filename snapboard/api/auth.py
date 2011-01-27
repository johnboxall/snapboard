from django.contrib.auth import authenticate
from piston.authentication import HttpBasicAuthentication


def staff_authenticate(username, password):
    """
    If the given credentials are valid, return a User object.

    """
    user = authenticate(username=username, password=password)
    return (user is not None and user.is_staff and user) or None


class StaffHttpBasicAuthentication(HttpBasicAuthentication):
    def __init__(self, auth_func=staff_authenticate, realm='API'):
        super(StaffHttpBasicAuthentication, self).__init__(auth_func=auth_func, 
            realm=realm)