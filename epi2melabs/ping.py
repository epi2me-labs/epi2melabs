"""Functions to send statistics to ONT."""

ENDPOINT = 'https://ping.oxfordnanoportal.com/epilaby'

def _send_ping(data):
    """Attempt to send a ping to home.

    :param data: a dictionary containing the data to send (should be
        json serializable).

    :returns: status code of HTTP request.
    """
    ping_version = '1.0.0'
    ping = {
        "tracking_id": {"msg_id": str(uuid.uuid4()), "version": ping_version},
        "hostname": socket.gethostname(), "os": platform.platform()}
    ping.update(data)
    try:
        r = requests.post(ENDPOINT, json=ping)
    except Exception as e:
        pass
    return r.status_code


def send_container_ping(action, container, image_name):
    """Ping a status message of a container.

    :param action: one of 'start', 'stop', or 'update'.
    :param container: a docker `Container` object.
    :param image_tag: the name of the image associated with the container.

    :returns: status code of HTTP request.
    """
    allowed_status = {"start", "stop", "update"}
    if action not in allowed_status:
        raise ValueError("`action` was not an allowed value.")
    return _send_ping({
        "source": "container"
        "action": action,
        "container_data": container.stats(stream=False),
        "image_data": image_name})


def send_notebook_ping(action, notebook, message=None):
    """Ping a message from a notebook."""

    allowed_status = {"start", "end", "update"}
    if action not in allowed_status:
        raise ValueError("`action` was not an allowed value.")
    return _send_ping({
        "source": "notebook"
        "action": action,
        "notebook_name": notebook,
        "message": image_name})
