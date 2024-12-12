import math
import requests

from django.utils.translation import gettext_lazy as _

from api.datasets.exceptions import TextPreviewFailed


def get_content_from_url_text(
        urls: list[str], 
        max_lines: int | None = 20,
        **kwargs) -> bytes:
    """
    Gets the preview from a json file url or list of urls
    validating column names and joining the file contents

    Returns:
        A string containing the first n lines from all given urls
    """

    assert len(urls) > 0, "It needs to be at least one url in the list"

    ml = 0 
    url_count = len(urls)
    if max_lines:
        ml = math.ceil(max_lines/url_count)

    content = []
    lines = 0
    for url in urls:
        r = requests.get(url, stream=True)

        if r.status_code != 200:
            raise TextPreviewFailed(detail=_("Invalid url or file/folder doesn't not exist"))

        for line in r.iter_lines():
            content.append(line)
            lines += 1

            if lines == ml:
                break

        if lines == ml:
            break

    return b"\n".join(content)


