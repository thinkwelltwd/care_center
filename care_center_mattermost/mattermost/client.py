# taken / modified from https://github.com/Vaelor/python-mattermost-driver/blob/master/src/mattermostdriver/client.py
import logging
import requests
import json
import urllib3
from requests.exceptions import HTTPError

from .exceptions import (
    InvalidOrMissingParameters,
    NoAccessTokenProvided,
    NotEnoughPermissions,
    ContentTooLarge,
    FeatureDisabled,
)

urllib3.disable_warnings()
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class Client:

    def __init__(self, url, port, token):
        if port == 443:
            uport = ''
        else:
            uport = ':%s' % port
        self._url = '{url}{port}/api/v4'.format(url=url, port=uport)
        self._token = token
        self._cookies = None
        self._userid = ''
        self._username = ''
        self._verify = False

    @property
    def userid(self):
        """
        :return: The user id of the logged in user
        """
        return self._userid

    @userid.setter
    def userid(self, user_id):
        self._userid = user_id

    @property
    def username(self):
        """
        :return: The username of the logged in user. If none, returns an emtpy string.
        """
        return self._username

    @username.setter
    def username(self, username):
        self._username = username

    @property
    def url(self):
        return self._url

    @property
    def cookies(self):
        """
        :return: The cookie given on login
        """
        return self._cookies

    @cookies.setter
    def cookies(self, cookies):
        self._cookies = cookies

    @property
    def token(self):
        """
        :return: The token for the login
        """
        return self._token

    @token.setter
    def token(self, t):
        self._token = t

    def auth_header(self):
        if self._token == '':
            return {}
        return {"Authorization": "Bearer {token:s}".format(token=self._token)}

    def make_request(self, method, endpoint, options=None, params=None, data=None, files=None):
        if options is None:
            options = {}
        if params is None:
            params = {}
        if data is None:
            data = {}
        method = method.lower()
        request = requests.get
        if method == 'post':
            request = requests.post
        elif method == 'put':
            request = requests.put
        elif method == 'delete':
            request = requests.delete

        response = request(
            self.url + endpoint,
            headers=self.auth_header(),
            verify=self._verify,
            json=options,
            params=params,
            data=json.dumps(data),
            files=files,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            data = e.response.json()
            if data['status_code'] == 400:
                raise InvalidOrMissingParameters(data['message'])
            elif data['status_code'] == 401:
                raise NoAccessTokenProvided(data['message'])
            elif data['status_code'] == 403:
                raise NotEnoughPermissions(data['message'])
            elif data['status_code'] == 413:
                raise ContentTooLarge(data['message'])
            elif data['status_code'] == 501:
                raise FeatureDisabled(data['message'])
            else:
                raise

        log.debug(response.json())
        return response

    def get(self, endpoint, options=None, params=None):
        return self.make_request('get', endpoint, options=options, params=params).json()

    def post(self, endpoint, options=None, params=None, data=None, files=None):
        return self.make_request(
            'post',
            endpoint,
            options=options,
            params=params,
            data=data,
            files=files,
        ).json()

    def put(self, endpoint, options=None, params=None, data=None):
        return self.make_request(
            'put',
            endpoint,
            options=options,
            params=params,
            data=data,
        ).json()

    def delete(self, endpoint, options=None, params=None, data=None):
        return self.make_request(
            'delete',
            endpoint,
            options=options,
            params=params,
            data=data,
        ).json()

    # -------------------------------------------------------------------------------------
    # Wrapper / helper methods
    # -------------------------------------------------------------------------------------
    def get_user(self, user):
        try:
            return self.get('/users/username/%s' % user)
        except HTTPError:
            log.error('Unable to get Mattermost user with username %s' % user)
            return None

    def get_user_by_email(self, email):
        try:
            return self.get('/users/email/%s' % email)
        except HTTPError:
            log.error('Unable to get Mattermost user with email %s' % email)
            return None

    def get_team(self, team):
        try:
            return self.get('/teams/name/%s' % team)
        except HTTPError:
            log.error('Unable to get Mattermost team %s' % team)
            return None

    def get_channel(self, team, channel):
        team = self.get_team(team)
        if not team:
            return None
        try:
            return self.get('/teams/%s/channels/name/%s' % (team['id'], channel))
        except HTTPError:
            log.error('Unable to get Mattermost channel %s' % channel)
            return None

    def create_direct_channel(self, email1, email2):
        user1 = self.get_user_by_email(email1)
        user2 = self.get_user_by_email(email2)

        if not all([user1, user2]):
            return None
        try:
            return self.post('/channels/direct', data=[user1['id'], user2['id']])
        except HTTPError:
            log.error('Unable to create direct channel between %s and %s' % (email1, email2))
            return None

    def send_message(self, sender, recipient, message):
        """
        Send message to User. Both sender and recipient must
        be users active on the Mattermost server.

        :param sender: Sending User's email address
        :@param recipient: Recipient's email address
        """

        channel = self.create_direct_channel(sender, recipient)
        if not channel:
            return None

        return self.post('/posts', data={'channel_id': channel['id'], 'message': message})
