"""Functions to send statistics to ONT."""
import configparser
import os
import platform
import socket
import uuid

import requests


ENDPOINT = 'https://ping-dev.oxfordnanoportal.com/epilaby'
CONTAINER_META = os.path.join(os.sep, 'epi2melabs', '.epi2melabsmeta')


def _send_ping(data, session, hostname=None, opsys=None):
    """Attempt to send a ping to home.

    :param data: a dictionary containing the data to send (should be
        json serializable).

    :returns: status code of HTTP request.
    """
    if not isinstance(session, uuid.UUID):
        raise ValueError('`session` should be a uuid.UUID object')
    ping_version = '1.1.0'
    if hostname is None:
        hostname = socket.gethostname()
    if opsys is None:
        opsys = platform.platform()
    ping = {
        "tracking_id": {"msg_id": str(uuid.uuid4()), "version": ping_version},
        "hostname": hostname, "os": opsys,
        "session": str(session)}
    ping.update(data)
    try:
        r = requests.post(ENDPOINT, json=ping)
    except Exception as e:
        print(e)
    return r.status_code


class Pingu(object):
    """Manage the sending of multiple pings."""

    def __init__(self, session=None):
        """Initialize pinger.

        :param session: a UUID session identifier
        """
        if session is None:
            session = uuid.uuid4()
        else:
            if not isinstance(session, uuid.UUID):
                raise ValueError('`session` should be a uuid.UUID object')
        self.session = session
        self.state = None
        self.hostname = None
        try:
            config = configparser.ConfigParser()
            config.read(CONTAINER_META)
            self.hostname = config['Host']['hostname']
            self.opsys = config['Host']['operating_system']
        except Exception:
            self.hostname = socket.gethostname()
            self.opsys = platform.platform()

    def send_container_ping(
            self, action, container_stats, image_name, message=None):
        """Ping a status message of a container.

        :param action: one of 'start', 'stop', or 'update'.
        :param container: the output of `container.stats(stream=False)`
        :param image_tag: the name of the image associated with the container.

        :returns: status code of HTTP request.
        """
        allowed_status = {"start", "stop", "update"}
        if action not in allowed_status:
            raise ValueError(
                "`action` was not an allowed value, got: '{}'".format(action))
        return _send_ping({
            "source": "container",
            "action": action,
            "container_data": container_stats,
            "image_data": image_name,
            "message": message},
            session=self.session, hostname=self.hostname, opsys=self.opsys)

    def send_notebook_ping(self, action, notebook, message=None):
        """Ping a message from a notebook.

        :param action: one of 'start', 'end', or 'update'.
        :param notebook: name of notebook.
        :param message: optional message (must be json serializable).
        """
        allowed_status = {"start", "stop", "update"}
        if action not in allowed_status:
            raise ValueError(
                "`action` was not an allowed value, got: '{}'".format(action))
        # check for spam
        if any((
                action == self.state,
                action == "stop" and self.state is None)):
            return
        self.state = action
        return _send_ping({
            "source": "notebook",
            "action": action,
            "notebook_name": notebook,
            "message": message},
            session=self.session, hostname=self.hostname, opsys=self.opsys)
