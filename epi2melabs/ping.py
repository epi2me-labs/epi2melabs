"""Functions to send statistics to ONT."""
import platform
import socket
import uuid

import requests


ENDPOINT = 'https://ping.oxfordnanoportal.com/epilaby'


def _send_ping(data, session):
    """Attempt to send a ping to home.

    :param data: a dictionary containing the data to send (should be
        json serializable).

    :returns: status code of HTTP request.
    """
    if not isinstance(session, uuid.UUID):
        raise ValueError('`session` should be a uuid.UUID object')
    ping_version = '1.0.0'
    ping = {
        "tracking_id": {"msg_id": str(uuid.uuid4()), "version": ping_version},
        "hostname": socket.gethostname(), "os": platform.platform(),
        "session": str(session)}
    ping.update(data)
    try:
        r = requests.post(ENDPOINT, json=ping)
    except Exception as e:
        pass
    return r.status_code


class Pingu(object):
    """Manage the sending of multiple pings."""

    def __init__(self, session=None):
        """Initialize pinger.

        :param session: a UUID session identifier
        """
        if session is None:
            self.session = uuid.uuid4()
        else:
            if not isinstance(session, uuid.UUID):
                raise ValueError('`session` should be a uuid.UUID object')
            self.session = session

    def send_container_ping(self, action, container, image_name, message=None):
        """Ping a status message of a container.

        :param action: one of 'start', 'stop', or 'update'.
        :param container: a docker `Container` object.
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
            "container_data": container.stats(stream=False),
            "image_data": image_name,
            "message": message},
            session=self.session)

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
        return _send_ping({
            "source": "notebook",
            "action": action,
            "notebook_name": notebook,
            "message": message},
            session=self.session)
