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


@pytest.fixture
def docker_images2_text(here):
    with open(os.path.join(here, 'docker_images2.txt')) as infile:
        return infile.read()


@pytest.fixture
def docker_ps_text(here):
    with open(os.path.join(here, 'docker_ps.txt')) as infile:
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
    assert '214f80f63b0f' not in test


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
    assert '214f80f63b0f' not in test


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


def test_get_container_image_id():
    """
    Testing method that obtains the image_id from a given container id.
    """

    from docker_ps_images2_map import containers
    container_id = '6b76b45873ae'

    module = FakeAnsibleModule()
    module.params.update({
        'repo': 'redis',
        'tag': 'latest',
        'keep_images': '3',
    })

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           container_id)] = (
        0, containers[container_id], ''
    )

    puller = DockerPuller(module)

    test = puller._get_container_image_id(container_id)
    assert test == containers[container_id][0:12]


def test_get_container_image_ids(docker_images2_text, docker_ps_text):
    """
    Testing method that returns the unique set of image ids for existing
    containers. These containers may be running or stopped.
    """

    module = FakeAnsibleModule()
    module.params.update({
        'repo': 'redis',
        'tag': 'latest',
        'keep_images': '3',
    })

    module.known_commands[('docker', 'images')] = (
        0, docker_images2_text, ''
    )

    module.known_commands[('docker', 'ps', '-a')] = (
        0, docker_ps_text, ''
    )

    # Don't know how to setup docker_ps_images2_map for this, so setting
    # up the mapping between container ids and image ids explicitly here.

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           '6b76b45873ae')] = (
        0, "c260c5345f656b271a2d587641d1bda95dc7599a83016d7249ff241ca4a8a8c8",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           'c8b7beeebbf6')] = (
        0, "6b4e8a7373fe8706183f15dc367564a723710f2214cab23d14d195d8abd8eccb",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           '6b44562d0ff6')] = (
        0, "6b4e8a7373fe8706183f15dc367564a723710f2214cab23d14d195d8abd8eccb",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           'f71977673be2')] = (
        0, "75af0ca1d93cad44e4d00ffa7d6c74862dc7f29bf1afda75f80edfc47a65633e",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           'e9082a00a862')] = (
        0, "c260c5345f656b271a2d587641d1bda95dc7599a83016d7249ff241ca4a8a8c8",
        ''
    )

    puller = DockerPuller(module)

    test = puller._get_container_image_ids()
    expected = ["c260c5345f65", "6b4e8a7373fe", "75af0ca1d93c"]

    assert test == expected


def test_image_ids_for_removal(docker_images2_text, docker_ps_text):
    """
    Ensure the image for an existing redis container is not up for removal.
    """

    module = FakeAnsibleModule()
    module.params.update({
        'repo': 'redis',
        'tag': 'latest',
        'keep_images': '3',
    })

    module.known_commands[('docker', 'ps', '-a')] = (
        0, docker_ps_text, ''
    )

    # Don't know how to setup docker_ps_images2_map for this, so setting
    # up the mapping between container ids and image ids explicitly here.

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           '6b76b45873ae')] = (
        0, "c260c5345f656b271a2d587641d1bda95dc7599a83016d7249ff241ca4a8a8c8",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           'c8b7beeebbf6')] = (
        0, "6b4e8a7373fe8706183f15dc367564a723710f2214cab23d14d195d8abd8eccb",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           '6b44562d0ff6')] = (
        0, "6b4e8a7373fe8706183f15dc367564a723710f2214cab23d14d195d8abd8eccb",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           'f71977673be2')] = (
        0, "75af0ca1d93cad44e4d00ffa7d6c74862dc7f29bf1afda75f80edfc47a65633e",
        ''
    )

    module.known_commands[('docker', 'inspect', '-f', '{{.Image}}',
                           'e9082a00a862')] = (
        0, "c260c5345f656b271a2d587641d1bda95dc7599a83016d7249ff241ca4a8a8c8",
        ''
    )

    puller = DockerPuller(module)

    test = puller._image_ids_for_removal(docker_images2_text)
    expected = ["f541aeac052e", "62f7406e8c04", "2e688289a160", "ea499d1d68b3",
                "a6030cdaa9dc", "429efa892431", "08090e4e8c32", "52f0307b92f8",
                "3d290a494333"]

    assert test == expected
