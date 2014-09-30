# vim:fileencoding=utf-8
import os

from codecs import open

import pytest

from docker_pull import DockerPuller


@pytest.fixture
def here():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def docker_images_text(here):
    with open(os.path.join(here, 'docker_images.txt')) as infile:
        return infile.read()


class FakeAnsibleModule(object):
    check_mode = False
    params = {}


def test_redis_pass(docker_images_text):
    """
    The official Redis image is curious, when pulled, the images that
    have seemingly been built most recently are the older images
    (2.8.[9-6]). The latest image, 2.8 / 2.8.13 comes after all of those.

    This test also ensures that 'tutum/redis' images is not deleted.
    """
    module = FakeAnsibleModule()
    module.params['repo'] = 'redis'
    module.params['tag'] = 'latest'
    module.params['keep_images'] = '3'

    puller = DockerPuller(module)

    test = puller._image_ids_for_removal(docker_images_text)
    expected = [
        '67b039bb2a0b', '90edc76cff8c', 'ee5226d9ed29',
        '4734b2f47317', '8c6a9dd0192a', 'e65fe09e1cd2'
    ]
    assert test == expected
    assert '214f80f63b0f' not in expected


def test_redis_fail(docker_images_text):
    """
    In this test, the image ids for 2.8.13, 2.8.12, and 2.8.11 are
    what are not deleted. This is what one would expect if the tag
    versions were respected. That could be done with help from
    distutils.version.

    This test also ensures that 'tutum/redis' images is not
    deleted.
    """
    module = FakeAnsibleModule()
    module.params['repo'] = 'redis'
    module.params['tag'] = 'latest'
    module.params['keep_images'] = '3'

    puller = DockerPuller(module)

    test = puller._image_ids_for_removal(docker_images_text)
    expected = [
        'e27d80fba3dd', '1a6a6bbf388d', '2cffbad5f0fb',
        '67b039bb2a0b', '90edc76cff8c', '8c6a9dd0192a', 'e65fe09e1cd2'
    ]
    assert test != expected
    assert '214f80f63b0f' not in expected


def test_tutum_pass(docker_images_text):
    """
    In this test, tutum/redis is up for pulling. As there is only
    one image of tutum/redis present, '_image_ids_for_removal'
    should return None.
    """
    module = FakeAnsibleModule()
    module.params['repo'] = 'tutum/redis'
    module.params['tag'] = 'latest'
    module.params['keep_images'] = '3'

    puller = DockerPuller(module)

    test = puller._image_ids_for_removal(docker_images_text)
    assert test is None
