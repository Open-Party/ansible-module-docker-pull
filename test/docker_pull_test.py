import unittest
import os
import os.path

import imp
imp.load_source('docker_pull', os.path.join(os.path.dirname(__file__), os.path.pardir, 'docker_pull'))

from docker_pull import DockerPuller

docker_images = """REPOSITORY                        TAG                 IMAGE ID            CREATED             VIRTUAL SIZE
redis                             2.8.9               e27d80fba3dd        41 hours ago        98.74 MB
redis                             2.8.8               1a6a6bbf388d        41 hours ago        98.66 MB
redis                             2.8.7               2cffbad5f0fb        41 hours ago        98.63 MB
redis                             2.8.6               67b039bb2a0b        41 hours ago        98.61 MB
redis                             2.8                 90edc76cff8c        41 hours ago        98.68 MB
redis                             2.8.13              90edc76cff8c        41 hours ago        98.68 MB
redis                             latest              90edc76cff8c        41 hours ago        98.68 MB
redis                             2.8.12              ee5226d9ed29        41 hours ago        98.61 MB
redis                             2.8.11              4734b2f47317        41 hours ago        98.75 MB
redis                             2.8.10              8c6a9dd0192a        41 hours ago        98.75 MB
redis                             2.6                 e65fe09e1cd2        41 hours ago        98.39 MB
redis                             2.6.17              e65fe09e1cd2        41 hours ago        98.39 MB
tutum/redis                       latest              214f80f63b0f        13 days ago         196.4 MB"""

class FakeAnsibleModule(object):
    check_mode = False
    params = {}
 
class TestSequenceFunctions(unittest.TestCase):

    def test_redis_pass(self):
        # The official Redis image is curious, when pulled, the images that
        # have seemingly been built first are the older images (2.8.[9-6]).
        # The latest image, 2.8 / 2.8.13 comes after all of those.
        # This test also ensures that 'tutum/redis' images is not deleted.
        module = FakeAnsibleModule()
        module.params['repo'] = "redis"
        module.params['tag'] = "latest"
        module.params['keep_images'] = "3"

        puller = DockerPuller(module)

        test = puller._image_ids_for_removal(docker_images)
        expected = ["67b039bb2a0b", "90edc76cff8c", "ee5226d9ed29", "4734b2f47317", "8c6a9dd0192a", "e65fe09e1cd2"]
        self.assertEqual(test, expected)        

    def test_redis_fail(self):
        # In this test, the image ids for 2.8.13, 2.8.12, and 2.8.11 are what
        # are not deleted. This is what one would expect if the tag versions
        # were respected. That could be done with help from distutils.version.
        module = FakeAnsibleModule()
        module.params['repo'] = "redis"
        module.params['tag'] = "latest"
        module.params['keep_images'] = "3"

        puller = DockerPuller(module)

        test = puller._image_ids_for_removal(docker_images)
        expected = ["e27d80fba3dd", "1a6a6bbf388d", "2cffbad5f0fb", "67b039bb2a0b", "90edc76cff8c", "8c6a9dd0192a", "e65fe09e1cd2"]
        self.assertNotEqual(test, expected)        

    def test_tutum_pass(self):
        # In this test, the image ids for 2.8.13, 2.8.12, and 2.8.11 are what
        # are not deleted. This is what one would expect if the tag versions
        # were respected.
        module = FakeAnsibleModule()
        module.params['repo'] = "tutum/redis"
        module.params['tag'] = "latest"
        module.params['keep_images'] = "3"

        puller = DockerPuller(module)

        test = puller._image_ids_for_removal(docker_images)
        self.assertIsNone(test)        

if __name__ == '__main__':
    unittest.main()

