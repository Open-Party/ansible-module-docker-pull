# vim:fileencoding=utf-8
import os

from codecs import open

import pytest

from docker_pull import DockerPuller, main


def setup():
    os.environ['PATH'] = ':'.join([
        os.path.join(here(), '..', '.binstubs'),
        os.environ['PATH']
    ])


@pytest.fixture
def here():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def docker_images_text(here):
    with open(os.path.join(here, 'docker_images.txt')) as infile:
        return infile.read()


class FakeAnsibleModule(object):
    check_mode = False

    def __init__(self, argument_spec=tuple(), supports_check_mode=False):
        self.argument_spec = argument_spec
        self.supports_check_mode = supports_check_mode
        self.params = {}
        self.known_commands = {}
        self.last_exit_json_kwargs = {}
        self.last_fail_json_kwargs = {}

    def fakeinit(self, argument_spec, supports_check_mode):
        self.argument_spec = argument_spec
        self.supports_check_mode = supports_check_mode
        return self

    def get_bin_path(self, exe, wat):
        return exe

    def run_command(self, cmd):
        self.last_cmd = cmd
        return self.known_commands.get(tuple(cmd), (0, '', ''))

    def exit_json(self, **kwargs):
        self.last_exit_json_kwargs = kwargs

    def fail_json(self, **kwargs):
        self.last_fail_json_kwargs = kwargs


def test_main(docker_images_text):
    module = FakeAnsibleModule()
    module.params.update({
        'repo': 'redis',
        'tag': 'latest',
        'keep_images': '2',
    })
    module.known_commands[('docker', 'images', '-q')] = (
        0, docker_images_text, ''
    )
    module.known_commands[('docker', 'images')] = (
        0, docker_images_text, ''
    )

    main(module.fakeinit)

    module.known_commands[('docker', 'images', '-q')] = (
        0, 'Usage:', ''
    )

    main(module.fakeinit)


def test_redis_pass(docker_images_text):
    """
    The official Redis image is curious, when pulled, the images that
    have seemingly been built most recently are the older images
    (2.8.[9-6]). The latest image, 2.8 / 2.8.13 comes after all of those.

    This test also ensures that 'tutum/redis' images is not deleted.
    """
    module = FakeAnsibleModule()
    module.params.update({
        'repo': 'redis',
        'tag': 'latest',
        'keep_images': '3',
    })

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
    module.params.update({
        'repo': 'redis',
        'tag': 'latest',
        'keep_images': '3',
    })

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
    module.params.update({
        'repo': 'tutum/redis',
        'tag': 'latest',
        'keep_images': '3',
    })

    puller = DockerPuller(module)

    test = puller._image_ids_for_removal(docker_images_text)
    assert test is None
